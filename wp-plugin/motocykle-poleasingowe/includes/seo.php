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
    $name = polea_vehicle_name($m);
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
    $name = polea_vehicle_name($m);
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
    // theme-color: domyślnie WYŁĄCZONY (by nie nadpisywać motywu). Klient włącza jedną linią:
    //   add_filter('polea_theme_color', fn() => '#0b5cad');
    $tc = apply_filters('polea_theme_color', '');
    if ($tc !== '') {
        echo '<meta name="theme-color" content="' . esc_attr($tc) . '">' . "\n";
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
    // JSON-LD (@graph: Product/Motorcycle + BreadcrumbList + FAQPage) emitujemy w treści
    // shortcode’u, gdzie dane są już wczytane — patrz polea_jsonld_single().
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
    echo '<meta name="twitter:card" content="' . ($imgs ? 'summary_large_image' : 'summary') . '">' . "\n";
    echo '<meta name="twitter:title" content="' . esc_attr($title) . '">' . "\n";
    echo '<meta name="twitter:description" content="' . esc_attr($desc) . '">' . "\n";
    if ($imgs) {
        echo '<meta name="twitter:image" content="' . esc_url($imgs[0]) . '">' . "\n";
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
    echo '<meta name="twitter:card" content="summary">' . "\n";
    echo '<meta name="twitter:title" content="' . esc_attr(wp_get_document_title()) . '">' . "\n";
    echo '<meta name="twitter:description" content="' . esc_attr($desc) . '">' . "\n";
}

function polea_seo_is_filtered() {
    foreach (array('polea_marka', 'polea_paliwo', 'polea_rok', 'polea_cena_max', 'polea_cena_min') as $k) {
        if (!empty($_GET[$k])) {
            return true;
        }
    }
    return isset($_GET['polea_str']) && (int) $_GET['polea_str'] > 1;
}

/* ------------------------------------------------------ H1 = nazwa pojazdu (single) */

add_filter('the_title', 'polea_seo_the_title', 10, 2);

/** Na widoku pojedynczego motocykla podmienia tytuł strony (H1 motywu) na nazwę pojazdu.
 *  Ściśle ograniczone: tylko nasza strona, główne zapytanie, w pętli treści. */
function polea_seo_the_title($title, $post_id = 0) {
    if (is_admin() || !is_main_query() || !in_the_loop()) {
        return $title;
    }
    $pid = (int) get_option(POLEA_PAGE_OPTION);
    if (!$pid || (int) $post_id !== $pid) {
        return $title;
    }
    $lot = polea_current_lot_id();
    if ($lot === '') {
        return $title;
    }
    $m = Polea_DB::get_one($lot);
    if (!$m) {
        return $title;
    }
    $name = polea_vehicle_name($m);
    $rok  = !empty($m['rok_produkcji']) ? ' ' . (int) $m['rok_produkcji'] : '';
    return $name !== '' ? wp_strip_all_tags(trim($name . $rok)) : $title;
}

/* --------------------------------------------------- helpery treści (współdzielone HTML + JSON-LD) */

/** Okruszki: Strona główna → Nasze motory → [pojazd]. Zwraca [ [name,url], ... ]. */
function polea_breadcrumb_items($m = null) {
    $pid = (int) get_option(POLEA_PAGE_OPTION);
    // get_post_field (NIE get_the_title) — inaczej filtr the_title zwróciłby tu nazwę pojazdu.
    $list_name = $pid ? (string) get_post_field('post_title', $pid) : '';
    if ($list_name === '') {
        $list_name = 'Nasze motory';
    }
    $items = array(
        array('name' => 'Strona główna', 'url' => home_url('/')),
        array('name' => ($list_name !== '' ? $list_name : 'Nasze motory'), 'url' => polea_page_url()),
    );
    if ($m) {
        $name = polea_vehicle_name($m);
        if (!empty($m['rok_produkcji'])) {
            $name = trim($name . ' ' . (int) $m['rok_produkcji']);
        }
        $items[] = array('name' => ($name !== '' ? $name : 'Motocykl'), 'url' => polea_single_url($m['lot_id']));
    }
    return $items;
}

/** Unikalny, syntetyzowany opis pojazdu z posiadanych pól (naturalny język, bez kopiowania). */
function polea_vehicle_description($m) {
    $name = polea_vehicle_name($m);
    if ($name === '') {
        $name = 'Ten motocykl';
    }
    $lead = $name;
    if (!empty($m['rok_produkcji'])) {
        $lead .= ' z ' . (int) $m['rok_produkcji'] . ' roku';
    }
    $eng = array();
    if (!empty($m['pojemnosc_ccm'])) { $eng[] = (int) $m['pojemnosc_ccm'] . ' ccm'; }
    if (!empty($m['moc_km']))        { $eng[] = (int) $m['moc_km'] . ' KM'; }
    $lead .= $eng ? ' to motocykl z silnikiem ' . implode(' / ', $eng) : ' to motocykl z aukcji poleasingowej';

    $parts = array($lead . '.');
    $s2 = array();
    if (!empty($m['paliwo']))      { $s2[] = 'paliwo: ' . $m['paliwo']; }
    if (!empty($m['skrzynia']))    { $s2[] = 'skrzynia: ' . $m['skrzynia']; }
    if (!empty($m['naped']))       { $s2[] = 'napęd: ' . $m['naped']; }
    if (!empty($m['przebieg_km'])) { $s2[] = 'przebieg: ' . number_format((int) $m['przebieg_km'], 0, ',', ' ') . ' km'; }
    if ($s2) {
        $parts[] = ucfirst(implode(', ', $s2)) . '.';
    }
    $s3 = array();
    if (!empty($m['lokalizacja'])) { $s3[] = 'Pojazd znajduje się w: ' . $m['lokalizacja']; }
    if ($m['cena_pln'] !== null && $m['cena_pln'] !== '') { $s3[] = 'cena w aukcji: ' . polea_price($m); }
    if ($s3) {
        $parts[] = implode('. ', $s3) . '.';
    }
    return implode(' ', $parts);
}

/** Pary FAQ generowane z danych pojazdu (tylko gdy dane istnieją). */
function polea_faq_pairs($m) {
    $name = polea_vehicle_name($m);
    if ($name === '') {
        $name = 'ten motocykl';
    }
    $pairs = array();
    if (!empty($m['rok_produkcji'])) {
        $pairs[] = array('q' => 'Z którego roku pochodzi ' . $name . '?',
                         'a' => $name . ' pochodzi z ' . (int) $m['rok_produkcji'] . ' roku.');
    }
    if (!empty($m['przebieg_km'])) {
        $pairs[] = array('q' => 'Jaki przebieg ma ' . $name . '?',
                         'a' => 'Przebieg wynosi ' . number_format((int) $m['przebieg_km'], 0, ',', ' ') . ' km.');
    }
    $ep = array();
    if (!empty($m['pojemnosc_ccm'])) { $ep[] = (int) $m['pojemnosc_ccm'] . ' ccm'; }
    if (!empty($m['moc_km']))        { $ep[] = (int) $m['moc_km'] . ' KM'; }
    if ($ep) {
        $pairs[] = array('q' => 'Jaka jest pojemność i moc silnika?',
                         'a' => 'Silnik ma ' . implode(' i ', $ep) . '.');
    }
    if (!empty($m['paliwo'])) {
        $pairs[] = array('q' => 'Jakim paliwem jeździ ' . $name . '?',
                         'a' => 'Rodzaj paliwa: ' . $m['paliwo'] . '.');
    }
    if (!empty($m['skrzynia'])) {
        $pairs[] = array('q' => 'Jaka skrzynia biegów?',
                         'a' => 'Skrzynia biegów: ' . $m['skrzynia'] . '.');
    }
    if (!empty($m['lokalizacja'])) {
        $pairs[] = array('q' => 'Gdzie znajduje się ' . $name . '?',
                         'a' => 'Pojazd zlokalizowany jest w: ' . $m['lokalizacja'] . '.');
    }
    if ($m['cena_pln'] !== null && $m['cena_pln'] !== '') {
        $pairs[] = array('q' => 'Ile kosztuje ' . $name . '?',
                         'a' => 'Cena w aukcji: ' . polea_price($m) . '.');
    }
    return $pairs;
}

/* ---------------------------------------------------------------- JSON-LD (@graph) */

/** Kolejkuje skrypt JSON-LD do wydruku w stopce — poza treścią, więc wpautop go nie rusza. */
function polea_jsonld_enqueue($script) {
    if ($script === '') {
        return;
    }
    if (empty($GLOBALS['polea_jsonld'])) {
        $GLOBALS['polea_jsonld'] = array();
        add_action('wp_footer', 'polea_jsonld_print', 20);
    }
    $GLOBALS['polea_jsonld'][] = $script;
}

function polea_jsonld_print() {
    if (empty($GLOBALS['polea_jsonld'])) {
        return;
    }
    foreach ($GLOBALS['polea_jsonld'] as $s) {
        echo $s; // już bezpiecznie zakodowane (wp_json_encode + JSON_HEX_TAG|JSON_HEX_AMP)
    }
}

function polea_jsonld_wrap($graph) {
    $data = array('@context' => 'https://schema.org', '@graph' => $graph);
    // JSON_HEX_TAG|JSON_HEX_AMP -> nie da się wyjść z <script> danymi ze źródła.
    $json = wp_json_encode($data, JSON_HEX_TAG | JSON_HEX_AMP);
    return '<script type="application/ld+json">' . $json . '</script>' . "\n";
}

function polea_jsonld_breadcrumb($m = null) {
    $items = array();
    $pos = 1;
    foreach (polea_breadcrumb_items($m) as $c) {
        $items[] = array('@type' => 'ListItem', 'position' => $pos++, 'name' => $c['name'], 'item' => $c['url']);
    }
    return array('@type' => 'BreadcrumbList', 'itemListElement' => $items);
}

function polea_jsonld_faq($pairs) {
    $q = array();
    foreach ($pairs as $p) {
        $q[] = array('@type' => 'Question', 'name' => $p['q'],
                     'acceptedAnswer' => array('@type' => 'Answer', 'text' => $p['a']));
    }
    return array('@type' => 'FAQPage', 'mainEntity' => $q);
}

/** Graf dla pojedynczego motocykla: Product/Motorcycle + Offer + BreadcrumbList + FAQPage. */
function polea_jsonld_single($m) {
    $url  = polea_single_url($m['lot_id']);
    $imgs = Polea_DB::get_images($m['lot_id']);
    $product = array(
        '@type'       => array('Product', 'Motorcycle'),
        'name'        => polea_vehicle_name($m),
        'sku'         => $m['lot_id'],
        'url'         => $url,
        'category'    => 'Motocykl',
        'description' => polea_vehicle_description($m),
    );
    if ($imgs)                       { $product['image'] = array_values($imgs); }
    if (!empty($m['marka']))         { $product['brand'] = array('@type' => 'Brand', 'name' => $m['marka']); }
    if (!empty($m['model']))         { $product['model'] = $m['model']; }
    if (!empty($m['rok_produkcji'])) { $product['vehicleModelDate'] = (string) (int) $m['rok_produkcji']; }
    if (!empty($m['vin']))           { $product['vehicleIdentificationNumber'] = $m['vin']; }
    if (!empty($m['kolor']))         { $product['color'] = $m['kolor']; }
    if (!empty($m['paliwo']))        { $product['fuelType'] = $m['paliwo']; }
    if (!empty($m['skrzynia']))      { $product['vehicleTransmission'] = $m['skrzynia']; }
    if (!empty($m['przebieg_km'])) {
        $product['mileageFromOdometer'] = array('@type' => 'QuantitativeValue', 'value' => (int) $m['przebieg_km'], 'unitCode' => 'KMT');
    }
    if (!empty($m['moc_km'])) {
        $product['vehicleEngine'] = array('@type' => 'EngineSpecification',
            'enginePower' => array('@type' => 'QuantitativeValue', 'value' => (int) $m['moc_km'], 'unitText' => 'KM'));
    }
    if ($m['cena_pln'] !== null && $m['cena_pln'] !== '') {
        $product['offers'] = array(
            '@type'         => 'Offer',
            'price'         => number_format((float) $m['cena_pln'], 2, '.', ''),
            'priceCurrency' => 'PLN',
            'availability'  => ($m['status'] === 'aktywna') ? 'https://schema.org/InStock' : 'https://schema.org/SoldOut',
            'url'           => $url,
        );
    }
    $graph = array($product, polea_jsonld_breadcrumb($m));
    $faq = polea_faq_pairs($m);
    if ($faq) {
        $graph[] = polea_jsonld_faq($faq);
    }
    return polea_jsonld_wrap($graph);
}

/** Graf dla listy: WebSite + Organization + CollectionPage + BreadcrumbList + ItemList. */
function polea_jsonld_list($data) {
    $base  = polea_page_url();
    $graph = array(
        array('@type' => 'WebSite', 'url' => home_url('/'), 'name' => get_bloginfo('name')),
    );
    $org  = array('@type' => 'Organization', 'name' => get_bloginfo('name'), 'url' => home_url('/'));
    $icon = function_exists('get_site_icon_url') ? get_site_icon_url() : '';
    if ($icon) {
        $org['logo'] = $icon;
    }
    $graph[] = $org;
    $graph[] = array('@type' => 'CollectionPage', 'url' => $base, 'name' => wp_get_document_title());
    $graph[] = polea_jsonld_breadcrumb(null);
    if (!empty($data['items'])) {
        $li = array();
        $pos = 1;
        foreach ($data['items'] as $it) {
            $li[] = array('@type' => 'ListItem', 'position' => $pos++,
                          'url' => polea_single_url($it['lot_id']),
                          'name' => polea_vehicle_name($it));
        }
        $graph[] = array('@type' => 'ItemList', 'itemListElement' => $li);
    }
    return polea_jsonld_wrap($graph);
}

/* ------------------------------------------------------------ sitemap (WP core) */

add_action('init', 'polea_register_sitemap', 20);

function polea_register_sitemap() {
    if (!function_exists('wp_register_sitemap_provider') || !class_exists('Polea_Sitemap_Provider')) {
        return;
    }
    if (!get_option('permalink_structure') || !(int) get_option(POLEA_PAGE_OPTION)) {
        return; // sitemap ofert ma sens tylko przy ładnych URL-ach
    }
    wp_register_sitemap_provider('poleamotocykle', new Polea_Sitemap_Provider());
}

if (class_exists('WP_Sitemaps_Provider')) {
    class Polea_Sitemap_Provider extends WP_Sitemaps_Provider {
        public function __construct() {
            $this->name        = 'poleamotocykle';
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
