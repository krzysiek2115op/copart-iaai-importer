-- =====================================================================
--  Nowa baza danych — WIERNA KOPIA struktury rekordu IAAI
--  Cel: agenci łapią KAŻDY nowy pojazd pojawiający się live na iaai.com
--       i wpisują tu wszystkie dane + zdjęcia (taka sama struktura jak u IAAI).
--
--  Silnik: MySQL 5.7+ / MariaDB 10.3+  (natywne dla WordPressa)
--  Kodowanie: utf8mb4, InnoDB
--  Pola odwzorowują rekord/kartę listingu IAAI 1:1 (patrz db/mapping.md).
--  Klucze: salvage_id (pojazd) + image_key (zdjęcie) — po nich agent
--          rozpoznaje, że rekord już istnieje (brak duplikatów).
-- =====================================================================

SET NAMES utf8mb4;
SET time_zone = '+00:00';

-- ---------------------------------------------------------------------
--  POJAZD — jeden wiersz na lot IAAI, pola 1:1 jak u nich
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `iaai_vehicles` (
  `salvage_id`        BIGINT UNSIGNED NOT NULL,   -- ID lotu (z /VehicleDetail/{id}~US)
  `stock_number`      VARCHAR(40)  NULL,          -- Stock #
  `item_id`           BIGINT UNSIGNED NULL,       -- Item #
  `vin`               VARCHAR(20)  NULL,          -- VIN

  -- nagłówek pojazdu (np. "2010 BMW 335I")
  `year`              SMALLINT UNSIGNED NULL,
  `make`              VARCHAR(60)  NULL,
  `model`             VARCHAR(80)  NULL,
  `series`            VARCHAR(80)  NULL,

  -- specyfikacja (jak na karcie / w szczegółach IAAI)
  `vehicle_type`      VARCHAR(60)  NULL,          -- Vehicle Type
  `body_style`        VARCHAR(80)  NULL,          -- Body Style
  `engine`            VARCHAR(120) NULL,          -- Engine
  `cylinders`         TINYINT UNSIGNED NULL,      -- Cylinders
  `fuel_type`         VARCHAR(40)  NULL,          -- Fuel Type
  `transmission`      VARCHAR(40)  NULL,          -- Transmission (np. Automatic)
  `drive_line`        VARCHAR(40)  NULL,
  `color`             VARCHAR(40)  NULL,          -- Color

  -- przebieg (np. "169,594 mi (Not Required/Exempt)")
  `odometer`          INT UNSIGNED NULL,          -- wartość liczbowa
  `odometer_uom`      VARCHAR(8)   NULL,          -- MI / KM
  `odometer_brand`    VARCHAR(40)  NULL,          -- Actual / Not Required/Exempt ...

  -- stan / szkody / tytuł
  `primary_damage`    VARCHAR(60)  NULL,          -- Primary Damage
  `secondary_damage`  VARCHAR(60)  NULL,          -- Secondary Damage
  `loss`              VARCHAR(60)  NULL,          -- Loss
  `title`             VARCHAR(80)  NULL,          -- Title
  `run_and_drive`     VARCHAR(30)  NULL,          -- Run & Drive (status startu/jazdy)
  `key_available`     VARCHAR(20)  NULL,          -- Key (Available / Not Available)

  -- aukcja / lokalizacja / sprzedaż
  `selling_branch`    VARCHAR(160) NULL,          -- Selling Branch (nazwa)
  `branch_id`         INT UNSIGNED NULL,
  `sale_date`         DATETIME NULL,              -- Sale Date
  `lane`              VARCHAR(20)  NULL,          -- Lane
  `aisle`             VARCHAR(20)  NULL,          -- Aisle / Run order
  `buy_now`           DECIMAL(12,2) NULL,         -- Buy Now (cena)
  `current_bid`       DECIMAL(12,2) NULL,         -- Current Bid

  `detail_url`        VARCHAR(255) NULL,          -- pełny URL listingu

  -- metadane przechwytywania (potrzebne do łapania "nowych live")
  `captured_at`       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (`salvage_id`),
  KEY `idx_vin` (`vin`),
  KEY `idx_make_model` (`make`, `model`),
  KEY `idx_sale_date` (`sale_date`),
  KEY `idx_captured` (`captured_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
--  ZDJĘCIA — z vis.iaai.com/dimensions -> keys[]
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `iaai_vehicle_images` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `salvage_id`    BIGINT UNSIGNED NOT NULL,       -- FK -> iaai_vehicles
  `image_key`     VARCHAR(120) NOT NULL,          -- keys[].K (klucz vis.iaai.com)
  `seq`           SMALLINT UNSIGNED NOT NULL,     -- keys[].IN (kolejność)
  `width`         SMALLINT UNSIGNED NULL,         -- keys[].W
  `height`        SMALLINT UNSIGNED NULL,         -- keys[].H
  `url`           VARCHAR(300) NULL,              -- gotowy URL (resizer) do wyświetlenia
  `captured_at`   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_image_key` (`image_key`),        -- brak duplikatów zdjęć
  KEY `idx_img_vehicle` (`salvage_id`, `seq`),
  CONSTRAINT `fk_image_vehicle` FOREIGN KEY (`salvage_id`)
      REFERENCES `iaai_vehicles` (`salvage_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
