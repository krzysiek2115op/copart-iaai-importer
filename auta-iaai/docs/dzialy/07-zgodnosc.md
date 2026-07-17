# Dział 7 · ZGODNOŚĆ — dokumentacja działu

> Jeden dział = jedna dokumentacja. 1 agent : 1 krytyk.

Cel: scraping zgodny z regułami źródła — robots.txt (RFC 9309), rate-limit, wykrywanie
blokad. Dotyczy strony pobierającej (działa obok działu 1).

Oryginał: [`docs/refs/robots-rfc9309.md`](../refs/robots-rfc9309.md).
Kod: [`scraper/dzialy/07_zgodnosc/zgody.py`](../../scraper/dzialy/07_zgodnosc/zgody.py).

### 🔵 `zgody` → 🔴 `blokady`  ✅ zaimplementowany
- **Agent:** `RobotsPolicy.can_fetch()` (urllib.robotparser = RFC 9309), `RateLimiter`
  (minimalny odstęp między żądaniami), `detect_block()` (403/429/503 + markery
  Incapsula/CAPTCHA).
- **Krytyk `blokady`:** flaguje (a) dostęp do ścieżek **zabronionych w robots.txt**,
  (b) realne blokady → nakazuje backoff.
- Zweryfikowane: `/VehicleDetail` dozwolone; **`/Search` zabronione** (krytyk flaguje);
  Incapsula/429 wykryte.

> ⚠️ Ustalenie: IAAI robots.txt **zabrania `/Search`** (tam są listingi). Krytyk to
> sygnalizuje — decyzja o scrapingu mimo to jest **biznesowo-prawna** (ToS) i należy
> do właściciela projektu, nie do kodu.

## Przepływ
Działa równolegle do `pobierania` (bramka przed każdym żądaniem) oraz jako bramka
zgodności przed publikacją. Dalej dział 8 (publikacja).
