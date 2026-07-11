<?php
// SPDX-License-Identifier: GPL-2.0-or-later
/**
 * Dział 10 (SEO) — optymalizacja podstrony „Nasze motory":
 *  - ładne URL-e pojedynczego motocykla: /<ścieżka-podstrony>/<lot_id>/ (rewrite),
 *  - per motocykl: unikalny <title>, meta description, canonical, Open Graph, JSON-LD (schema.org Motorcycle/Offer),
 *  - noindex dla widoków filtrowanych/paginowanych oraz aukcji zakończonych/nieistniejących,
 *  - sitemap XML aktywnych ofert (WP core Sitemaps),
 *  - automatyczne USTĄPIENIE miejsca wtyczce SEO (Yoast/Rank Math/SEOPress/AIOSEO) — bez dublowania metatagów.
 * Wszystko tylko na podstronie wtyczki; nie dotyka reszty serwisu.
 */
if (!defined('ABSPATH')) {
    exit;
}

/* ------------------------------------------------------- ładne URL-e (rewrite) */

add_filter('query_vars', 'polea_seo_query_vars');
add_action('init', 'polea_register_rewrites');

function polea_seo_query_vars($vars) {
    $vars[] = 'motocykl';
    return $vars;
}

/** Ścieżka podstrony względem korzenia, np. "nasze-motory" lub "rodzic/nasze-motory". */
function polea_page_path() {
    $pid = (int) get_option(POLEA_PAGE_OPTION);
    if (!$pid) {
        return '';
    }
    $uri = get_page_uri($pid);
    return $uri ? trim($uri, '/') : '';
}

/** Rejestruje regułę /<ścieżka>/<lot_id>/ -> ta sama strona + query var motocykl. */
function polea_register_rewrites() {
    $path = polea_page_path();
    if ($path === '') {
        return;
    }
    add_rewrite_rule(
        '^' . preg_quote($path) . '/([A-Za-z0-9]{1,32})/?$',
        'index.php?pagename=' . $path . '&motocykl=$matches[1]',
        'top'
    );
}

/** Kanoniczny URL pojedynczego motocykla (ładny, gdy włączone przyjazne odnośniki; inaczej ?motocykl=). */
function polea_single_url($lot) {
    $base = polea_page_url();
    if (get_option('permalink_structure')) {
        return trailingslashit($base) . rawurlencode($lot) . '/';
    }
    return add_query_arg('motocykl', rawurlencode($lot), $base);
}

/* ------------------------------------------------------------------ pomocnicy */

function polea_seo_plugin_active() {
    return defined('WPSEO_VERSION')        // Yoast
        || class_exists('RankMath')        // Rank Math
        || defined('SEOPRESS_VERSION')     // SEOPress
        || function_exists('aioseo');      // All in One SEO
}

function polea_is_our_page() {
    $pid = (int) get_option(POLEA_PAGE_OPTION);
    return $pid && is_page($pid);
}

function polea_seo_strlen($s) {
    return function_exists('mb_strlen') ? mb_strlen($s) : strlen($s);
}

function polea_seo_trim($s, $len) {
    $s = trim(wp_strip_all_tags($s));
    if (polea_seo_strlen($s) <= $len) {
        return $s;
    }
    $cut = function_exists('mb_substr') ? mb_substr($s, 0, $len - 1) : substr($s, 0, $len - 1);
    $sp  = function_exists('mb_strrpos') ? mb_strrpos($cut, ' ') : strrpos($cut, ' ');
    if ($sp !== false && $sp > 40) {
        $cut = function_exists('mb_substr') ? mb_substr($cut, 0, $sp) : substr($cut, 0, $sp);
    }
    return rtrim($cut) . '…';
}

function polea_seo_desc_single($m) {
    $bits = array();
    $name = trim(($m['marka'] ?? '') . ' ' . ($m['model'] ?? ''));
    if ($name !== '')                 { $bits[] = $name; }
    if (!empty($m['rok_produkcji']))  { $bits[] = 'rok ' . (int) $m['rok_produkcji']; }
    if (!empty($m['przebieg_km']))    { $bits[] = number_format((int) $m['przebieg_km'], 0, ',', ' ') . ' km'; }
    if (!empty($m['pojemnosc_ccm']))  { $bits[] = (int) $m['pojemnosc_ccm'] . ' ccm'; }
    if (!empty($m['moc_km']))         { $bits[] = (int) $m['moc_km'] . ' KM'; }
    if (!empty($m['paliwo']))         { $bits[] = $m['paliwo']; }
    $desc = implode(', ', $bits) . '. Aukcja motocykla — ' . polea_price($m) . '.';
    return polea_seo_trim($desc, 160);
}

