# SPDX-License-Identifier: GPL-2.0-or-later
"""Dzial 1A — Pobieranie listy: crawl kategorii ecr_motorcycles -> stuby lotow."""
import re
import logging
from . import config

log = logging.getLogger("polea.lista")

# Reklamy partnerow linkuja poza wzorzec /pl/auctions/details/<slug>/<lot_id>,
# wiec ten regex naturalnie je pomija.
_DETAIL = re.compile(r'/pl/auctions/details/([^/"?\s]+)/([^/"?\s]+)')


def parse_list_page(html):
    """Zwraca liste stubow (lot_id, slug, url) z jednej strony listy (unikat lot_id)."""
    seen = {}
    for slug, lot_id in _DETAIL.findall(html):
        if lot_id not in seen:
            seen[lot_id] = {
                "lot_id": lot_id,
                "slug": slug,
                "url": f"{config.BASE_URL}/pl/auctions/details/{slug}/{lot_id}",
            }
    return list(seen.values())


def crawl_list(fetcher):
    """Przechodzi ?page=N az do wyczerpania (brak nowych lotow). Zwraca liste stubow."""
    stubs = {}
    for page in range(1, config.MAX_PAGES + 1):
        url = f"{config.BASE_URL}{config.CATEGORY_PATH}?page={page}"
        html = fetcher.get(url)
        new = [s for s in parse_list_page(html) if s["lot_id"] not in stubs]
        if not new:
            log.info("Strona %s: brak nowych lotow — koniec paginacji.", page)
            break
        for s in new:
            stubs[s["lot_id"]] = s
        log.info("Strona %s: +%s lotow (razem %s).", page, len(new), len(stubs))
    return list(stubs.values())
