# SPDX-License-Identifier: GPL-2.0-or-later
"""Testy integracyjne rdzenia scrapera na atrapach (bez sieci i bazy):
Dzial 4 (sync/reconcile/upsert), Dzial 7 (Fetcher.get: redirecty/Content-Type/limity),
orkiestracja main.run (prog odrzucen, dry-run, limit) oraz brzegi normalizacji/audytu."""
import types
import unittest
from unittest import mock

from scraper import config
from scraper import main as main_mod
from scraper import dzial4_synchronizacja as sync_mod
from scraper.dzial7_zgodnosc import Fetcher, BlockedError, url_allowed
from scraper.dzial1a_lista import crawl_list
from scraper.dzial2_normalizacja import normalize, _capint, _int, _date, vin_valid
from scraper.dzial5_audyt import audit


# ----------------------------------------------------------------- Dzial 4: sync

class FakeCursor:
    def __init__(self, active_now=0):
        self.calls = []
        self._active = active_now
        self.rowcount = 0
        self.raise_on = None   # podnies wyjatek gdy SQL zawiera ten fragment
    def __enter__(self):
        return self
    def __exit__(self, *a):
        return False
    def execute(self, sql, params=None):
        if self.raise_on and self.raise_on in sql:
            raise RuntimeError("DB boom")
        self.calls.append((sql, params))
        if sql.strip().upper().startswith("UPDATE"):
            self.rowcount = 3
    def fetchone(self):
        return (self._active,)
    def updates(self):
        return [c for c in self.calls if c[0].strip().upper().startswith("UPDATE")]
    def upserts(self):
        return [c for c in self.calls if "INSERT INTO polea_motocykle" in c[0]]


class FakeConn:
    def __init__(self, cur):
        self._cur = cur
        self.committed = self.rolledback = self.closed = False
    def cursor(self):
        return self._cur
    def commit(self):
        self.committed = True
    def rollback(self):
        self.rolledback = True
    def close(self):
        self.closed = True


def _rec(lot, cena=100.0, status="aktywna", imgs=1):
    return {
        "lot_id": lot, "marka": "BMW", "model": "R", "cena_pln": cena,
        "cena_netto": 1, "status": status,
        "images": [{"image_key": "k%d" % i, "url": "u", "sort_order": i} for i in range(imgs)],
    }


class TestSync(unittest.TestCase):
    def test_upsert_per_rekord_i_zdjecia(self):
        cur = FakeCursor(active_now=0)
        conn = FakeConn(cur)
        sync_mod.sync([_rec("a", imgs=2), _rec("b", imgs=0)], conn=conn, reconcile=False)
        self.assertEqual(len(cur.upserts()), 2)                 # 2 loty
        imgs = [c for c in cur.calls if "INSERT INTO polea_zdjecia" in c[0]]
        self.assertEqual(len(imgs), 2)                          # tylko lot 'a' ma 2 zdjecia
        # P-2: lot 'a' (ma zdjecia) dostaje DELETE prune usunietych ze zrodla; lot 'b'
        # (0 zdjec) NIE czysci galerii (pusty zestaw = mozliwy chwilowy blad detalu).
        dels = [c for c in cur.calls if c[0].strip().upper().startswith("DELETE") and "polea_zdjecia" in c[0]]
        self.assertEqual(len(dels), 1)
        self.assertEqual(dels[0][1][0], "a")
        self.assertTrue(conn.committed)
        self.assertFalse(cur.updates())                         # reconcile=False -> brak UPDATE

    def test_reconcile_zamyka_gdy_powyzej_progu(self):
        cur = FakeCursor(active_now=4)                          # 4 aktywne w bazie
        conn = FakeConn(cur)
        # present = pelna lista z crawla (3 loty) >= 0.5*4 -> reconcile wykonany
        sync_mod.sync([_rec("a")], conn=conn, present_ids={"a", "b", "c"})
        ups = cur.updates()
        self.assertEqual(len(ups), 1)
        self.assertIn("zakonczona", ups[0][0])
        self.assertEqual(sorted(ups[0][1]), ["a", "b", "c"])    # NOT IN present

    def test_reconcile_pominiety_ponizej_progu(self):
        cur = FakeCursor(active_now=10)                         # 10 aktywnych
        conn = FakeConn(cur)
        sync_mod.sync([_rec("a")], conn=conn, present_ids={"a"})  # 1 < 0.5*10 -> pominiete
        self.assertFalse(cur.updates())
        self.assertTrue(conn.committed)

    def test_reconcile_present_none_uzywa_zapisanych(self):
        cur = FakeCursor(active_now=1)
        conn = FakeConn(cur)
        sync_mod.sync([_rec("a")], conn=conn)                   # present_ids=None -> seen=['a']
        ups = cur.updates()
        self.assertEqual(len(ups), 1)
        self.assertEqual(ups[0][1], ["a"])

    def test_rollback_i_reraise_przy_bledzie(self):
        cur = FakeCursor()
        cur.raise_on = "INSERT INTO polea_motocykle"
        conn = FakeConn(cur)
        with self.assertRaises(RuntimeError):
            sync_mod.sync([_rec("a")], conn=conn)
        self.assertTrue(conn.rolledback)
        self.assertFalse(conn.committed)


