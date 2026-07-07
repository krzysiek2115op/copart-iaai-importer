<?php
/**
 * Dział 9 (SEO) — agent `seo`, krytyk `indeksacja`.
 *
 * Optymalizacja pod wyszukiwarki dla podstrony „Nasze auta" i stron pojazdów:
 *  - dane strukturalne Schema.org (Car + Offer) w JSON-LD → rich results w Google,
 *  - meta description + Open Graph + Twitter Card (fallback),
 *  - poprawne alt zdjęć, semantyka.
 *
 * ANTY-KONFLIKT: jeśli aktywna jest wtyczka SEO (Yoast/RankMath/AIOSEO/SEOPress),
 * NIE dublujemy title/description/OG — te robi wtyczka SEO. JSON-LD „Car" i tak
 * dodajemy (wtyczki SEO nie generują schematu pojazdu), pilnując braku duplikatu.
 *
 * Sitemapa: CPT „pojazd" jest `public` + `show_in_rest` → trafia do sitemap.xml
 * rdzenia WP (od 5.5) automatycznie. Kanoniczne URL-e: rdzeń WP.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/** Czy działa zewnętrzna wtyczka SEO (żeby nie dublować meta/OG). */
function iaai_seo_plugin_active() : bool {
	$active = defined( 'WPSEO_VERSION' )              // Yoast
		|| class_exists( 'RankMath' )                 // Rank Math
		|| defined( 'AIOSEO_VERSION' )                // All in One SEO
		|| defined( 'SEOPRESS_VERSION' )              // SEOPress
		|| function_exists( 'the_seo_framework' );    // The SEO Framework
	return (bool) apply_filters( 'iaai_seo_plugin_active', $active );
}

/** Zbiera „czyste" (nieescapowane) dane pojazdu potrzebne do SEO. */
function iaai_seo_vehicle_data( int $post_id ) : array {
	$m = static function ( string $k ) use ( $post_id ) {
		return (string) get_post_meta( $post_id, 'iaai_' . $k, true );
	};
	$year  = trim( $m( 'year' ) );
	$make  = trim( $m( 'make' ) );
	$model = trim( $m( 'model' ) );
	$title = trim( "$year $make $model" );

	$odo_val = (int) $m( 'odometer' );
	$odo_uom = strtolower( $m( 'odometer_uom' ) ?: 'mi' );
	$odo_km  = 'km' === $odo_uom ? $odo_val : (int) round( $odo_val * 1.609344 );
	$odo_txt = $odo_val > 0 ? number_format_i18n( $odo_km ) . ' km' : '';

	return array(
		'title'    => $title,
		'year'     => $year,
		'make'     => $make,
		'model'    => $model,
		'vin'      => trim( $m( 'vin' ) ),
		'color'    => trim( $m( 'color' ) ),
		'fuel'     => trim( $m( 'fuel_type' ) ),
		'trans'    => trim( $m( 'transmission' ) ),
		'damage'   => trim( $m( 'primary_damage' ) ),
		'branch'   => trim( $m( 'selling_branch' ) ),
		'odo_km'   => $odo_km,
		'odo_txt'  => $odo_txt,
		'buy_now'  => (float) $m( 'buy_now' ),
	);
}

/** Buduje meta description (~155 znaków) z danych pojazdu. */
function iaai_seo_description( array $d ) : string {
	$parts = array();
	if ( $d['title'] !== '' ) {
		$parts[] = $d['title'];
	}
	if ( $d['damage'] !== '' ) {
		$parts[] = 'uszkodzenie: ' . $d['damage'];
	}
	if ( $d['odo_txt'] !== '' ) {
		$parts[] = 'przebieg ' . $d['odo_txt'];
	}
	if ( $d['branch'] !== '' ) {
		$parts[] = 'oddział ' . $d['branch'];
	}
	$desc = implode( ', ', $parts );
	$desc = $desc !== '' ? $desc . '. Auto z aukcji samochodowych w USA (IAAI / Copart) — zdjęcia i pełne dane.' : '';
	if ( function_exists( 'mb_substr' ) && mb_strlen( $desc ) > 160 ) {
		$desc = rtrim( mb_substr( $desc, 0, 157 ) ) . '…';
	}
	return $desc;
}

/* ====================================================================
 * <head> — meta description, Open Graph, Twitter, JSON-LD
 * ==================================================================== */
