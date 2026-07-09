<?php
// SPDX-License-Identifier: GPL-2.0-or-later
/**
 * Dział 8 (repo) + Dział 6 (bezpieczne połączenie) — odczyt z osobnej bazy MySQL (polea_*).
 *
 * Świadoma decyzja: łączymy się przez mysqli z obsługą błędów, a NIE przez `new wpdb`,
 * bo wpdb przy złych danych logowania potrafi wywołać wp_die i wyłączyć stronę klienta.
 * Poświadczenia wyłącznie ze stałych POLEA_DB_* (wp-config.php) — nigdy w kodzie.
 */
if (!defined('ABSPATH')) {
    exit;
}

class Polea_DB {

    /** @var mysqli|false|null null=nietknięte, false=błąd/niedostępne */
    private static $m = null;

    public static function is_configured() {
        return defined('POLEA_DB_HOST') && defined('POLEA_DB_NAME')
            && defined('POLEA_DB_USER') && defined('POLEA_DB_PASSWORD');
    }

    /** Zwraca połączenie mysqli albo null (nigdy nie przerywa działania strony). */
    public static function conn() {
        if (self::$m !== null) {
            return self::$m ?: null;
        }
        if (!self::is_configured()) {
            self::$m = false;
            return null;
        }
        $port = defined('POLEA_DB_PORT') ? (int) POLEA_DB_PORT : 3306;
        if (function_exists('mysqli_report')) {
            mysqli_report(MYSQLI_REPORT_OFF); // sami obsługujemy błędy, bez wyjątków
        }
        $m = mysqli_init();
        if (!$m) {
            self::$m = false;
            return null;
        }
        // Twardy timeout połączenia — awaria/spowolnienie bazy nie może zawiesić strony klienta.
        @mysqli_options($m, MYSQLI_OPT_CONNECT_TIMEOUT, 3);
        if (defined('MYSQLI_OPT_READ_TIMEOUT')) {
            @mysqli_options($m, MYSQLI_OPT_READ_TIMEOUT, 5);
        }
        // Wyłącz LOCAL INFILE — obrona przed złośliwym/zmanipulowanym serwerem MySQL czytającym pliki klienta.
        if (defined('MYSQLI_OPT_LOCAL_INFILE')) {
            @mysqli_options($m, MYSQLI_OPT_LOCAL_INFILE, false);
        }
        if (!@mysqli_real_connect($m, POLEA_DB_HOST, POLEA_DB_USER, POLEA_DB_PASSWORD, POLEA_DB_NAME, $port)) {
            @mysqli_close($m);
            self::$m = false;
            return null;
        }
        @mysqli_set_charset($m, 'utf8mb4');
        self::$m = $m;
        return $m;
    }

    /** Prepared query -> tablica wierszy (assoc). */
    private static function q($sql, $types = '', $params = array()) {
        $m = self::conn();
        if (!$m) {
            return array();
        }
        $stmt = @mysqli_prepare($m, $sql);
        if (!$stmt) {
            return array();
        }
        if ($params) {
            mysqli_stmt_bind_param($stmt, $types, ...$params);
        }
        if (!mysqli_stmt_execute($stmt)) {
            mysqli_stmt_close($stmt);
            return array();
        }
        $res  = mysqli_stmt_get_result($stmt);
        $rows = $res ? mysqli_fetch_all($res, MYSQLI_ASSOC) : array();
        mysqli_stmt_close($stmt);
        return $rows;
    }

    private static function scalar($sql, $types = '', $params = array()) {
        $rows = self::q($sql, $types, $params);
        if (!$rows) {
            return null;
        }
        $first = reset($rows[0]);
        return $first;
    }

