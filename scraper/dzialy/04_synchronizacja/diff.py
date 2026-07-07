# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Importer Aukcji (IAAI + Copart).
# Licencja: GNU GPL v2 lub pozniejsza - pelny tekst w pliku LICENSE.
"""
Dział 4 · SYNCHRONIZACJA — agent `diff`  (+ krytyk `spójność`).

Porównuje przychodzące rekordy ze stanem w bazie po `raw_hash`:
  - brak w bazie            -> status `new`
  - jest, ale inny hash     -> status `changed`
  - jest, ten sam hash      -> status `unchanged`
(Wykrywanie `sold/removed` — loty w bazie nieobecne w feedzie — opcjonalnie --feed-complete.)

Wymagania: pip install pymysql
Użycie:   python diff.py --in out/dedup.jsonl --out out/diff.jsonl
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

from common import connect, compute_hash, tbl

_T_VEH = tbl("iaai_vehicles")  # prefiks WP na VPS (wp_iaai_vehicles); dev: iaai_vehicles


def diff_records(records: list[dict], conn) -> list[dict]:
    out = []
    with conn.cursor() as cur:
        for rec in records:
            h = compute_hash(rec)
            cur.execute(f"SELECT raw_hash FROM {_T_VEH} WHERE salvage_id=%s",
                        (rec.get("salvage_id"),))
            row = cur.fetchone()
            if row is None:
                status = "new"
            elif row[0] != h:
                status = "changed"
            else:
                status = "unchanged"
            rec = dict(rec, raw_hash=h, _sync_status=status)
            out.append(rec)
    return out


# ---- 🔴 KRYTYK: spójność --------------------------------------------------
def krytyk_spojnosc(records: list[dict]) -> list[str]:
    issues = []
    for rec in records:
        h = rec.get("raw_hash", "")
        if not re.fullmatch(r"[0-9a-f]{40}", h or ""):
            issues.append(f"{rec.get('salvage_id')}: raw_hash niepoprawny")
        if rec.get("_sync_status") not in ("new", "changed", "unchanged"):
            issues.append(f"{rec.get('salvage_id')}: nieznany status {rec.get('_sync_status')}")
        # hash musi być deterministyczny
        if compute_hash(rec) != h:
            issues.append(f"{rec.get('salvage_id')}: hash niestabilny")
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("out/diff.jsonl"))
    args = ap.parse_args()

    records = [json.loads(l) for l in args.infile.read_text().splitlines() if l.strip()]
    conn = connect()
    annotated = diff_records(records, conn)
    conn.close()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    counts = {"new": 0, "changed": 0, "unchanged": 0}
    with args.out.open("w", encoding="utf-8") as fh:
        for rec in annotated:
            counts[rec["_sync_status"]] = counts.get(rec["_sync_status"], 0) + 1
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[diff] new={counts['new']} changed={counts['changed']} unchanged={counts['unchanged']}")

    issues = krytyk_spojnosc(annotated)
    if issues:
        print("[krytyk:spójność] ZASTRZEŻENIA:")
        for i in issues[:20]:
            print("   -", i)
        sys.exit(1)
    print("[krytyk:spójność] OK ✅")
    print(f"[diff] zapisano -> {args.out}")


if __name__ == "__main__":
    main()
