# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Importer Aukcji (IAAI + Copart).
# Licencja: GNU GPL v2 lub pozniejsza - pelny tekst w pliku LICENSE.
"""
Dział 4 · SYNCHRONIZACJA — agent `json`  (+ krytyk `poprawność-json`).

Zapisuje rekordy do nowej bazy (`iaai_vehicles`) przez upsert
`INSERT ... ON DUPLICATE KEY UPDATE` (wersja przenośna: parametry dwukrotnie).
Aktualizuje tylko `new`/`changed` (z agenta diff); ustawia `raw_hash`, `status='active'`.

Wymagania: pip install pymysql
Użycie:   python json_agent.py --in out/diff.jsonl
"""
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path

# P1: prog bezpieczenstwa reconcile — nie oznaczaj masowo lotow jako 'removed', gdy biezacy
# feed pokrywa mniej niz ten ulamek dotychczas AKTYWNYCH lotow danego zrodla (prawdopodobnie
# zawezony --base albo urwany crawl). Konfigurowalny; 0.9 = wymagaj niemal pelnego pokrycia.
RECONCILE_MIN_RATIO = float(os.environ.get("IAAI_RECONCILE_MIN_RATIO", "0.9"))

from common import connect, DATA_COLS, to_db_row, compute_hash, tbl

# Tabele z prefiksem WP (na VPS: wp_iaai_*; dev: iaai_*). Patrz common.tbl().
_T_VEH = tbl("iaai_vehicles")
_T_IMG = tbl("iaai_vehicle_images")

# `source` (iaai/copart) jest częścią klucza — wstawiany, ale NIE aktualizowany.
ALL_COLS = ["salvage_id", "source"] + DATA_COLS + ["raw_hash", "status"]
UPD_COLS = DATA_COLS + ["raw_hash", "status"]
_INSERT = (f"INSERT INTO {_T_VEH} ({','.join('`'+c+'`' for c in ALL_COLS)}) "
           f"VALUES ({','.join(['%s'] * len(ALL_COLS))}) "
           f"ON DUPLICATE KEY UPDATE {','.join('`'+c+'`=%s' for c in UPD_COLS)}")


def upsert(rec: dict, cur, source: str = "iaai") -> int:
    row = to_db_row(rec)
    h = rec.get("raw_hash") or compute_hash(rec)
    ins = [row["salvage_id"], source] + [row[c] for c in DATA_COLS] + [h, "active"]
    upd = [row[c] for c in DATA_COLS] + [h, "active"]
    cur.execute(_INSERT, ins + upd)
    return cur.rowcount      # 1=insert, 2=update, 0=bez zmian


# ---- H1: upsert ZDJĘĆ do iaai_vehicle_images (klucz: source+image_key UNIQUE) -----
_IMG_COLS = ["salvage_id", "source", "image_key", "seq", "width", "height", "url"]
_IMG_UPD = ["seq", "width", "height", "url"]
_IMG_INSERT = (f"INSERT INTO {_T_IMG} ({','.join('`'+c+'`' for c in _IMG_COLS)}) "
               f"VALUES ({','.join(['%s'] * len(_IMG_COLS))}) "
               f"ON DUPLICATE KEY UPDATE {','.join('`'+c+'`=%s' for c in _IMG_UPD)}")


def upsert_image(rec: dict, cur, source: str = "iaai") -> int:
    rec.setdefault("source", source)
    ins = [rec.get(c) for c in _IMG_COLS]
    upd = [rec.get(c) for c in _IMG_UPD]
    cur.execute(_IMG_INSERT, ins + upd)
    return cur.rowcount


