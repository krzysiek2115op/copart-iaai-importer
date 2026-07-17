<?php
// SPDX-License-Identifier: GPL-2.0-or-later
/**
 * Dział 10 — Podstrona i motyw: automatyczne utworzenie „Nasze motory" + wpięcie w menu.
 * Idempotentne (guard przed duplikatem). Obsługa motywów block (wp_navigation) i classic (menu location).
 */
if (!defined('ABSPATH')) {
    exit;
}

function polea_activate() {
    polea_create_page();
    polea_add_to_menu();
    // Rejestrujemy regułę ładnych URL-i PRZED flush (na tym żądaniu 'init' odpalił się,
    // gdy opcja strony była jeszcze pusta), aby trafiła do przepisanych reguł.
    if (function_exists('polea_register_rewrites')) {
        polea_register_rewrites();
    }
    flush_rewrite_rules();
}

function polea_deactivate() {
    polea_flush_cache();
    flush_rewrite_rules();
}

/** Tworzy stronę „Nasze motory" z shortcode [motocykle]. Zwraca ID (idempotentnie). */
function polea_create_page() {
    $existing = (int) get_option(POLEA_PAGE_OPTION);
    if ($existing && ($p = get_post($existing)) && $p->post_status !== 'trash') {
        return $existing;
    }
    $by_path = get_page_by_path('nasze-motory');
    if ($by_path) {
        update_option(POLEA_PAGE_OPTION, $by_path->ID);
        return $by_path->ID;
    }
    $id = wp_insert_post(array(
        'post_title'   => 'Nasze motory',
        'post_name'    => 'nasze-motory',
        'post_content' => '[motocykle]',
        'post_status'  => 'publish',
        'post_type'    => 'page',
    ));
    if ($id && !is_wp_error($id)) {
        update_option(POLEA_PAGE_OPTION, $id);
        return $id;
    }
    return 0;
}

function polea_add_to_menu() {
    $page_id = (int) get_option(POLEA_PAGE_OPTION);
    if (!$page_id) {
        return;
    }
    if (function_exists('wp_is_block_theme') && wp_is_block_theme()) {
        polea_add_to_block_nav($page_id);
    } else {
        polea_add_to_classic_menu($page_id);
    }
}

/** Motyw klasyczny: dodaje pozycję do menu przypisanego do lokalizacji (lub pierwszego). */
function polea_add_to_classic_menu($page_id) {
    $locations = get_nav_menu_locations();
    $menu_id = 0;
    if (!empty($locations['primary'])) {
        $menu_id = (int) $locations['primary'];
    } elseif (!empty($locations)) {
        $menu_id = (int) reset($locations);
    } else {
        $menus = wp_get_nav_menus();
        if ($menus) {
            $menu_id = (int) $menus[0]->term_id;
        }
    }
    if (!$menu_id) {
        return;
    }
    foreach ((array) wp_get_nav_menu_items($menu_id) as $it) {
        if ((int) $it->object_id === $page_id && $it->object === 'page') {
            return; // już jest — bez duplikatu
        }
    }
    wp_update_nav_menu_item($menu_id, 0, array(
        'menu-item-title'     => 'Nasze motory',
        'menu-item-object'    => 'page',
        'menu-item-object-id' => $page_id,
        'menu-item-type'      => 'post_type',
        'menu-item-status'    => 'publish',
    ));
}

/** Motyw blokowy: dopina page-link do pierwszej nawigacji (jeśli jeszcze go nie ma). */
function polea_add_to_block_nav($page_id) {
    $navs = get_posts(array(
        'post_type'   => 'wp_navigation',
        'numberposts' => 1,
        'post_status' => 'publish',
    ));
    if (!$navs) {
        return;
    }
    $nav = $navs[0];
    // Gdy nawigacja używa bloku „Lista stron" (page-list), WSZYSTKIE opublikowane
    // strony (w tym nasza) renderują się automatycznie — jawny link zrobiłby DUPLIKAT.
    if (strpos($nav->post_content, 'wp:page-list') !== false) {
        return; // page-list pokazuje stronę sam z siebie
    }
    if (strpos($nav->post_content, '"id":' . $page_id . ',') !== false
        || strpos($nav->post_content, '"id":' . $page_id . '}') !== false) {
        return; // już jest
    }
    $url   = get_permalink($page_id);
    $block = '<!-- wp:navigation-link {"label":"Nasze motory","type":"page","id":' . $page_id
        . ',"url":"' . esc_url($url) . '","kind":"post-type"} /-->';
    wp_update_post(array(
        'ID'           => $nav->ID,
        'post_content' => $nav->post_content . $block,
    ));
}

/**
 * Wpięcie w motywy z menu „na sztywno" (np. „Kredyt Kompas" przez kk_menu_items()).
 * Takie motywy nie używają menu WP ani page-list, więc standardowe dopięcie ich nie
 * dotyczy — ale jeśli motyw wystawia filtr, dokładamy podstronę RAZ (po slugu),
 * dziedzicząc styl menu klienta. Na innych motywach filtr nie istnieje → hak bezczynny.
 */
add_filter('kk_menu_items', 'polea_theme_menu_item');
function polea_theme_menu_item($items) {
    if (!is_array($items)) {
        return $items;
    }
    $page_id = (int) get_option(POLEA_PAGE_OPTION);
    if (!$page_id) {
        return $items;
    }
    $slug = get_post_field('post_name', $page_id);
    if ($slug && !isset($items[$slug])) {           // raz — bez duplikatu
        $title = get_the_title($page_id);
        $items[$slug] = ($title !== '') ? $title : 'Nasze motory';
    }
    return $items;
}
