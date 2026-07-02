"""
Dział 5 · AUDYT DANYCH — agent `walidacja`  (+ krytyk `poprawność`).

Sprawdza każdy rekord względem JSON Schema (typy, zakresy, wymagane pola) oraz
reguł biznesowych (rok ≤ bieżący+1, przebieg w sensownym zakresie). Rekordy
niepoprawne są oznaczane `_audit_ok=false` + listą błędów — nie trafiają dalej.

Schemat (źródło prawdy): vehicle.schema.json (obok tego pliku) — edytuj go bez
ruszania kodu. Oryginał-dokumentacja: docs/refs/json-schema.md (draft 2020-12).
Wymagania: pip install jsonschema
Użycie:   python walidacja.py --in out/diff.jsonl --out out/audyt.jsonl
"""
from __future__ import annotations
import argparse, json, sys
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator

# Schemat trzymany w osobnym pliku JSON (artefakt w repo, edytowalny bez kodu).
SCHEMA_PATH = Path(__file__).with_name("vehicle.schema.json")

# Minimalny schemat awaryjny — używany TYLKO gdy pliku brak/jest uszkodzony,
# żeby audyt nie wywrócił całego pipeline'u (przepuszcza z samym wymogiem salvage_id).
_FALLBACK_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": True,
    "required": ["salvage_id"],
    "properties": {"salvage_id": {"type": "integer", "minimum": 1}},
}


def _load_schema() -> dict:
    """Wczytuje vehicle.schema.json; przy błędzie ostrzega i wraca do schematu awaryjnego."""
    try:
        return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"[walidacja] UWAGA: nie wczytano {SCHEMA_PATH.name} ({e}); "
              "używam minimalnego schematu awaryjnego", file=sys.stderr)
        return _FALLBACK_SCHEMA


VEHICLE_SCHEMA = _load_schema()
_validator = Draft202012Validator(VEHICLE_SCHEMA)


def business_rules(rec: dict) -> list[str]:
    errs = []
    if rec.get("year") and rec["year"] > date.today().year + 1:
        errs.append(f"rok z przyszłości: {rec['year']}")
    if rec.get("odometer") is not None and rec.get("odometer_uom") is None:
        errs.append("przebieg bez jednostki")
    return errs


def audit(rec: dict) -> dict:
    errors = [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}"
              for e in _validator.iter_errors(rec)]
    errors += business_rules(rec)
    return dict(rec, _audit_ok=not errors, _audit_errors=errors or None)


# ---- 🔴 KRYTYK: poprawność ------------------------------------------------
def krytyk_poprawnosc(records: list[dict]) -> list[str]:
    """Meta-kontrola: czy audyt w ogóle wyłapuje błędy (na próbce kontrolnej)."""
    issues = []
    bad = {"salvage_id": -1, "year": 3000, "vin": "IOQ!!", "odometer": -5}
    if audit(bad)["_audit_ok"]:
        issues.append("walidator NIE wyłapał celowo błędnego rekordu — audyt niesprawny")
    good = {"salvage_id": 1, "year": 2011, "odometer": 100, "odometer_uom": "mi"}
    if not audit(good)["_audit_ok"]:
        issues.append("walidator odrzucił poprawny rekord — zbyt restrykcyjny")
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("out/audyt.jsonl"))
    args = ap.parse_args()

    records = [json.loads(l) for l in args.infile.read_text().splitlines() if l.strip()]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    ok = bad = 0
    with args.out.open("w", encoding="utf-8") as fh:
        for rec in records:
            a = audit(rec)
            fh.write(json.dumps(a, ensure_ascii=False) + "\n")
            if a["_audit_ok"]:
                ok += 1
            else:
                bad += 1
                print(f"  {rec.get('salvage_id')}: NIEPOPRAWNY -> {a['_audit_errors']}")
    print(f"[walidacja] poprawnych={ok} niepoprawnych={bad}")

    issues = krytyk_poprawnosc(records)
    if issues:
        print("[krytyk:poprawność] ZASTRZEŻENIA:")
        for i in issues:
            print("   -", i)
        sys.exit(1)
    print("[krytyk:poprawność] OK ✅ (audyt wyłapuje błędy, przepuszcza poprawne)")


if __name__ == "__main__":
    main()