/* --------------------------------------------------------------- <title> */

add_filter('pre_get_document_title', 'polea_seo_title', 20);

function polea_seo_title($title) {
    if (!polea_is_our_page() || polea_seo_plugin_active()) {
        return $title;
    }
    $lot = polea_current_lot_id();
    if ($lot === '') {
        return $title; // lista — zostaw tytuł strony
    }
    $m = Polea_DB::get_one($lot);
    if (!$m) {
        return $title;
    }
    $name = trim(($m['marka'] ?? '') . ' ' . ($m['model'] ?? ''));
    $rok  = !empty($m['rok_produkcji']) ? ' ' . (int) $m['rok_produkcji'] : '';
    // Rdzeń WP nie escapuje treści <title> — czyścimy z ewentualnych tagów z danych źródła.
    return wp_strip_all_tags(trim($name . $rok) . ' — ' . polea_price($m) . ' | ' . get_bloginfo('name'));
}

/* --------------------------------------------------- meta / canonical / OG / JSON-LD */

add_action('wp_head', 'polea_seo_head', 5);

function polea_seo_head() {
    if (!polea_is_our_page()) {
        return;
    }
    $seo_plugin = polea_seo_plugin_active();
    $lot = polea_current_lot_id();
    if ($lot !== '') {
        $m = Polea_DB::get_one($lot);
        if (!$m) {
            echo '<meta name="robots" content="noindex,follow">' . "\n";
            return;
        }
        polea_seo_single($m, $seo_plugin);
    } else {
        polea_seo_list($seo_plugin);
    }
}

function polea_seo_single($m, $seo_plugin) {
    $url    = polea_single_url($m['lot_id']);
    $desc   = polea_seo_desc_single($m);
    $active = ($m['status'] === 'aktywna');

    // Zakończona/usunięta aukcja: nie chcemy jej w indeksie jako żywej oferty.
    if (!$active) {
        echo '<meta name="robots" content="noindex,follow">' . "\n";
    }
    // JSON-LD wypuszczamy ZAWSZE (dane strukturalne są addytywne i bezpieczne, nawet z wtyczką SEO).
    polea_seo_jsonld_single($m, $url);

    if ($seo_plugin) {
        return; // <title>/meta/canonical/OG zostawiamy aktywnej wtyczce SEO — bez dublowania
    }
    remove_action('wp_head', 'rel_canonical'); // nasz canonical zamiast rdzeniowego (ten wskazywałby na listę)

    $imgs  = Polea_DB::get_images($m['lot_id']);
    $title = wp_get_document_title();
    echo '<link rel="canonical" href="' . esc_url($url) . '">' . "\n";
    echo '<meta name="description" content="' . esc_attr($desc) . '">' . "\n";
    echo '<meta property="og:type" content="product">' . "\n";
    echo '<meta property="og:title" content="' . esc_attr($title) . '">' . "\n";
    echo '<meta property="og:description" content="' . esc_attr($desc) . '">' . "\n";
    echo '<meta property="og:url" content="' . esc_url($url) . '">' . "\n";
    echo '<meta property="og:site_name" content="' . esc_attr(get_bloginfo('name')) . '">' . "\n";
    echo '<meta property="og:locale" content="pl_PL">' . "\n";
    if ($imgs) {
        echo '<meta property="og:image" content="' . esc_url($imgs[0]) . '">' . "\n";
    }
    if ($m['cena_pln'] !== null && $m['cena_pln'] !== '') {
        echo '<meta property="product:price:amount" content="' . esc_attr(number_format((float) $m['cena_pln'], 2, '.', '')) . '">' . "\n";
        echo '<meta property="product:price:currency" content="PLN">' . "\n";
    }
}

function polea_seo_list($seo_plugin) {
    $base     = polea_page_url();
    $filtered = polea_seo_is_filtered();

    if ($filtered) {
        // Widoki filtrowane/paginowane: nie indeksuj (cienka/duplikująca się treść), ale podążaj za linkami.
        echo '<meta name="robots" content="noindex,follow">' . "\n";
    }
    if ($seo_plugin) {
        return;
    }
    $desc = 'Aktualne aukcje motocykli z poleasingowe.pl — ceny, przebieg, pojemność i szczegóły. Oferty aktualizowane automatycznie.';
    echo '<meta name="description" content="' . esc_attr($desc) . '">' . "\n";
    if ($filtered) {
        remove_action('wp_head', 'rel_canonical');
        echo '<link rel="canonical" href="' . esc_url($base) . '">' . "\n"; // konsolidacja do bazowej listy
    }
    echo '<meta property="og:type" content="website">' . "\n";
    echo '<meta property="og:title" content="' . esc_attr(wp_get_document_title()) . '">' . "\n";
    echo '<meta property="og:description" content="' . esc_attr($desc) . '">' . "\n";
    echo '<meta property="og:url" content="' . esc_url($base) . '">' . "\n";
    echo '<meta property="og:site_name" content="' . esc_attr(get_bloginfo('name')) . '">' . "\n";
    echo '<meta property="og:locale" content="pl_PL">' . "\n";
}