# ---------------------------------------------------------- Dzial 7: Fetcher.get

class _RE(Exception):
    pass


class FakeResp:
    def __init__(self, status=200, ctype="text/html; charset=utf-8", body=b"OK",
                 location=None, url="https://poleasingowe.pl/x"):
        self.status_code = status
        self.headers = {}
        if ctype is not None:
            self.headers["Content-Type"] = ctype
        if location is not None:
            self.headers["Location"] = location
        self._body = body
        self.url = url
        self.encoding = "utf-8"
        self.apparent_encoding = "utf-8"
    def iter_content(self, chunk_size=65536):
        yield self._body
    def raise_for_status(self):
        pass
    def close(self):
        pass


class FakeSession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.headers = {}
    def get(self, url, timeout=None, allow_redirects=None, stream=None):
        return self._responses.pop(0)


def _make_fetcher(responses):
    f = Fetcher.__new__(Fetcher)              # bez __init__ (brak sieci/robots)
    f._requests = types.SimpleNamespace(RequestException=_RE)
    f.s = FakeSession(responses)
    f._last = 0.0
    f.rp = None                               # brak robots -> allowed()=True
    return f


class TestFetcherGet(unittest.TestCase):
    def setUp(self):
        self._d, self._j = config.REQUEST_DELAY, config.REQUEST_JITTER
        config.REQUEST_DELAY = config.REQUEST_JITTER = 0.0       # bez throttlingu w tescie
        # DNS: allowlistowany host rozwiazuje sie na adres publiczny
        self._p = mock.patch("scraper.dzial7_zgodnosc.socket.getaddrinfo",
                             return_value=[(2, 1, 6, "", ("93.184.216.34", 0))])
        self._p.start()

    def tearDown(self):
        config.REQUEST_DELAY, config.REQUEST_JITTER = self._d, self._j
        self._p.stop()

    def test_html_zwraca_tresc(self):
        f = _make_fetcher([FakeResp(body=b"HELLO")])
        self.assertEqual(f.get("https://poleasingowe.pl/x"), "HELLO")

    def test_odrzuca_nietekstowy_content_type(self):
        f = _make_fetcher([FakeResp(ctype="image/png", body=b"\x89PNG")])
        with self.assertRaises(BlockedError):
            f.get("https://poleasingowe.pl/x")

    def test_brak_content_type_akceptowany(self):
        f = _make_fetcher([FakeResp(ctype=None, body=b"DATA")])
        self.assertEqual(f.get("https://poleasingowe.pl/x"), "DATA")

    def test_limit_rozmiaru_odpowiedzi(self):
        old = config.MAX_RESPONSE_BYTES
        config.MAX_RESPONSE_BYTES = 4
        try:
            f = _make_fetcher([FakeResp(body=b"x" * 100)])
            with self.assertRaises(BlockedError):
                f.get("https://poleasingowe.pl/x")
        finally:
            config.MAX_RESPONSE_BYTES = old

    def test_redirect_na_obcy_host_odrzucony(self):
        f = _make_fetcher([FakeResp(status=302, location="https://evil.example.com/x")])
        with self.assertRaises(BlockedError):
            f.get("https://poleasingowe.pl/x")

    def test_403_blokada(self):
        f = _make_fetcher([FakeResp(status=403)])
        with self.assertRaises(BlockedError):
            f.get("https://poleasingowe.pl/x")


class TestSSRFResolve(unittest.TestCase):
    def test_prywatny_ip_odrzucony_po_rozwiazaniu(self):
        with mock.patch("scraper.dzial7_zgodnosc.socket.getaddrinfo",
                        return_value=[(2, 1, 6, "", ("10.0.0.5", 0))]):
            ok, why = url_allowed("https://poleasingowe.pl/x", resolve=True)
            self.assertFalse(ok)
            self.assertEqual(why, "adres prywatny/lokalny")

    def test_publiczny_ip_przechodzi(self):
        with mock.patch("scraper.dzial7_zgodnosc.socket.getaddrinfo",
                        return_value=[(2, 1, 6, "", ("93.184.216.34", 0))]):
            ok, _ = url_allowed("https://poleasingowe.pl/x", resolve=True)
            self.assertTrue(ok)

    def test_dns_blad_fail_closed(self):
        with mock.patch("scraper.dzial7_zgodnosc.socket.getaddrinfo", side_effect=OSError):
            ok, why = url_allowed("https://poleasingowe.pl/x", resolve=True)
            self.assertFalse(ok)


