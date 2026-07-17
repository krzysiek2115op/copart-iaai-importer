# SPDX-License-Identifier: GPL-2.0-or-later
"""Dzial 1B — Pobieranie szczegolow: pola (auction-data-item) + zdjecia. Stdlib (regex)."""
import re
import html as _html
import logging
from . import config

log = logging.getLogger("polea.szczegoly")

_ITEM = re.compile(
    r'auction-data-label">(.*?)</div>\s*<div class="auction-data-value">(.*?)</div>',
    re.S | re.I,
)
_TAG = re.compile(r'<[^>]+>')
_OG = re.compile(r'og:description"[^>]*content="([^"]*)"', re.I)
_STATUS = re.compile(r'(Aukcja nr[^<]*)', re.I)
# Adres jest pod naglowkiem "Lokalizacja:", a NIE pod "WŁAŚCICIEL:" (ten sam blok).
_LOKAL = re.compile(r'Lokalizacja:\s*</h2>\s*<div class="mb-3">(.*?)</div>', re.S | re.I)
# Najnizsza cena z 30 dni (Omnibus) — blok "sidebar-data" na stronie szczegolu.
_CENA30 = re.compile(
    r'Najni[żz]sza cena z 30 dni:\s*</div>\s*<div>\s*<strong>\s*([\d\s\xa0]+?)\s*PLN',
    re.S | re.I,
)
_IMG = re.compile(r'sgallery_([0-9a-f-]{36})_\d+\.(?:png|jpe?g|webp)', re.I)
_CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')  # znaki sterujace C0 (bez \t \n \r)


def _clean(s, maxlen=1000):
    s = _TAG.sub(' ', s)
    s = _html.unescape(s).replace('\xa0', ' ')
    s = _CTRL.sub('', s)                       # usun znaki sterujace z niezaufanego HTML
    s = re.sub(r'\s+', ' ', s).strip()
    return s[:maxlen]                          # twardy limit dlugosci pola


def parse_detail(html_text, url):
    """Parsuje surowe pola (tekst) + zdjecia. Wyjscie -> Dzial 2 (normalizacja)."""
    raw = {"url": url}

    for lab, val in _ITEM.findall(html_text):
        label = _clean(lab)
        if label:
            raw[label] = _clean(val)

    og = _OG.search(html_text)
    raw["_og_description"] = _html.unescape(og.group(1)) if og else ""

    st = _STATUS.search(html_text)
    raw["_status_text"] = _clean(st.group(1)) if st else ""

    loc = _LOKAL.search(html_text)
    raw["_lokalizacja"] = _clean(loc.group(1)).strip(", ") if loc else ""

    c30 = _CENA30.search(html_text)
    raw["_cena_30d"] = c30.group(1) if c30 else ""

    keys = []
    for m in _IMG.finditer(html_text):
        k = m.group(1).lower()
        if k not in keys:
            keys.append(k)
    raw["_images"] = [
        {"image_key": k, "url": f"{config.BASE_URL}/images/sgallery_{k}_75.png", "sort_order": i}
        for i, k in enumerate(keys)
    ]
    return raw


def fetch_detail(fetcher, stub):
    raw = parse_detail(fetcher.get(stub["url"]), stub["url"])
    raw["lot_id"] = stub["lot_id"]
    raw["slug"] = stub["slug"]
    return raw
