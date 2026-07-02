<?php
/**
 * Dział 9 · FRONT I MEDIA — agenci `front` + `media`, krytyk `render`.
 *
 * `media`: tryb zdjęć (decyzja projektu: HOTLINK). Domyślnie zdjęcia są pokazywane
 *          bezpośrednio z vis.iaai.com po URL-ach z {$wpdb->prefix}iaai_vehicle_images
 *          (0 miejsca na dysku). Opcjonalny tryb „download" sideloaduje do mediów WP.
 * `front`: renderuje listę i stronę pojazdu (dane escapowane przez dział 6).
 *
 * Oryginał: docs/refs/wordpress-media.md (media_sideload_image + szablony).
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/* ====================================================================
 * 🔵 AGENT `media` — zdjęcia pojazdu
 * ==================================================================== */

/**
 * Tryb zdjęć: 'hotlink' (domyślny, decyzja projektu) lub 'download'.
 * Można nadpisać filtrem: add_filter('iaai_image_mode', fn() => 'download');
 */
function iaai_image_mode() : string {
	$mode = apply_filters( 'iaai_image_mode', 'hotlink' );
	return in_array( $mode, array( 'hotlink', 'download' ), true ) ? $mode : 'hotlink';
}

/** Górny limit zdjęć renderowanych na pojazd (ochrona przed nadmiarem / DoS). */
const IAAI_MAX_IMAGES = 40;

/**
 * Adresy zdjęć pojazdu prosto z nowej bazy (hotlink z vis.iaai.com).
 * Każdy URL przechodzi przez allowlist hosta IAAI (SSRF / podstawione URL-e odrzucone).
 * @return string[] bezpieczne URL-e w kolejności seq.
 */
function iaai_get_image_urls( int $salvage_id, int $limit = 0 ) : array {
	global $wpdb;
	$table = $wpdb->prefix . 'iaai_vehicle_images';
	$cap   = $limit > 0 ? min( absint( $limit ), IAAI_MAX_IMAGES ) : IAAI_MAX_IMAGES;
	$urls  = $wpdb->get_col( $wpdb->prepare(
		"SELECT url FROM {$table} WHERE salvage_id = %d AND url IS NOT NULL ORDER BY seq ASC LIMIT %d",
		$salvage_id,
		$cap
	) );
	$safe = array();
	foreach ( (array) $urls as $u ) {
		$s = iaai_safe_image_url( (string) $u );   // dział 6: tylko host IAAI, https/http
		if ( '' !== $s ) {
			$safe[] = $s;
		}
	}
	return $safe;
}

/**
 * F3 — czytelny przebieg z jednostką + przeliczeniem na km (baza pozostaje wierną
 * kopią IAAI: km liczymy przy wyświetlaniu, nie zapisujemy własnej kolumny).
 * "169594" + "mi" -> "169 594 km (105 380 mi)". Gdy uom=km, pokazujemy km bez przeliczeń.
 * @return string już bezpieczny (esc_html w środku) tekst HTML.
 */
function iaai_format_odometer( $value, string $uom = 'mi' ) : string {
	$value = (int) $value;
	if ( $value <= 0 ) {
		return '';
	}
	$uom = strtolower( $uom ?: 'mi' );
	if ( 'km' === $uom ) {
		return esc_html( number_format_i18n( $value ) . ' km' );
	}
	$km = (int) round( $value * 1.609344 );          // mi -> km
	return esc_html( number_format_i18n( $km ) . ' km (' . number_format_i18n( $value ) . ' mi)' );
}

/**
 * Sideloaduje zdjęcia pojazdu do mediów WP (lazy — tylko raz). Pierwsze zdjęcie =
 * miniatura (featured), reszta = galeria (meta iaai_gallery).
 * @return int liczba zaimportowanych załączników.
 */
function iaai_import_images( int $salvage_id, int $post_id ) : int {
	if ( get_post_meta( $post_id, '_iaai_media_done', true ) ) {
		return 0;                                   // już zaimportowane
	}
	require_once ABSPATH . 'wp-admin/includes/media.php';
	require_once ABSPATH . 'wp-admin/includes/file.php';
	require_once ABSPATH . 'wp-admin/includes/image.php';

	global $wpdb;
	$table = $wpdb->prefix . 'iaai_vehicle_images';
	$rows  = $wpdb->get_results(
		$wpdb->prepare(
			"SELECT url FROM {$table} WHERE salvage_id = %d AND url IS NOT NULL ORDER BY seq ASC LIMIT %d",
			$salvage_id,
			IAAI_MAX_IMAGES
		),
		ARRAY_A
	);
	$gallery = array();
	foreach ( $rows as $i => $r ) {
		$src = iaai_safe_image_url( (string) $r['url'] );   // SSRF: tylko host IAAI
		if ( '' === $src ) {
			iaai_log( 'media: pominięto niedozwolony URL zdjęcia dla lotu ' . $salvage_id, 'warn' );
			continue;
		}
		$att = media_sideload_image( $src, $post_id, null, 'id' );
		if ( is_wp_error( $att ) ) {
			iaai_log( 'media: sideload nieudany (' . $att->get_error_code() . ') lot ' . $salvage_id, 'warn' );
			continue;
		}
		// Upewnij się, że pobrany załącznik to OBRAZ (blokuje podmianę na inny typ pliku).
		if ( 0 !== strpos( (string) get_post_mime_type( $att ), 'image/' ) ) {
			wp_delete_attachment( (int) $att, true );
			continue;
		}
		if ( empty( $gallery ) ) {
			set_post_thumbnail( $post_id, $att );   // miniatura = pierwsze poprawne zdjęcie
		}
		$gallery[] = (int) $att;
	}
	update_post_meta( $post_id, 'iaai_gallery', $gallery );
	update_post_meta( $post_id, '_iaai_media_done', 1 );
	return count( $gallery );
}

