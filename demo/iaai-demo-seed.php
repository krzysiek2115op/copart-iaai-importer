<?php
/**
 * IAAI Importer — SEED DEMO „Kredyt Kompas" (WYŁĄCZNIE dla wersji demonstracyjnej w WordPress Playground).
 *
 * Ładowany jako mu-plugin. Jednorazowo (guard: opcja iaai_demo_seeded):
 *   1) pozwala pokazywać obrazki z placehold.co (produkcja: tylko host iaai.com — anty-SSRF),
 *   2) odtwarza prawdziwe strony Kredyt Kompas (Start, Kredyty, Kalkulator, O nas, FAQ, Kontakt…)
 *      z pliku danych kredyt-kompas-content.php i ustawia „Start" jako stronę główną,
 *   3) wstawia przykładowe auta + zdjęcia i publikuje je jako CPT „pojazd”,
 *   4) buduje górne menu (prawdziwe strony + „Nasze auta").
 *
 * ⚠ To jest wersja pokazowa. NIE używać na produkcji.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/* Demo: dopuść hotlink obrazków z placehold.co (na produkcji zostaje sam iaai.com). */
add_filter( 'iaai_allowed_image_hosts', function ( $hosts ) {
	$hosts[] = 'placehold.co';
	return $hosts;
} );

/* Demo: wyglad marki Kredyt Kompas — fonty (Sora / IBM Plex) + design system
   (demo/pages/assets/styles.css skopiowany jako wp-content/kredyt-kompas.css).
   Enqueue site-wide, priorytet 20 (po stylach motywu), by nadpisac tlo/typografie. */
add_action( 'wp_enqueue_scripts', function () {
	wp_enqueue_style(
		'kk-fonts',
		'https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap',
		array(),
		null
	);
	wp_enqueue_style( 'kk-brand', content_url( 'kredyt-kompas.css' ), array( 'kk-fonts' ), '1' );
}, 20 );

add_action( 'init', 'iaai_demo_seed_now', 99 );

/** Jednorazowy seed całej strony demonstracyjnej. */
function iaai_demo_seed_now() : void {
	if ( get_option( 'iaai_demo_seeded' ) ) {
		return;                                   // już zasiane
	}
	if ( ! function_exists( 'iaai_publish_vehicle' ) ) {
		return;                                   // wtyczka jeszcze się nie załadowała
	}

	// Ładne odnośniki (potrzebne dla /nasze-auta/ i slugów stron).
	if ( '/%postname%/' !== get_option( 'permalink_structure' ) ) {
		update_option( 'permalink_structure', '/%postname%/' );
	}

	$slug_to_id = iaai_demo_create_pages();

	// Strona główna = „Start”.
	if ( ! empty( $slug_to_id['start'] ) ) {
		update_option( 'show_on_front', 'page' );
		update_option( 'page_on_front', (int) $slug_to_id['start'] );
	}

	iaai_demo_seed_cars();
	iaai_demo_build_menu();

	flush_rewrite_rules();
	if ( function_exists( 'iaai_flush_list_cache' ) ) {
		iaai_flush_list_cache();
	}
	update_option( 'iaai_demo_seeded', 1 );
}

/**
 * Tworzy strony Kredyt Kompas z pliku danych (idempotentnie po slugu).
 * @return array<string,int> slug => post_id
 */
function iaai_demo_create_pages() : array {
	$map  = array();
	$file = WP_CONTENT_DIR . '/kredyt-kompas-content.php';
	if ( ! is_readable( $file ) ) {
		return $map;
	}
	$pages = include $file;                       // zwraca tablicę stron
	if ( ! is_array( $pages ) ) {
		return $map;
	}
	foreach ( $pages as $p ) {
		$slug = sanitize_title( $p['slug'] ?? '' );
		if ( '' === $slug ) {
			continue;
		}
		$existing = get_page_by_path( $slug );
		if ( $existing ) {
			$map[ $slug ] = (int) $existing->ID;
			continue;
		}
		// Lokalne linki -> względne (żeby działały pod adresem Playground).
		$content = (string) ( $p['content'] ?? '' );
		$content = str_replace( array( 'http://127.0.0.1:9410', 'https://127.0.0.1:9410' ), '', $content );

		$id = wp_insert_post( array(
			'post_type'    => 'page',
			'post_status'  => 'publish',
			'post_title'   => (string) ( $p['title'] ?? $slug ),
			'post_name'    => $slug,
			'post_content' => $content,
			'menu_order'   => (int) ( $p['menu_order'] ?? 0 ),
		) );
		if ( $id && ! is_wp_error( $id ) ) {
			$map[ $slug ] = (int) $id;
		}
	}
	return $map;
}