# --------------------------------------------------------- Dzial 1A: paginacja

class FakeCrawlFetcher:
    def __init__(self, pages):
        self.pages = pages
    def get(self, url):
        import re
        n = int(re.search(r"page=(\d+)", url).group(1))
        return self.pages.get(n, "")


class TestCrawl(unittest.TestCase):
    def test_paginacja_stop_na_braku_nowych(self):
        det = '<a href="https://poleasingowe.pl/pl/auctions/details/s/{id}">x</a>'
        p1 = det.format(id="a") + det.format(id="b")
        p2 = det.format(id="a") + det.format(id="b")   # te same -> brak nowych -> stop
        stubs = crawl_list(FakeCrawlFetcher({1: p1, 2: p2}))
        self.assertEqual({s["lot_id"] for s in stubs}, {"a", "b"})

    def test_pusta_strona_konczy(self):
        stubs = crawl_list(FakeCrawlFetcher({1: ""}))
        self.assertEqual(stubs, [])


# --------------------------------------------------------- main.run: orkiestracja

class _FakeFetcherCls:
    def __init__(self, *a, **k):
        pass


def _stub(i):
    return {"lot_id": "l%d" % i, "slug": "s",
            "url": "https://poleasingowe.pl/pl/auctions/details/s/l%d" % i}


class TestRun(unittest.TestCase):
    def test_prog_odrzucen_wstrzymuje_zapis(self):
        stubs = [_stub(i) for i in range(5)]
        raw_bad = lambda f, s: {"lot_id": s["lot_id"], "url": s["url"]}  # brak marki/ceny -> audyt HARD
        with mock.patch("scraper.dzial7_zgodnosc.Fetcher", _FakeFetcherCls), \
             mock.patch("scraper.main.crawl_list", return_value=stubs), \
             mock.patch("scraper.main.fetch_detail", side_effect=raw_bad):
            with self.assertRaises(SystemExit) as cm:
                main_mod.run(dry_run=False)
            self.assertEqual(cm.exception.code, 2)

    def test_dry_run_zwraca_rekordy_i_respektuje_limit(self):
        stubs = [_stub(i) for i in range(3)]
        raw_ok = lambda f, s: {"lot_id": s["lot_id"], "Marka": "BMW",
                               "_og_description": "cena: 1000 PLN netto", "_status_text": "", "_images": []}
        with mock.patch("scraper.dzial7_zgodnosc.Fetcher", _FakeFetcherCls), \
             mock.patch("scraper.main.crawl_list", return_value=stubs), \
             mock.patch("scraper.main.fetch_detail", side_effect=raw_ok):
            out = main_mod.run(dry_run=True, limit=2)
        self.assertEqual(len(out), 2)                       # limit zastosowany
        self.assertTrue(all(r["cena_pln"] == 1000.0 for r in out))


# ------------------------------------------------------- brzegi normalizacji/audytu

class TestBrzegi(unittest.TestCase):
    def test_capint_i_int(self):
        self.assertEqual(_int("17\xa0460 km"), 17460)          # nbsp
        self.assertIsNone(_int("brak"))
        self.assertEqual(_capint(999999, 100), 100)            # gorny limit
        self.assertIsNone(_capint(None, 100))

    def test_data_bledna_i_poprawna(self):
        self.assertIsNone(_date("2022-02-31"))                 # dzien poza zakresem
        self.assertEqual(_date("z dnia 2022-05-10 xx"), "2022-05-10")
        self.assertIsNone(_date("brak"))

    def test_cena_limit_i_netto(self):
        r = normalize({"lot_id": "x", "Marka": "BMW",
                       "_og_description": "cena: 2000000000 PLN netto"})
        self.assertEqual(r["cena_pln"], 1_000_000_000.0)       # cap 1e9
        self.assertEqual(r["cena_netto"], 1)

    def test_audyt_reguly_twarde(self):
        ok, errs = audit({"lot_id": "", "marka": "", "cena_pln": 0, "status": "x"})
        self.assertFalse(ok)
        msgs = {m for _, m in errs}
        self.assertIn("brak lot_id", msgs)
        self.assertIn("cena_pln <= 0", msgs)
        self.assertIn("brak marki", msgs)

    def test_audyt_rok_poza_zakresem(self):
        ok, errs = audit({"lot_id": "a", "marka": "BMW", "cena_pln": 1,
                          "status": "aktywna", "rok_produkcji": 1900})
        self.assertFalse(ok)

    def test_vin_ioq_odrzucony(self):
        self.assertFalse(vin_valid("1M8GDM9AXKPO42788"))       # litera O niedozwolona


if __name__ == "__main__":
    unittest.main()
