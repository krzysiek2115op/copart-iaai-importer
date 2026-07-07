<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Dział 2 · NORMALIZACJA

**Cel:** zamienić surowy tekst z Działu 1B na czyste, typowane wartości zgodne ze schematem bazy. Lekka — dane są już PL/PLN/km (bez mile→km).

## Agenci
### agent: VIN
- **Zadanie:** walidacja VIN — 17 znaków, dozwolone znaki (bez I/O/Q), **cyfra kontrolna** (pozycja 9, ISO 3779). Niepoprawne oznacza flagą, nie odrzuca całego rekordu. **Nie odpytuje NHTSA** (marka/model są u źródła).
- **Wyjście:** `vin` + `vin_valid` (bool).

### agent: jednostki
- **Zadanie:** parsowanie PL → typy:
  - `"17 460 PLN"` → `Decimal(17460.00)` + `cena_netto`,
  - `"3708 km"` → `int`, `"76 KM"` → `int`, `"754 ccm"` → `int`,
  - `"2022-06-03"` → `DATE`,
  - `"10 godzin (2026-07-08)"` / `"zakończyła się 2026-07-08 12:00:00"` → `termin_zakonczenia` DATETIME + `status`.

## Krytycy
### krytyk: poprawność-VIN
Odrzuca gdy: poprawny VIN oznaczony jako błędny (fałszywy negatyw) **lub** błędny VIN przepuszczony jako `vin_valid=true`.

### krytyk: jakość-jednostek
Odrzuca gdy: w polu liczbowym została jednostka/spacja; `cena_pln ≤ 0`; data nie w ISO; `termin_zakonczenia` w przeszłości przy `status=aktywna` (spójność z Działem 4).
