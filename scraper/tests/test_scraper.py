# SPDX-License-Identifier: GPL-2.0-or-later
"""Testy rdzenia scrapera (stdlib, bez sieci i bazy) na syntetycznym HTML."""
import unittest

from scraper.dzial1a_lista import parse_list_page
from scraper.dzial1b_szczegoly import parse_detail
from scraper.dzial2_normalizacja import normalize, vin_valid
from scraper.dzial3_deduplikacja import deduplicate
from scraper.dzial5_audyt import audit
from scraper.dzial7_zgodnosc import url_allowed

DETAIL = '''<html><head>
<meta property="og:description" content="Numer aukcji: 3110/BZ/AU/2026, cena: 17 460 PLN netto"/>
</head><body>
<div class="auction-data-item"><div class="auction-data-label">Marka</div><div class="auction-data-value">BENELLI</div></div>
<div class="auction-data-item"><div class="auction-data-label">Model</div><div class="auction-data-value">TRAIL</div></div>
<div class="auction-data-item"><div class="auction-data-label">Rok produkcji</div><div class="auction-data-value">2022</div></div>
<div class="auction-data-item"><div class="auction-data-label">VIN</div><div class="auction-data-value">ZBNP3701XNBE02219</div></div>
<div class="auction-data-item"><div class="auction-data-label">Przebieg</div><div class="auction-data-value">3708 km</div></div>
<div class="auction-data-item"><div class="auction-data-label">Moc silnika</div><div class="auction-data-value">76 KM</div></div>
<div class="auction-data-item"><div class="auction-data-label">Pojemno&#347;&#263; silnika</div><div class="auction-data-value">754 ccm</div></div>
<div class="auction-data-item"><div class="auction-data-label">Skrzynia bieg&oacute;w</div><div class="auction-data-value">Manualna</div></div>
<span class="font-weight-bold ml-2"> Aukcja nr 3110/BZ/AU/2026 zakończyła się 2026-07-08 12:00:00</span>
<div class="row"><div class="col-12 col-lg-6"><h2 class="auction-header">WŁAŚCICIEL :</h2><div class="mb-3"> Erste Leasing </div></div>
<div class="col-12 col-lg-6"><h2 class="auction-header">Lokalizacja:</h2><div class="mb-3"> Tarczyn,<br/> Żytnia 2 </div></div></div>
<img src="https://poleasingowe.pl/images/sgallery_630d88e9-2d9b-4f79-9487-6fa9debe8c4c_75.png"/>
<img src="https://poleasingowe.pl/images/sgallery_072bc462-9e5c-47aa-b4eb-1d32d5c206a9_75.png"/>
<img src="https://poleasingowe.pl/images/sgallery_072bc462-9e5c-47aa-b4eb-1d32d5c206a9_75.png"/>
</body></html>'''

LIST = '''
<a href="https://poleasingowe.pl/pl/auctions/details/benelli-leoncino-800-trial-motocykl/9pm53mj9">x</a>
<a href="https://poleasingowe.pl/pl/auctions/details/benelli-leoncino-800-trial-motocykl/9pm53mj9">dup</a>
<a href="https://poleasingowe.pl/pl/auctions/details/bmw-g-310-gs/9rymmkoe">y</a>
<a href="https://partner.example.com/promo">reklama</a>
'''


class TestLista(unittest.TestCase):
    def test_unikat_i_filtr_reklam(self):
        stubs = parse_list_page(LIST)
        self.assertEqual(len(stubs), 2)                 # dedup + reklama pominieta
        self.assertEqual(stubs[0]["lot_id"], "9pm53mj9")
        self.assertTrue(stubs[0]["url"].endswith("/9pm53mj9"))


class TestSzczegolyNorm(unittest.TestCase):
    def setUp(self):
        raw = parse_detail(DETAIL, "http://x")
        raw["lot_id"], raw["slug"] = "9pm53mj9", "benelli"
        self.rec = normalize(raw)

    def test_pola_tekstowe(self):
        self.assertEqual(self.rec["marka"], "BENELLI")
        self.assertEqual(self.rec["model"], "TRAIL")
        self.assertEqual(self.rec["skrzynia"], "Manualna")   # &oacute; -> o

    def test_jednostki(self):
        self.assertEqual(self.rec["przebieg_km"], 3708)
        self.assertEqual(self.rec["moc_km"], 76)
        self.assertEqual(self.rec["pojemnosc_ccm"], 754)     # numeryczne encje
        self.assertEqual(self.rec["rok_produkcji"], 2022)
        self.assertEqual(self.rec["cena_pln"], 17460.0)
        self.assertEqual(self.rec["cena_netto"], 1)

    def test_status_termin_lokalizacja(self):
        self.assertEqual(self.rec["status"], "zakonczona")
        self.assertEqual(self.rec["termin_zakonczenia"], "2026-07-08 12:00:00")
        self.assertIn("Tarczyn", self.rec["lokalizacja"])

    def test_zdjecia_unikat(self):
        self.assertEqual(len(self.rec["images"]), 2)         # duplikat UUID scalony
        self.assertEqual(self.rec["images"][0]["sort_order"], 0)


