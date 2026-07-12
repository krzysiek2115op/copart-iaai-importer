<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Scraper poleasingowe.pl (motocykle)

Pipeline działów: **1A** crawl listy → **1B** szczegóły+zdjęcia → **2** normalizacja → **5** audyt → **3** deduplikacja → **4** upsert+reconcile do bazy `polea_*`. Bramka **7** (zgodność/rate-limit) obsługuje wszystkie żądania. Zob. [../docs/ARCHITEKTURA.md](../docs/ARCHITEKTURA.md).

## Uruchomienie
```bash
pip install -r scraper/requirements.txt      # requests + PyMySQL (rdzen dziala na stdlib)

# Baza (osobna MySQL) — poswiadczenia TYLKO przez env, nigdy w kodzie:
export POLEA_DB_HOST=127.0.0.1 POLEA_DB_USER=polea POLEA_DB_PASSWORD=... POLEA_DB_NAME=polea

python3 -m scraper.main --dry-run --limit 3   # test bez zapisu
python3 -m scraper.main                        # pelny import do bazy
```

## Testy (bez sieci i bazy, stdlib)
```bash
python3 -m unittest discover -s scraper/tests -t . -v   # 43 testy: rdzeń + integracja (atrapy, bez sieci/bazy)
```

## Zmienne środowiskowe
| Zmienna | Domyślnie | Opis |
|---|---|---|
| `POLEA_DELAY` / `POLEA_JITTER` | 2.0 / 1.0 | odstęp [s] między żądaniami + jitter (Dział 7) |
| `POLEA_MAX_PAGES` | 50 | bezpiecznik paginacji |
| `POLEA_USER_AGENT` | PoleasingoweImporter/0.1 | User-Agent |
| `POLEA_DB_*` | — | host/port/user/password/name osobnej bazy MySQL |

## Uwagi
- Źródło = server-side HTML (bez JS) → `requests` + regex, **bez Playwright**.
- Reklamy partnerów na innych domenach (np. `aukcje.pkoleasing.pl`) są pomijane — poza zakresem.
- Zdjęcia: hotlink `poleasingowe.pl/images/sgallery_<UUID>_75.png` (nie pobieramy plików).
