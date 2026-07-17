# SPDX-License-Identifier: GPL-2.0-or-later
"""Dodatkowe testy brzegowe/regresyjne (audyt przedwdrozeniowy plugin-2).
Cel: luki pokrycia i potencjalne bledy, ktorych nie dotykaja test_scraper/test_pipeline.
Stdlib only (bez sieci i bazy)."""
import unittest

from scraper import config
from scraper.dzial1a_lista import parse_list_page, crawl_list
from scraper.dzial1b_szczegoly import parse_detail
from scraper.dzial2_normalizacja import normalize, vin_valid, _int, _capint, _date
from scraper.dzial3_deduplikacja import deduplicate
from scraper.dzial4_synchronizacja import raw_hash
from scraper.dzial5_audyt import audit


def _mk(**over):
    """Minimalny poprawny rekord (przechodzi audyt), do modyfikacji w testach."""
    rec = {
        "lot_id": "abc123", "marka": "BENELLI", "cena_pln": 17460.0,
        "status": "aktywna", "rok_produkcji": 2022, "vin": None, "vin_valid": False,
        "images": [{"image_key": "k", "url": "u", "sort_order": 0}],
        "termin_zakonczenia": "2026-01-01 12:00:00",
        # normalize() zawsze wstawia relist_of=None (dzial2) — dedup ustawia je tylko dla relistow.
        "relist_of": None,
    }
    rec.update(over)
    return rec


class FakeFetcher:
    """fetcher.get(url) -> HTML. Kazda strona ma unikalne loty (nigdy 'brak nowych')."""
    def __init__(self):
        self.calls = 0

    def get(self, url):
        self.calls += 1
        n = self.calls
        return (f'<a href="/pl/auctions/details/moto-{n}/lot{n}">x</a>'
                f'<a href="/pl/auctions/details/moto-{n}b/lot{n}b">y</a>')


class TestCrawlHardCap(unittest.TestCase):
    def test_max_pages_konczy_nawet_gdy_zawsze_nowe(self):
        """Bezpiecznik paginacji: crawl NIE zapetla sie w nieskonczonosc,
        gdy zrodlo zawsze zwraca nowe loty — konczy na config.MAX_PAGES."""
        old = config.MAX_PAGES
        config.MAX_PAGES = 5
        try:
            f = FakeFetcher()
            stubs = crawl_list(f)
            self.assertEqual(f.calls, 5, "powinien pobrac dokladnie MAX_PAGES stron")
            self.assertEqual(len(stubs), 10, "2 loty/strone * 5 stron")
        finally:
            config.MAX_PAGES = old


class TestRawHash(unittest.TestCase):
    def test_deterministyczny_i_niezalezny_od_kolejnosci_kluczy(self):
        a = _mk()
        b = dict(reversed(list(_mk().items())))
        self.assertEqual(raw_hash(a), raw_hash(b))

    def test_zmiana_ceny_zmienia_hash(self):
        self.assertNotEqual(raw_hash(_mk(cena_pln=100.0)), raw_hash(_mk(cena_pln=200.0)))

    def test_pola_meta_nie_wchodza_do_hasha(self):
        """raw_hash liczy sie z _FIELDS bez raw_hash; 'images' nie jest polem bazy."""
        self.assertEqual(raw_hash(_mk(images=[])), raw_hash(_mk(images=[{"x": 1}])))
        self.assertEqual(raw_hash(_mk(raw_hash="stare")), raw_hash(_mk(raw_hash="inne")))