function polea_seo_is_filtered() {
    foreach (array('polea_marka', 'polea_paliwo', 'polea_rok', 'polea_cena_max', 'polea_cena_min') as $k) {
        if (!empty($_GET[$k])) {
            return true;
        }
    }
    return isset($_GET['polea_str']) && (int) $_GET['polea_str'] > 1;
}

/** JSON-LD schema.org: Product+Motorcycle z Offer. Bezpieczne wstawienie do <script>. */
function polea_seo_jsonld_single($m, $url) {
    $imgs = Polea_DB::get_images($m['lot_id']);
    $data = array(
        '@context' => 'https://schema.org',
        '@type'    => array('Product', 'Motorcycle'),
        'name'     => trim(($m['marka'] ?? '') . ' ' . ($m['model'] ?? '')),
        'sku'      => $m['lot_id'],
        'url'      => $url,
        'category' => 'Motocykl',
    );
    if ($imgs)                        { $data['image'] = array_values($imgs); }
    if (!empty($m['marka']))          { $data['brand'] = array('@type' => 'Brand', 'name' => $m['marka']); }
    if (!empty($m['model']))          { $data['model'] = $m['model']; }
    if (!empty($m['rok_produkcji']))  { $data['vehicleModelDate'] = (string) (int) $m['rok_produkcji']; }
    if (!empty($m['vin']))            { $data['vehicleIdentificationNumber'] = $m['vin']; }
    if (!empty($m['kolor']))          { $data['color'] = $m['kolor']; }
    if (!empty($m['paliwo']))         { $data['fuelType'] = $m['paliwo']; }
    if (!empty($m['skrzynia']))       { $data['vehicleTransmission'] = $m['skrzynia']; }
    if (!empty($m['przebieg_km'])) {
        $data['mileageFromOdometer'] = array('@type' => 'QuantitativeValue', 'value' => (int) $m['przebieg_km'], 'unitCode' => 'KMT');
    }
    if (!empty($m['moc_km'])) {
        $data['vehicleEngine'] = array('@type' => 'EngineSpecification',
            'enginePower' => array('@type' => 'QuantitativeValue', 'value' => (int) $m['moc_km'], 'unitText' => 'KM'));
    }
    if ($m['cena_pln'] !== null && $m['cena_pln'] !== '') {
        $data['offers'] = array(
            '@type'         => 'Offer',
            'price'         => number_format((float) $m['cena_pln'], 2, '.', ''),
            'priceCurrency' => 'PLN',
            'availability'  => ($m['status'] === 'aktywna') ? 'https://schema.org/InStock' : 'https://schema.org/SoldOut',
            'url'           => $url,
        );
    }
    // JSON_HEX_TAG|JSON_HEX_AMP: escapuje < > & na < > & -> nie da się wyjść z <script>.
    $json = wp_json_encode($data, JSON_HEX_TAG | JSON_HEX_AMP);
    echo '<script type="application/ld+json">' . $json . '</script>' . "\n";
}

/* ------------------------------------------------------------ sitemap (WP core) */

add_action('init', 'polea_register_sitemap', 20);

function polea_register_sitemap() {
    if (!function_exists('wp_sitemaps_register_provider') || !class_exists('Polea_Sitemap_Provider')) {
        return;
    }
    if (!get_option('permalink_structure') || !(int) get_option(POLEA_PAGE_OPTION)) {
        return; // sitemap ofert ma sens tylko przy ładnych URL-ach
    }
    wp_sitemaps_register_provider('polea_motocykle', new Polea_Sitemap_Provider());
}

if (class_exists('WP_Sitemaps_Provider')) {
    class Polea_Sitemap_Provider extends WP_Sitemaps_Provider {
        public function __construct() {
            $this->name        = 'polea_motocykle';
            $this->object_type = 'polea_motocykl';
        }
        public function get_url_list($page_num, $object_subtype = '') {
            $list = array();
            foreach (Polea_DB::active_lot_ids(2000) as $lot) {
                $list[] = array('loc' => polea_single_url($lot));
            }
            return $list;
        }
        public function get_max_num_pages($object_subtype = '') {
            return 1;
        }
    }
}
