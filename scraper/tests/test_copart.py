# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Importer Aukcji (IAAI + Copart).
# Licencja: GNU GPL v2 lub pozniejsza - pelny tekst w pliku LICENSE.
"""
Testy DWÓCH ŹRÓDEŁ (IAAI + Copart) — mapowanie Copart oraz kolumna `source`
w zapisie do bazy (json_agent). Bez sieci i bazy.

Uruchom:  python -m unittest discover -s scraper/tests
     lub: python scraper/tests/test_copart.py

Moduły z ciężkimi zależnościami są importowane miękko (skip gdy brak zależności).
`copart._map_detail` jest CZYSTE i ładuje się bez `requests` (import leniwy w _session),
więc te testy przechodzą także w środowisku deweloperskim.
"""
import importlib.util
import sys
import unittest
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
    except Exception:                      # brak requests/pymysql itp.
        return None


copart = _load("01_pobieranie", "copart")
json_agent = _load("04_synchronizacja", "json_agent")


class FakeCursor:
    """Atrapa kursora DB — zapamiętuje ostatnie execute(sql, params), zwraca rowcount=1."""
    def __init__(self):
        self.sql = None
        self.params = None
        self.rowcount = 1

    def execute(self, sql, params=None):
        self.sql = sql
        self.params = list(params) if params is not None else None

    def fetchone(self):
        return None


@unittest.skipIf(copart is None, "brak modułu copart")
class TestCopartMapowanie(unittest.TestCase):
    """_map_detail: klucze skrócone Copart -> wspólny kształt, zawsze source='copart'."""

    def test_pelny_rekord(self):
        d = {"ln": "12345678", "lcy": 2019, "mkn": "JEEP", "lmg": "GRAND CHEROKEE",
             "orr": "45000", "fv": "1J4RR4GG0BC531234", "key": "Y", "rd": 1,
             "dd": "FRONT END", "bnp": 8200, "hb": 5100, "yn": "TX - DALLAS"}
        out = copart._map_detail(d)
        self.assertEqual(out["source"], "copart")          # zawsze copart
        self.assertEqual(out["salvage_id"], 12345678)      # ln -> int
        self.assertEqual(out["year"], 2019)                # lcy -> int
        self.assertEqual(out["make"], "JEEP")
        self.assertEqual(out["model"], "GRAND CHEROKEE")
        self.assertEqual(out["odometer"], 45000)           # orr -> int
        self.assertEqual(out["odometer_uom"], "mi")        # Copart w milach
        self.assertEqual(out["vin"], "1J4RR4GG0BC531234")
        self.assertEqual(out["primary_damage"], "FRONT END")
        self.assertEqual(out["key_available"], "Yes")      # key=Y -> Yes
        self.assertEqual(out["run_and_drive"], "Run and Drive")

    def test_pusty_rekord_nie_wywala(self):
        out = copart._map_detail({})
        self.assertEqual(out["source"], "copart")          # nadal oznaczone źródłem
        self.assertIsNone(out["salvage_id"])               # brak ln -> None (nie wyjątek)
        self.assertEqual(out["key_available"], "No")        # brak key -> No
        self.assertIsNone(out["run_and_drive"])            # brak rd -> None

    def test_liczby_niepoprawne_na_none(self):
        out = copart._map_detail({"ln": "abc", "lcy": "", "orr": None})
        self.assertIsNone(out["salvage_id"])
        self.assertIsNone(out["year"])
        self.assertIsNone(out["odometer"])

    def test_zdjecia_maja_source_key_seq(self):
        """Etap 'zdjecia' buduje rekordy z source=copart, unikalnym image_key i seq."""
        # odwzorowanie logiki stage_zdjecia (bez sieci): image_key = copart-{lot}-{i}
        lot, i = 987654, 3
        rec = {"salvage_id": lot, "source": "copart",
               "image_key": f"copart-{lot}-{i}", "seq": i}
        self.assertEqual(rec["source"], "copart")
        self.assertTrue(rec["image_key"].startswith("copart-"))
        self.assertEqual(rec["seq"], 3)


@unittest.skipIf(json_agent is None, "brak modułu json_agent (pymysql?)")
class TestJsonAgentSource(unittest.TestCase):
    """Zapis do bazy niesie kolumnę `source` na właściwej pozycji dla obu tabel."""

    def test_kolumny_zawieraja_source(self):
        self.assertIn("source", json_agent.ALL_COLS)
        self.assertEqual(json_agent.ALL_COLS[1], "source")     # zaraz po salvage_id
        self.assertIn("source", json_agent._IMG_COLS)

    def test_upsert_przekazuje_source(self):
        cur = FakeCursor()
        json_agent.upsert({"salvage_id": 111, "make": "BMW", "model": "330I"},
                          cur, source="copart")
        # ins = [salvage_id, source, ...DATA..., hash, status]; source jako 2. wartość
        self.assertEqual(cur.params[0], 111)
        self.assertEqual(cur.params[1], "copart")

    def test_upsert_image_setdefault_source(self):
        cur = FakeCursor()
        json_agent.upsert_image({"salvage_id": 111, "image_key": "copart-111-0", "seq": 0},
                                cur, source="copart")
        # _IMG_COLS = [salvage_id, source, image_key, ...]; source na pozycji 1
        self.assertEqual(cur.params[1], "copart")

    def test_upsert_image_nie_nadpisuje_jawnego_source(self):
        cur = FakeCursor()
        json_agent.upsert_image({"salvage_id": 1, "source": "iaai",
                                 "image_key": "k", "seq": 0}, cur, source="copart")
        self.assertEqual(cur.params[1], "iaai")   # setdefault nie nadpisuje istniejącego


if __name__ == "__main__":
    unittest.main(verbosity=2)
