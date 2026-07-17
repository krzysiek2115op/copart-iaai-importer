# SPDX-License-Identifier: GPL-2.0-or-later
"""Dzial 7 — Zgodnosc: robots.txt, rate-limit, anty-SSRF, detekcja blokad. Brama dla wszystkich zadan."""
import time
import random
import socket
import logging
import ipaddress
import urllib.request
import urllib.robotparser as robotparser
from urllib.parse import urlsplit, urljoin
from . import config

log = logging.getLogger("polea.zgodnosc")

_REDIRECT_CODES = (301, 302, 303, 307, 308)


class BlockedError(RuntimeError):
    """Zadanie zablokowane (robots.txt / 403 / SSRF / wyczerpane proby)."""


def _host_is_private(host):
    """True gdy host wskazuje na adres prywatny/lokalny/metadanych (anty-SSRF).
    Bezpieczny fail-closed: gdy nie da sie rozwiazac -> traktujemy jako niebezpieczny."""
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return True
    for info in infos:
        try:
            addr = ipaddress.ip_address(info[4][0])
        except ValueError:
            return True
        if (addr.is_private or addr.is_loopback or addr.is_link_local
                or addr.is_reserved or addr.is_multicast or addr.is_unspecified):
            return True
    return False


def url_allowed(url, resolve=True):
    """Zwraca (ok, powod). Wymusza https/http, host z allowlisty i publiczny adres IP.
    resolve=False pomija sprawdzenie DNS (do testow offline)."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        return False, "niedozwolony schemat"
    host = (parts.hostname or "").lower()
    if host not in config.ALLOWED_HOSTS:
        return False, "host spoza allowlisty"
    if resolve and _host_is_private(host):
        return False, "adres prywatny/lokalny"
    return True, ""


class Fetcher:
    def __init__(self):
        import requests  # leniwy import — potrzebny tylko przy realnym pobieraniu
        self._requests = requests
        self.s = requests.Session()
        # Ignoruj proxy/.netrc ze srodowiska (anty-SSRF: zlosliwy HTTP(S)_PROXY nie przekieruje ruchu).
        self.s.trust_env = config.TRUST_ENV
        self.s.verify = True   # jawna weryfikacja certyfikatu TLS (CWE-295) — nie polegaj na domyslnej
        self.s.max_redirects = config.MAX_REDIRECTS
        self.s.headers.update({
            "User-Agent": config.USER_AGENT,
            "Accept-Language": "pl-PL,pl;q=0.9",
        })
        self._last = 0.0
        self.rp = robotparser.RobotFileParser()
        try:
            # Pobranie robots.txt z TWARDYM timeoutem i limitem rozmiaru (init nie moze zawisnac).
            req = urllib.request.Request(
                config.BASE_URL + "/robots.txt",
                headers={"User-Agent": config.USER_AGENT},
            )
            with urllib.request.urlopen(req, timeout=config.TIMEOUT) as resp:
                data = resp.read(512 * 1024).decode("utf-8", "replace")
            self.rp.parse(data.splitlines())
        except Exception as e:  # brak robots -> nie blokujemy, ale logujemy
            log.warning("Nie udalo sie wczytac robots.txt: %s", e)
            self.rp = None

    def allowed(self, url):
        return True if self.rp is None else self.rp.can_fetch(config.USER_AGENT, url)

    def _check(self, url):
        """Bramka: allowlista/anty-SSRF + robots.txt. Rzuca BlockedError gdy niedozwolone."""
        ok, why = url_allowed(url)
        if not ok:
            raise BlockedError(f"URL odrzucony ({why}): {url}")
        if not self.allowed(url):
            raise BlockedError(f"robots.txt zabrania: {url}")

    def _throttle(self):
        wait = config.REQUEST_DELAY + random.uniform(0, config.REQUEST_JITTER)
        dt = time.monotonic() - self._last
        if dt < wait:
            time.sleep(wait - dt)
        self._last = time.monotonic()

    def _read_capped(self, r):
        """Czyta tresc strumieniowo z limitem bajtow (po dekompresji) i CALKOWITYM budzetem czasu.
        Chroni przed bomba dekompresyjna oraz slow-loris (serwer saczacy bajty w nieskonczonosc)."""
        limit = config.MAX_RESPONSE_BYTES
        deadline = time.monotonic() + config.MAX_TOTAL_SECONDS
        chunks, total = [], 0
        for chunk in r.iter_content(chunk_size=65536):
            if time.monotonic() > deadline:
                raise BlockedError(f"Przekroczono budzet czasu odpowiedzi: {r.url}")
            total += len(chunk)
            if total > limit:
                raise BlockedError(f"Odpowiedz przekracza limit {limit} B: {r.url}")
            chunks.append(chunk)
        enc = r.encoding or r.apparent_encoding or "utf-8"
        return b"".join(chunks).decode(enc, errors="replace")

    def get(self, url):
        """Pobiera URL z allowlisty. Przekierowania obslugiwane RECZNIE i walidowane per skok
        (allow_redirects=False) — 302 na localhost/metadane/obcy host jest odrzucany."""
        self._check(url)
        current = url
        redirects = 0
        attempt = 0
        last = None
        while True:
            attempt += 1
            if attempt > config.MAX_RETRIES:
                raise BlockedError(f"Nie pobrano po {config.MAX_RETRIES} probach: {url} ({last})")
            self._throttle()
            try:
                r = self.s.get(current, timeout=config.TIMEOUT,
                               allow_redirects=False, stream=True)
            except self._requests.RequestException as e:
                last = e
                log.warning("Blad sieci (%s/%s) %s: %s", attempt, config.MAX_RETRIES, current, e)
                time.sleep(2 ** attempt)
                continue
            try:
                code = r.status_code
                if code in _REDIRECT_CODES:
                    nxt = urljoin(current, r.headers.get("Location", ""))
                    self._check(nxt)  # waliduje host/allowlist/prywatne IP + robots
                    redirects += 1
                    if redirects > config.MAX_REDIRECTS:
                        raise BlockedError(f"Za duzo przekierowan ({redirects}): {url}")
                    current = nxt
                    attempt = 0  # przekierowanie nie liczy sie jako nieudana proba
                    continue
                if code in (429, 503):
                    back = (2 ** attempt) * config.REQUEST_DELAY
                    log.warning("HTTP %s — backoff %.0fs (%s)", code, back, current)
                    time.sleep(back)
                    continue
                if code == 403:
                    raise BlockedError(f"HTTP 403 (mozliwa blokada): {current}")
                r.raise_for_status()
                # Walidacja Content-Type: parsujemy TYLKO HTML/tekst (CWE-20/CWE-436).
                # Odrzucamy nieoczekiwane typy (obraz/pdf/zip/binaria) z wrogiego/zmanipulowanego serwera.
                ctype = (r.headers.get("Content-Type") or "").lower()
                if ctype and "html" not in ctype and not ctype.startswith("text/"):
                    raise BlockedError(f"Nieoczekiwany Content-Type ({ctype}): {current}")
                return self._read_capped(r)
            finally:
                r.close()
