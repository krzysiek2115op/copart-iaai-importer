-- SPDX-License-Identifier: GPL-2.0-or-later
-- Inicjalizacja bazy ofert (polea_*) dla srodowiska LOKALNEGO. Uruchamiane raz,
-- przy pierwszym starcie kontenera MySQL. Hasla DEWELOPERSKIE - tylko lokalnie.
--
-- Odwzorowuje podzial rol z produkcji:
--   * polea    -> konto zapisu dla scrapera (INSERT/UPDATE/DELETE/SELECT),
--   * polea_ro -> konto read-only dla WordPressa (tylko SELECT, least privilege).
-- Sam schemat tabel zakladasz osobno (krok w docs/TESTY-RECZNE.md):
--   docker compose ... exec -T db mysql -uroot -proot_dev polea < db/schema.sql

CREATE DATABASE IF NOT EXISTS polea
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'polea'@'%'    IDENTIFIED BY 'polea_dev_pass';
GRANT SELECT, INSERT, UPDATE, DELETE ON polea.* TO 'polea'@'%';

CREATE USER IF NOT EXISTS 'polea_ro'@'%' IDENTIFIED BY 'polea_ro_dev_pass';
GRANT SELECT ON polea.* TO 'polea_ro'@'%';

FLUSH PRIVILEGES;