/** Buduje górne menu (blokowe): prawdziwe strony + „Nasze auta". */
function iaai_demo_build_menu() : void {
	// Kolejność i etykiety pozycji menu (slug => etykieta). Start = strona główna („/").
	$items = array(
		'start'                => 'Start',
		'kredyty-hipoteczne'   => 'Kredyty hipoteczne',
		'kalkulator'           => 'Kalkulator',
		'o-nas'                => 'O nas',
		'faq'                  => 'FAQ',
		'kontakt'              => 'Kontakt',
	);

	$links = '';
	foreach ( $items as $slug => $label ) {
		$page = get_page_by_path( $slug );
		if ( ! $page ) {
			continue;
		}
		$url  = ( 'start' === $slug ) ? '/' : '/' . $slug . '/';
		$links .= sprintf(
			'<!-- wp:navigation-link {"label":%s,"url":%s,"kind":"custom","isTopLevelLink":true} /-->' . "\n",
			wp_json_encode( $label ),
			wp_json_encode( $url )
		);
	}

	// „Nasze auta" (podstrona z wtyczki) — wyróżniona na końcu.
	$nasze = get_page_by_path( 'nasze-auta' );
	if ( $nasze ) {
		$links .= '<!-- wp:navigation-link {"label":"Nasze auta","url":"/nasze-auta/","kind":"custom","isTopLevelLink":true} /-->' . "\n";
	}

	if ( '' === $links ) {
		return;
	}

	// Nadpisz istniejący wpis nawigacji (motyw blokowy używa jedynej nawigacji) albo utwórz nowy.
	$nav = get_posts( array( 'post_type' => 'wp_navigation', 'numberposts' => 1, 'post_status' => 'any', 'fields' => 'ids' ) );
	$args = array(
		'post_type'    => 'wp_navigation',
		'post_status'  => 'publish',
		'post_title'   => 'Menu',
		'post_content' => $links,
	);
	if ( $nav ) {
		$args['ID'] = (int) $nav[0];
		wp_update_post( $args );
	} else {
		wp_insert_post( $args );
	}
}

/** Wstawia przykładowe auta + zdjęcia i publikuje je jako CPT. */
function iaai_demo_seed_cars() : void {
	global $wpdb;
	if ( function_exists( 'iaai_activate' ) ) {
		iaai_activate();                          // bezpiecznik: tabele (idempotentne dbDelta)
	}
	$veh = $wpdb->prefix . 'iaai_vehicles';
	$img = $wpdb->prefix . 'iaai_vehicle_images';

	foreach ( iaai_demo_cars() as $c ) {
		$src = (string) ( $c['v']['source'] ?? 'iaai' );   // domyślnie IAAI; auta Copart mają source=copart
		$c['v']['source'] = $src;
		$wpdb->replace( $veh, $c['v'] );
		foreach ( $c['img'] as $seq => $url ) {
			$wpdb->replace( $img, array(
				'salvage_id' => $c['v']['salvage_id'],
				'source'     => $src,
				'image_key'  => 'demo-' . $src . '-' . $c['v']['salvage_id'] . '-' . ( $seq + 1 ),
				'seq'        => $seq + 1,
				'width'      => 700,
				'height'     => 500,
				'url'        => $url,
			) );
		}
		iaai_publish_vehicle( (int) $c['v']['salvage_id'], $src );   // dual-source: publikuj wg źródła
	}
}

