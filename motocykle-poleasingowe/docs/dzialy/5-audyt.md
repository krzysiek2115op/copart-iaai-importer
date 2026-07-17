<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Dział 5 · AUDYT

**Cel:** ostatnia bramka jakości przed publikacją — reguły na finalny rekord.

## Agent
### agent: walidacja
- **Zadanie:** sprawdzić rekord regułami:
  - **twarde** (blokują publikację): `lot_id` obecny, `cena_pln > 0`, `rok_produkcji ∈ [1950, rok+1]`, wymagane pola nie-`null`, `status` ze słownika,
  - **miękkie** (tylko flaga): VIN niepoprawny, brak zdjęć, brak `termin_zakonczenia`.

## Krytyk
### krytyk: poprawność
Odrzuca gdy: rekord łamiący twardą regułę trafił jednak do bazy/publikacji; reguła miękka błędnie zablokowała rekord; raport audytu nie zgadza się z liczbą realnych odrzuceń.
