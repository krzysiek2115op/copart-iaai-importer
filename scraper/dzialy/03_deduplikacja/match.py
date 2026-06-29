"""
Dział 3 · DEDUPLIKACJA — agent `match`  (+ krytyk `fałszywe-trafienia`).

Wykrywa duplikaty, by to samo auto nie wpadło do bazy dwa razy. Polityka (ważna,
bo VIN anonimowo jest maskowany):

  1) `salvage_id` — PEWNY klucz lotu. Dokładne duplikaty usuwamy.
  2) pełny VIN (NIE zamaskowany, 17 znaków) — to samo fizyczne auto wystawione
     ponownie pod innym lotem => grupa „relist" (oznaczamy, nie kasujemy).
  3) dopasowanie miękkie (ta sama marka/model/rok/przebieg/oddział) => KANDYDAT
     do weryfikacji. NIE łączymy automatycznie (różne auta mogą być podobne).

Krytyk pilnuje, żeby nie powstało FAŁSZYWE połączenie (merge różnych aut).

Wymagania: brak (stdlib)
Użycie:   python match.py --in out/norm_jedn.jsonl --out out/dedup.jsonl
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path


def _full_vin(rec: dict) -> str | None:
    v = rec.get("vin")
    if v and not rec.get("vin_masked") and "*" not in v and len(v) == 17:
        return v
    return None


def deduplicate(records: list[dict]):
    by_id, exact_dups = {}, []
    for r in records:
        sid = r.get("salvage_id")
        if sid in by_id:
            exact_dups.append(sid)
            continue
        by_id[sid] = r
    uniques = list(by_id.values())

    # grupy „relist" po PEŁNYM VIN
    vin_groups = {}
    for r in uniques:
        v = _full_vin(r)
        if v:
            vin_groups.setdefault(v, []).append(r["salvage_id"])
    relists = {v: ids for v, ids in vin_groups.items() if len(ids) > 1}

    # miękkie dopasowania (kandydaci, NIE auto-merge)
    soft = {}
    for r in uniques:
        key = (str(r.get("make")).lower(), str(r.get("model")).lower(),
               r.get("year"), r.get("odometer"), r.get("selling_branch"))
        if all(k not in (None, "none", "") for k in key):
            soft.setdefault(key, []).append(r["salvage_id"])
    candidates = {" | ".join(map(str, k)): ids for k, ids in soft.items() if len(ids) > 1}

    # oznacz rekordy
    relist_of = {sid: ids for ids in relists.values() for sid in ids}
    cand_of = {sid: ids for ids in candidates.values() for sid in ids}
    for r in uniques:
        sid = r["salvage_id"]
        r["relist_group"] = [x for x in relist_of.get(sid, []) if x != sid] or None
        r["dup_candidates"] = [x for x in cand_of.get(sid, []) if x != sid] or None

    report = {"in": len(records), "unique": len(uniques),
              "exact_dups": exact_dups, "relists": relists, "soft_candidates": candidates}
    return uniques, report


# ---- 🔴 KRYTYK: fałszywe-trafienia ----------------------------------------
def krytyk_falszywe_trafienia(report: dict) -> list[str]:
    """Pilnuje, by nie doszło do błędnego połączenia różnych aut."""
    issues = []
    # relisty muszą opierać się na PEŁNYM VIN (deduplicate już to gwarantuje) —
    # tu ostrzegamy o miękkich kandydatach, których NIE wolno łączyć automatycznie
    for key, ids in report.get("soft_candidates", {}).items():
        issues.append(f"miękki kandydat (NIE łączyć auto): [{key}] -> loty {ids}")
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("out/dedup.jsonl"))
    args = ap.parse_args()

    records = [json.loads(l) for l in args.infile.read_text().splitlines() if l.strip()]
    uniques, report = deduplicate(records)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as fh:
        for r in uniques:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[match] wejście {report['in']} -> unikalnych {report['unique']} "
          f"(dokładne duplikaty: {len(report['exact_dups'])})")
    print(f"[match] grupy relist (pełny VIN): {len(report['relists'])} "
          f"| miękcy kandydaci: {len(report['soft_candidates'])}")
    for v, ids in report["relists"].items():
        print(f"   relist VIN {v}: loty {ids}")

    issues = krytyk_falszywe_trafienia(report)
    if issues:
        print("[krytyk:fałszywe-trafienia] do WERYFIKACJI (nie łączono automatycznie):")
        for i in issues:
            print("   -", i)
    else:
        print("[krytyk:fałszywe-trafienia] brak ryzykownych dopasowań ✅")
    print(f"[match] zapisano -> {args.out}")


if __name__ == "__main__":
    main()
