<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Dział 1A · POBIERANIE LISTY (crawl)

**Powstał z rozbicia Działu 1** (był za szeroki: 4 agentów, 2 różne cele). 1A = *odkryć co istnieje*; [1B](1B-pobieranie-szczegoly.md) = *pobrać szczegóły*.

**Cel:** przejść całą kategorię `ecr_motorcycles` i zebrać listę lotów (stub-rekordów) do pogłębienia w 1B. Server-side HTML, `requests` + parser, paginacja `?page=N`.

## Agenci
### agent: pokrycie
- **Zadanie:** przejść wszystkie strony listy kategorii aż do wyczerpania (pusta strona / powtórka / brak „następnej").
- **Wejście:** URL bazowy `…/list/pub/all/ecr_motorcycles`.
- **Wyjście:** uporządkowany zbiór URL-i stron listy (`?page=1..N`).

### agent: listingi
- **Zadanie:** sparsować karty na każdej stronie; **odfiltrować reklamy partnerów** (~2/stronę); wyciągnąć `lot_id`, `slug`, `url_szczegolow` + skrót (marka/model, cena, miniatura).
- **Wejście:** strony z agenta *pokrycie*.
- **Wyjście:** lista rekordów-zalążków (stub) — wejście dla Działu 1B.

## Krytycy
### krytyk: kompletność-pokrycia
Odrzuca gdy: crawl urwał się przedwcześnie (np. tylko `page=1`), ostatnia strona źle wykryta, albo liczba zebranych ≠ deklarowanej liczbie wyników kategorii (tolerancja na znikające loty).

### krytyk: kompletność-listy
Odrzuca gdy: karta bez `lot_id`/URL, reklama partnera przepuszczona jako lot, duplikat `lot_id` w obrębie jednego crawla.
