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
    "status", "liczba_ofert", "uwagi", "raw_hash",
]


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


def sync(records, conn=None):
    """Upsert lotow + zdjec, potem reconcile (nieobecne aktywne -> zakonczona)."""
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
            reconciled = 0
            if seen:
                fmt = ",".join(["%s"] * len(seen))
                cur.execute(
                    f"UPDATE polea_motocykle SET status='zakonczona' "
                    f"WHERE status='aktywna' AND lot_id NOT IN ({fmt})", seen)
                reconciled = cur.rowcount
        conn.commit()
        log.info("Zapis: %s lotow; reconcile: %s zamknietych.", len(records), reconciled)
    except Exception:
        conn.rollback()
        raise
    finally:
        if close:
            conn.close()
