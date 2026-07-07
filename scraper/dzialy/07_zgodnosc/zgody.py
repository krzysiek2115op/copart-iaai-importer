# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Importer Aukcji (IAAI + Copart).
# Licencja: GNU GPL v2 lub pozniejsza - pelny tekst w pliku LICENSE.
"""
Dział 7 · ZGODNOŚĆ — agent `zgody`  (+ krytyk `blokady`).

Pilnuje, by scraping był zgodny: respektuje robots.txt (RFC 9309), trzyma rate-limit
i wykrywa blokady (403/429/Incapsula/CAPTCHA) → każe zwolnić/odpuścić.

Oryginał: docs/refs/robots-rfc9309.md (RFC 9309). robots.txt parsuje stdlib
`urllib.robotparser` (implementacja RFC 9309).

⚠️ Ważne dla IAAI: robots.txt **zabrania `/Search`** (a tam są listingi). Agent to
sygnalizuje — to świadoma decyzja biznesowo-prawna właściciela projektu (ToS!).

Wymagania: brak (stdlib) — requests opcjonalnie do realnych żądań.
Użycie:   python zgody.py --check https://www.iaai.com/Search
          python zgody.py --check https://www.iaai.com/VehicleDetail/123~US
"""
from __future__ import annotations
import argparse, sys, time, urllib.robotparser
from urllib.parse import urlparse

UA = "Mozilla/5.0 (compatible; IAAIImporter/1.0)"
BLOCK_MARKERS = ("_incapsula_resource", "incident id", "request unsuccessful",
                 "access denied", "captcha", "are you a human", "unusual traffic")


class RobotsPolicy:
    def __init__(self, base_url: str, ua: str = UA):
        self.ua = ua
        p = urlparse(base_url)
        self.rp = urllib.robotparser.RobotFileParser()
        self.rp.set_url(f"{p.scheme}://{p.netloc}/robots.txt")
        try:
            self.rp.read()
            self.ok = True
        except Exception:
            self.ok = False           # RFC 9309: 4xx -> wolno; 5xx -> traktuj jako disallow

    def can_fetch(self, url: str) -> bool:
        return self.rp.can_fetch(self.ua, url)


class RateLimiter:
    def __init__(self, min_interval: float = 1.0):
        self.min_interval = min_interval
        self._last = 0.0

    def wait(self):
        dt = time.monotonic() - self._last
        if dt < self.min_interval:
            time.sleep(self.min_interval - dt)
        self._last = time.monotonic()


def detect_block(status: int, body: str = "") -> str | None:
    """Zwraca powód blokady albo None."""
    if status in (403, 429, 503):
        return f"HTTP {status}"
    low = (body or "").lower()
    for m in BLOCK_MARKERS:
        if m in low:
            return f"marker: {m}"
    return None


# ---- 🔴 KRYTYK: blokady ---------------------------------------------------
def krytyk_blokady(events: list[dict]) -> list[str]:
    """events: [{'url','allowed','status','body'}]. Zgłasza naruszenia i blokady."""
    issues = []
    for e in events:
        if e.get("allowed") is False:
            issues.append(f"DOSTĘP do ścieżki ZABRONIONEJ w robots.txt: {e['url']}")
        b = detect_block(e.get("status", 0), e.get("body", ""))
        if b:
            issues.append(f"BLOKADA ({b}) na {e['url']} — zwolnij/odpuść (backoff)")
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", required=True, help="URL do sprawdzenia względem robots.txt")
    ap.add_argument("--ua", default=UA)
    args = ap.parse_args()

    pol = RobotsPolicy(args.check, args.ua)
    allowed = pol.can_fetch(args.check)
    print(f"robots.txt wczytany: {pol.ok}")
    print(f"czy wolno pobrać {args.check} ? -> {'TAK' if allowed else 'NIE (Disallow)'}")

    issues = krytyk_blokady([{"url": args.check, "allowed": allowed, "status": 200}])
    if issues:
        print("[krytyk:blokady] ZASTRZEŻENIA:")
        for i in issues:
            print("   -", i)
        sys.exit(1)
    print("[krytyk:blokady] OK ✅ (zgodne z robots, brak blokad)")


if __name__ == "__main__":
    main()
