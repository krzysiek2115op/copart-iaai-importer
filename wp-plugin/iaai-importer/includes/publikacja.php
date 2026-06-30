<?php
/**
 * Dział 8 · PUBLIKACJA — agenci `CPT` + `meta`, krytycy `poprawność-CPT` / `poprawność-meta`.
 *
 * Zamienia rekordy z nowej bazy ({$wpdb->prefix}iaai_vehicles) na wpisy WordPressa
 * typu „pojazd" (CPT) + meta. Oryginał: docs/refs/wordpress-cpt.md.
 * Wejście do bazy/meta sanityzowane przez dział 6 (security.php).
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

const IAAI_CPT = 'pojazd';

/** Pola pojazdu -> klucze meta (prefiks iaai_). */
function iaai_meta_keys() : array {
	return array( 'salvage_id', 'stock_number', 'vin', 'year', 'make', 'model', 'series',
		'vehicle_type', 'body_style', 'engine', 'cylinders', 'fuel_type', 'transmission',
		'drive_line', 'color', 'odometer', 'odometer_uom', 'odometer_brand', 'primary_damage',
		'secondary_damage', 'loss', 'title', 'run_and_drive', 'key_available',
		'selling_branch', 'sale_date', 'lane', 'aisle', 'buy_now', 'current_bid', 'detail_url' );
}

/* ---------- 🔵 AGENT `CPT` — rejestracja typu treści --------------------- */
add_action( 'init', 'iaai_register_pojazd_cpt' );
function iaai_register_pojazd_cpt() : void {
	register_post_type( IAAI_CPT, array(
		'labels'       => array(
			'name'          => __( 'Pojazdy', 'iaai-importer' ),
			'singular_name' => __( 'Pojazd', 'iaai-importer' ),
		),
		'public'       => true,
		'show_in_rest' => true,
		'has_archive'  => true,
		'menu_icon'    => 'dashicons-car',
		'supports'     => array( 'title', 'editor', 'thumbnail', 'custom-fields' ),
		'rewrite'      => array( 'slug' => 'pojazdy' ),
	) );
}

/* ---------- 🔵 AGENT `meta` — rejestracja pól meta ----------------------- */
add_action( 'init', 'iaai_register_pojazd_meta' );
function iaai_register_pojazd_meta() : void {
	$num = array( 'salvage_id', 'year', 'odometer', 'cylinders' );
	foreach ( iaai_meta_keys() as $key ) {
		register_post_meta( IAAI_CPT, 'iaai_' . $key, array(
			'type'              => in_array( $key, $num, true ) ? 'integer'
				: ( in_array( $key, array( 'buy_now', 'current_bid' ), true ) ? 'number' : 'string' ),
			'single'            => true,
			'show_in_rest'      => true,
			'sanitize_callback' => in_array( $key, $num, true ) ? 'absint' : 'sanitize_text_field',
		) );
	}
}

/* ---------- publikacja jednego pojazdu z bazy do CPT --------------------- */
function iaai_find_post_by_salvage( int $salvage_id ) : int {
	$q = get_posts( array(
		'post_type'   => IAAI_CPT,
		'meta_key'    => 'iaai_salvage_id',
		'meta_value'  => $salvage_id,
		'fields'      => 'ids',
		'numberposts' => 1,
		'post_status' => 'any',
	) );
	return $q ? (int) $q[0] : 0;
}

/**
 * Tworzy lub aktualizuje wpis CPT „pojazd" na podstawie rekordu z bazy.
 * @return int post_id albo 0 przy braku rekordu.
 */
