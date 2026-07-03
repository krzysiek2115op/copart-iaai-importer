<?php
/**
 * IAAI Importer — SEED DEMO (WYŁĄCZNIE dla wersji demonstracyjnej w WordPress Playground).
 *
 * Ładowany jako mu-plugin. Robi dwie rzeczy:
 *   1) Pozwala pokazywać obrazki z placehold.co (produkcja: tylko host iaai.com — anty-SSRF).
 *   2) Jednorazowo wstawia przykładowe auta + zdjęcia do bazy i publikuje je jako CPT „pojazd”,
 *      żeby podstrona „Nasze auta” od razu prezentowała ofertę (bez scrapera i MySQL).
 *
 * ⚠ To jest tylko atrapa danych do prezentacji. NIE używać na produkcji.
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/* Demo: dopuść hotlink obrazków z placehold.co (na produkcji zostaje sam iaai.com). */
add_filter( 'iaai_allowed_image_hosts', function ( $hosts ) {
	$hosts[] = 'placehold.co';
	return $hosts;
} );

add_action( 'init', 'iaai_demo_seed_now', 99 );

/** Jednorazowy seed przykładowych aut (guard: opcja iaai_demo_seeded). */
function iaai_demo_seed_now() : void {
	if ( get_option( 'iaai_demo_seeded' ) ) {
		return;                                   // już zasiane
	}
	if ( ! function_exists( 'iaai_publish_vehicle' ) ) {
		return;                                   // wtyczka jeszcze się nie załadowała
	}

	global $wpdb;

	// Bezpiecznik: gdyby aktywacja nie założyła tabel (idempotentne dbDelta).
	if ( function_exists( 'iaai_activate' ) ) {
		iaai_activate();
	}

	$veh = $wpdb->prefix . 'iaai_vehicles';
	$img = $wpdb->prefix . 'iaai_vehicle_images';

	foreach ( iaai_demo_cars() as $c ) {
		$wpdb->replace( $veh, $c['v'] );
		foreach ( $c['img'] as $seq => $url ) {
			$wpdb->replace( $img, array(
				'salvage_id' => $c['v']['salvage_id'],
				'image_key'  => 't' . $c['v']['salvage_id'] . '-' . ( $seq + 1 ),
				'seq'        => $seq + 1,
				'width'      => 700,
				'height'     => 500,
				'url'        => $url,
			) );
		}
		iaai_publish_vehicle( (int) $c['v']['salvage_id'] );
	}

	if ( function_exists( 'iaai_flush_list_cache' ) ) {
		iaai_flush_list_cache();
	}
	update_option( 'iaai_demo_seeded', 1 );
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
	);
}
