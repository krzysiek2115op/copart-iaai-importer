-- SPDX-License-Identifier: GPL-2.0-or-later
-- Importer Motocykli (poleasingowe.pl) — schemat osobnej bazy MySQL
-- Etap 1. Właściciel schematu: scraper Python (upsert). Wtyczka WP czyta te tabele.
-- Jedno źródło (poleasingowe.pl), kategoria: motocykle (ecr_motorcycles).
--
-- Wymagania: MySQL 5.7+/MariaDB 10.2+, silnik InnoDB, kodowanie utf8mb4.
-- Uruchomienie (przykład):
--   CREATE DATABASE polea CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
--   mysql -u <user> -p polea < db/schema.sql

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ---------------------------------------------------------------------------
-- Tabela główna: jeden wiersz = jedna aukcja motocykla
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS polea_motocykle (
    lot_id              VARCHAR(32)     NOT NULL,               -- ID z URL, np. "9pm53mj9" (stały klucz lotu)
    numer_aukcji        VARCHAR(64)     DEFAULT NULL,           -- np. "3110/BZ/AU/2026"
    slug                VARCHAR(255)    DEFAULT NULL,           -- człon URL, np. "benelli-leoncino-800-trial-motocykl"
    url                 VARCHAR(512)    DEFAULT NULL,           -- pełny URL strony szczegółów

    -- Dane pojazdu
    marka               VARCHAR(64)     DEFAULT NULL,
    model               VARCHAR(128)    DEFAULT NULL,
    typ                 VARCHAR(64)     DEFAULT NULL,           -- np. "KROSOWY"
    rok_produkcji       SMALLINT UNSIGNED DEFAULT NULL,
    data_pierwszej_rej  DATE            DEFAULT NULL,
    vin                 VARCHAR(20)     DEFAULT NULL,           -- 17 znaków + bufor
    nr_rej              VARCHAR(32)     DEFAULT NULL,
    naped               VARCHAR(64)     DEFAULT NULL,           -- rodzaj napędu, np. "Łańcuch"
    skrzynia            VARCHAR(64)     DEFAULT NULL,           -- np. "Manualna"
    moc_km              SMALLINT UNSIGNED DEFAULT NULL,         -- moc w KM
    pojemnosc_ccm       INT UNSIGNED    DEFAULT NULL,           -- pojemność w ccm
    paliwo              VARCHAR(32)     DEFAULT NULL,
    przebieg_km         INT UNSIGNED    DEFAULT NULL,
    kolor               VARCHAR(64)     DEFAULT NULL,
    ilosc_kluczykow     TINYINT UNSIGNED DEFAULT NULL,
    forma_sprzedazy     VARCHAR(64)     DEFAULT NULL,           -- np. "faktura VAT"

    -- Dane aukcyjne
    cena_pln            DECIMAL(12,2)   DEFAULT NULL,           -- aktualna cena
    cena_netto          TINYINT(1)      NOT NULL DEFAULT 1,     -- 1 = cena netto
    najnizsza_cena_30d  DECIMAL(12,2)   DEFAULT NULL,           -- najniższa cena z 30 dni
    tryb_licytacji      VARCHAR(64)     DEFAULT NULL,           -- np. "sprzedaż ofertowa"
    lokalizacja         VARCHAR(255)    DEFAULT NULL,           -- np. "Tarczyn, Żytnia 2"
    termin_zakonczenia  DATETIME        DEFAULT NULL,           -- data/godzina końca aukcji (czas lokalny źródła, Europe/Warsaw; używane do sortowania, nie do odliczeń)
    status              VARCHAR(32)     NOT NULL DEFAULT 'aktywna',  -- aktywna | zakonczona | usunieta
    liczba_ofert        INT UNSIGNED    NOT NULL DEFAULT 0,
    uwagi               TEXT            DEFAULT NULL,           -- np. "BRAK WAŻNEGO BADANIA TECHNICZNEGO"

    -- Meta pipeline (dedup / diff / reconcile)
    raw_hash            CHAR(32)        DEFAULT NULL,           -- MD5 znormalizowanego rekordu -> new/changed/unchanged
    relist_of           VARCHAR(32)     DEFAULT NULL,           -- lot_id nowszej aukcji tego samego VIN (relist); NULL = najnowszy
    first_seen          TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen           TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- odświeżane przy każdym imporcie
    updated_at          TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (lot_id),
    KEY idx_marka (marka),
    KEY idx_status (status),
    KEY idx_termin (termin_zakonczenia),
    KEY idx_status_termin (status, termin_zakonczenia),  -- pod zapytanie listy (WHERE status + ORDER BY termin)
    KEY idx_vin (vin),
    KEY idx_last_seen (last_seen)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Migracja istniejacej bazy (gdy tabela juz istnieje bez powyzszych) — uruchom raz, ignoruj bledy "duplicate":
--   ALTER TABLE polea_motocykle ADD COLUMN relist_of VARCHAR(32) DEFAULT NULL AFTER raw_hash;
--   ALTER TABLE polea_motocykle ADD KEY idx_status_termin (status, termin_zakonczenia);

-- ---------------------------------------------------------------------------
-- Zdjęcia (hotlink) — wiele na lot; kolejność zachowana przez sort_order
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS polea_zdjecia (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    lot_id      VARCHAR(32)     NOT NULL,
    image_key   VARCHAR(64)     NOT NULL,                       -- UUID z nazwy pliku sgallery_<UUID>_75.png
    url         VARCHAR(512)    NOT NULL,                       -- pełny URL zdjęcia (hotlink)
    sort_order  SMALLINT UNSIGNED NOT NULL DEFAULT 0,

    PRIMARY KEY (id),
    UNIQUE KEY uq_lot_image (lot_id, image_key),               -- idempotentny upsert zdjęć
    KEY idx_lot (lot_id),
    CONSTRAINT fk_zdjecia_lot FOREIGN KEY (lot_id)
        REFERENCES polea_motocykle (lot_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