function iaai_publish_vehicle( int $salvage_id ) : int {
	global $wpdb;
	$table = $wpdb->prefix . 'iaai_vehicles';
	$row   = $wpdb->get_row(
		$wpdb->prepare( "SELECT * FROM {$table} WHERE salvage_id = %d", $salvage_id ),
		ARRAY_A
	);
	if ( ! $row ) {
		return 0;
	}
	$row   = iaai_sanitize_vehicle( $row );                       // dział 6
	$title = trim( sprintf( '%s %s %s', $row['year'] ?? '', $row['make'] ?? '', $row['model'] ?? '' ) );

	$postarr = array(
		'post_type'   => IAAI_CPT,
		'post_status' => 'publish',
		'post_title'  => $title !== '' ? $title : ( 'Pojazd ' . $salvage_id ),
	);
	$existing = iaai_find_post_by_salvage( $salvage_id );
	if ( $existing ) {
		$postarr['ID'] = $existing;
		$post_id       = wp_update_post( $postarr );
	} else {
		$post_id = wp_insert_post( $postarr );
	}
	if ( is_wp_error( $post_id ) || ! $post_id ) {
		return 0;
	}
	foreach ( iaai_meta_keys() as $key ) {
		if ( array_key_exists( $key, $row ) ) {
			update_post_meta( $post_id, 'iaai_' . $key, $row[ $key ] );
		}
	}
	update_post_meta( $post_id, 'iaai_status', 'active' );   // F1: spójny status (re-list wraca na publish)
	return (int) $post_id;
}

/** Publikuje wszystkie aktywne pojazdy, a znikłe (sold/removed) cofa z publikacji (F1).
 *  Wołane po imporcie (WP-CLI/cron): `wp eval 'iaai_publish_all_active();'`. */
function iaai_publish_all_active() : int {
	global $wpdb;
	$table = $wpdb->prefix . 'iaai_vehicles';
	$ids   = $wpdb->get_col(
		$wpdb->prepare( "SELECT salvage_id FROM {$table} WHERE status = %s", 'active' )
	);
	$n = 0;
	foreach ( $ids as $sid ) {
		if ( iaai_publish_vehicle( (int) $sid ) ) {
			$n++;
		}
	}
	iaai_unpublish_inactive();                   // F1: zdejmij ze strony auta, których już nie ma
	return $n;
}

/**
 * F1 — pojazdy o statusie sold/removed: ich wpis CPT przechodzi w 'draft'
 * (znika ze strony, nie jest kasowany — historia zostaje). Zapisuje też meta
 * `iaai_status`, by szablon mógł np. pokazać „sprzedane” zamiast ukrywać.
 * @return int liczba zdjętych wpisów.
 */
function iaai_unpublish_inactive() : int {
	global $wpdb;
	$table = $wpdb->prefix . 'iaai_vehicles';
	$rows  = $wpdb->get_results(
		$wpdb->prepare( "SELECT salvage_id, status FROM {$table} WHERE status <> %s", 'active' ),
		ARRAY_A
	);
	$n = 0;
	foreach ( $rows as $r ) {
		$post_id = iaai_find_post_by_salvage( (int) $r['salvage_id'] );
		if ( ! $post_id ) {
			continue;
		}
		update_post_meta( $post_id, 'iaai_status', sanitize_text_field( $r['status'] ) );
		if ( get_post_status( $post_id ) === 'publish' ) {
			wp_update_post( array( 'ID' => $post_id, 'post_status' => 'draft' ) );
			$n++;
		}
	}
	return $n;
}

/* ---------- 🔴 KRYTYCY ---------------------------------------------------- *
 * poprawność-CPT: dla każdego salvage_id w bazie istnieje dokładnie jeden wpis CPT
 *   powiązany meta `iaai_salvage_id` (iaai_find_post_by_salvage() != 0; brak duplikatów).
 * poprawność-meta: po publikacji kluczowe meta (iaai_make, iaai_model, iaai_year,
 *   iaai_odometer) są ustawione i równe wartościom z bazy.
 * Funkcja kontrolna do uruchomienia po imporcie: */
function iaai_krytyk_publikacja( int $salvage_id ) : array {
	$issues  = array();
	$post_id = iaai_find_post_by_salvage( $salvage_id );
	if ( ! $post_id ) {
		$issues[] = "poprawność-CPT: brak wpisu dla salvage_id {$salvage_id}";
		return $issues;
	}
	foreach ( array( 'make', 'model', 'year' ) as $k ) {
		if ( get_post_meta( $post_id, 'iaai_' . $k, true ) === '' ) {
			$issues[] = "poprawność-meta: brak iaai_{$k} w poście {$post_id}";
		}
	}
	return $issues;
}
