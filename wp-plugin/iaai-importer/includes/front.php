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

/**
 * Adresy zdjęć pojazdu prosto z nowej bazy (hotlink z vis.iaai.com).
 * @return string[] URL-e w kolejności seq (już przez esc_url_raw).
 */
function iaai_get_image_urls( int $salvage_id, int $limit = 0 ) : array {
	global $wpdb;
	$table = $wpdb->prefix . 'iaai_vehicle_images';
	$sql   = "SELECT url FROM {$table} WHERE salvage_id = %d AND url IS NOT NULL ORDER BY seq ASC";
	if ( $limit > 0 ) {
		$sql .= ' LIMIT ' . absint( $limit );
	}
	$urls = $wpdb->get_col( $wpdb->prepare( $sql, $salvage_id ) );
	return array_map( 'esc_url_raw', (array) $urls );
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
		$wpdb->prepare( "SELECT url FROM {$table} WHERE salvage_id = %d ORDER BY seq ASC", $salvage_id ),
		ARRAY_A
	);
	$gallery = array();
	foreach ( $rows as $i => $r ) {
		$att = media_sideload_image( esc_url_raw( $r['url'] ), $post_id, null, 'id' );
		if ( is_wp_error( $att ) ) {
			continue;
		}
		if ( $i === 0 ) {
			set_post_thumbnail( $post_id, $att );   // miniatura = pierwsze zdjęcie
		}
		$gallery[] = (int) $att;
	}
	update_post_meta( $post_id, 'iaai_gallery', $gallery );
	update_post_meta( $post_id, '_iaai_media_done', 1 );
	return count( $gallery );
}

/* ====================================================================
 * 🔵 AGENT `front` — render listy i strony pojazdu (escapowane!)
 * ==================================================================== */

/** [iaai_pojazdy ile="12"] — siatka pojazdów. */
add_shortcode( 'iaai_pojazdy', 'iaai_render_list' );
function iaai_render_list( $atts ) : string {
	$a = shortcode_atts( array( 'ile' => 12 ), $atts );
	$q = new WP_Query( array(
		'post_type'      => IAAI_CPT,
		'posts_per_page' => absint( $a['ile'] ),
		'post_status'    => 'publish',
	) );
	if ( ! $q->have_posts() ) {
		return '<p>' . esc_html__( 'Brak pojazdów.', 'iaai-importer' ) . '</p>';
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
			$thumb = $first
				? '<img class="iaai-thumb" loading="lazy" src="' . esc_url( $first[0] ) . '" alt="'
					. esc_attr( get_the_title() ) . '" />'
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
	return $out . '</ul>';
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
		foreach ( $sid ? iaai_get_image_urls( $sid ) : array() as $u ) {
			$imgs .= '<img class="iaai-gallery-img" loading="lazy" src="' . esc_url( $u )
				. '" alt="' . esc_attr( get_the_title() ) . '" />';
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