    /** Lista motocykli z filtrami + paginacją. */
    public static function query_list($a) {
        $where  = 'status = ?';
        $types  = 's';
        $params = array('aktywna');

        if (!empty($a['marka']))  { $where .= ' AND marka = ?';           $types .= 's'; $params[] = $a['marka']; }
        if (!empty($a['paliwo'])) { $where .= ' AND paliwo = ?';          $types .= 's'; $params[] = $a['paliwo']; }
        if (!empty($a['rok']))    { $where .= ' AND rok_produkcji = ?';   $types .= 'i'; $params[] = (int) $a['rok']; }
        if (isset($a['cena_min']) && $a['cena_min'] !== '') { $where .= ' AND cena_pln >= ?'; $types .= 'd'; $params[] = (float) $a['cena_min']; }
        if (isset($a['cena_max']) && $a['cena_max'] !== '') { $where .= ' AND cena_pln <= ?'; $types .= 'd'; $params[] = (float) $a['cena_max']; }

        $per   = max(1, min(60, (int) ($a['per_page'] ?? 12)));
        $paged = max(1, (int) ($a['paged'] ?? 1));
        $off   = ($paged - 1) * $per;

        $total = (int) self::scalar("SELECT COUNT(*) FROM polea_motocykle WHERE {$where}", $types, $params);

        $lt = $types . 'ii';
        $lp = array_merge($params, array($per, $off));
        $items = self::q(
            "SELECT * FROM polea_motocykle WHERE {$where} " .
            "ORDER BY (termin_zakonczenia IS NULL), termin_zakonczenia ASC LIMIT ? OFFSET ?",
            $lt, $lp
        );

        return array(
            'items'    => $items,
            'total'    => $total,
            'per_page' => $per,
            'paged'    => $paged,
            'pages'    => (int) ceil($total / $per),
        );
    }

    public static function get_one($lot_id) {
        $rows = self::q('SELECT * FROM polea_motocykle WHERE lot_id = ? LIMIT 1', 's', array($lot_id));
        return $rows ? $rows[0] : null;
    }

    public static function get_images($lot_id) {
        $rows = self::q(
            'SELECT url FROM polea_zdjecia WHERE lot_id = ? ORDER BY sort_order ASC',
            's', array($lot_id)
        );
        return array_map(static function ($r) { return $r['url']; }, $rows);
    }

    /** Pierwsze zdjęcie (miniatura) dla wielu lotów naraz — unika N+1 na liście. */
    public static function first_images_map($lot_ids) {
        if (!$lot_ids) {
            return array();
        }
        $in    = implode(',', array_fill(0, count($lot_ids), '?'));
        $types = str_repeat('s', count($lot_ids));
        $rows  = self::q(
            "SELECT z.lot_id, z.url FROM polea_zdjecia z " .
            "JOIN (SELECT lot_id, MIN(sort_order) AS ms FROM polea_zdjecia " .
            "      WHERE lot_id IN ({$in}) GROUP BY lot_id) t " .
            "  ON t.lot_id = z.lot_id AND t.ms = z.sort_order",
            $types, $lot_ids
        );
        $map = array();
        foreach ($rows as $r) {
            $map[$r['lot_id']] = $r['url'];
        }
        return $map;
    }

    /** Wartości do filtrów (kolumna z allowlisty). Cache w transient — używane też do
     *  walidacji wejścia (bramkuje zaśmiecanie cache listy), więc nie może dokładać zapytań. */
    public static function distinct($col) {
        $allow = array('marka', 'paliwo', 'rok_produkcji');
        if (!in_array($col, $allow, true)) {
            return array();
        }
        $tkey   = 'polea_distinct_' . $col;
        $cached = get_transient($tkey);
        if (is_array($cached)) {
            return $cached;
        }
        $rows = self::q(
            "SELECT DISTINCT {$col} AS v FROM polea_motocykle " .
            "WHERE status = 'aktywna' AND {$col} IS NOT NULL AND {$col} <> '' ORDER BY {$col}"
        );
        $vals = array_map(static function ($r) { return $r['v']; }, $rows);
        set_transient($tkey, $vals, HOUR_IN_SECONDS);
        return $vals;
    }

    /** Status połączenia dla panelu admina. */
    public static function status() {
        if (!self::is_configured()) {
            return array('ok' => false, 'msg' => 'Brak stałych POLEA_DB_* w wp-config.php.');
        }
        if (!self::conn()) {
            return array('ok' => false, 'msg' => 'Nie udało się połączyć z bazą (sprawdź host/login/hasło).');
        }
        $n = self::scalar('SELECT COUNT(*) FROM polea_motocykle');
        if ($n === null) {
            return array('ok' => false, 'msg' => 'Połączono, ale brak tabeli polea_motocykle (uruchom db/schema.sql).');
        }
        return array('ok' => true, 'msg' => 'Połączono. Motocykli w bazie: ' . (int) $n);
    }
}
