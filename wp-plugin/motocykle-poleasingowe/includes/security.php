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

/**
 * Ogranicza filtry do REALNYCH wartości ze źródła (allowlista z bazy) + kubełkuje cenę.
 * Cel: bramka przeciw zaśmiecaniu cache transientów nieograniczoną przestrzenią kluczy
 * (storage DoS) oraz ignorowanie śmieciowych wartości. Listy wartości są cache'owane.
 */
function polea_constrain_filters($f) {
    if ($f['marka'] !== '' && !in_array($f['marka'], Polea_DB::distinct('marka'), true)) {
        $f['marka'] = '';
    }
    if ($f['paliwo'] !== '' && !in_array($f['paliwo'], Polea_DB::distinct('paliwo'), true)) {
        $f['paliwo'] = '';
    }
    if ($f['rok'] !== '' && !in_array((int) $f['rok'], array_map('intval', Polea_DB::distinct('rok_produkcji')), true)) {
        $f['rok'] = '';
    }
    foreach (array('cena_min', 'cena_max') as $ck) {
        if ($f[$ck] !== '') {
            $v = min(10000000.0, max(0.0, (float) $f[$ck]));
            $f[$ck] = round($v / 500) * 500; // krok 500 = skończona liczba kubełków
        }
    }
    $f['paged'] = min(500, max(1, (int) $f['paged']));
    return $f;
}

/** Bezpieczny lot_id (alfanumeryczny) z query var motocykl (ładny URL) lub $_GET; '' gdy brak/niepoprawny. */
function polea_current_lot_id() {
    $v = get_query_var('motocykl');           // ustawiane przez rewrite /<podstrona>/<lot_id>/
    if ($v === '' || $v === null) {
        $v = isset($_GET['motocykl']) ? wp_unslash($_GET['motocykl']) : '';
    }
    $v = sanitize_text_field((string) $v);
    return preg_match('/^[A-Za-z0-9]{1,32}$/', $v) ? $v : '';
}

/**
 * Generacja cache — wpięta w klucze list/related. Flush = jej INKREMENTACJA, dzięki czemu
 * unieważnienie działa też pod ZEWNĘTRZNYM object cache (Redis/Memcached), gdzie transienty
 * nie są w tabeli options i bezpośredni DELETE by ich nie ruszył. Stare klucze wygasają po TTL.
 */
function polea_cache_gen() {
    return (int) get_option('polea_cache_gen', 1);
}

/** Klucz cache dla danego zestawu filtrów (z generacją). */
function polea_cache_key($args) {
    return 'polea_list_' . polea_cache_gen() . '_' . md5(wp_json_encode($args));
}

/** Czyści cache list + related + listy wartości filtrów. Po ręcznym odświeżeniu / dezaktywacji. */
function polea_flush_cache() {
    // Podstawowe unieważnienie (działa pod KAŻDYM backendem cache): podbij generację —
    // wszystkie klucze polea_list_<gen>_* / polea_rel_<gen>_* stają się nieosiągalne.
    update_option('polea_cache_gen', polea_cache_gen() + 1);
    foreach (array('marka', 'paliwo', 'rok_produkcji') as $col) {
        delete_transient('polea_distinct_' . $col);   // delete_transient działa też pod object cache
    }
    global $wpdb;
    // Dodatkowo: sprzątnij stare wiersze transientów z tabeli options (gdy cache jest w DB),
    // by nie zalegały do wygaśnięcia TTL. Pod object cache ten DELETE nic nie znajdzie — i dobrze.
    $wpdb->query(
        "DELETE FROM {$wpdb->options} WHERE option_name LIKE '\\_transient\\_polea\\_list\\_%' " .
        "OR option_name LIKE '\\_transient\\_timeout\\_polea\\_list\\_%' " .
        "OR option_name LIKE '\\_transient\\_polea\\_rel\\_%' " .
        "OR option_name LIKE '\\_transient\\_timeout\\_polea\\_rel\\_%'"
    );
}
