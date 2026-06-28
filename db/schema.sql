-- =====================================================================
--  Nowa baza danych — importer IAAI → WordPress
--  Silnik: MySQL 5.7+ / MariaDB 10.3+  (natywne dla WordPressa)
--  Kodowanie: utf8mb4 (pełny Unicode), InnoDB (klucze obce, transakcje)
--
--  W kontekście wtyczki WP tabele dostają prefiks instalacji, np.
--  {wp_prefix}iaai_vehicles.  Tu używamy stałego prefiksu `iaai_`.
--  Mapowanie pól ze źródła: patrz db/mapping.md
-- =====================================================================

SET NAMES utf8mb4;
SET time_zone = '+00:00';

-- ---------------------------------------------------------------------
-- 1) BRANCHE / LOKALIZACJE IAAI (słownik)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `iaai_branches` (
  `branch_id`     INT UNSIGNED NOT NULL,           -- inventory.branchId
  `branch_number` INT UNSIGNED NULL,               -- inventory.branchNumber
  `name`          VARCHAR(160) NULL,               -- inventory.locName / name
  `address`       VARCHAR(255) NULL,
  `city`          VARCHAR(120) NULL,
  `state`         VARCHAR(8)   NULL,
  `zip`           VARCHAR(16)  NULL,
  `phone`         VARCHAR(40)  NULL,
  `latitude`      DECIMAL(9,6) NULL,               -- inventory.locLatitude
  `longitude`     DECIMAL(9,6) NULL,               -- inventory.locLongitude
  `is_offsite`    TINYINT(1)   NOT NULL DEFAULT 0,
  `updated_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`branch_id`),
  KEY `idx_branch_state` (`state`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 2) POJAZDY (rdzeń) — jeden wiersz na lot IAAI (salvage_id)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `iaai_vehicles` (
  `salvage_id`        BIGINT UNSIGNED NOT NULL,    -- inventory.salvageId (PK źródła)
  `item_id`           BIGINT UNSIGNED NULL,        -- inventory.itemId
  `stock_number`      VARCHAR(40)  NULL,           -- inventory.stockNumber
  `vin`               VARCHAR(20)  NULL,           -- inventory.vin
  `vin_status`        VARCHAR(20)  NULL,

  -- identyfikacja pojazdu
  `year`              SMALLINT UNSIGNED NULL,
  `make`              VARCHAR(60)  NULL,
  `model`             VARCHAR(80)  NULL,
  `series`            VARCHAR(80)  NULL,
  `body_style`        VARCHAR(80)  NULL,
  `vehicle_class`     VARCHAR(60)  NULL,

  -- napęd / silnik
  `engine_info`       VARCHAR(120) NULL,
  `engine_size`       VARCHAR(40)  NULL,
  `cylinders`         TINYINT UNSIGNED NULL,
  `fuel_type`         VARCHAR(40)  NULL,
  `transmission`      VARCHAR(40)  NULL,
  `drive_line`        VARCHAR(40)  NULL,           -- driveLineTypeDesc
  `drives`            TINYINT(1)   NULL,           -- inventory.drives

  -- kolor / wnętrze
  `color`             VARCHAR(40)  NULL,           -- colorDesc
  `interior_color`    VARCHAR(40)  NULL,

  -- przebieg
  `odometer_value`    INT UNSIGNED NULL,           -- inventory.odoValue
  `odometer_uom`      VARCHAR(8)   NULL,           -- odoUoM (MI/KM)
  `odometer_brand`    VARCHAR(40)  NULL,           -- odoBrand (Actual/Not Actual...)

  -- stan / szkody / tytuł
  `primary_damage`    VARCHAR(60)  NULL,           -- primaryDamageDesc
  `secondary_damage`  VARCHAR(60)  NULL,           -- secondaryDamageDesc
  `loss_type`         VARCHAR(60)  NULL,
  `title_brand`       VARCHAR(60)  NULL,
  `title_state`       VARCHAR(8)   NULL,           -- certState
  `keys_present`      TINYINT(1)   NULL,           -- inventory.keys
  `key_fob`           TINYINT(1)   NULL,
  `airbags_count`     TINYINT UNSIGNED NULL,
  `airbag_state`      TINYINT UNSIGNED NULL,

  -- powiązania
  `branch_id`         INT UNSIGNED NULL,           -- FK -> iaai_branches

  -- media (flagi i wskaźniki; same pliki w iaai_vehicle_images)
  `image_count`       SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  `has_360`           TINYINT(1)   NOT NULL DEFAULT 0,
  `video_count`       SMALLINT UNSIGNED NOT NULL DEFAULT 0,

  -- daty źródłowe
  `src_created_at`    DATETIME NULL,               -- inventory.createdDateTime
  `src_modified_at`   DATETIME NULL,               -- inventory.modifiedDateTime
  `src_version_id`    BIGINT UNSIGNED NULL,        -- inventory.versionId

  -- metadane importu / cyklu życia
  `source`            VARCHAR(16) NOT NULL DEFAULT 'iaai',
  `status`            ENUM('active','sold','removed','unknown')
                        NOT NULL DEFAULT 'unknown',
  `raw_hash`          CHAR(40) NULL,               -- SHA1 surowego JSON (do diff/sync)
  `wp_post_id`        BIGINT UNSIGNED NULL,        -- powiązany wpis WP (CPT), gdy opublikowany
  `first_seen_at`     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_seen_at`      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (`salvage_id`),
  UNIQUE KEY `uq_vin_year` (`vin`, `year`),        -- pomoc przy deduplikacji
  KEY `idx_make_model` (`make`, `model`),
  KEY `idx_branch` (`branch_id`),
  KEY `idx_status` (`status`),
  KEY `idx_wp_post` (`wp_post_id`),
  KEY `idx_last_seen` (`last_seen_at`),
  CONSTRAINT `fk_vehicle_branch` FOREIGN KEY (`branch_id`)
      REFERENCES `iaai_branches` (`branch_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 3) ZDJĘCIA POJAZDU  (z vis.iaai.com/dimensions -> keys[])
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `iaai_vehicle_images` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `salvage_id`    BIGINT UNSIGNED NOT NULL,        -- FK -> iaai_vehicles
  `image_key`     VARCHAR(120) NOT NULL,           -- keys[].K (pełny klucz vis)
  `seq`           SMALLINT UNSIGNED NOT NULL,      -- keys[].IN (kolejność)
  `width`         SMALLINT UNSIGNED NULL,          -- keys[].W
  `height`        SMALLINT UNSIGNED NULL,          -- keys[].H
  `is_360`        TINYINT(1) NOT NULL DEFAULT 0,
  `local_path`    VARCHAR(255) NULL,               -- ścieżka po pobraniu (opcjonalnie)
  `wp_attachment_id` BIGINT UNSIGNED NULL,         -- ID załącznika WP po imporcie do mediów
  `downloaded_at` DATETIME NULL,
  `created_at`    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_image_key` (`image_key`),
  KEY `idx_img_vehicle` (`salvage_id`, `seq`),
  CONSTRAINT `fk_image_vehicle` FOREIGN KEY (`salvage_id`)
      REFERENCES `iaai_vehicles` (`salvage_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 4) AUKCJA / DANE LIVE  (status licytacji, ceny — z SignalR/AJAX)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `iaai_auctions` (
  `salvage_id`        BIGINT UNSIGNED NOT NULL,    -- FK 1:1 -> iaai_vehicles
  `auction_id`        BIGINT UNSIGNED NULL,        -- inventory.auctionId
  `timed_auction`     TINYINT(1) NOT NULL DEFAULT 0,
  `auction_close_at`  DATETIME NULL,               -- timedAuctionCloseDateTime
  `buy_now`           TINYINT(1) NOT NULL DEFAULT 0,
  `buy_now_sold`      TINYINT(1) NOT NULL DEFAULT 0,
  `current_bid`       DECIMAL(12,2) NULL,          -- aktualizowane live
  `bid_count`         INT UNSIGNED NULL,
  `live_updated_at`   DATETIME NULL,               -- ostatnia aktualizacja live
  PRIMARY KEY (`salvage_id`),
  KEY `idx_auction_close` (`auction_close_at`),
  CONSTRAINT `fk_auction_vehicle` FOREIGN KEY (`salvage_id`)
      REFERENCES `iaai_vehicles` (`salvage_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 5) SUROWE PAYLOADY  (#ProductDetailsVM) — dla działu AUDYT / reprocess
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `iaai_raw_payloads` (
  `id`           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `salvage_id`   BIGINT UNSIGNED NOT NULL,
  `payload`      JSON NOT NULL,                    -- pełny #ProductDetailsVM
  `raw_hash`     CHAR(40) NOT NULL,                -- SHA1 payloadu
  `fetched_at`   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_raw_vehicle` (`salvage_id`, `fetched_at`),
  KEY `idx_raw_hash` (`raw_hash`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- 6) DZIENNIK IMPORTÓW / SYNC  (dział synchronizacja + audyt)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `iaai_sync_runs` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `run_type`      ENUM('full','incremental','live') NOT NULL,
  `started_at`    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `finished_at`   DATETIME NULL,
  `fetched`       INT UNSIGNED NOT NULL DEFAULT 0,
  `inserted`      INT UNSIGNED NOT NULL DEFAULT 0,
  `updated`       INT UNSIGNED NOT NULL DEFAULT 0,
  `skipped`       INT UNSIGNED NOT NULL DEFAULT 0,
  `errors`        INT UNSIGNED NOT NULL DEFAULT 0,
  `status`        ENUM('running','ok','failed') NOT NULL DEFAULT 'running',
  `notes`         TEXT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_run_status` (`status`, `started_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
