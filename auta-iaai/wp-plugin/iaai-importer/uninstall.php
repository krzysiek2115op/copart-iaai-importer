<?php
// SPDX-License-Identifier: GPL-2.0-or-later
// Sprzątanie przy USUNIĘCIU wtyczki (nie dezaktywacji). Uninstall = wtyczka ma zniknąć bez
// śladu, więc kasujemy wszystko, co utworzyła: podstronę „Nasze auta", wpisy CPT „pojazd"
// (+ meta), tabele danych (iaai_vehicles / iaai_vehicle_images), opcje i transienty.
// WP uruchamia ten plik automatycznie (sama obecność w katalogu wtyczki) i BEZ załadowanej
// wtyczki — dlatego slug CPT i nazwy wpisane są „na twardo" (stałe IAAI_* tu nie istnieją).
if ( ! defined( 'WP_UNINSTALL_PLUGIN' ) ) {
	exit;
}

global $wpdb;

// 1) Podstrona „Nasze auta" (auto-utworzona przy aktywacji).
$pid = (int) get_option( 'iaai_page_id' );
if ( $pid ) {
	wp_delete_post( $pid, true );
}

// 2) Wpisy CPT „pojazd" + ich meta. Bezpośredni SQL — wydajne przy tysiącach wpisów
//    (brak załączników: zdjęcia są hotlinkowane, więc nie ma osieroconych mediów).
$ids = $wpdb->get_col( $wpdb->prepare( "SELECT ID FROM {$wpdb->posts} WHERE post_type = %s", 'pojazd' ) );
if ( $ids ) {
	$in = implode( ',', array_map( 'intval', $ids ) );
	$wpdb->query( "DELETE FROM {$wpdb->postmeta} WHERE post_id IN ({$in})" );
	$wpdb->query( "DELETE FROM {$wpdb->posts}    WHERE ID       IN ({$in})" );
}

// 3) Tabele danych utworzone przez wtyczkę (dbDelta). Kolejność: najpierw zdjęcia.
$wpdb->query( "DROP TABLE IF EXISTS {$wpdb->prefix}iaai_vehicle_images" );
$wpdb->query( "DROP TABLE IF EXISTS {$wpdb->prefix}iaai_vehicles" );

// 4) Opcje wtyczki (iaai_page_id, iaai_db_version, iaai_landing_done, iaai_pk_checked,
//    iaai_publish_watermark, iaai_list_cv). '\\_' escapuje '_' (inaczej '_' = wildcard LIKE).
$wpdb->query( "DELETE FROM {$wpdb->options} WHERE option_name LIKE 'iaai\\_%'" );

// 5) Transienty listy/cache (iaai_list_*, iaai_filter_opts_*).
$wpdb->query(
	"DELETE FROM {$wpdb->options} WHERE option_name LIKE '\\_transient\\_iaai\\_%' " .
	"OR option_name LIKE '\\_transient\\_timeout\\_iaai\\_%'"
);