/* ====================================================================
 * Style frontu — minimalny CSS, DZIEDZICZY MOTYW (dział 9).
 * Wczytywany TYLKO tam, gdzie potrzebny: strona/archiwum pojazdu albo
 * strona z shortcode [iaai_pojazdy]. Zero obciążenia reszty witryny.
 * ==================================================================== */
add_action( 'wp_enqueue_scripts', 'iaai_enqueue_styles' );
function iaai_enqueue_styles() : void {
	wp_register_style( 'iaai-importer', IAAI_IMPORTER_URL . 'assets/iaai.css', array(), IAAI_IMPORTER_VERSION );

	$need = is_singular( IAAI_CPT ) || is_post_type_archive( IAAI_CPT );
	if ( ! $need && is_singular() ) {
		$post = get_post();
		if ( $post instanceof WP_Post && has_shortcode( (string) $post->post_content, 'iaai_pojazdy' ) ) {
			$need = true;
		}
	}
	if ( $need ) {
		wp_enqueue_style( 'iaai-importer' );
	}
}

/* ====================================================================
 * 🔵 AGENT `front` — render listy i strony pojazdu (escapowane!)
 * ==================================================================== */

/** [iaai_pojazdy ile="12"] — siatka pojazdów. Wynik cache'owany (Transient API). */
add_shortcode( 'iaai_pojazdy', 'iaai_render_list' );
function iaai_render_list( $atts ) : string {
	$a   = shortcode_atts( array( 'ile' => 12 ), $atts, 'iaai_pojazdy' );
	// Clamp 1..48 — ochrona przed [iaai_pojazdy ile="999999"] (DoS / ciężkie zapytanie).
	$ile = max( 1, min( 48, absint( $a['ile'] ) ) );

	// Fallback: gdy shortcode użyty poza wykrytą stroną (widget/blok) — dołóż styl.
	if ( ! wp_style_is( 'iaai-importer', 'enqueued' ) ) {
		wp_enqueue_style( 'iaai-importer' );
	}

	// Cache na 5 min — odciąża bazę przy ruchu (DoS/throttling). Unieważniany przy publikacji.
	$cache_key = 'iaai_list_' . $ile;
	$cached    = get_transient( $cache_key );
	if ( false !== $cached ) {
		return $cached;
	}

	$q = new WP_Query( array(
		'post_type'           => IAAI_CPT,
		'posts_per_page'      => $ile,
		'post_status'         => 'publish',
		'no_found_rows'       => true,
		'ignore_sticky_posts' => true,
	) );
	if ( ! $q->have_posts() ) {
		$empty = '<p>' . esc_html__( 'Brak pojazdów.', 'iaai-importer' ) . '</p>';
		set_transient( $cache_key, $empty, 5 * MINUTE_IN_SECONDS );
		return $empty;
	}
	$out = '<ul class="iaai-pojazdy-grid">';
	while ( $q->have_posts() ) {
		$q->the_post();
		$id    = get_the_ID();
		$odo   = iaai_format_odometer(
			get_post_meta( $id, 'iaai_odometer', true ),
			(string) get_post_meta( $id, 'iaai_odometer_uom', true )
		);
		$dmg   = get_post_meta( $id, 'iaai_primary_damage', true );
		// Miniatura: hotlink (1. zdjęcie z bazy) albo — w trybie download — miniatura WP.
		if ( 'hotlink' === iaai_image_mode() ) {
			$sid   = (int) get_post_meta( $id, 'iaai_salvage_id', true );
			$first = $sid ? iaai_get_image_urls( $sid, 1 ) : array();
			$alt   = get_the_title() . ( $dmg ? ' – ' . $dmg : '' );   // opisowy alt (SEO/dostępność)
			$thumb = $first
				? '<img class="iaai-thumb" loading="lazy" src="' . esc_url( $first[0] ) . '" alt="'
					. esc_attr( $alt ) . '" />'
				: '';
		} else {
			$thumb = get_the_post_thumbnail( $id, 'medium' );       // już bezpieczne
		}
		$out  .= '<li class="iaai-card"><a href="' . esc_url( get_permalink( $id ) ) . '">'
			. $thumb
			. '<h3>' . esc_html( get_the_title() ) . '</h3>'
			. ( $odo ? '<span class="odo">' . $odo . '</span> ' : '' )
			. '<span class="dmg">' . esc_html( $dmg ) . '</span>'
			. '</a></li>';
	}
	wp_reset_postdata();
	$out .= '</ul>';
	set_transient( $cache_key, $out, 5 * MINUTE_IN_SECONDS );
	return $out;
}

