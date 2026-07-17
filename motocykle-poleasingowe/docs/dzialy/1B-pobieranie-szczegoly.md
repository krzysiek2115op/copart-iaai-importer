<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Dział 1B · POBIERANIE SZCZEGÓŁÓW

**Powstał z rozbicia Działu 1.** Wejście: stuby z [1A](1A-pobieranie-lista.md).

**Cel:** dla każdego lotu pobrać stronę szczegółów i pełny zestaw pól + zdjęcia. Rekord „surowy" (raw) trafia do normalizacji (Dział 2).

## Agenci
### agent: szczegóły
- **Zadanie:** pobrać `/pl/auctions/details/<slug>/<lot_id>`, sparsować wszystkie pola kontraktu danych (marka, model, typ, rok, data 1. rej., VIN, nr rej., napęd, skrzynia, moc, pojemność, paliwo, przebieg, kolor, kluczyki, forma sprzedaży, numer aukcji, cena, najniższa 30 dni, tryb licytacji, lokalizacja, termin, status, liczba ofert, uwagi).
- **Wejście:** stub (`lot_id`, `url_szczegolow`).
- **Wyjście:** pełny rekord surowy (raw, wartości jako tekst).

### agent: zdjęcia
- **Zadanie:** wyciągnąć wszystkie `sgallery_<UUID>_75.png`; wyznaczyć `image_key` (UUID) + URL + kolejność; sprawdzić czy istnieje wariant większy niż `_75`.
- **Wyjście:** lista zdjęć (`image_key`, `url`, `sort_order`) dla lotu.

## Krytycy
### krytyk: kompletność-pól
Odrzuca gdy: brak pola wymaganego (`lot_id`, `marka`, `cena`, `url`, `termin_zakonczenia`); pola opcjonalne jako `""` zamiast `null`; pomieszana etykieta↔wartość (parser złapał złą kolumnę).

### krytyk: kompletność-zdjęć
Odrzuca gdy: 0 zdjęć mimo że źródło je ma; duplikat `image_key` w locie; próbka URL-i zwraca ≠200 (HEAD).
