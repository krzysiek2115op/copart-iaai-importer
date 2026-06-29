<?php
/**
 * Dział 6 · BEZPIECZEŃSTWO — agenci `sanityzacja` + `nonce`, krytyk `podatności`.
 *
 * Zasady WordPress: sanityzuj WEJŚCIE, escapuj WYJŚCIE, weryfikuj NONCE, SQL przez
 * $wpdb->prepare(). Oryginał: docs/refs/wordpress-security.md.
 *
 * Bezpieczna ścieżka jest tu DOMYŚLNA — inne działy używają tych funkcji.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/* =====================================================================
 * 🔵 AGENT `sanityzacja` — czyści dane wchodzące do bazy/WP
 * ===================================================================== */

/**
 * Sanityzuje rekord pojazdu (z agentów Pythona / formularzy) przed zapisem.
 * Każde pole przez właściwą funkcję WP wg typu.
 */
function iaai_sanitize_vehicle( array $v ) : array {
	$int    = array( 'salvage_id', 'item_id', 'year', 'odometer', 'cylinders', 'branch_id' );
	$text   = array( 'stock_number', 'vin', 'make', 'model', 'series', 'vehicle_type',
		'body_style', 'engine', 'fuel_type', 'transmission', 'drive_line', 'color',
		'odometer_uom', 'odometer_brand', 'primary_damage', 'secondary_damage', 'loss',
		'title', 'run_and_drive', 'key_available', 'selling_branch', 'lane', 'aisle' );
	$float  = array( 'buy_now', 'current_bid' );
	$out    = array();

	foreach ( $int as $k ) {
		if ( isset( $v[ $k ] ) && $v[ $k ] !== null ) {
			$out[ $k ] = absint( $v[ $k ] );
		}
	}
	foreach ( $text as $k ) {
		if ( isset( $v[ $k ] ) && $v[ $k ] !== null ) {
			$out[ $k ] = sanitize_text_field( (string) $v[ $k ] );
		}
	}
	foreach ( $float as $k ) {
		if ( isset( $v[ $k ] ) && $v[ $k ] !== null ) {
			$out[ $k ] = (float) $v[ $k ];
		}
	}
	if ( isset( $v['detail_url'] ) ) {
		$out['detail_url'] = esc_url_raw( $v['detail_url'] );          // do zapisu w bazie
	}
	if ( isset( $v['status'] ) ) {
		$allowed       = array( 'active', 'sold', 'removed' );
		$s             = sanitize_key( $v['status'] );
		$out['status'] = in_array( $s, $allowed, true ) ? $s : 'active';
	}
	return $out;
}

/**
 * Escapuje rekord do BEZPIECZNEGO WYŚWIETLENIA (wywoływane tuż przed echo — dział 9).
 */
function iaai_escape_vehicle_for_output( array $v ) : array {
	$out = array();
	foreach ( $v as $k => $val ) {
		if ( $val === null ) {
			$out[ $k ] = '';
		} elseif ( $k === 'detail_url' || $k === 'url' ) {
			$out[ $k ] = esc_url( $val );
		} else {
			$out[ $k ] = esc_html( $val );
		}
	}
	return $out;
}

/* =====================================================================
 * 🔵 AGENT `nonce` — chroni akcje admina (CSRF)
 * ===================================================================== */

/** Pole nonce do formularza/akcji admina. */
function iaai_nonce_field( string $action = 'iaai_action' ) : void {
	wp_nonce_field( $action, '_iaai_nonce' );
}

/** Weryfikacja nonce + uprawnień przy obsłudze akcji admina; przerywa, gdy niepoprawne. */
function iaai_verify_admin_action( string $action = 'iaai_action', string $cap = 'manage_options' ) : void {
	if ( ! current_user_can( $cap ) ) {
		wp_die( esc_html__( 'Brak uprawnień.', 'iaai-importer' ) );
	}
	check_admin_referer( $action, '_iaai_nonce' );   // sam przerywa przy złym nonce
}

/* =====================================================================
 * 🔴 KRYTYK `podatności` — checklista wymuszana przez kod
 * ===================================================================== *
 * 1. Każde echo danych pojazdu MUSI przejść przez iaai_escape_vehicle_for_output()
 *    albo esc_html()/esc_attr()/esc_url() (XSS).
 * 2. Każda akcja admina MUSI wołać iaai_verify_admin_action() (CSRF/uprawnienia).
 * 3. Każde zapytanie SQL MUSI używać $wpdb->prepare() z placeholderami (SQLi):
 *       $wpdb->get_results( $wpdb->prepare(
 *           "SELECT * FROM {$wpdb->prefix}iaai_vehicles WHERE salvage_id = %d", $id ) );
 * 4. Wejście do bazy zawsze przez iaai_sanitize_vehicle().
 * Egzekwowanie: te funkcje są DOMYŚLNĄ ścieżką; brak ich użycia = błąd w code review. */