# ---- 🔴 KRYTYK: poprawność-json -------------------------------------------
def krytyk_poprawnosc_json(rec: dict, cur, source: str = "iaai") -> list[str]:
    """Odczyt zwrotny: czy zapis odpowiada intencji (raw_hash + kluczowe pola)."""
    issues = []
    cur.execute(f"SELECT raw_hash, make, model, odometer FROM {_T_VEH} WHERE salvage_id=%s AND source=%s",
                (rec.get("salvage_id"), source))
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
    ap.add_argument("--source", choices=["iaai", "copart"], default="iaai",
                    help="źródło danych — zapisywane do kolumny `source`; reconcile ograniczony do tego źródła")
    args = ap.parse_args()
    source = args.source

    records = [json.loads(l) for l in args.infile.read_text().splitlines() if l.strip()]
    conn = connect()
    inserted = updated = skipped = rejected = failed = 0
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
            # Odporność: pojedynczy zły rekord (np. wartość za długa dla kolumny, brak
            # salvage_id) NIE może wywrócić całego importu — pomijamy go i liczymy.
            try:
                n = upsert(rec, cur, source)
                if n == 1:
                    inserted += 1
                elif n == 2:
                    updated += 1
                all_issues += krytyk_poprawnosc_json(rec, cur, source)
            except Exception as e:
                failed += 1
                print(f"[json] POMINIĘTO rekord salvage_id={rec.get('salvage_id')}: {e}",
                      file=sys.stderr)
                continue

        # H1: zdjęcia -> iaai_vehicle_images (po pojazdach). Grupujemy po locie, by po
        # upsercie PRZYCIĄĆ nieaktualne zdjęcia (zestaw się skurczył — inaczej stare
        # image_key/wysokie seq zostają w galerii). Prune tylko gdy mamy klucze (pusty
        # zestaw = możliwy chwilowy błąd; nie czyścimy wtedy całej galerii).
        img_ins = img_fail = img_pruned = 0
        if args.images and args.images.exists():
            by_lot: dict = {}
            for line in args.images.read_text().splitlines():
                if not line.strip():
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    img_fail += 1
                    continue
                by_lot.setdefault(r.get("salvage_id"), []).append(r)
            for sid, imgs in by_lot.items():
                keys = []
                for r in imgs:
                    try:
                        upsert_image(r, cur, source)
                        img_ins += 1
                        if r.get("image_key") is not None:
                            keys.append(r["image_key"])
                    except Exception:
                        img_fail += 1      # np. brak pojazdu — pojazd odrzucony/niezapisany
                if keys:
                    fmt = ",".join(["%s"] * len(keys))
                    cur.execute(
                        f"DELETE FROM {_T_IMG} WHERE salvage_id=%s AND source=%s "
                        f"AND image_key NOT IN ({fmt})", [sid, source, *keys])
                    img_pruned += cur.rowcount
        # M3: reconcile — loty active nieobecne w bieżącym (pełnym) feedzie -> removed
        removed = None
        if args.reconcile:
            # P2: "widziany" = OBECNY w feedzie (lot nadal wystawiony), niezależnie od wyniku
            # audytu. Rekord, który obleje audyt tego przebiegu, NIE jest zniknięty — wykluczenie
            # go z `current` powodowało fałszywe status='removed' i zdejmowanie wpisu ze strony.
            current = [r["salvage_id"] for r in records if r.get("salvage_id")]
            seen = len(set(current))
            # P1: policz aktualnie aktywne loty TEGO źródła i wymagaj, by feed pokrywał
            # co najmniej RECONCILE_MIN_RATIO z nich. Zawężony --base (np. ?Keyword=BMW)
            # albo urwany crawl (Copart 1 strona) → seen << active → reconcile POMINIĘTY,
            # zamiast błędnie zdejmować całą resztę oferty. Pusta baza (pierwszy backfill) → przepuść.
            cur.execute(f"SELECT COUNT(*) FROM {_T_VEH} WHERE status='active' AND source=%s", (source,))
            active_now = int((cur.fetchone() or [0])[0] or 0)
            if not current:
                print("[json] reconcile POMINIĘTY — puste wejście (zabezpieczenie)")
            elif active_now > 0 and seen < RECONCILE_MIN_RATIO * active_now:
                print(f"[json] reconcile POMINIĘTY — feed pokrywa {seen} lotów < "
                      f"{RECONCILE_MIN_RATIO:.0%} aktywnych={active_now} (source={source}); "
                      f"możliwy zawężony --base lub urwany crawl.", file=sys.stderr)
            else:
                cur.execute("CREATE TEMPORARY TABLE _iaai_seen (salvage_id BIGINT UNSIGNED PRIMARY KEY)")
                cur.executemany("INSERT IGNORE INTO _iaai_seen (salvage_id) VALUES (%s)",
                                [(i,) for i in current])
                cur.execute(
                    f"UPDATE {_T_VEH} v LEFT JOIN _iaai_seen s ON v.salvage_id = s.salvage_id "
                    "SET v.status = 'removed' WHERE v.status = 'active' AND v.source = %s AND s.salvage_id IS NULL",
                    (source,))
                removed = cur.rowcount
                cur.execute("DROP TEMPORARY TABLE _iaai_seen")
    conn.close()

    print(f"[json] wstawiono={inserted} zaktualizowano={updated} "
          f"pominięto(unchanged)={skipped} odrzucono(audyt)={rejected} błędy={failed}")
    if removed is not None:
        print(f"[json] reconcile: oznaczono removed={removed}")
    if args.images:
        print(f"[json] zdjęcia: zapisano={img_ins} pominięto(FK/błąd)={img_fail} przycięto(nieaktualne)={img_pruned}")
    if all_issues:
        print("[krytyk:poprawność-json] ZASTRZEŻENIA:")
        for i in all_issues[:20]:
            print("   -", i)
        sys.exit(1)
    print("[krytyk:poprawność-json] OK ✅ (odczyt zwrotny zgodny)")


if __name__ == "__main__":
    main()