class TestVin(unittest.TestCase):
    def test_poprawny(self):
        self.assertTrue(vin_valid("1M8GDM9AXKP042788"))     # kanoniczny przyklad (check=X)

    def test_niepoprawny(self):
        self.assertFalse(vin_valid("1M8GDM9A0KP042788"))    # zla cyfra kontrolna
        self.assertFalse(vin_valid("KROTKI"))
        self.assertFalse(vin_valid("1M8GDM9AXKP04278I"))    # niedozwolone I


class TestDedup(unittest.TestCase):
    def test_relist_po_vin(self):
        a = {"lot_id": "a", "vin": "1M8GDM9AXKP042788", "vin_valid": True, "termin_zakonczenia": "2025-01-01 10:00:00"}
        b = {"lot_id": "b", "vin": "1M8GDM9AXKP042788", "vin_valid": True, "termin_zakonczenia": "2026-01-01 10:00:00"}
        out = {r["lot_id"]: r for r in deduplicate([a, b])}
        self.assertEqual(out["a"]["relist_of"], "b")         # starszy wskazuje na nowszy
        self.assertIsNone(out["b"]["relist_of"])

    def test_nie_laczy_pustego_vin(self):
        a = {"lot_id": "a", "vin": None, "vin_valid": False}
        b = {"lot_id": "b", "vin": None, "vin_valid": False}
        out = deduplicate([a, b])
        self.assertEqual(len(out), 2)
        self.assertNotIn("relist_of", out[0])


class TestAudyt(unittest.TestCase):
    def test_ok(self):
        raw = parse_detail(DETAIL, "http://x")
        raw["lot_id"] = "9pm53mj9"
        ok, _ = audit(normalize(raw))
        self.assertTrue(ok)

    def test_twarda_regula_cena(self):
        rec = {"lot_id": "x", "marka": "BMW", "status": "aktywna", "cena_pln": 0}
        ok, errs = audit(rec)
        self.assertFalse(ok)
        self.assertTrue(any(m == "cena_pln <= 0" for _, m in errs))


class TestNormOdpornosc(unittest.TestCase):
    """Regresja audytu: niezaufane wejscie nie moze rzucac wyjatku w normalize (pkt 1)."""

    def test_zla_data_nie_wywala(self):
        rec = normalize({"lot_id": "x", "Marka": "BMW",
                         "Data pierwszej rejestracji": "2022-02-31"})  # dzien poza zakresem
        self.assertIsNone(rec["data_pierwszej_rej"])

    def test_pusta_cena_nie_wywala(self):
        rec = normalize({"lot_id": "x", "Marka": "BMW",
                         "_og_description": "Numer aukcji: 1/A, cena:  PLN netto"})
        self.assertIsNone(rec["cena_pln"])

    def test_dlugosc_pol_zgodna_ze_schematem(self):
        rec = normalize({"lot_id": "x", "Marka": "A" * 300, "Model": "B" * 300,
                         "VIN": "Z" * 40})
        self.assertLessEqual(len(rec["marka"]), 64)     # kolumna VARCHAR(64)
        self.assertLessEqual(len(rec["model"]), 128)    # kolumna VARCHAR(128)
        self.assertLessEqual(len(rec["vin"]), 20)       # kolumna VARCHAR(20)


class TestSSRF(unittest.TestCase):
    """Bramka anty-SSRF (Dzial 7): tylko host z allowlisty i schemat http/https."""

    def test_dozwolony_host(self):
        ok, _ = url_allowed("https://poleasingowe.pl/pl/auctions/details/x/1", resolve=False)
        self.assertTrue(ok)

    def test_obcy_host_odrzucony(self):
        ok, why = url_allowed("https://evil.example.com/x", resolve=False)
        self.assertFalse(ok)
        self.assertEqual(why, "host spoza allowlisty")

    def test_localhost_odrzucony(self):
        ok, _ = url_allowed("http://127.0.0.1/x", resolve=False)
        self.assertFalse(ok)

    def test_metadane_cloud_odrzucone(self):
        ok, _ = url_allowed("http://169.254.169.254/latest/meta-data/", resolve=False)
        self.assertFalse(ok)

    def test_zly_schemat_odrzucony(self):
        for u in ("file:///etc/passwd", "gopher://poleasingowe.pl/", "javascript:alert(1)"):
            ok, why = url_allowed(u, resolve=False)
            self.assertFalse(ok, u)
            self.assertEqual(why, "niedozwolony schemat")


if __name__ == "__main__":
    unittest.main()
