<?php
/**
 * Plugin Name:       IAAI Importer
 * Description:        Import danych i zdjęć pojazdów z IAAI do WordPressa (CPT „Pojazd").
 * Version:           0.12.0
 * Requires at least: 6.0
 * Requires PHP:      7.4
 * Author:            (projekt importer Copart/IAAI)
 * License:           GPL-2.0-or-later
 * Text Domain:       iaai-importer
 *
 * Wtyczka = górne działy pipeline'u (6 bezpieczeństwo, 8 publikacja, 9 front/media).
 * Czyta z nowej bazy (te same tabele co db/schema.sql, z prefiksem WP: {$wpdb->prefix}iaai_*)
 * i prezentuje pojazdy na stronie. Dane do bazy wkładają agenci Pythona (działy 1–5).
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit; // brak bezpośredniego dostępu
}

define( 'IAAI_IMPORTER_VERSION', '0.12.0' );
define( 'IAAI_IMPORTER_DIR', plugin_dir_path( __FILE__ ) );

require_once IAAI_IMPORTER_DIR . 'includes/security.php';     // Dział 6
// require_once IAAI_IMPORTER_DIR . 'includes/publikacja.php'; // Dział 8 (dodany później)
// require_once IAAI_IMPORTER_DIR . 'includes/front.php';      // Dział 9 (dodany później)
