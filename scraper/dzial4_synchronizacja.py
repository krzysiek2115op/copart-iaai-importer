# SPDX-License-Identifier: GPL-2.0-or-later
"""Dzial 4 — Synchronizacja: raw_hash (diff) + upsert + reconcile do bazy polea_*."""
import os
import hashlib
import json
import logging
from . import config

log = logging.getLogger("polea.sync")

_FIELDS = [
    "lot_id", "numer_aukcji", "slug", "url", "marka", "model", "typ", "rok_produkcji",
    "data_pierwszej_rej", "vin", "nr_rej", "naped", "skrzynia", "moc_km", "pojemnosc_ccm",
    "paliwo", "przebieg_km", "kolor", "ilosc_kluczykow", "forma_sprzedazy", "cena_pln",
    "cena_netto", "najnizsza_cena_30d", "tryb_licytacji", "lokalizacja", "termin_zakonczenia",
    "status", "liczba_ofert", "uwagi", "relist_of", "raw_hash",
]

# Prog bezpieczenstwa reconcile: nie zamykaj masowo aukcji, gdy biezacy przebieg
# "widzi" mniej niz ten ulamek dotychczas aktywnych (prawdopodobnie urwany/pusty crawl).
RECONCILE_MIN_RATIO = float(os.environ.get("POLEA_RECONCILE_MIN_RATIO", "0.5"))


def raw_hash(rec):
    """MD5 znormalizowanego rekordu (bez pol meta) — stabilny, do wykrywania zmian."""
    payload = {k: rec.get(k) for k in _FIELDS if k != "raw_hash"}
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.md5(blob.encode("utf-8")).hexdigest()


def connect():
    import pymysql  # leniwy import — potrzebny tylko przy realnym zapisie
    kw = dict(
        charset="utf8mb4",
        autocommit=False,
        local_infile=False,  # obrona przed LOAD DATA LOCAL ze zlosliwego serwera
        connect_timeout=int(os.environ.get("POLEA_DB_CONNECT_TIMEOUT", "10")),
        read_timeout=int(os.environ.get("POLEA_DB_READ_TIMEOUT", "30")),
        write_timeout=int(os.environ.get("POLEA_DB_WRITE_TIMEOUT", "30")),
        **config.DB,
    )
    ca = os.environ.get("POLEA_DB_SSL_CA")
    if ca:  # opcjonalny TLS do zdalnej bazy
        kw["ssl"] = {"ca": ca}
    return pymysql.connect(**kw)


def sync(records, conn=None, present_ids=None, reconcile=True):
    """Upsert lotow + zdjec, potem reconcile (nieobecne aktywne -> zakonczona).

    present_ids: pelny zbior lot_id ogloszonych na LISCIE zrodla (z crawla). Reconcile
        zamyka tylko aukcje spoza tego zbioru — lot wciaz ogloszony, ale z chwilowym
        bledem detalu/audytu NIE zostanie zamkniety. Gdy None -> baza = faktycznie zapisane.
    reconcile: False wylacza reconcile (np. przebieg czesciowy z --limit)."""
    close = conn is None
    if conn is None:
        conn = connect()
    seen = []
    cols = ",".join(_FIELDS)
    ph = ",".join(["%s"] * len(_FIELDS))
    upd = ",".join(f"{c}=VALUES({c})" for c in _FIELDS if c != "lot_id")
    sql_lot = (f"INSERT INTO polea_motocykle ({cols}) VALUES ({ph}) "
               f"ON DUPLICATE KEY UPDATE {upd}, last_seen=CURRENT_TIMESTAMP")
    sql_img = ("INSERT INTO polea_zdjecia (lot_id,image_key,url,sort_order) VALUES (%s,%s,%s,%s) "
               "ON DUPLICATE KEY UPDATE url=VALUES(url), sort_order=VALUES(sort_order)")
    try:
        with conn.cursor() as cur:
            for rec in records:
                rec["raw_hash"] = raw_hash(rec)
                seen.append(rec["lot_id"])
                cur.execute(sql_lot, [rec.get(c) for c in _FIELDS])
                for img in rec.get("images", []):
                    cur.execute(sql_img, (rec["lot_id"], img["image_key"], img["url"], img["sort_order"]))

            # Podstawa reconcile: pelna lista z crawla, jesli podana; inaczej faktycznie zapisane.
            present = list(present_ids) if present_ids is not None else seen
            reconciled = 0
            if reconcile and present:
                cur.execute("SELECT COUNT(*) FROM polea_motocykle WHERE status='aktywna'")
                active_now = int((cur.fetchone() or [0])[0] or 0)
                if active_now == 0 or len(set(present)) >= RECONCILE_MIN_RATIO * active_now:
                    uniq = list(set(present))
                    fmt = ",".join(["%s"] * len(uniq))
                    cur.execute(
                        f"UPDATE polea_motocykle SET status='zakonczona' "
                        f"WHERE status='aktywna' AND lot_id NOT IN ({fmt})", uniq)
                    reconciled = cur.rowcount
                else:
                    log.warning("Reconcile POMINIETY: widziano %s lotow < %.0f%% aktywnych=%s "
                                "(mozliwy urwany crawl).", len(set(present)),
                                RECONCILE_MIN_RATIO * 100, active_now)
        conn.commit()
        log.info("Zapis: %s lotow; reconcile: %s zamknietych.", len(records), reconciled)
    except Exception:
        conn.rollback()
        raise
    finally:
        if close:
            conn.close()
