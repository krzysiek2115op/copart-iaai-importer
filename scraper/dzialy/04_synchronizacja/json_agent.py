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


# ---- H1: upsert ZDJĘĆ do iaai_vehicle_images (klucz: image_key UNIQUE) -----
_IMG_COLS = ["salvage_id", "image_key", "seq", "width", "height", "url"]
_IMG_UPD = ["seq", "width", "height", "url"]
_IMG_INSERT = (f"INSERT INTO iaai_vehicle_images ({','.join('`'+c+'`' for c in _IMG_COLS)}) "
               f"VALUES ({','.join(['%s'] * len(_IMG_COLS))}) "
               f"ON DUPLICATE KEY UPDATE {','.join('`'+c+'`=%s' for c in _IMG_UPD)}")


def upsert_image(rec: dict, cur) -> int:
    ins = [rec.get(c) for c in _IMG_COLS]
    upd = [rec.get(c) for c in _IMG_UPD]
    cur.execute(_IMG_INSERT, ins + upd)
    return cur.rowcount


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
    ap.add_argument("--in", dest="infile", type=Path, required=True,
                    help="JSONL pojazdów (najlepiej po audycie — pole _audit_ok)")
    ap.add_argument("--images", type=Path, help="JSONL zdjęć z agenta `zdjecia` (H1)")
    ap.add_argument("--all", action="store_true", help="zapisz też 'unchanged' (domyślnie pomijane)")
    ap.add_argument("--reconcile", action="store_true",
                    help="M3: po PEŁNYM feedzie oznacz brakujące aktywne loty jako 'removed' "
                         "(używać TYLKO przy full backfill — nie przy live/incremental!)")
    args = ap.parse_args()

    records = [json.loads(l) for l in args.infile.read_text().splitlines() if l.strip()]
    conn = connect()
    inserted = updated = skipped = rejected = 0
    all_issues = []
    with conn.cursor() as cur:
        for rec in records:
            # H2: nie zapisuj rekordów odrzuconych przez audyt
            if rec.get("_audit_ok") is False:
                rejected += 1
                continue
            if rec.get("_sync_status") == "unchanged" and not args.all:
                skipped += 1
                continue
            n = upsert(rec, cur)
            if n == 1:
                inserted += 1
            elif n == 2:
                updated += 1
            all_issues += krytyk_poprawnosc_json(rec, cur)

        # H1: zdjęcia -> iaai_vehicle_images (po pojazdach, bo FK)
        img_ins = img_fail = 0
        if args.images and args.images.exists():
            for line in args.images.read_text().splitlines():
                if not line.strip():
                    continue
                try:
                    upsert_image(json.loads(line), cur)
                    img_ins += 1
                except Exception:
                    img_fail += 1      # np. brak pojazdu (FK) — pojazd odrzucony/niezapisany
        # M3: reconcile — loty active nieobecne w bieżącym (pełnym) feedzie -> removed
        removed = None
        if args.reconcile:
            current = [r["salvage_id"] for r in records
                       if r.get("_audit_ok") is not False and r.get("salvage_id")]
            if not current:
                print("[json] reconcile POMINIĘTY — puste wejście (zabezpieczenie)")
            else:
                cur.execute("CREATE TEMPORARY TABLE _iaai_seen (salvage_id BIGINT UNSIGNED PRIMARY KEY)")
                cur.executemany("INSERT IGNORE INTO _iaai_seen (salvage_id) VALUES (%s)",
                                [(i,) for i in current])
                cur.execute(
                    "UPDATE iaai_vehicles v LEFT JOIN _iaai_seen s ON v.salvage_id = s.salvage_id "
                    "SET v.status = 'removed' WHERE v.status = 'active' AND s.salvage_id IS NULL")
                removed = cur.rowcount
                cur.execute("DROP TEMPORARY TABLE _iaai_seen")
    conn.close()

    print(f"[json] wstawiono={inserted} zaktualizowano={updated} "
          f"pominięto(unchanged)={skipped} odrzucono(audyt)={rejected}")
    if removed is not None:
        print(f"[json] reconcile: oznaczono removed={removed}")
    if args.images:
        print(f"[json] zdjęcia: zapisano={img_ins} pominięto(FK/błąd)={img_fail}")
    if all_issues:
        print("[krytyk:poprawność-json] ZASTRZEŻENIA:")
        for i in all_issues[:20]:
            print("   -", i)
        sys.exit(1)
    print("[krytyk:poprawność-json] OK ✅ (odczyt zwrotny zgodny)")


if __name__ == "__main__":
    main()
