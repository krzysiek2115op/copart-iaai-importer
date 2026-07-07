<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Dział 8 · PUBLIKACJA (WordPress)

**Cel:** wystawić dane z bazy jako treść WordPress (CPT + meta).

## Agenci
### agent: CPT
- **Zadanie:** zarejestrować typ treści `motocykl` (`public`, archiwum, `rewrite` slug, etykiety PL).

### agent: meta
- **Zadanie:** zmapować pola bazy na meta pojazdu (VIN, rok, cena, przebieg, pojemność, moc, paliwo, skrzynia, kolor, lokalizacja, termin, status, liczba_ofert) przez `register_post_meta` z typami; klucz `lot_id` w meta.

## Krytyk
### krytyk: poprawność-publikacji
Odrzuca gdy: jeden `lot_id` daje >1 wpis (duplikat przy re-imporcie); typy meta niezgodne; pole ze źródła zgubione przy mapowaniu; wpis-sierota bez `lot_id`.
