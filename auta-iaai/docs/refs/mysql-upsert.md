# Referencja: MySQL upsert — oryginał dla działu „synchronizacja"

> Z oficjalnej dokumentacji MySQL (dev.mysql.com, INSERT ... ON DUPLICATE KEY UPDATE).
> Stan: 2026-06-29.

## INSERT ... ON DUPLICATE KEY UPDATE
Wstawia wiersz; jeśli kolidowałby z **PRIMARY KEY / UNIQUE** — zamiast błędu robi UPDATE
tylko kolidującego wiersza.

```sql
INSERT INTO iaai_vehicles (salvage_id, make, model, raw_hash, status)
VALUES (%s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE make=%s, model=%s, raw_hash=%s, status=%s;
```

### Liczba zmienionych wierszy (rowcount)
- **1** = wstawiono nowy wiersz
- **2** = zaktualizowano istniejący
- **0** = istniał i bez zmian

### Sposoby odwołania do „nowych" wartości (różnice wersji)
- `VALUES(col)` — **deprecyjne** od MySQL 8.0.20 (ale działa w MariaDB).
- Alias `AS new (...)` — **MySQL 8.0.19+**, ale **MariaDB go nie wspiera**.
- ✅ **Nasze podejście (przenośne):** w klauzuli UPDATE podajemy parametry `%s`
  **drugi raz** (te same wartości). Działa identycznie na **MySQL i MariaDB**, niezależnie
  od wersji. Stąd w kodzie przekazujemy listę wartości insert + listę wartości update.

### Pułapki
- Tabela z wieloma indeksami UNIQUE → przy kolizji aktualizowany jest tylko jeden wiersz
  (nieprzewidywalnie). U nas klucz jest jeden (PK `salvage_id`) — bezpiecznie.
- Statement-based replication oznacza takie zapytania jako „unsafe" → preferuj row-based.

## Sterownik: PyMySQL
`pip install pymysql` — czysty Python, działa z MySQL i MariaDB. Połączenie:
`pymysql.connect(host, port, user, password, database, charset="utf8mb4", autocommit=True)`.
Parametry bazy konfigurowalne przez env `IAAI_DB_*` (patrz `common.py`).
