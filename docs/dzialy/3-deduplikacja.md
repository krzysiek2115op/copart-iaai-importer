<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Dział 3 · DEDUPLIKACJA

**Cel:** jeden rekord = jeden realny lot; rozpoznać relist (ten sam pojazd, nowa aukcja).

## Agent
### agent: match
- **Zadanie:**
  - klucz główny `lot_id` (unikat) — usuwa powtórki z crawla,
  - **relist:** ten sam **pełny VIN** pod nowym `lot_id` → oznacza jako relist (nowa aukcja tego samego motocykla), zachowuje oba, linkuje (`relist_of`).
- **Wyjście:** zbiór unikalnych lotów z oznaczeniem relistów.

## Krytyk
### krytyk: fałszywe-trafienia
Odrzuca gdy: różne pojazdy (różny VIN) złączone jako duplikat; legalny relist zgubiony (nadpisany); **pusty/niepoprawny VIN użyty do łączenia** (nigdy nie wolno).
