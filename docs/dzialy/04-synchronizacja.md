# Dział 4 · SYNCHRONIZACJA — dokumentacja działu

> Jeden dział = jedna dokumentacja. 1 agent : 1 krytyk.

Cel: porównać przychodzące rekordy ze stanem **nowej bazy** i zapisać zmiany — to
**pierwsze realne podpięcie do bazy** (MariaDB/MySQL).

Oryginał techniczny: [`docs/refs/mysql-upsert.md`](../refs/mysql-upsert.md)
(`INSERT … ON DUPLICATE KEY UPDATE` + sterownik PyMySQL). Wspólny moduł:
[`scraper/dzialy/04_synchronizacja/common.py`](../../scraper/dzialy/04_synchronizacja/common.py).

## Agenci i krytycy

### 🔵 `diff` → 🔴 `spójność`  ✅ zaimplementowany
Kod: [`diff.py`](../../scraper/dzialy/04_synchronizacja/diff.py).
- **Agent:** liczy `raw_hash` (SHA1 pól danych) i porównuje z bazą:
  brak → `new`, inny hash → `changed`, ten sam → `unchanged`.
- **Krytyk `spójność`:** `raw_hash` to 40 znaków hex, status z dozwolonego zbioru,
  hash **deterministyczny** (ten sam rekord → ten sam hash).
- Zweryfikowane na żywej bazie: pierwszy przebieg `new`, po zapisie `unchanged`,
  po zmianie pola `changed`.

### 🔵 `json` → 🔴 `poprawność-json`  ✅ zaimplementowany
Kod: [`json_agent.py`](../../scraper/dzialy/04_synchronizacja/json_agent.py).
- **Agent:** upsert do `iaai_vehicles` przez `INSERT … ON DUPLICATE KEY UPDATE`
  (wersja **przenośna** — parametry podawane dwukrotnie; działa na MySQL i MariaDB).
  Zapisuje `raw_hash`, `status='active'`. Pomija `unchanged` (chyba że `--all`).
- **Krytyk `poprawność-json`:** **odczyt zwrotny** — po zapisie czyta wiersz i sprawdza,
  że `raw_hash` i kluczowe pola w bazie zgadzają się z intencją.
- Zweryfikowane: rekord 45574140 (2011 BMW 335I XDRIVE) zapisany i odczytany zgodnie.

## Połączenie z bazą
`common.connect()` — PyMySQL; parametry przez env `IAAI_DB_HOST/PORT/USER/PASS/NAME`
(domyślnie lokalna instancja `127.0.0.1:3307`, baza `iaai`). Schemat: `db/schema.sql`
(dodano kolumny `raw_hash`, `status`).

## Przepływ
`deduplikacja` (JSONL) → `diff` (status new/changed/unchanged) → `json` (upsert) → baza.
Dalej dział 5 (audyt danych).
