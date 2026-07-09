# SPDX-License-Identifier: GPL-2.0-or-later
"""Orkiestrator pipeline'u: 1A crawl -> 1B szczegoly -> 2 norm -> 5 audyt -> 3 dedup -> 4 zapis."""
import argparse
import logging
import os

from . import config
from .dzial1a_lista import crawl_list
from .dzial1b_szczegoly import fetch_detail
from .dzial2_normalizacja import normalize
from .dzial3_deduplikacja import deduplicate
from .dzial5_audyt import audit

log = logging.getLogger("polea.main")


def run(limit=None, dry_run=False):
    from .dzial7_zgodnosc import Fetcher, BlockedError  # leniwy (wymaga requests)
    fetcher = Fetcher()
    stubs = crawl_list(fetcher)
    if limit:
        stubs = stubs[:limit]
    log.info("Do pobrania: %s lotow.", len(stubs))

    records = []
    for i, stub in enumerate(stubs, 1):
        try:
            raw = fetch_detail(fetcher, stub)
        except BlockedError as e:
            log.error("Blokada przy %s: %s — przerywam.", stub["url"], e)
            break
        except Exception as e:
            log.warning("Pominieto %s: %s", stub["url"], e)
            continue
        rec = normalize(raw)
        ok, errs = audit(rec)
        if not ok:
            log.warning("Audyt odrzucil %s: %s", rec.get("lot_id"),
                        [m for s, m in errs if s == "hard"])
            continue
        records.append(rec)
        log.info("[%s/%s] OK %s %s", i, len(stubs), rec.get("marka"), rec.get("model"))

    records = deduplicate(records)
    log.info("Po deduplikacji: %s rekordow.", len(records))

    if dry_run:
        log.info("DRY-RUN — pomijam zapis do bazy.")
        return records

    from . import dzial4_synchronizacja as sync_mod  # leniwy (wymaga PyMySQL)
    sync_mod.sync(records)
    return records


def _acquire_lock():
    """Blokada pojedynczej instancji (cron) — flock nieblokujacy. None gdy juz dziala inny import."""
    import fcntl
    f = open(config.LOCK_PATH, "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        return None
    f.write(str(os.getpid()))
    f.flush()
    return f  # trzymamy referencje otwarta -> lock aktywny do konca procesu


def main():
    ap = argparse.ArgumentParser(description="Importer motocykli poleasingowe.pl -> baza polea_*")
    ap.add_argument("--limit", type=int, default=None, help="pobierz max N lotow (test)")
    ap.add_argument("--dry-run", action="store_true", help="bez zapisu do bazy")
    ap.add_argument("--no-lock", action="store_true", help="pomin blokade pojedynczej instancji")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if a.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    lock = None
    if not a.no_lock:
        lock = _acquire_lock()
        if lock is None:
            log.error("Inny import juz dziala (lock %s) — przerywam.", config.LOCK_PATH)
            raise SystemExit(1)
    try:
        run(limit=a.limit, dry_run=a.dry_run)
    finally:
        if lock is not None:
            lock.close()


if __name__ == "__main__":
    main()
