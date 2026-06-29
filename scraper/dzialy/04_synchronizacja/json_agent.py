"""
Dział 4 · SYNCHRONIZACJA — agent `json`  (+ krytyk `poprawność-json`).

Zapisuje rekordy do nowej bazy (`iaai_vehicles`) przez upsert
`INSERT ... ON DUPLICATE KEY UPDATE` (wersja przenośna: parametry dwukrotnie).
Aktualizuje tylko `new`/`changed` (z agenta diff); ustawia `raw_hash`, `status='active'`.

Wymagania: pip install pymysql
Użycie:   python json_agent.py --in out/diff.jsonl
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

from common import connect, DATA_COLS, to_db_row, compute_hash

ALL_COLS = ["salvage_id"] + DATA_COLS + ["raw_hash", "status"]
UPD_COLS = DATA_COLS + ["raw_hash", "status"]
_INSERT = (f"INSERT INTO iaai_vehicles ({','.join('`'+c+'`' for c in ALL_COLS)}) "
           f"VALUES ({','.join(['%s'] * len(ALL_COLS))}) "
           f"ON DUPLICATE KEY UPDATE {','.join('`'+c+'`=%s' for c in UPD_COLS)}")


def upsert(rec: dict, cur) -> int:
    row = to_db_row(rec)
    h = rec.get("raw_hash") or compute_hash(rec)
    ins = [row["salvage_id"]] + [row[c] for c in DATA_COLS] + [h, "active"]
    upd = [row[c] for c in DATA_COLS] + [h, "active"]
    cur.execute(_INSERT, ins + upd)
    return cur.rowcount      # 1=insert, 2=update, 0=bez zmian


# ---- 🔴 KRYTYK: poprawność-json -------------------------------------------
def krytyk_poprawnosc_json(rec: dict, cur) -> list[str]:
    """Odczyt zwrotny: czy zapis odpowiada intencji (raw_hash + kluczowe pola)."""
    issues = []
    cur.execute("SELECT raw_hash, make, model, odometer FROM iaai_vehicles WHERE salvage_id=%s",
                (rec.get("salvage_id"),))
    row = cur.fetchone()
    if row is None:
        return [f"{rec.get('salvage_id')}: brak wiersza po zapisie"]
    want = rec.get("raw_hash") or compute_hash(rec)
    if row[0] != want:
        issues.append(f"{rec.get('salvage_id')}: raw_hash w bazie != zapisany")
    if rec.get("make") and str(row[1]) != str(rec["make"]):
        issues.append(f"{rec.get('salvage_id')}: make w bazie ({row[1]}) != ({rec['make']})")
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", type=Path, required=True)
    ap.add_argument("--all", action="store_true", help="zapisz też 'unchanged' (domyślnie pomijane)")
    args = ap.parse_args()

    records = [json.loads(l) for l in args.infile.read_text().splitlines() if l.strip()]
    conn = connect()
    inserted = updated = skipped = 0
    all_issues = []
    with conn.cursor() as cur:
        for rec in records:
            if rec.get("_sync_status") == "unchanged" and not args.all:
                skipped += 1
                continue
            n = upsert(rec, cur)
            if n == 1:
                inserted += 1
            elif n == 2:
                updated += 1
            all_issues += krytyk_poprawnosc_json(rec, cur)
    conn.close()

    print(f"[json] wstawiono={inserted} zaktualizowano={updated} pominięto(unchanged)={skipped}")
    if all_issues:
        print("[krytyk:poprawność-json] ZASTRZEŻENIA:")
        for i in all_issues[:20]:
            print("   -", i)
        sys.exit(1)
    print("[krytyk:poprawność-json] OK ✅ (odczyt zwrotny zgodny)")


if __name__ == "__main__":
    main()
