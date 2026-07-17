<?php
// SPDX-License-Identifier: GPL-2.0-or-later
/**
 * Dział 6 — panel admina: status połączenia z bazą, instrukcja wp-config, czyszczenie cache.
 */
if (!defined('ABSPATH')) {
    exit;
}

add_action('admin_menu', 'polea_admin_menu');

function polea_admin_menu() {
    add_options_page(
        'Motocykle (poleasingowe.pl)',
        'Motocykle',
        'manage_options',
        'polea-motocykle',
        'polea_admin_page'
    );
}

function polea_admin_page() {
    if (!current_user_can('manage_options')) {
        return;
    }
    if (isset($_POST['polea_flush']) && check_admin_referer('polea_flush_cache')) {
        polea_flush_cache();
        echo '<div class="notice notice-success is-dismissible"><p>Cache listy wyczyszczony.</p></div>';
    }

    $st  = Polea_DB::status();
    $pid = (int) get_option(POLEA_PAGE_OPTION);
    ?>
    <div class="wrap">
        <h1>Importer Motocykli (poleasingowe.pl)</h1>

        <h2>Status bazy</h2>
        <p><strong><?php echo $st['ok'] ? '✅ ' : '⚠️ '; ?></strong><?php echo esc_html($st['msg']); ?></p>

        <?php if (!$st['ok']) : ?>
            <h3>Konfiguracja połączenia (wp-config.php)</h3>
            <p>Dodaj poniższe stałe do <code>wp-config.php</code> (powyżej linii „That's all, stop editing"):</p>
            <pre style="background:#f6f7f7;padding:1rem;border-radius:6px;overflow:auto;">define('POLEA_DB_HOST', '127.0.0.1');
define('POLEA_DB_NAME', 'polea');
define('POLEA_DB_USER', 'polea');
define('POLEA_DB_PASSWORD', 'TWOJE_HASLO');
// opcjonalnie: define('POLEA_DB_PORT', 3306);</pre>
            <p>To osobna baza MySQL zasilana przez scraper — nie koliduje z bazą WordPressa.</p>
        <?php endif; ?>

        <h2>Podstrona</h2>
        <p>
            <?php if ($pid) : ?>
                Strona „Nasze motory": <a href="<?php echo esc_url(get_permalink($pid)); ?>"><?php echo esc_html(get_the_title($pid)); ?></a>
            <?php else : ?>
                Strona „Nasze motory" nie została jeszcze utworzona (dezaktywuj i aktywuj wtyczkę ponownie).
            <?php endif; ?>
        </p>

        <h2>Cache</h2>
        <form method="post">
            <?php wp_nonce_field('polea_flush_cache'); ?>
            <button class="button" name="polea_flush" value="1">Wyczyść cache listy</button>
        </form>
    </div>
    <?php
}
