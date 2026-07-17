# SPDX-License-Identifier: GPL-2.0-or-later
"""Dzial 3 — Deduplikacja: unikat lot_id + relist po PELNYM, poprawnym VIN."""
import logging

log = logging.getLogger("polea.dedup")


def deduplicate(records):
    """Usuwa powtorki lot_id; oznacza relisty (ten sam VIN, nowy lot_id) polem relist_of."""
    by_lot = {r["lot_id"]: r for r in records}  # unikat lot_id (ostatni wygrywa)
    recs = list(by_lot.values())

    vin_map = {}
    for r in recs:
        vin = r.get("vin")
        if vin and r.get("vin_valid"):  # NIGDY nie laczymy po pustym/niepoprawnym VIN
            vin_map.setdefault(vin, []).append(r)

    for vin, group in vin_map.items():
        if len(group) > 1:
            group.sort(key=lambda r: r.get("termin_zakonczenia") or "")
            newest = group[-1]["lot_id"]
            for r in group:
                r["relist_of"] = None if r["lot_id"] == newest else newest
            log.info("Relist VIN %s: %s lotow (najnowszy %s).", vin, len(group), newest)
    return recs
