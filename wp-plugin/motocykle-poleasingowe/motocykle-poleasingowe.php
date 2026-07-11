<?php
/**
 * Plugin Name:       Importer Motocykli (poleasingowe.pl)
 * Description:       Podstrona „Nasze motory" z aukcjami motocykli z poleasingowe.pl, automatycznie dopasowana do motywu. Dane z osobnej bazy MySQL (polea_*).
 * Version:           0.11.0
 * Requires at least: 6.0
 * Requires PHP:      7.4
 * Author:            Krzysztof Leszczyński
 * License:           GPL-2.0-or-later
 * License URI:       https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain:       motocykle-poleasingowe
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 */

if (!defined('ABSPATH')) {
    exit;
}

define('POLEA_VERSION', '0.11.0');
define('POLEA_FILE', __FILE__);
define('POLEA_DIR', plugin_dir_path(__FILE__));
define('POLEA_URL', plugin_dir_url(__FILE__));
define('POLEA_PAGE_OPTION', 'polea_nasze_motory_page_id');
define('POLEA_CACHE_TTL', 5 * MINUTE_IN_SECONDS);

require_once POLEA_DIR . 'includes/security.php';
require_once POLEA_DIR . 'includes/class-db.php';
require_once POLEA_DIR . 'includes/shortcode.php';
require_once POLEA_DIR . 'includes/seo.php';
require_once POLEA_DIR . 'includes/activation.php';
if (is_admin()) {
    require_once POLEA_DIR . 'includes/admin.php';
}

register_activation_hook(__FILE__, 'polea_activate');
register_deactivation_hook(__FILE__, 'polea_deactivate');

add_action('init', 'polea_register_shortcode');
add_action('wp_enqueue_scripts', 'polea_register_assets');

/** Rejestruje (bez ładowania) styl frontu — shortcode ładuje go na żądanie. */
function polea_register_assets() {
    wp_register_style('polea-front', POLEA_URL . 'assets/front.css', array(), POLEA_VERSION);
}
