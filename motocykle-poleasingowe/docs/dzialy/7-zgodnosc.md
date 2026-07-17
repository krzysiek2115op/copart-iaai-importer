<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Dział 7 · ZGODNOŚĆ

**Cel:** pobierać legalnie i grzecznie — respektować robots.txt, trzymać tempo, nie obciążać serwera poleasingowe.pl, wykrywać blokady.

## Agent
### agent: zgody
- **Zadanie:**
  - honoruje `robots.txt` (dozwolone `/pl/auctions/list/`, `/pl/auctions/details/`; zakazane bidder-panel, files, calc-commission, autodna),
  - rate-limit: import **co kilka godzin**, odstęp N sekund między żądaniami + jitter,
  - opisowy `User-Agent` (kontakt),
  - detekcja blokad (`429`/`403`/captcha) → backoff/pauza.
- **Wejście/Wyjście:** brama dla wszystkich żądań Działów 1A/1B.

## Krytyk
### krytyk: blokady
Odrzuca gdy: żądanie trafia w ścieżkę `Disallow`; tempo przekracza limit; przy `429` scraper nie zwalnia (młóci dalej); równoległy flood zamiast sekwencyjnego/ograniczonego pobierania.
