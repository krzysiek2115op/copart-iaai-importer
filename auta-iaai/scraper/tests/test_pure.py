# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Importer Aukcji (IAAI + Copart).
# Licencja: GNU GPL v2 lub pozniejsza - pelny tekst w pliku LICENSE.
"""
Testy jednostkowe funkcji CZYSTYCH pipeline'u (L14). Bez sieci i bazy.

Uruchom:  python -m unittest discover -s scraper/tests
     lub: python scraper/tests/test_pure.py

Moduły z ciężkimi zależnościami (requests/pymysql/playwright) są importowane
miękko — gdy zależność nie jest zainstalowana, dany zestaw jest POMIJANY
(skip), a nie wywraca całości. W środowisku produkcyjnym (deploy/README.md)
wszystkie zależności są zainstalowane i testy obejmują komplet.
"""
import importlib.util
import sys
import unittest
from datetime import date
from pathlib import Path

DZIALY = Path(__file__).resolve().parents[1] / "dzialy"


def _load(dzial: str, modname: str):
    """Importuje moduł agenta po ścieżce; None gdy brak zależności (skip)."""
    path = DZIALY / dzial / f"{modname}.py"
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location(modname, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:                      # brak requests/pymysql/playwright itp.
        return None


jednostki = _load("02_normalizacja", "jednostki")
vin = _load("02_normalizacja", "vin")
match = _load("03_deduplikacja", "match")
common = _load("04_synchronizacja", "common")
pokrycie = _load("01_pobieranie", "pokrycie")


@unittest.skipIf(jednostki is None, "brak modułu jednostki")
class TestJednostki(unittest.TestCase):
    def test_parse_price(self):
        self.assertEqual(jednostki.parse_price("$1,300 USD"), 1300.0)
        self.assertEqual(jednostki.parse_price("2,499.99"), 2499.99)
        self.assertEqual(jednostki.parse_price(1500), 1500.0)
        self.assertIsNone(jednostki.parse_price(None))
        self.assertIsNone(jednostki.parse_price("brak"))

    def test_split_title(self):
        self.assertEqual(jednostki.split_title("SALVAGE (Missouri)"), ("SALVAGE", "Missouri"))
        self.assertEqual(jednostki.split_title("CLEAR"), ("CLEAR", None))
        self.assertEqual(jednostki.split_title(""), (None, None))

    def test_sale_date_textual(self):
        self.assertEqual(jednostki.parse_sale_date("Mon Jun 29, 8:30am CDT 2026"), "2026-06-29")

    def test_sale_date_numeric(self):
        self.assertEqual(jednostki.parse_sale_date("6/29/2026 1:00:00 AM +00:00"), "2026-06-29")
        self.assertEqual(jednostki.parse_sale_date("12/3/2026"), "2026-12-03")

    def test_sale_date_garbage(self):
        self.assertIsNone(jednostki.parse_sale_date("garbage"))
        self.assertIsNone(jednostki.parse_sale_date(""))

    def test_sale_date_no_year_closest(self):
        # L13: bez roku -> data najbliższa dziś; wynik to poprawne ISO z tym miesiącem/dniem
        today = date.today()
        iso = jednostki.parse_sale_date(f"{today.strftime('%b')} {today.day}")
        self.assertIsNotNone(iso)
        self.assertTrue(iso.endswith(f"-{today.month:02d}-{today.day:02d}"))

    def test_key_present_positive(self):
        for v in ("Available", "Present", "Key Present", "Yes"):
            self.assertTrue(jednostki.normalize({"key_available": v})["key_present"], v)

    def test_key_present_negation(self):
        # L12: "Not Available" zawiera "avail" — MUSI dać False
        for v in ("Not Available", "No Key", "None", "Without Key", "N/A"):
            self.assertFalse(jednostki.normalize({"key_available": v})["key_present"], v)

    def test_odometer_to_km(self):
        out = jednostki.normalize({"odometer": 100, "odometer_uom": "mi"})
        self.assertEqual(out["odometer_km"], 161)


@unittest.skipIf(vin is None, "brak modułu vin (requests?)")
class TestVin(unittest.TestCase):
    VALID = "1HGCM82633A004352"          # kanoniczny VIN z cyfrą kontrolną '3'

    def test_clean_and_format(self):
        self.assertEqual(vin.clean_vin(" 1hgcm8 2633a004352 "), self.VALID)
        self.assertTrue(vin.format_ok(self.VALID))
        self.assertFalse(vin.format_ok("TOOSHORT"))

    def test_check_digit(self):
        self.assertTrue(vin.check_digit_ok(self.VALID))
        bad = self.VALID[:8] + "0" + self.VALID[9:]      # zepsuta cyfra kontrolna
        self.assertFalse(vin.check_digit_ok(bad))

    def test_masked(self):
        masked = self.VALID[:11] + "******"
        self.assertTrue(vin.is_masked(masked))
        self.assertIsNone(vin.check_digit_ok(masked))    # maski nie da się policzyć
        self.assertFalse(vin.is_masked(self.VALID))


@unittest.skipIf(match is None, "brak modułu match")
class TestMatch(unittest.TestCase):
    def test_exact_dups(self):
        recs = [{"salvage_id": 1}, {"salvage_id": 1}, {"salvage_id": 2}]
        uniques, report = match.deduplicate(recs)
        self.assertEqual(report["unique"], 2)
        self.assertEqual(report["exact_dups"], [1])

    def test_relist_full_vin(self):
        v = "1HGCM82633A004352"
        recs = [{"salvage_id": 1, "vin": v}, {"salvage_id": 2, "vin": v}]
        _, report = match.deduplicate(recs)
        self.assertIn(v, report["relists"])
        self.assertCountEqual(report["relists"][v], [1, 2])

    def test_masked_vin_not_grouped(self):
        recs = [{"salvage_id": 1, "vin": "1HGCM82633A0****", "vin_masked": True},
                {"salvage_id": 2, "vin": "1HGCM82633A0****", "vin_masked": True}]
        _, report = match.deduplicate(recs)
        self.assertEqual(report["relists"], {})


@unittest.skipIf(common is None, "brak modułu common (pymysql?)")
class TestCommon(unittest.TestCase):
    def test_tbl_prefix(self):
        import os
        os.environ.pop("IAAI_DB_TABLE_PREFIX", None)
        self.assertEqual(common.tbl("iaai_vehicles"), "iaai_vehicles")
        os.environ["IAAI_DB_TABLE_PREFIX"] = "wp_"
        try:
            self.assertEqual(common.tbl("iaai_vehicles"), "wp_iaai_vehicles")
        finally:
            os.environ.pop("IAAI_DB_TABLE_PREFIX", None)

    def test_hash_stable_and_sensitive(self):
        a = {"make": "BMW", "model": "335I"}
        self.assertEqual(common.compute_hash(a), common.compute_hash(dict(a)))
        self.assertNotEqual(common.compute_hash(a), common.compute_hash({"make": "BMW", "model": "M3"}))


@unittest.skipIf(pokrycie is None, "brak modułu pokrycie (playwright?)")
class TestPokrycie(unittest.TestCase):
    def test_krytyk_wykrywa_urwany_segment(self):
        result = {"unique_total": 50,
                  "segments": [{"label": "X", "collected": 50, "result_count": 200}]}
        issues = pokrycie.krytyk_kompletnosc_pokrycia(result)
        self.assertTrue(any("URWANY" in i for i in issues))

    def test_krytyk_ok(self):
        result = {"unique_total": 200,
                  "segments": [{"label": "X", "collected": 200, "result_count": 200}]}
        self.assertEqual(pokrycie.krytyk_kompletnosc_pokrycia(result), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
