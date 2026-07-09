<?php
// SPDX-License-Identifier: GPL-2.0-or-later
/**
 * Dział 6 — Bezpieczeństwo: sanityzacja wejścia, pomocnicy uprawnień/nonce.
 */
if (!defined('ABSPATH')) {
    exit;
}

/** Zwraca oczyszczone filtry listy z $_GET (allowlist pól). */
function polea_sanitize_filters() {
    $g = static function ($k) {
        return isset($_GET[$k]) ? sanitize_text_field(wp_unslash($_GET[$k])) : '';
    };
    return array(
        'marka'    => $g('polea_marka'),
        'paliwo'   => $g('polea_paliwo'),
        'rok'      => $g('polea_rok') !== '' ? (int) $g('polea_rok') : '',
        'cena_min' => $g('polea_cena_min') !== '' ? (float) $g('polea_cena_min') : '',
        'cena_max' => $g('polea_cena_max') !== '' ? (float) $g('polea_cena_max') : '',
        'paged'    => max(1, (int) $g('polea_str')),
    );
}

/** Bezpieczny lot_id z $_GET['motocykl'] (alfanumeryczny) lub '' gdy brak/niepoprawny. */
function polea_current_lot_id() {
    if (empty($_GET['motocykl'])) {
        return '';
    }
    $v = sanitize_text_field(wp_unslash($_GET['motocykl']));
    return preg_match('/^[A-Za-z0-9]{1,32}$/', $v) ? $v : '';
}

/** Klucz cache dla danego zestawu filtrów. */
function polea_cache_key($args) {
    return 'polea_list_' . md5(wp_json_encode($args));
}

/** Czyści cache list (transienty). Wołane po ręcznym odświeżeniu / dezaktywacji. */
function polea_flush_cache() {
    global $wpdb;
    $wpdb->query(
        "DELETE FROM {$wpdb->options} WHERE option_name LIKE '\\_transient\\_polea\\_list\\_%' " .
        "OR option_name LIKE '\\_transient\\_timeout\\_polea\\_list\\_%'"
    );
}
