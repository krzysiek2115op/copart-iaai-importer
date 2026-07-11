<?php
// SPDX-License-Identifier: GPL-2.0-or-later
/**
 * Dział 9 — Front i media: shortcode [motocykle] (lista + szczegóły), filtry, cache, galeria hotlink.
 * Wszystkie dane z bazy są escapowane na wyjściu. Błędy nigdy nie trafiają do klienta.
 */
if (!defined('ABSPATH')) {
    exit;
}

function polea_register_shortcode() {
    add_shortcode('motocykle', 'polea_shortcode');
}

function polea_shortcode($atts) {
    wp_enqueue_style('polea-front');
    if (!Polea_DB::is_configured()) {
        return polea_notice('Oferta motocykli będzie dostępna wkrótce.');
    }
    $lot = polea_current_lot_id();
    return $lot !== '' ? polea_render_single($lot) : polea_render_list($atts);
}

/* ------------------------------------------------------------------ lista */

function polea_render_list($atts) {
    $a       = shortcode_atts(array('ile' => 12), $atts, 'motocykle');
    $filters = polea_constrain_filters(polea_sanitize_filters());
    $per     = max(1, min(60, (int) $a['ile']));
    $args    = array_merge($filters, array('per_page' => $per, 'paged' => $filters['paged']));

    $key  = polea_cache_key($args);
    $data = get_transient($key);
    if ($data === false) {
        $data = Polea_DB::query_list($args);
        $ids  = array_map(static function ($m) { return $m['lot_id']; }, $data['items']);
        $data['thumbs'] = Polea_DB::first_images_map($ids); // miniatury w cache -> brak dodatkowego zapytania przy trafieniu
        set_transient($key, $data, POLEA_CACHE_TTL);
    }

    ob_start();
    echo '<div class="polea-wrap">';
    echo polea_render_filters($filters);
    if (empty($data['items'])) {
        echo '<p class="polea-empty">Brak motocykli spełniających kryteria.</p>';
    } else {
        $thumbs = isset($data['thumbs']) ? $data['thumbs'] : array();
        echo '<div class="polea-grid">';
        foreach ($data['items'] as $m) {
            $thumb = isset($thumbs[$m['lot_id']]) ? $thumbs[$m['lot_id']] : '';
            echo polea_render_card($m, $thumb);
        }
        echo '</div>';
        echo polea_render_pager($data);
    }
    echo '</div>';
    return ob_get_clean();
}

function polea_render_card($m, $thumb = '') {
    $lot    = $m['lot_id'];
    $title  = trim(($m['marka'] ?? '') . ' ' . ($m['model'] ?? ''));
    $url    = polea_single_url($lot);   // ładny URL /<podstrona>/<lot_id>/ (SEO), z fallbackiem na ?motocykl=

    ob_start(); ?>
    <article class="polea-card">
        <a class="polea-card__link" href="<?php echo esc_url($url); ?>">
            <div class="polea-card__media">
                <?php if ($thumb) : ?>
                    <img loading="lazy" referrerpolicy="no-referrer" src="<?php echo esc_url($thumb); ?>" alt="<?php echo esc_attr($title); ?>">
                <?php else : ?>
                    <span class="polea-card__noimg">brak zdjęcia</span>
                <?php endif; ?>
            </div>
            <div class="polea-card__body">
                <h3 class="polea-card__title"><?php echo esc_html($title); ?></h3>
                <p class="polea-card__price"><?php echo esc_html(polea_price($m)); ?></p>
                <ul class="polea-card__specs">
                    <?php
                    echo polea_spec_li('Rok', $m['rok_produkcji']);
                    echo polea_spec_li('Przebieg', polea_km($m['przebieg_km']));
                    echo polea_spec_li('Pojemność', $m['pojemnosc_ccm'] ? $m['pojemnosc_ccm'] . ' ccm' : '');
                    echo polea_spec_li('Paliwo', $m['paliwo']);
                    ?>
                </ul>
            </div>
        </a>
    </article>
    <?php
    return ob_get_clean();
}

function polea_render_filters($f) {
    $marki  = Polea_DB::distinct('marka');
    $paliwa = Polea_DB::distinct('paliwo');
    $lata   = Polea_DB::distinct('rok_produkcji');
    rsort($lata);

    ob_start(); ?>
    <form class="polea-filters" method="get">
        <label>Marka
            <select name="polea_marka">
                <option value="">— wszystkie —</option>
                <?php foreach ($marki as $v) : ?>
                    <option value="<?php echo esc_attr($v); ?>" <?php selected($f['marka'], $v); ?>><?php echo esc_html($v); ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>Paliwo
            <select name="polea_paliwo">
                <option value="">— dowolne —</option>
                <?php foreach ($paliwa as $v) : ?>
                    <option value="<?php echo esc_attr($v); ?>" <?php selected($f['paliwo'], $v); ?>><?php echo esc_html($v); ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>Rok
            <select name="polea_rok">
                <option value="">— dowolny —</option>
                <?php foreach ($lata as $v) : ?>
                    <option value="<?php echo esc_attr($v); ?>" <?php selected((string) $f['rok'], (string) $v); ?>><?php echo esc_html($v); ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>Cena do (PLN)
            <input type="number" name="polea_cena_max" value="<?php echo esc_attr($f['cena_max']); ?>" min="0" step="500" placeholder="np. 30000">
        </label>
        <button type="submit" class="polea-filters__btn">Filtruj</button>
    </form>
    <?php
    return ob_get_clean();
}