class TestNormalizacjaBrzegi(unittest.TestCase):
    def test_cena_pln_bez_cyfr_daje_none(self):
        rec = normalize({"_og_description": "cena:  PLN netto", "Marka": "X"})
        self.assertIsNone(rec["cena_pln"])
        self.assertEqual(rec["cena_netto"], 1)

    def test_cena_z_separatorem_spacja(self):
        rec = normalize({"_og_description": "cena: 17 460 PLN netto"})
        self.assertEqual(rec["cena_pln"], 17460.0)

    def test_cena_ograniczona_gornym_limitem(self):
        rec = normalize({"_og_description": "cena: 9 999 999 999 PLN"})
        self.assertEqual(rec["cena_pln"], 1_000_000_000.0)

    def test_int_bierze_pierwsza_liczbe(self):
        self.assertEqual(_int("od 2 000 do 3 000"), 2000)

    def test_int_przecinek_nie_jest_separatorem_tysiecy(self):
        # Zrodlo uzywa spacji; przecinek NIE laczy grup -> potencjalna pulapka przy zmianie formatu.
        self.assertEqual(_int("1,200 ccm"), 1)

    def test_capint_zwraca_none_dla_none(self):
        self.assertIsNone(_capint(None, 100))
        self.assertEqual(_capint(500, 100), 100)

    def test_date_bledny_dzien_daje_none(self):
        self.assertIsNone(_date("2022-02-31"))
        self.assertEqual(_date("2022-02-28"), "2022-02-28")

    def test_dlugie_pola_przycinane_do_schematu(self):
        rec = normalize({"Marka": "M" * 200, "Model": "D" * 300})
        self.assertLessEqual(len(rec["marka"]), 64)
        self.assertLessEqual(len(rec["model"]), 128)


class TestVinCheckDigit(unittest.TestCase):
    def test_cyfra_kontrolna_X(self):
        # 1M8GDM9AXKP042788 — klasyczny VIN z cyfra kontrolna 'X' (poz. 9).
        self.assertTrue(vin_valid("1M8GDM9AXKP042788"))

    def test_zla_dlugosc(self):
        self.assertFalse(vin_valid("ABC"))

    def test_znaki_ioq_odrzucone(self):
        self.assertFalse(vin_valid("1M8GDM9AIKP042788"))


class TestDedupTieBreak(unittest.TestCase):
    def test_relist_wybiera_najnowszy_po_terminie(self):
        r1 = _mk(lot_id="stary", vin="1M8GDM9AXKP042788", vin_valid=True,
                 termin_zakonczenia="2025-01-01 10:00:00")
        r2 = _mk(lot_id="nowy", vin="1M8GDM9AXKP042788", vin_valid=True,
                 termin_zakonczenia="2026-06-01 10:00:00")
        out = {r["lot_id"]: r for r in deduplicate([r1, r2])}
        self.assertEqual(out["nowy"]["relist_of"], None)
        self.assertEqual(out["stary"]["relist_of"], "nowy")

    def test_nie_laczy_gdy_vin_niepoprawny(self):
        r1 = _mk(lot_id="a", vin="BADVIN", vin_valid=False)
        r2 = _mk(lot_id="b", vin="BADVIN", vin_valid=False)
        out = deduplicate([r1, r2])
        self.assertTrue(all(r["relist_of"] is None for r in out))


class TestAudytBrzegi(unittest.TestCase):
    def test_status_spoza_slownika_jest_twardy(self):
        ok, errs = audit(_mk(status="dziwny"))
        self.assertFalse(ok)
        self.assertIn("nieznany status: dziwny", [m for s, m in errs])

    def test_rok_w_przyszlosci_dozwolony_plus1(self):
        from datetime import datetime
        ok, _ = audit(_mk(rok_produkcji=datetime.now().year + 1))
        self.assertTrue(ok)

    def test_rok_zbyt_daleko_w_przyszlosci_odrzucony(self):
        from datetime import datetime
        ok, _ = audit(_mk(rok_produkcji=datetime.now().year + 2))
        self.assertFalse(ok)


class TestParseDetailObrazyIEncje(unittest.TestCase):
    def test_deduplikacja_obrazow_i_kolejnosc(self):
        uuid = "12345678-1234-1234-1234-1234567890ab"
        html = (f'<img src="sgallery_{uuid}_1.png">'
                f'<img src="sgallery_{uuid}_2.jpg">'
                f'<img src="sgallery_{uuid.upper()}_3.webp">')
        raw = parse_detail(html, "https://poleasingowe.pl/pl/auctions/details/x/y")
        self.assertEqual(len(raw["_images"]), 1, "ten sam UUID -> jeden klucz")
        self.assertEqual(raw["_images"][0]["sort_order"], 0)

    def test_og_description_unescape(self):
        html = '<meta property="og:description" content="cena: 1 000 PLN &amp; wiecej"/>'
        raw = parse_detail(html, "https://poleasingowe.pl/pl/auctions/details/x/y")
        self.assertIn("&", raw["_og_description"])
        self.assertNotIn("&amp;", raw["_og_description"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
