<?php
/**
 * AKTYWACJA — zakładanie tabel nowej bazy przez dbDelta (blok A, pkt 2).
 *
 * Tabele {$wpdb->prefix}iaai_vehicles + {$wpdb->prefix}iaai_vehicle_images tworzą się
 * SAME przy włączeniu wtyczki. Te same tabele (z prefiksem WP) zasilają agenci Pythona —
 * po stronie scrapera ustaw IAAI_DB_TABLE_PREFIX = $wpdb->prefix (np. "wp_").
 *
 * Schemat = db/schema.sql, ale w wariancie zgodnym z dbDelta:
 *   - każde pole w osobnej linii,
 *   - dwa odstępy po "PRIMARY KEY",
 *   - KEY (nie INDEX), każdy klucz nazwany,
 *   - bez FOREIGN KEY (dbDelta tego nie obsługuje — spójność pilnuje kod/reconcile),
 *   - bez backticków (dbDelta porównuje definicje tekstowo).
 * Hook rejestrowany w pliku głównym: register_activation_hook( __FILE__, 'iaai_activate' ).
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/** Wersja schematu — podbij przy zmianie struktury tabel (wymusza ponowne dbDelta). */
const IAAI_DB_VERSION = '1.0.0';

/**
 * Buduje instrukcje CREATE TABLE (dbDelta-friendly) z prefiksem WP i collation.
 * @return string[] dwie instrukcje (pojazdy, zdjęcia).
 */
function iaai_schema_statements() : array {
	global $wpdb;
	$charset_collate = $wpdb->get_charset_collate();
	$veh = $wpdb->prefix . 'iaai_vehicles';
	$img = $wpdb->prefix . 'iaai_vehicle_images';

	$sql_veh = "CREATE TABLE {$veh} (
  salvage_id bigint(20) unsigned NOT NULL,
  stock_number varchar(40) DEFAULT NULL,
  item_id bigint(20) unsigned DEFAULT NULL,
  vin varchar(20) DEFAULT NULL,
  year smallint(5) unsigned DEFAULT NULL,
  make varchar(60) DEFAULT NULL,
  model varchar(80) DEFAULT NULL,
  series varchar(80) DEFAULT NULL,
  vehicle_type varchar(60) DEFAULT NULL,
  body_style varchar(80) DEFAULT NULL,
  engine varchar(120) DEFAULT NULL,
  cylinders tinyint(3) unsigned DEFAULT NULL,
  fuel_type varchar(40) DEFAULT NULL,
  transmission varchar(40) DEFAULT NULL,
  drive_line varchar(40) DEFAULT NULL,
  color varchar(40) DEFAULT NULL,
  odometer int(10) unsigned DEFAULT NULL,
  odometer_uom varchar(8) DEFAULT NULL,
  odometer_brand varchar(40) DEFAULT NULL,
  primary_damage varchar(60) DEFAULT NULL,
  secondary_damage varchar(60) DEFAULT NULL,
  loss varchar(60) DEFAULT NULL,
  title varchar(80) DEFAULT NULL,
  run_and_drive varchar(30) DEFAULT NULL,
  key_available varchar(20) DEFAULT NULL,
  selling_branch varchar(160) DEFAULT NULL,
  branch_id int(10) unsigned DEFAULT NULL,
  sale_date datetime DEFAULT NULL,
  lane varchar(20) DEFAULT NULL,
  aisle varchar(20) DEFAULT NULL,
  buy_now decimal(12,2) DEFAULT NULL,
  current_bid decimal(12,2) DEFAULT NULL,
  detail_url varchar(255) DEFAULT NULL,
  raw_hash char(40) DEFAULT NULL,
  status varchar(10) NOT NULL DEFAULT 'active',
  captured_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY  (salvage_id),
  KEY idx_vin (vin),
  KEY idx_make_model (make,model),
  KEY idx_sale_date (sale_date),
  KEY idx_status (status),
  KEY idx_captured (captured_at)
) {$charset_collate};";

	$sql_img = "CREATE TABLE {$img} (
  id bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  salvage_id bigint(20) unsigned NOT NULL,
  image_key varchar(120) NOT NULL,
  seq smallint(5) unsigned NOT NULL,
  width smallint(5) unsigned DEFAULT NULL,
  height smallint(5) unsigned DEFAULT NULL,
  url varchar(300) DEFAULT NULL,
  captured_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY  (id),
  UNIQUE KEY uq_image_key (image_key),
  KEY idx_img_vehicle (salvage_id,seq)
) {$charset_collate};";

	return array( $sql_veh, $sql_img );
}

/**
 * Hook aktywacji: zakłada/aktualizuje tabele. dbDelta jest idempotentne —
 * przy istniejących tabelach tylko dorównuje brakujące kolumny/klucze.
 *
 * UWAGA: `status` celowo varchar(10) (nie ENUM) — dbDelta nie radzi sobie z ENUM
 * (każdorazowo próbowałoby ALTER). Wartości active/sold/removed pilnuje kod.
 */
function iaai_activate() : void {
	require_once ABSPATH . 'wp-admin/includes/upgrade.php';
	foreach ( iaai_schema_statements() as $sql ) {
		dbDelta( $sql );
	}
	update_option( 'iaai_db_version', IAAI_DB_VERSION );
}

/**
 * Bezpiecznik: jeśli wtyczkę zaktualizowano przez podmianę plików (bez ponownej
 * aktywacji), a wersja schematu się zmieniła — dorównaj tabele przy starcie.
 */
add_action( 'plugins_loaded', 'iaai_maybe_upgrade_db' );
function iaai_maybe_upgrade_db() : void {
	if ( get_option( 'iaai_db_version' ) !== IAAI_DB_VERSION ) {
		iaai_activate();
	}
}