function polea_render_pager($data) {
    if ($data['pages'] <= 1) {
        return '';
    }
    $base = polea_page_url();
    $keep = array();
    foreach (array('polea_marka', 'polea_paliwo', 'polea_rok', 'polea_cena_max', 'polea_cena_min') as $k) {
        if (!empty($_GET[$k])) {
            $keep[$k] = sanitize_text_field(wp_unslash($_GET[$k]));
        }
    }
    $pages = (int) $data['pages'];
    $cur   = (int) $data['paged'];
    $win   = 2; // okno stron wokol biezacej — pager nie puchnie przy setkach stron
    ob_start();
    echo '<nav class="polea-pager">';
    $gap = false;
    for ($i = 1; $i <= $pages; $i++) {
        // Pokazuj: skrajne strony, oraz okno +/- $win wokol biezacej; reszta -> wielokropek.
        if ($i !== 1 && $i !== $pages && abs($i - $cur) > $win) {
            if (!$gap) {
                echo '<span class="polea-pager__gap">…</span>';
                $gap = true;
            }
            continue;
        }
        $gap = false;
        $url = esc_url(add_query_arg(array_merge($keep, array('polea_str' => $i)), $base));
        if ($i === $cur) {
            echo '<span class="polea-pager__cur">' . (int) $i . '</span>';
        } else {
            echo '<a href="' . $url . '">' . (int) $i . '</a>';
        }
    }
    echo '</nav>';
    return ob_get_clean();
}

/* --------------------------------------------------------------- szczegóły */

function polea_render_single($lot) {
    $m = Polea_DB::get_one($lot);
    if (!$m) {
        return polea_notice('Nie znaleziono tego motocykla.');
    }
    $imgs  = Polea_DB::get_images($lot);
    $title = trim(($m['marka'] ?? '') . ' ' . ($m['model'] ?? ''));

    ob_start(); ?>
    <div class="polea-wrap polea-single">
        <a class="polea-back" href="<?php echo esc_url(polea_page_url()); ?>">&larr; Wróć do listy</a>
        <h2 class="polea-single__title"><?php echo esc_html($title); ?></h2>
        <div class="polea-single__grid">
            <div class="polea-gallery">
                <?php if ($imgs) : foreach ($imgs as $i => $u) : ?>
                    <img loading="lazy" referrerpolicy="no-referrer" src="<?php echo esc_url($u); ?>" alt="<?php echo esc_attr($title . ' — zdjęcie ' . ($i + 1)); ?>">
                <?php endforeach; else : ?>
                    <span class="polea-card__noimg">brak zdjęć</span>
                <?php endif; ?>
            </div>
            <div class="polea-single__info">
                <p class="polea-single__price"><?php echo esc_html(polea_price($m)); ?></p>
                <table class="polea-specs">
                    <?php
                    echo polea_spec_row('VIN', $m['vin']);
                    echo polea_spec_row('Rok produkcji', $m['rok_produkcji']);
                    echo polea_spec_row('Przebieg', polea_km($m['przebieg_km']));
                    echo polea_spec_row('Pojemność', $m['pojemnosc_ccm'] ? $m['pojemnosc_ccm'] . ' ccm' : '');
                    echo polea_spec_row('Moc', $m['moc_km'] ? $m['moc_km'] . ' KM' : '');
                    echo polea_spec_row('Paliwo', $m['paliwo']);
                    echo polea_spec_row('Skrzynia', $m['skrzynia']);
                    echo polea_spec_row('Napęd', $m['naped']);
                    echo polea_spec_row('Kolor', $m['kolor']);
                    echo polea_spec_row('Lokalizacja', $m['lokalizacja']);
                    echo polea_spec_row('Numer aukcji', $m['numer_aukcji']);
                    ?>
                </table>
                <?php if (!empty($m['url'])) : ?>
                    <a class="polea-source" href="<?php echo esc_url($m['url']); ?>" target="_blank" rel="noopener nofollow">Zobacz aukcję na poleasingowe.pl</a>
                <?php endif; ?>
            </div>
        </div>
    </div>
    <?php
    return ob_get_clean();
}

/* ---------------------------------------------------------------- pomocnicy */

function polea_price($m) {
    if ($m['cena_pln'] === null || $m['cena_pln'] === '') {
        return 'Cena do ustalenia';
    }
    $s = number_format((float) $m['cena_pln'], 0, ',', ' ') . ' PLN';
    if ((int) $m['cena_netto'] === 1) {
        $s .= ' netto';
    }
    return $s;
}

function polea_km($v) {
    return ($v !== null && $v !== '') ? number_format((int) $v, 0, ',', ' ') . ' km' : '';
}

function polea_spec_li($label, $val) {
    if ($val === null || $val === '' || $val === 0 || $val === '0') {
        return '';
    }
    return '<li><span>' . esc_html($label) . '</span> ' . esc_html($val) . '</li>';
}

function polea_spec_row($label, $val) {
    if ($val === null || $val === '' || $val === 0 || $val === '0') {
        return '';
    }
    return '<tr><th>' . esc_html($label) . '</th><td>' . esc_html($val) . '</td></tr>';
}

function polea_page_url() {
    $pid = (int) get_option(POLEA_PAGE_OPTION);
    return $pid ? get_permalink($pid) : remove_query_arg(array('motocykl', 'polea_str'));
}

function polea_notice($msg) {
    return '<div class="polea-wrap"><p class="polea-empty">' . esc_html($msg) . '</p></div>';
}