/** Zestaw przykładowych aut do prezentacji (dane wymyślone). */
function iaai_demo_cars() : array {
	$ph = function ( $bg, $txt ) {
		return 'https://placehold.co/700x500/' . $bg . '/ffffff?text=' . rawurlencode( $txt );
	};
	return array(
		array( 'v' => array(
			'salvage_id' => 900001, 'vin' => '1HGCM82633A004352', 'year' => 2018, 'make' => 'Toyota', 'model' => 'Camry',
			'body_style' => 'Sedan', 'odometer' => 105380, 'odometer_uom' => 'mi', 'primary_damage' => 'Front End',
			'secondary_damage' => 'Minor Dent/Scratches', 'color' => 'White', 'fuel_type' => 'Gasoline',
			'transmission' => 'Automatic', 'drive_line' => 'FWD', 'key_available' => 'Yes', 'run_and_drive' => 'Run and Drive',
			'title' => 'Salvage', 'selling_branch' => 'TX - Dallas', 'buy_now' => 8200, 'current_bid' => 5100,
			'detail_url' => 'https://www.iaai.com/VehicleDetail/900001', 'status' => 'active',
		), 'img' => array( $ph( '1f4fd8', 'Toyota Camry' ), $ph( '12203a', 'Camry - wnetrze' ), $ph( '2b6cb0', 'Camry - tyl' ) ) ),

		array( 'v' => array(
			'salvage_id' => 900002, 'vin' => '2C3CDXBG5FH123456', 'year' => 2016, 'make' => 'Dodge', 'model' => 'Charger',
			'body_style' => 'Sedan', 'odometer' => 88231, 'odometer_uom' => 'mi', 'primary_damage' => 'Rear End',
			'color' => 'Black', 'fuel_type' => 'Gasoline', 'transmission' => 'Automatic', 'drive_line' => 'RWD',
			'key_available' => 'Yes', 'run_and_drive' => 'Run and Drive', 'title' => 'Salvage', 'selling_branch' => 'CA - Los Angeles',
			'buy_now' => 6900, 'current_bid' => 4300, 'detail_url' => 'https://www.iaai.com/VehicleDetail/900002', 'status' => 'active',
		), 'img' => array( $ph( '111111', 'Dodge Charger' ), $ph( '333333', 'Charger - bok' ) ) ),

		array( 'v' => array(
			'salvage_id' => 900003, 'vin' => '1FTFW1ET5DFC12345', 'year' => 2019, 'make' => 'Ford', 'model' => 'F-150',
			'body_style' => 'Pickup', 'odometer' => 42210, 'odometer_uom' => 'mi', 'primary_damage' => 'Side',
			'secondary_damage' => 'All Over', 'color' => 'Blue', 'fuel_type' => 'Gasoline', 'transmission' => 'Automatic',
			'drive_line' => '4WD', 'key_available' => 'Yes', 'run_and_drive' => 'Run and Drive', 'title' => 'Clean',
			'selling_branch' => 'FL - Miami', 'buy_now' => 15400, 'current_bid' => 11200,
			'detail_url' => 'https://www.iaai.com/VehicleDetail/900003', 'status' => 'active',
		), 'img' => array( $ph( '2b6cb0', 'Ford F-150' ), $ph( '1a3d6b', 'F-150 - pak' ) ) ),

		array( 'v' => array(
			'salvage_id' => 900004, 'vin' => '5YJ3E1EA7KF123456', 'year' => 2019, 'make' => 'Tesla', 'model' => 'Model 3',
			'body_style' => 'Sedan', 'odometer' => 33110, 'odometer_uom' => 'mi', 'primary_damage' => 'Front End',
			'color' => 'Red', 'fuel_type' => 'Electric', 'transmission' => 'Automatic', 'drive_line' => 'RWD',
			'key_available' => 'No', 'run_and_drive' => 'Starts', 'title' => 'Salvage', 'selling_branch' => 'NJ - Somerville',
			'buy_now' => 18900, 'current_bid' => 14000, 'detail_url' => 'https://www.iaai.com/VehicleDetail/900004', 'status' => 'active',
		), 'img' => array( $ph( 'c53030', 'Tesla Model 3' ), $ph( '7a1f1f', 'Model 3 - wnetrze' ) ) ),

		array( 'v' => array(
			'salvage_id' => 900005, 'vin' => 'WBA8E9G50GNT12345', 'year' => 2016, 'make' => 'BMW', 'model' => '328i',
			'body_style' => 'Sedan', 'odometer' => 77650, 'odometer_uom' => 'mi', 'primary_damage' => 'Rear',
			'secondary_damage' => 'Minor Dent/Scratches', 'color' => 'Gray', 'fuel_type' => 'Gasoline', 'transmission' => 'Automatic',
			'drive_line' => 'RWD', 'key_available' => 'Yes', 'run_and_drive' => 'Run and Drive', 'title' => 'Salvage',
			'selling_branch' => 'IL - Chicago', 'buy_now' => 7300, 'current_bid' => 4900,
			'detail_url' => 'https://www.iaai.com/VehicleDetail/900005', 'status' => 'active',
		), 'img' => array( $ph( '4a5568', 'BMW 328i' ), $ph( '2d3644', '328i - tyl' ) ) ),

		array( 'v' => array(
			'salvage_id' => 900006, 'vin' => '1N4AL3AP7JC123456', 'year' => 2018, 'make' => 'Nissan', 'model' => 'Altima',
			'body_style' => 'Sedan', 'odometer' => 60120, 'odometer_uom' => 'mi', 'primary_damage' => 'Water/Flood',
			'color' => 'Silver', 'fuel_type' => 'Gasoline', 'transmission' => 'Automatic', 'drive_line' => 'FWD',
			'key_available' => 'No', 'run_and_drive' => 'Does Not Run', 'title' => 'Salvage', 'selling_branch' => 'TX - Houston',
			'buy_now' => 3200, 'current_bid' => 2100, 'detail_url' => 'https://www.iaai.com/VehicleDetail/900006', 'status' => 'active',
		), 'img' => array( $ph( '718096', 'Nissan Altima' ) ) ),

		array( 'v' => array(
			'salvage_id' => 900007, 'vin' => '1G1ZD5ST7JF123456', 'year' => 2018, 'make' => 'Chevrolet', 'model' => 'Malibu',
			'body_style' => 'Sedan', 'odometer' => 51230, 'odometer_uom' => 'mi', 'primary_damage' => 'Front End',
			'color' => 'Blue', 'fuel_type' => 'Gasoline', 'transmission' => 'Automatic', 'drive_line' => 'FWD',
			'key_available' => 'Yes', 'run_and_drive' => 'Run and Drive', 'title' => 'Salvage', 'selling_branch' => 'GA - Atlanta',
			'buy_now' => 6100, 'current_bid' => 3900, 'detail_url' => 'https://www.iaai.com/VehicleDetail/900007', 'status' => 'active',
		), 'img' => array( $ph( '285e8a', 'Chevrolet Malibu' ), $ph( '17384f', 'Malibu - bok' ) ) ),

		array( 'v' => array(
			'salvage_id' => 900008, 'vin' => 'JH4KA8260MC123456', 'year' => 2020, 'make' => 'Honda', 'model' => 'Accord',
			'body_style' => 'Sedan', 'odometer' => 28900, 'odometer_uom' => 'mi', 'primary_damage' => 'Minor Dent/Scratches',
			'color' => 'White', 'fuel_type' => 'Gasoline', 'transmission' => 'Automatic', 'drive_line' => 'FWD',
			'key_available' => 'Yes', 'run_and_drive' => 'Run and Drive', 'title' => 'Clean', 'selling_branch' => 'NC - Charlotte',
			'buy_now' => 13500, 'current_bid' => 9800, 'detail_url' => 'https://www.iaai.com/VehicleDetail/900008', 'status' => 'active',
		), 'img' => array( $ph( '0d7a5f', 'Honda Accord' ), $ph( '064230', 'Accord - wnetrze' ) ) ),

		array( 'v' => array(
			'salvage_id' => 900009, 'vin' => '3VWDX7AJ5BM123456', 'year' => 2017, 'make' => 'Volkswagen', 'model' => 'Jetta',
			'body_style' => 'Sedan', 'odometer' => 69540, 'odometer_uom' => 'mi', 'primary_damage' => 'Side',
			'color' => 'Gray', 'fuel_type' => 'Gasoline', 'transmission' => 'Manual', 'drive_line' => 'FWD',
			'key_available' => 'Yes', 'run_and_drive' => 'Run and Drive', 'title' => 'Salvage', 'selling_branch' => 'AZ - Phoenix',
			'buy_now' => 5400, 'current_bid' => 3300, 'detail_url' => 'https://www.iaai.com/VehicleDetail/900009', 'status' => 'active',
		), 'img' => array( $ph( '5b4b8a', 'VW Jetta' ), $ph( '332b52', 'Jetta - tyl' ) ) ),

		// ——— DRUGIE ŹRÓDŁO: COPART (plakietka „Copart" + filtr źródła na liście) ———
		array( 'v' => array(
			'salvage_id' => 800001, 'source' => 'copart', 'vin' => '1C4RJFAG5FC601234', 'year' => 2018, 'make' => 'Jeep', 'model' => 'Grand Cherokee',
			'body_style' => 'SUV', 'odometer' => 61240, 'odometer_uom' => 'mi', 'primary_damage' => 'Front End',
			'color' => 'Black', 'fuel_type' => 'Gasoline', 'transmission' => 'Automatic', 'drive_line' => '4WD',
			'key_available' => 'Yes', 'run_and_drive' => 'Run and Drive', 'title' => 'Salvage', 'selling_branch' => 'TX - Dallas (Copart)',
			'buy_now' => 12800, 'current_bid' => 8600, 'detail_url' => 'https://www.copart.com/lot/800001', 'status' => 'active',
		), 'img' => array( $ph( '1e5fb0', 'Jeep Grand Cherokee' ), $ph( '133b6e', 'Grand Cherokee - bok' ) ) ),

		array( 'v' => array(
			'salvage_id' => 800002, 'source' => 'copart', 'vin' => '5NPD84LF2JH123456', 'year' => 2018, 'make' => 'Hyundai', 'model' => 'Elantra',
			'body_style' => 'Sedan', 'odometer' => 44500, 'odometer_uom' => 'mi', 'primary_damage' => 'Rear End',
			'color' => 'White', 'fuel_type' => 'Gasoline', 'transmission' => 'Automatic', 'drive_line' => 'FWD',
			'key_available' => 'Yes', 'run_and_drive' => 'Run and Drive', 'title' => 'Clean', 'selling_branch' => 'CA - Los Angeles (Copart)',
			'buy_now' => 7600, 'current_bid' => 5200, 'detail_url' => 'https://www.copart.com/lot/800002', 'status' => 'active',
		), 'img' => array( $ph( '1e5fb0', 'Hyundai Elantra' ) ) ),

		array( 'v' => array(
			'salvage_id' => 800003, 'source' => 'copart', 'vin' => '1C6RR7GT6JS123456', 'year' => 2019, 'make' => 'Ram', 'model' => '1500',
			'body_style' => 'Pickup', 'odometer' => 38700, 'odometer_uom' => 'mi', 'primary_damage' => 'Side',
			'color' => 'Silver', 'fuel_type' => 'Gasoline', 'transmission' => 'Automatic', 'drive_line' => '4WD',
			'key_available' => 'Yes', 'run_and_drive' => 'Run and Drive', 'title' => 'Salvage', 'selling_branch' => 'FL - Miami (Copart)',
			'buy_now' => 19900, 'current_bid' => 14500, 'detail_url' => 'https://www.copart.com/lot/800003', 'status' => 'active',
		), 'img' => array( $ph( '1e5fb0', 'Ram 1500' ), $ph( '123a63', 'Ram 1500 - tyl' ) ) ),
	);
}
