# SPDX-License-Identifier: GPL-2.0-or-later
"""Dzial 7 — Zgodnosc: robots.txt, rate-limit, detekcja blokad. Brama dla wszystkich zadan."""
import time
import random
import logging
import urllib.robotparser as robotparser
from . import config

log = logging.getLogger("polea.zgodnosc")


class BlockedError(RuntimeError):
    """Zadanie zablokowane (robots.txt / 403 / wyczerpane proby)."""


class Fetcher:
    def __init__(self):
        import requests  # leniwy import — potrzebny tylko przy realnym pobieraniu
        self._requests = requests
        self.s = requests.Session()
        self.s.headers.update({
            "User-Agent": config.USER_AGENT,
            "Accept-Language": "pl-PL,pl;q=0.9",
        })
        self._last = 0.0
        self.rp = robotparser.RobotFileParser()
        try:
            self.rp.set_url(config.BASE_URL + "/robots.txt")
            self.rp.read()
        except Exception as e:  # brak robots -> nie blokujemy, ale logujemy
            log.warning("Nie udalo sie wczytac robots.txt: %s", e)
            self.rp = None

    def allowed(self, url):
        return True if self.rp is None else self.rp.can_fetch(config.USER_AGENT, url)

    def _throttle(self):
        wait = config.REQUEST_DELAY + random.uniform(0, config.REQUEST_JITTER)
        dt = time.monotonic() - self._last
        if dt < wait:
            time.sleep(wait - dt)
        self._last = time.monotonic()

    def get(self, url):
        if not self.allowed(url):
            raise BlockedError(f"robots.txt zabrania: {url}")
        last = None
        for attempt in range(1, config.MAX_RETRIES + 1):
            self._throttle()
            try:
                r = self.s.get(url, timeout=config.TIMEOUT)
            except self._requests.RequestException as e:
                last = e
                log.warning("Blad sieci (%s/%s) %s: %s", attempt, config.MAX_RETRIES, url, e)
                time.sleep(2 ** attempt)
                continue
            if r.status_code in (429, 503):
                back = (2 ** attempt) * config.REQUEST_DELAY
                log.warning("HTTP %s — backoff %.0fs (%s)", r.status_code, back, url)
                time.sleep(back)
                continue
            if r.status_code == 403:
                raise BlockedError(f"HTTP 403 (mozliwa blokada): {url}")
            r.raise_for_status()
            return r.text
        raise BlockedError(f"Nie pobrano po {config.MAX_RETRIES} probach: {url} ({last})")
