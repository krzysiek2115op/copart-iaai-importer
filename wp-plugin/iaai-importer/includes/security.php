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
 * SSRF / host-allowlist dla zdjęć (vis.iaai.com)
 * ===================================================================== */

/** Dozwolone hosty zdjęć — tylko domena IAAI (blokuje SSRF / podstawione URL-e). */
function iaai_allowed_image_host( string $url ) : bool {
	$host = wp_parse_url( $url, PHP_URL_HOST );
	if ( ! is_string( $host ) || '' === $host ) {
		return false;
	}
	$host    = strtolower( $host );
	$allowed = apply_filters( 'iaai_allowed_image_hosts', array( 'iaai.com', 'vis.iaai.com' ) );
	foreach ( (array) $allowed as $a ) {
		$a = strtolower( (string) $a );
		if ( $host === $a || ( strlen( $host ) > strlen( $a ) && substr( $host, - ( strlen( $a ) + 1 ) ) === '.' . $a ) ) {
			return true;
		}
	}
	return false;
}

/**
 * Zwraca BEZPIECZNY URL zdjęcia do wyświetlenia (https + host IAAI), albo '' gdy niedozwolony.
 * Blokuje inne schematy (javascript:, data:), inne hosty (SSRF/hotlink na obce serwery).
 */
function iaai_safe_image_url( string $url ) : string {
	$url = esc_url_raw( $url, array( 'https', 'http' ) );
	if ( '' === $url || ! iaai_allowed_image_host( $url ) ) {
		return '';
	}
	return $url;
}

/* =====================================================================
 * Logowanie (nigdy do użytkownika końcowego) + lock importu (mutex)
 * ===================================================================== */

/** Log do dziennika serwera (error_log). NIE trafia do przeglądarki użytkownika. */
function iaai_log( string $message, string $level = 'info' ) : void {
	$line = '[iaai-importer][' . sanitize_key( $level ) . '] ' . $message;
	if ( defined( 'IAAI_LOG_FILE' ) && IAAI_LOG_FILE ) {
		error_log( gmdate( 'c' ) . ' ' . $line . "\n", 3, IAAI_LOG_FILE );
	} else {
		error_log( $line );
	}
}

/**
 * Mutex oparty na MySQL GET_LOCK (atomowy, per-połączenie) — chroni przed równoległym
 * importem/publikacją (double-run, race condition, cron + WP-CLI naraz).
 * @return bool true gdy zdobyto blokadę.
 */
function iaai_db_lock( string $name, int $timeout = 0 ) : bool {
	global $wpdb;
	$got = $wpdb->get_var( $wpdb->prepare( 'SELECT GET_LOCK(%s, %d)', 'iaai_' . $name, $timeout ) );
	return '1' === (string) $got;
}

/** Zwolnienie blokady GET_LOCK. */
function iaai_db_unlock( string $name ) : void {
	global $wpdb;
	$wpdb->get_var( $wpdb->prepare( 'SELECT RELEASE_LOCK(%s)', 'iaai_' . $name ) );
}

/* =====================================================================
 * Nagłówki bezpieczeństwa (na stronach pojazdów) — bezpieczny podzbiór
 * ===================================================================== */

/**
 * Wysyła zachowawcze nagłówki na stronach CPT „pojazd”. CSP/HSTS celowo NIE są
 * wymuszane z wtyczki (HSTS musi być globalny na serwerze, CSP wymaga strojenia
 * pod motyw) — to rekomendacja serwerowa (patrz raport bezpieczeństwa).
 * Wyłączalne: add_filter('iaai_send_security_headers','__return_false').
 */
add_action( 'template_redirect', 'iaai_maybe_send_security_headers' );
function iaai_maybe_send_security_headers() : void {
	if ( headers_sent() || ! apply_filters( 'iaai_send_security_headers', true ) ) {
		return;
	}
	if ( ! function_exists( 'is_singular' ) || ! defined( 'IAAI_CPT' ) ) {
		return;
	}
	if ( is_singular( IAAI_CPT ) || is_post_type_archive( IAAI_CPT ) ) {
		header( 'X-Content-Type-Options: nosniff' );
		header( 'X-Frame-Options: SAMEORIGIN' );
		header( 'Referrer-Policy: strict-origin-when-cross-origin' );
		header( 'Permissions-Policy: geolocation=(), microphone=(), camera=()' );
	}
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
 * 5. URL-e zdjęć WYŁĄCZNIE przez iaai_safe_image_url() (SSRF / host-allowlist IAAI).
 * 6. Import/publikacja pod MUTEX-em (iaai_db_lock) — brak równoległych przebiegów.
 * 7. Błędy logujemy (iaai_log) — NIGDY nie pokazujemy użytkownikowi końcowemu.
 * Egzekwowanie: te funkcje są DOMYŚLNĄ ścieżką; brak ich użycia = błąd w code review. */
