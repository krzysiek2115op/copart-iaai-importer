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
	iaai_create_landing_page();   // auto-podstrona „Nasze auta" + wpięcie do menu
	flush_rewrite_rules();        // by archiwum CPT /pojazdy działało od razu
}

/* =====================================================================
 * AUTO-PODSTRONA — Strona WP „Nasze auta" z shortcode [iaai_pojazdy]
 * tworzona SAMA po aktywacji i dopinana do głównego menu.
 * Wszystko idempotentne: przy ponownej aktywacji nic się nie duplikuje.
 * ===================================================================== */

/** Zwraca ID istniejącej podstrony IAAI (opcja lub meta `_iaai_landing`), albo 0. */
function iaai_get_landing_page_id() : int {
	$id = (int) get_option( 'iaai_page_id' );
	if ( $id && 'publish' === get_post_status( $id ) ) {
		return $id;
	}
	$q = get_posts( array(
		'post_type'   => 'page',
		'post_status' => 'any',
		'numberposts' => 1,
		'fields'      => 'ids',
		'meta_key'    => '_iaai_landing',
		'meta_value'  => '1',
	) );
	return $q ? (int) $q[0] : 0;
}

/**
 * Tworzy Stronę WP „Nasze auta" z shortcode (jeśli jej nie ma) i dopina do menu.
 * Strona to zwykła treść WP — klient może ją przenieść, zmienić nazwę, dodać sekcje.
 */
function iaai_create_landing_page() : void {
	$id = iaai_get_landing_page_id();
	if ( ! $id ) {
		$id = wp_insert_post( array(
			'post_title'   => __( 'Nasze auta', 'iaai-importer' ),
			'post_name'    => 'nasze-auta',
			'post_status'  => 'publish',
			'post_type'    => 'page',
			'post_content' => "<p>" . esc_html__( 'Aktualna oferta pojazdów z aukcji IAAI — zdjęcia, przebieg, zakres uszkodzeń i pełne dane techniczne każdego auta. Lista odświeża się automatycznie.', 'iaai-importer' ) . "</p>\n[iaai_pojazdy ile=\"24\"]",
		) );
		if ( is_wp_error( $id ) || ! $id ) {
			if ( function_exists( 'iaai_log' ) ) {
				iaai_log( 'activation: nie udało się utworzyć podstrony „Nasze auta"', 'error' );
			}
			return;
		}
		update_post_meta( $id, '_iaai_landing', '1' );
		update_option( 'iaai_page_id', (int) $id );
	}
	update_option( 'iaai_landing_done', 1 );
	iaai_maybe_add_page_to_menu( (int) $id );
}

/**
 * Dopina podstronę do menu — obsługuje OBA typy motywów:
 *   • blokowe (Twenty Twenty-Four/Five itp.) → blok Nawigacja (wp_navigation),
 *   • klasyczne → menu przypisane do lokalizacji motywu.
 * Nie duplikuje pozycji. Gdy motyw ma nagłówek „na sztywno" (bez menu WP) —
 * po cichu odpuszcza; wtedy dodanie jest fizycznie niemożliwe z poziomu wtyczki.
 */
function iaai_maybe_add_page_to_menu( int $page_id ) : void {
	if ( ! $page_id ) {
		return;
	}
	iaai_add_page_to_block_nav( $page_id );          // motywy blokowe

	if ( ! function_exists( 'wp_update_nav_menu_item' ) ) {
		return;
	}
	$locations = (array) get_nav_menu_locations();
	$menu_id   = isset( $locations['primary'] ) ? (int) $locations['primary'] : 0;
	if ( ! $menu_id ) {
		foreach ( $locations as $loc_menu ) {
			if ( $loc_menu ) {
				$menu_id = (int) $loc_menu;
				break;
			}
		}
	}
	if ( ! $menu_id || ! wp_get_nav_menu_object( $menu_id ) ) {
		return;   // brak menu — klient doda ręcznie (patrz docs/klient)
	}
	foreach ( (array) wp_get_nav_menu_items( $menu_id ) as $it ) {
		if ( (int) $it->object_id === $page_id && 'page' === $it->object ) {
			return;   // już w menu — nie duplikuj
		}
	}
	wp_update_nav_menu_item( $menu_id, 0, array(
		'menu-item-title'     => __( 'Nasze auta', 'iaai-importer' ),
		'menu-item-object'    => 'page',
		'menu-item-object-id' => $page_id,
		'menu-item-type'      => 'post_type',
		'menu-item-status'    => 'publish',
	) );
}

/**
 * Motywy BLOKOWE: dopisuje link do podstrony w bloku Nawigacja (wp_navigation).
 * - jeśli nawigacja używa „Listy stron" (page-list), nasza strona i tak się pokaże → pomija,
 * - jeśli link już jest → pomija (bez duplikatu),
 * - w przeciwnym razie dokleja <!-- wp:navigation-link ... /--> do treści nawigacji.
 * Bez efektu na motywach klasycznych i tych z nagłówkiem „na sztywno".
 */
function iaai_add_page_to_block_nav( int $page_id ) : void {
	if ( ! $page_id || ! function_exists( 'wp_is_block_theme' ) || ! wp_is_block_theme() ) {
		return;
	}
	$navs = get_posts( array(
		'post_type'   => 'wp_navigation',
		'post_status' => 'publish',
		'numberposts' => -1,
	) );
	if ( ! $navs ) {
		return;   // brak bloku Nawigacja (np. nagłówek na sztywno) — nic nie zrobimy
	}
	$url   = get_permalink( $page_id );
	$title = get_the_title( $page_id );
	$link  = sprintf(
		'<!-- wp:navigation-link {"label":%s,"type":"page","id":%d,"url":%s,"kind":"post-type"} /-->',
		wp_json_encode( $title ),
		$page_id,
		wp_json_encode( esc_url_raw( $url ) )
	);
	foreach ( $navs as $nav ) {
		$content = (string) $nav->post_content;
		if ( false !== strpos( $content, 'wp:page-list' ) ) {
			continue;   // page-list pokazuje wszystkie strony automatycznie
		}
		if ( false !== strpos( $content, '"id":' . $page_id . ',' ) ) {
			continue;   // już dodane
		}
		wp_update_post( array( 'ID' => $nav->ID, 'post_content' => $content . $link ) );
	}
}

/**
 * Bezpiecznik dla AKTUALIZACJI przez podmianę plików (bez ponownej aktywacji):
 * gdy podstrona jeszcze nie istnieje, utwórz ją raz przy wejściu do panelu.
 */
add_action( 'admin_init', 'iaai_maybe_create_landing' );
function iaai_maybe_create_landing() : void {
	if ( get_option( 'iaai_landing_done' ) ) {
		return;
	}
	iaai_create_landing_page();
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
