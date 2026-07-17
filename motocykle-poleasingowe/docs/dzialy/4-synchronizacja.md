<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Dział 4 · SYNCHRONIZACJA

**Cel:** zapisać zmiany do bazy `polea_*` bez duplikatów i pogodzić stan (co zniknęło/zakończyło się).

## Agenci
### agent: diff
- **Zadanie:** policzyć `raw_hash` ze znormalizowanego rekordu; klasyfikować `new` / `changed` / `unchanged`; dalej idą tylko `new`+`changed`.

### agent: zapis
- **Zadanie:** upsert do `polea_motocykle` + `polea_zdjecia` (PyMySQL, transakcja); **reconcile:** loty nieobecne w bieżącym crawlu lub po terminie → `status = zakonczona/usunieta` (nie kasuje, oznacza); aktualizuje `last_seen`.

## Krytycy
### krytyk: spójność
Odrzuca gdy: `raw_hash` niestabilny — te same dane dają inny hash (przez kolejność pól/whitespace) → fałszywe `changed`.

### krytyk: poprawność-zapisu
Odrzuca gdy: upsert tworzy duplikat (zamiast trafić w PK); zdjęcia nieidempotentne (łamią UNIQUE `lot_id,image_key`); reconcile oznaczył aktywny lot jako usunięty; naruszona spójność FK.