/** Czyści cache list po publikacji/zmianach (woła to dział 8). */
function iaai_flush_list_cache() : void {
	for ( $i = 1; $i <= 48; $i++ ) {
		delete_transient( 'iaai_list_' . $i );
	}
}

/** Strona pojedynczego pojazdu: dokleja tabelę danych + galerię do treści. */
add_filter( 'the_content', 'iaai_render_single' );
function iaai_render_single( string $content ) : string {
	if ( ! is_singular( IAAI_CPT ) || ! in_the_loop() || ! is_main_query() ) {
		return $content;
	}
	$id     = get_the_ID();
	$fields = array(
		'stock_number' => 'Stock #', 'item_id' => 'Item #',
		'vin' => 'VIN', 'year' => 'Rok', 'make' => 'Marka', 'model' => 'Model',
		'odometer' => 'Przebieg', 'primary_damage' => 'Uszkodzenie', 'title' => 'Tytuł',
		'run_and_drive' => 'Run & Drive', 'key_available' => 'Kluczyk', 'buy_now' => 'Buy Now',
	);
	$rows = '';
	foreach ( $fields as $key => $label ) {
		$val = get_post_meta( $id, 'iaai_' . $key, true );
		if ( $val === '' ) {
			continue;
		}
		// F3: przebieg z przeliczeniem na km (już zescapowany); reszta przez esc_html.
		if ( 'odometer' === $key ) {
			$cell = iaai_format_odometer( $val, (string) get_post_meta( $id, 'iaai_odometer_uom', true ) );
		} else {
			$cell = esc_html( $val );
		}
		$rows .= '<tr><th>' . esc_html( $label ) . '</th><td>' . $cell . '</td></tr>';
	}
	// Galeria: hotlink (URL-e z bazy, vis.iaai.com) albo załączniki WP (tryb download).
	$imgs = '';
	if ( 'hotlink' === iaai_image_mode() ) {
		$sid = (int) get_post_meta( $id, 'iaai_salvage_id', true );
		$n   = 0;
		foreach ( $sid ? iaai_get_image_urls( $sid ) : array() as $u ) {
			$n++;
			$alt   = get_the_title() . ' – zdjęcie ' . $n;   // unikalny, opisowy alt (SEO)
			$imgs .= '<img class="iaai-gallery-img" loading="lazy" src="' . esc_url( $u )
				. '" alt="' . esc_attr( $alt ) . '" />';
		}
	} else {
		foreach ( (array) get_post_meta( $id, 'iaai_gallery', true ) as $att ) {
			$imgs .= wp_get_attachment_image( (int) $att, 'large', false, array( 'class' => 'iaai-gallery-img' ) );
		}
	}
	return $content
		. '<table class="iaai-specs">' . $rows . '</table>'
		. ( $imgs ? '<div class="iaai-gallery">' . $imgs . '</div>' : '' );
}

/* ---------- 🔴 KRYTYK `render` ------------------------------------------- *
 * media (hotlink): pojazd ze zdjęciami w bazie ma niepuste URL-e do hotlinka.
 * media (download): post ma miniaturę i liczba załączników == liczba zdjęć w bazie.
 * front: całe wyjście przez esc_html/esc_url/esc_attr/wp_get_attachment_image
 *        (brak surowego echo) — brak XSS. */
function iaai_krytyk_render( int $salvage_id, int $post_id ) : array {
	global $wpdb;
	$issues = array();
	$table  = $wpdb->prefix . 'iaai_vehicle_images';
	$db     = (int) $wpdb->get_var( $wpdb->prepare(
		"SELECT COUNT(*) FROM {$table} WHERE salvage_id = %d", $salvage_id ) );

	if ( 'hotlink' === iaai_image_mode() ) {
		if ( $db > 0 && count( iaai_get_image_urls( $salvage_id ) ) < $db ) {
			$issues[] = "render(media/hotlink): brak URL-i do hotlinka dla części z {$db} zdjęć";
		}
		return $issues;
	}
	// tryb download
	if ( ! has_post_thumbnail( $post_id ) ) {
		$issues[] = "render(media): post {$post_id} bez miniatury";
	}
	$got = count( (array) get_post_meta( $post_id, 'iaai_gallery', true ) );
	if ( $db && $got < $db ) {
		$issues[] = "render(media): zaimportowano {$got}/{$db} zdjęć";
	}
	return $issues;
}
