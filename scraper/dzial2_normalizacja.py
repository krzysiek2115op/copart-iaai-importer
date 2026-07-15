# SPDX-License-Identifier: GPL-2.0-or-later
"""Dzial 2 — Normalizacja: VIN (walidacja) + jednostki (tekst PL -> typy)."""
import re
from datetime import date

# Transliteracja VIN (ISO 3779 / FMVSS) — bez I, O, Q
_VIN_TRANS = {**{c: i for i, c in enumerate("0123456789")},
              **{c: v for c, v in zip("ABCDEFGHJKLMNPRSTUVWXYZ",
                 [1, 2, 3, 4, 5, 6, 7, 8, 1, 2, 3, 4, 5, 7, 9, 2, 3, 4, 5, 6, 7, 8, 9])}}
_VIN_WEIGHTS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]


def vin_valid(vin):
    """True gdy VIN 17-znakowy z poprawna cyfra kontrolna (poz. 9). Miekka flaga."""
    if not vin or len(vin) != 17:
        return False
    vin = vin.upper()
    if re.search(r'[IOQ]', vin):
        return False
    try:
        total = sum(_VIN_TRANS[c] * w for c, w in zip(vin, _VIN_WEIGHTS))
    except KeyError:
        return False
    check = total % 11
    return vin[8] == ('X' if check == 10 else str(check))


_CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')


def _txt(s, maxlen=255):
    """Tekst do bazy: usuwa znaki sterujace i przycina do dlugosci kolumny."""
    if s is None:
        return None
    s = _CTRL.sub('', str(s)).strip()
    return s[:maxlen] if s else None


def _int(s):
    if not s:
        return None
    m = re.search(r'\d[\d\s\xa0]*', s)
    return int(re.sub(r'[\s\xa0]', '', m.group(0))) if m else None


def _capint(v, hi):
    """Zdroworozsadkowy gorny limit (anty-absurd/overflow); None gdy brak."""
    if v is None:
        return None
    return v if v <= hi else hi


def _date(s):
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', s or "")
    if not m:
        return None
    try:
        return date(int(m[1]), int(m[2]), int(m[3])).isoformat()
    except ValueError:      # np. 2022-02-31 w niezaufanym HTML — nie wywalaj importu
        return None


def normalize(raw):
    """Surowy rekord (tekst) -> rekord zgodny ze schematem polea_motocykle."""
    g = raw.get
    vin = (g("VIN") or "").strip().upper() or None

    og = raw.get("_og_description", "")
    cena = None
    cm = re.search(r'cena:\s*([\d\s\xa0]+)\s*PLN', og)
    if cm:
        digits = re.sub(r'[\s\xa0]', '', cm.group(1))
        if digits.isdigit():                          # obrona przed float("") gdy "cena:  PLN"
            cena = min(float(digits), 1_000_000_000.0)  # gorny limit ceny (anty-absurd/overflow)
    netto = 1 if 'netto' in og.lower() else 0

    # Najnizsza cena z 30 dni (Omnibus) — wyciagana przez Dzial 1B z bloku sidebar-data.
    cena_30d = None
    d30 = re.sub(r'[\s\xa0]', '', raw.get("_cena_30d") or "")
    if d30.isdigit():
        cena_30d = min(float(d30), 1_000_000_000.0)

    st = raw.get("_status_text", "")
    term, status = None, "aktywna"
    m = re.search(r'zako[nń]czy[łl]a si[eę]\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', st)
    if m:
        term, status = m.group(1), "zakonczona"
    else:
        m2 = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', st)
        if m2:
            term = m2.group(1)

    return {
        "lot_id": _txt(raw.get("lot_id"), 32),
        "numer_aukcji": _txt(g("Numer aukcji"), 64),
        "slug": _txt(raw.get("slug"), 191),
        "url": _txt(raw.get("url"), 512),
        # Limity dlugosci ZGODNE ze schematem (db/schema.sql) — inaczej za dlugie pole
        # ze zrodla wywala cala transakcje zapisu (STRICT sql_mode -> "Data too long").
        "marka": _txt(g("Marka"), 64),
        "model": _txt(g("Model"), 128),
        "typ": _txt(g("Typ"), 64),
        "rok_produkcji": _int(g("Rok produkcji")),
        "data_pierwszej_rej": _date(g("Data pierwszej rejestracji")),
        "vin": _txt(vin, 20),
        "vin_valid": vin_valid(vin) if vin else False,
        "nr_rej": _txt(g("Nr rejestracyjny"), 32),
        "naped": _txt(g("Rodzaj napędu"), 64),
        "skrzynia": _txt(g("Skrzynia biegów"), 64),
        "moc_km": _capint(_int(g("Moc silnika")), 65535),   # P-1: cap = max SMALLINT UNSIGNED (kolumna moc_km); 100000 wywalało transakcję
        "pojemnosc_ccm": _capint(_int(g("Pojemność silnika")), 1000000),
        "paliwo": _txt(g("Paliwo"), 32),
        "przebieg_km": _capint(_int(g("Przebieg")), 100000000),
        "kolor": _txt(g("Kolor"), 64),
        "ilosc_kluczykow": _capint(_int(g("Ilość kluczyków")), 100),
        "forma_sprzedazy": _txt(g("Forma sprzedaży"), 64),
        "cena_pln": cena,
        "cena_netto": netto,
        "najnizsza_cena_30d": cena_30d,   # Omnibus — z bloku sidebar-data (potwierdzone na zywym HTML)
        # tryb_licytacji/liczba_ofert: brak jako statyczne pole (dane sa w JS) -> pozostaja puste.
        "tryb_licytacji": None,
        "lokalizacja": _txt(raw.get("_lokalizacja"), 255),
        "termin_zakonczenia": term,
        "status": status,
        "liczba_ofert": 0,
        "uwagi": None,
        "relist_of": None,          # ustawiane przez Dzial 3 (dedup po VIN); zapisywane przez Dzial 4
        "images": raw.get("_images", []),
    }
