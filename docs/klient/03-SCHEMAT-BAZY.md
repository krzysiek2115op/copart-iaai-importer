<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Schemat bazy danych — polea_*

Opis osobnej bazy MySQL zasilanej przez scraper i czytanej (tylko do odczytu)
przez wtyczke WordPress. Plik zrodlowy DDL: **db/schema.sql** (to on jest
autorytatywny — ten dokument go objasnia).

## Zasady ogolne

- Silnik **InnoDB**, kodowanie **utf8mb4** (`utf8mb4_unicode_ci`).
- Wlascicielem danych jest **scraper** (upsert). Wtyczka WP tylko czyta.
- Dwie tabele: `polea_motocykle` (1 wiersz = 1 aukcja) i `polea_zdjecia`
  (wiele zdjec na aukcje). Relacja przez `lot_id`.
- Wymagania: MySQL 5.7+ / MariaDB 10.2+.
- Utworzenie: `CREATE DATABASE polea CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`
  potem `mysql -u <user> -p polea < db/schema.sql`.

## Tabela: polea_motocykle

Klucz glowny: `lot_id` (staly identyfikator lotu z URL zrodla).

### Identyfikacja i adresy
| Kolumna | Typ | Opis |
|---|---|---|
| lot_id | VARCHAR(32) NOT NULL | PK; ID lotu z URL |
| numer_aukcji | VARCHAR(64) | np. 3110/BZ/AU/2026 |
| slug | VARCHAR(255) | czlon URL |
| url | VARCHAR(512) | pelny URL szczegolow |

### Dane pojazdu
| Kolumna | Typ | Opis |
|---|---|---|
| marka | VARCHAR(64) | producent |
| model | VARCHAR(128) | model |
| typ | VARCHAR(64) | np. KROSOWY |
| rok_produkcji | SMALLINT UNSIGNED | rok |
| data_pierwszej_rej | DATE | data 1. rejestracji |
| vin | VARCHAR(20) | numer VIN (17+bufor) |
| nr_rej | VARCHAR(32) | nr rejestracyjny |
| naped | VARCHAR(64) | np. Lancuch |
| skrzynia | VARCHAR(64) | np. Manualna |
| moc_km | SMALLINT UNSIGNED | moc w KM |
| pojemnosc_ccm | INT UNSIGNED | pojemnosc w ccm |
| paliwo | VARCHAR(32) | rodzaj paliwa |
| przebieg_km | INT UNSIGNED | przebieg |
| kolor | VARCHAR(64) | kolor |
| ilosc_kluczykow | TINYINT UNSIGNED | liczba kluczykow |
| forma_sprzedazy | VARCHAR(64) | np. faktura VAT |

### Dane aukcyjne
| Kolumna | Typ | Opis |
|---|---|---|
| cena_pln | DECIMAL(12,2) | aktualna cena |
| cena_netto | TINYINT(1) NOT NULL=1 | 1=netto, 0=brutto |
| najnizsza_cena_30d | DECIMAL(12,2) | Omnibus: najnizsza z 30 dni |
| tryb_licytacji | VARCHAR(64) | np. sprzedaz ofertowa |
| lokalizacja | VARCHAR(255) | miejsce pojazdu |
| termin_zakonczenia | DATETIME | koniec aukcji (czas lokalny zrodla) |
| status | VARCHAR(32) NOT NULL | aktywna / zakonczona / usunieta |
| liczba_ofert | INT UNSIGNED NOT NULL=0 | liczba ofert |
| uwagi | TEXT | uwagi zrodla |

### Meta pipeline (dedup / diff / reconcile)
| Kolumna | Typ | Opis |
|---|---|---|
| raw_hash | CHAR(32) | MD5 rekordu -> wykrywanie zmian |
| relist_of | VARCHAR(32) | lot_id nowszej aukcji tego VIN; NULL=najnowszy |
| first_seen | TIMESTAMP | pierwsze zobaczenie (auto) |
| last_seen | TIMESTAMP | ostatni import (auto) |
| updated_at | TIMESTAMP ON UPDATE | ostatnia zmiana (auto) |

Kolumny `first_seen / last_seen / updated_at` ustawia sama baza — scraper ich nie podaje.

### Indeksy
| Indeks | Kolumny | Cel |
|---|---|---|
| PRIMARY | lot_id | klucz glowny |
| idx_marka | marka | filtr po marce |
| idx_status | status | filtr aktywnych |
| idx_termin | termin_zakonczenia | sortowanie |
| idx_status_termin | status, termin_zakonczenia | zapytanie listy (WHERE status + ORDER BY termin) |
| idx_vin | vin | dedup po VIN |
| idx_last_seen | last_seen | reconcile / diagnostyka |

## Tabela: polea_zdjecia

Zdjecia hotlinkowane; kolejnosc przez `sort_order`.

| Kolumna | Typ | Opis |
|---|---|---|
| id | BIGINT UNSIGNED AI | PK |
| lot_id | VARCHAR(32) NOT NULL | FK -> polea_motocykle.lot_id |
| image_key | VARCHAR(64) NOT NULL | UUID z nazwy pliku |
| url | VARCHAR(512) NOT NULL | pelny URL zdjecia |
| sort_order | SMALLINT UNSIGNED NOT NULL=0 | kolejnosc |

Klucze: PK `id`; UNIQUE `uq_lot_image (lot_id, image_key)` — idempotentny upsert;
KEY `idx_lot (lot_id)`; FK `fk_zdjecia_lot` z `ON DELETE CASCADE` (usuniecie lotu
kasuje jego zdjecia).

## Przeplyw danych (upsert)

- Aukcje: `INSERT ... ON DUPLICATE KEY UPDATE ...` po `lot_id` (+ `last_seen=NOW()`).
- Zdjecia: `INSERT ... ON DUPLICATE KEY UPDATE url, sort_order` po `(lot_id, image_key)`.
- Reconcile: aukcje aktywne, ktorych nie ma w biezacym crawlu -> `status='zakonczona'`
  (z bezpiecznikiem `POLEA_RECONCILE_MIN_RATIO`).

## Zgodnosc (zapis = schemat = odczyt)

Zapis scrapera (`scraper/dzial4_synchronizacja.py`, lista `_FIELDS`) pokrywa
dokladnie kolumny schematu (poza auto-timestampami). Normalizacja
(`scraper/dzial2_normalizacja.py`) przycina teksty do dlugosci kolumn i zawsze
wypelnia pola NOT NULL. Wtyczka czyta wylacznie podzbior tych kolumn. Ten
kontrakt jest zweryfikowany testami i audytem.
