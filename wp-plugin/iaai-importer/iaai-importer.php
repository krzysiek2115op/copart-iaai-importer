<?php
/**
 * Plugin Name:       Importer Aukcji (IAAI + Copart)
 * Description:        Import danych i zdjęć pojazdów z aukcji IAAI oraz Copart do WordPressa (CPT „Pojazd").
 * Version:           0.30.4
 * Requires at least: 6.0
 * Requires PHP:      7.4
 * Author:            (projekt importer IAAI + Copart)
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

define( 'IAAI_IMPORTER_VERSION', '0.30.4' );
define( 'IAAI_IMPORTER_DIR', plugin_dir_path( __FILE__ ) );
define( 'IAAI_IMPORTER_URL', plugin_dir_url( __FILE__ ) );

require_once IAAI_IMPORTER_DIR . 'includes/activation.php';   // Aktywacja + dbDelta (blok A)
require_once IAAI_IMPORTER_DIR . 'includes/security.php';     // Dział 6
require_once IAAI_IMPORTER_DIR . 'includes/publikacja.php';   // Dział 8
require_once IAAI_IMPORTER_DIR . 'includes/front.php';        // Dział 9
require_once IAAI_IMPORTER_DIR . 'includes/seo.php';          // Dział 9 (SEO)

// Tabele nowej bazy zakładają się przy włączeniu wtyczki (idempotentne dbDelta).
register_activation_hook( __FILE__, 'iaai_activate' );