add_action( 'wp_head', 'iaai_seo_head', 5 );
function iaai_seo_head() : void {
	if ( ! defined( 'IAAI_CPT' ) ) {
		return;
	}

	// --- Podstrona „Nasze auta" / archiwum: tylko opis (gdy brak wtyczki SEO) ---
	$is_landing = is_page() && function_exists( 'iaai_get_landing_page_id' )
		&& get_the_ID() === iaai_get_landing_page_id();
	if ( ( is_post_type_archive( IAAI_CPT ) || $is_landing ) && ! iaai_seo_plugin_active() ) {
		$desc = esc_attr__( 'Aktualna oferta pojazdów z aukcji IAAI i Copart — zdjęcia, przebieg, zakres uszkodzeń i pełne dane techniczne. Oferta odświeża się automatycznie.', 'iaai-importer' );
		echo '<meta name="description" content="' . $desc . "\" />\n";
		return;
	}

	if ( ! is_singular( IAAI_CPT ) ) {
		return;
	}

	$post_id = get_the_ID();
	$d       = iaai_seo_vehicle_data( $post_id );
	$url     = get_permalink( $post_id );
	$sid     = (int) get_post_meta( $post_id, 'iaai_salvage_id', true );
	$imgs    = ( $sid && function_exists( 'iaai_get_image_urls' ) ) ? iaai_get_image_urls( $sid, 10 ) : array();
	$desc    = iaai_seo_description( $d );

	// --- meta description + Open Graph + Twitter (tylko gdy brak wtyczki SEO) ---
	if ( ! iaai_seo_plugin_active() ) {
		if ( $desc !== '' ) {
			echo '<meta name="description" content="' . esc_attr( $desc ) . "\" />\n";
		}
		echo '<meta property="og:type" content="product" />' . "\n";
		echo '<meta property="og:title" content="' . esc_attr( get_the_title( $post_id ) ) . "\" />\n";
		echo '<meta property="og:url" content="' . esc_url( $url ) . "\" />\n";
		if ( $desc !== '' ) {
			echo '<meta property="og:description" content="' . esc_attr( $desc ) . "\" />\n";
		}
		if ( ! empty( $imgs[0] ) ) {
			echo '<meta property="og:image" content="' . esc_url( $imgs[0] ) . "\" />\n";
			echo '<meta name="twitter:card" content="summary_large_image" />' . "\n";
			echo '<meta name="twitter:image" content="' . esc_url( $imgs[0] ) . "\" />\n";
		}
	}

	// --- JSON-LD Schema.org „Car" (ZAWSZE — wtyczki SEO tego nie robią) ---
	$schema = array(
		'@context' => 'https://schema.org',
		'@type'    => 'Car',
		'name'     => $d['title'] !== '' ? $d['title'] : get_the_title( $post_id ),
		'url'      => $url,
	);
	if ( $desc !== '' ) {
		$schema['description'] = $desc;
	}
	if ( $d['make'] !== '' ) {
		$schema['brand'] = array( '@type' => 'Brand', 'name' => $d['make'] );
	}
	if ( $d['model'] !== '' ) {
		$schema['model'] = $d['model'];
	}
	if ( $d['year'] !== '' ) {
		$schema['vehicleModelDate'] = $d['year'];
		$schema['productionDate']   = $d['year'];
	}
	if ( $d['color'] !== '' ) {
		$schema['color'] = $d['color'];
	}
	if ( $d['fuel'] !== '' ) {
		$schema['fuelType'] = $d['fuel'];
	}
	if ( $d['trans'] !== '' ) {
		$schema['vehicleTransmission'] = $d['trans'];
	}
	// VIN tylko gdy PEŁNY (17 znaków, bez maski) — nie publikujemy zamaskowanego.
	if ( 17 === strlen( $d['vin'] ) && ! preg_match( '/[*x]/i', $d['vin'] ) ) {
		$schema['vehicleIdentificationNumber'] = $d['vin'];
	}
	if ( $d['odo_km'] > 0 ) {
		$schema['mileageFromOdometer'] = array(
			'@type'    => 'QuantitativeValue',
			'value'    => $d['odo_km'],
			'unitCode' => 'KMT',
		);
	}
	if ( $imgs ) {
		$schema['image'] = array_values( $imgs );
	}
	if ( $d['buy_now'] > 0 ) {
		$schema['offers'] = array(
			'@type'         => 'Offer',
			'price'         => $d['buy_now'],
			'priceCurrency' => apply_filters( 'iaai_seo_currency', 'USD' ),
			'availability'  => 'https://schema.org/InStock',
			'url'           => $url,
		);
	}

	echo '<script type="application/ld+json">'
		. wp_json_encode( $schema, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE )
		. "</script>\n";
}

/* ---------- 🔴 KRYTYK `indeksacja` --------------------------------------- *
 * - Strona pojazdu ma JSON-LD @type=Car z name, brand/model i (gdy są) image/offers.
 * - Zamaskowany VIN NIE trafia do schematu (tylko pełny 17-znakowy).
 * - Przy aktywnej wtyczce SEO nie emitujemy własnych meta/OG (brak duplikatów).
 * - CPT public+show_in_rest → obecny w sitemap.xml rdzenia WP. */
function iaai_krytyk_seo( int $post_id ) : array {
	$issues = array();
	$d      = iaai_seo_vehicle_data( $post_id );
	if ( $d['title'] === '' ) {
		$issues[] = 'indeksacja: brak roku/marki/modelu — słaby tytuł SEO';
	}
	if ( 17 === strlen( $d['vin'] ) && preg_match( '/[*x]/i', $d['vin'] ) ) {
		$issues[] = 'indeksacja: VIN wygląda na zamaskowany — pominięty w schemacie (OK)';
	}
	return $issues;
}
