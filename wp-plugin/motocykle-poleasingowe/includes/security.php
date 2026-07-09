<?php
// SPDX-License-Identifier: GPL-2.0-or-later
/**
 * Dział 6 — Bezpieczeństwo: sanityzacja wejścia, pomocnicy uprawnień/nonce.
 */
if (!defined('ABSPATH')) {
    exit;
}

/** Zwraca oczyszczone filtry listy z $_GET (allowlist pól, typy, długości, zakresy). */
function polea_sanitize_filters() {
    // Sanityzacja + twardy limit długości (obrona w głąb; wartości i tak trafiają do prepared statements).
    $g = static function ($k) {
        if (!isset($_GET[$k])) {
            return '';
        }
        $v = sanitize_text_field(wp_unslash($_GET[$k]));
        return function_exists('mb_substr') ? mb_substr($v, 0, 64) : substr($v, 0, 64);
    };
    // Rok: sensowny zakres (0 = brak filtra); cena: nieujemna.
    $rok = $g('polea_rok') !== '' ? (int) $g('polea_rok') : '';
    if ($rok !== '' && ($rok < 1900 || $rok > 2100)) {
        $rok = '';
    }
    $cena_min = $g('polea_cena_min') !== '' ? max(0.0, (float) $g('polea_cena_min')) : '';
    $cena_max = $g('polea_cena_max') !== '' ? max(0.0, (float) $g('polea_cena_max')) : '';
    return array(
        'marka'    => $g('polea_marka'),
        'paliwo'   => $g('polea_paliwo'),
        'rok'      => $rok,
        'cena_min' => $cena_min,
        'cena_max' => $cena_max,
        'paged'    => min(100000, max(1, (int) $g('polea_str'))),
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
