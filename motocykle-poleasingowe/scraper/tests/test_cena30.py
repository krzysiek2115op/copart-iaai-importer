# SPDX-License-Identifier: GPL-2.0-or-later
"""Test: parsowanie 'Najnizsza cena z 30 dni' (Omnibus) — Dzial 1B + 2.

Markup potwierdzony na zywym HTML poleasingowe.pl (blok sidebar-data,
PLN wewnatrz <strong>)."""
import unittest

from scraper.dzial1b_szczegoly import parse_detail
from scraper.dzial2_normalizacja import normalize

_SIDEBAR = ('<div class="sidebar-data"> <div>Najniższa cena z 30 dni:</div> '
            '<div><strong>{} PLN</strong></div></div>')


def _cena30(html):
    raw = parse_detail(html, "http://x")
    return raw["_cena_30d"], normalize({**raw, "Marka": "X"})["najnizsza_cena_30d"]


class TestCena30(unittest.TestCase):
    def test_blok_obecny(self):
        surowa, wartosc = _cena30(_SIDEBAR.format("29 900"))
        self.assertEqual(surowa, "29 900")
        self.assertEqual(wartosc, 29900.0)

    def test_nbsp_i_spacje(self):
        _, wartosc = _cena30(_SIDEBAR.format("32\xa0042"))
        self.assertEqual(wartosc, 32042.0)

    def test_brak_bloku_none(self):
        surowa, wartosc = _cena30("<div>bez sidebar-data</div>")
        self.assertEqual(surowa, "")
        self.assertIsNone(wartosc)

    def test_smieciowa_wartosc_none(self):
        _, wartosc = _cena30(_SIDEBAR.format("brak"))
        self.assertIsNone(wartosc)


if __name__ == "__main__":
    unittest.main()
