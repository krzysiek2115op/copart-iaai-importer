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
    echo '<section class="polea-wrap" aria-label="Aukcje motocykli">';
    echo polea_render_breadcrumbs();
    echo '<p class="polea-intro">Aktualne aukcje motocykli poleasingowych — porównaj ceny, rok produkcji, przebieg i pojemność. Wybierz ofertę, aby zobaczyć pełne dane i zdjęcia.</p>';
    echo polea_render_filters($filters);
    if (empty($data['items'])) {
        echo '<p class="polea-empty">Brak motocykli spełniających kryteria.</p>';
    } else {
        $thumbs = isset($data['thumbs']) ? $data['thumbs'] : array();
        // H2 sekcji (utrzymuje hierarchię H1 motywu -> H2 -> H3 kart, bez przeskoku).
        echo '<h2 class="polea-h polea-sr-only">Dostępne motocykle: ' . (int) $data['total'] . '</h2>';
        echo '<ul class="polea-grid" role="list">';
        $i = 0;
        foreach ($data['items'] as $m) {
            $thumb = isset($thumbs[$m['lot_id']]) ? $thumbs[$m['lot_id']] : '';
            echo '<li>' . polea_render_card($m, $thumb, $i === 0) . '</li>'; // pierwsza karta = kandydat na LCP
            $i++;
        }
        echo '</ul>';
        echo polea_render_pager($data);
    }
    echo '</section>';
    polea_jsonld_enqueue(polea_jsonld_list($data)); // CollectionPage + ItemList + WebSite + Organization + Breadcrumb
    return ob_get_clean();
}

function polea_render_card($m, $thumb = '', $eager = false) {
    $lot   = $m['lot_id'];
    $name  = trim(($m['marka'] ?? '') . ' ' . ($m['model'] ?? ''));
    $rok   = !empty($m['rok_produkcji']) ? ' ' . (int) $m['rok_produkcji'] : '';
    $alt   = trim($name . $rok) . ' — ' . polea_price($m);       // alt generowany automatycznie z danych
    $url   = polea_single_url($lot);                              // ładny URL, fallback ?motocykl=

    ob_start(); ?>
    <article class="polea-card">
        <a class="polea-card__link" href="<?php echo esc_url($url); ?>">
            <figure class="polea-card__media">
                <?php if ($thumb) : ?>
                    <img src="<?php echo esc_url($thumb); ?>" alt="<?php echo esc_attr($alt); ?>" title="<?php echo esc_attr(trim($name . $rok)); ?>"
                         loading="<?php echo $eager ? 'eager' : 'lazy'; ?>" decoding="async"<?php echo $eager ? ' fetchpriority="high"' : ''; ?> referrerpolicy="no-referrer">
                <?php else : ?>
                    <span class="polea-card__noimg" aria-hidden="true">brak zdjęcia</span>
                <?php endif; ?>
            </figure>
            <div class="polea-card__body">
                <h3 class="polea-card__title"><?php echo esc_html($name); ?></h3>
                <p class="polea-card__price"><?php echo esc_html(polea_price($m)); ?></p>
                <ul class="polea-card__specs">
                    <?php
                    echo polea_spec_li('Rok', $m['rok_produkcji'] ?? null);
                    echo polea_spec_li('Przebieg', polea_km($m['przebieg_km'] ?? null));
                    echo polea_spec_li('Pojemność', !empty($m['pojemnosc_ccm']) ? (int) $m['pojemnosc_ccm'] . ' ccm' : '');
                    echo polea_spec_li('Paliwo', $m['paliwo'] ?? '');
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
    <form class="polea-filters" method="get" role="search" aria-label="Filtruj motocykle">
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
    echo '<nav class="polea-pager" aria-label="Paginacja ofert">';
    $gap = false;
    for ($i = 1; $i <= $pages; $i++) {
        // Pokazuj: skrajne strony, oraz okno +/- $win wokol biezacej; reszta -> wielokropek.
        if ($i !== 1 && $i !== $pages && abs($i - $cur) > $win) {
            if (!$gap) {
                echo '<span class="polea-pager__gap" aria-hidden="true">…</span>';
                $gap = true;
            }
            continue;
        }
        $gap = false;
        $url = esc_url(add_query_arg(array_merge($keep, array('polea_str' => $i)), $base));
        if ($i === $cur) {
            echo '<span class="polea-pager__cur" aria-current="page">' . (int) $i . '</span>';
        } else {
            $rel = ($i === $cur - 1) ? ' rel="prev"' : (($i === $cur + 1) ? ' rel="next"' : '');
            echo '<a href="' . $url . '"' . $rel . ' aria-label="Strona ' . (int) $i . '">' . (int) $i . '</a>';
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
    $imgs = Polea_DB::get_images($lot);
    $name = trim(($m['marka'] ?? '') . ' ' . ($m['model'] ?? ''));
    $status_map = array('aktywna' => 'Aktywna', 'zakonczona' => 'Zakończona', 'usunieta' => 'Usunięta');
    $status = isset($status_map[$m['status']]) ? $status_map[$m['status']] : $m['status'];

    ob_start();
    echo '<div class="polea-wrap polea-single">';
    echo polea_render_breadcrumbs($m);
    // H1 pochodzi z motywu (tytuł strony podmieniony filtrem the_title na nazwę pojazdu).
    ?>
    <article class="polea-vehicle">
        <p class="polea-single__price"><?php echo esc_html(polea_price($m)); ?></p>

        <?php if ($imgs) : ?>
        <figure class="polea-gallery">
            <?php foreach ($imgs as $i => $u) : $eager = ($i === 0); ?>
                <img src="<?php echo esc_url($u); ?>" alt="<?php echo esc_attr($name . ' — zdjęcie ' . ($i + 1)); ?>"
                     loading="<?php echo $eager ? 'eager' : 'lazy'; ?>" decoding="async"<?php echo $eager ? ' fetchpriority="high"' : ''; ?> referrerpolicy="no-referrer">
            <?php endforeach; ?>
            <figcaption class="polea-sr-only"><?php echo esc_html('Galeria zdjęć: ' . $name); ?></figcaption>
        </figure>
        <?php endif; ?>

        <section class="polea-sec" aria-labelledby="polea-h-opis">
            <h2 id="polea-h-opis" class="polea-h">Opis</h2>
            <p class="polea-desc"><?php echo esc_html(polea_vehicle_description($m)); ?></p>
        </section>

        <?php $chips = polea_highlight_chips($m); if ($chips) : ?>
        <section class="polea-sec" aria-labelledby="polea-h-param">
            <h2 id="polea-h-param" class="polea-h">Najważniejsze parametry</h2>
            <ul class="polea-chips" role="list"><?php echo $chips; ?></ul>
        </section>
        <?php endif; ?>

        <section class="polea-sec" aria-labelledby="polea-h-tab">
            <h2 id="polea-h-tab" class="polea-h">Dane techniczne</h2>
            <table class="polea-specs">
                <caption class="polea-sr-only"><?php echo esc_html('Parametry techniczne: ' . $name); ?></caption>
                <tbody>
                <?php
                echo polea_spec_row('Marka', $m['marka']);
                echo polea_spec_row('Model', $m['model']);
                echo polea_spec_row('Typ', $m['typ']);
                echo polea_spec_row('Rok produkcji', $m['rok_produkcji']);
                echo polea_spec_row('Data 1. rejestracji', $m['data_pierwszej_rej']);
                echo polea_spec_row('Przebieg', polea_km($m['przebieg_km']));
                echo polea_spec_row('Pojemność', !empty($m['pojemnosc_ccm']) ? (int) $m['pojemnosc_ccm'] . ' ccm' : '');
                echo polea_spec_row('Moc', !empty($m['moc_km']) ? (int) $m['moc_km'] . ' KM' : '');
                echo polea_spec_row('Paliwo', $m['paliwo']);
                echo polea_spec_row('Skrzynia', $m['skrzynia']);
                echo polea_spec_row('Napęd', $m['naped']);
                echo polea_spec_row('Kolor', $m['kolor']);
                echo polea_spec_row('Liczba kluczyków', $m['ilosc_kluczykow']);
                echo polea_spec_row('VIN', $m['vin']);
                echo polea_spec_row('Nr rejestracyjny', $m['nr_rej']);
                ?>
                </tbody>
            </table>
        </section>

        <section class="polea-sec" aria-labelledby="polea-h-info">
            <h2 id="polea-h-info" class="polea-h">Informacje o aukcji</h2>
            <dl class="polea-info">
                <?php
                echo polea_info_row('Status', $status);
                if (!empty($m['termin_zakonczenia'])) {
                    $iso = str_replace(' ', 'T', $m['termin_zakonczenia']);
                    echo '<dt>Termin zakończenia</dt><dd><time datetime="' . esc_attr($iso) . '">' . esc_html($m['termin_zakonczenia']) . '</time></dd>';
                }
                if (!empty($m['lokalizacja'])) {
                    echo '<dt>Lokalizacja</dt><dd><address class="polea-addr">' . esc_html($m['lokalizacja']) . '</address></dd>';
                }
                echo polea_info_row('Numer aukcji', $m['numer_aukcji']);
                echo polea_info_row('Forma sprzedaży', $m['forma_sprzedazy']);
                echo polea_info_row('Rodzaj ceny', ((int) $m['cena_netto'] === 1) ? 'netto' : 'brutto');
                if ($m['najnizsza_cena_30d'] !== null && $m['najnizsza_cena_30d'] !== '') {
                    echo polea_info_row('Najniższa cena z 30 dni', number_format((float) $m['najnizsza_cena_30d'], 0, ',', ' ') . ' PLN');
                }
                ?>
            </dl>
        </section>

        <?php $faq = polea_faq_pairs($m); if ($faq) : ?>
        <section class="polea-sec polea-faqs" aria-labelledby="polea-h-faq">
            <h2 id="polea-h-faq" class="polea-h">Najczęstsze pytania</h2>
            <?php foreach ($faq as $k => $p) : ?>
                <details class="polea-faq"<?php echo $k === 0 ? ' open' : ''; ?>>
                    <summary><?php echo esc_html($p['q']); ?></summary>
                    <p><?php echo esc_html($p['a']); ?></p>
                </details>
            <?php endforeach; ?>
        </section>
        <?php endif; ?>

        <div class="polea-cta">
            <?php if (!empty($m['url'])) : ?>
                <a class="polea-source polea-btn" href="<?php echo esc_url($m['url']); ?>" target="_blank" rel="noopener nofollow">Zobacz aukcję na poleasingowe.pl</a>
            <?php endif; ?>
            <a class="polea-back" href="<?php echo esc_url(polea_page_url()); ?>">&larr; Wróć do listy</a>
        </div>
    </article>
    <?php
    echo polea_render_related($m);
    echo '</div>';
    polea_jsonld_enqueue(polea_jsonld_single($m)); // Product/Motorcycle + Offer + Breadcrumb + FAQ
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

/** Okruszki (HTML). Ostatni element = bieżąca strona (aria-current). Schema w JSON-LD @graph. */
function polea_render_breadcrumbs($m = null) {
    $items = polea_breadcrumb_items($m);
    $last  = count($items) - 1;
    ob_start();
    echo '<nav class="polea-breadcrumbs" aria-label="Okruszki">';
    echo '<ol>';
    foreach ($items as $i => $c) {
        if ($i === $last) {
            echo '<li aria-current="page">' . esc_html($c['name']) . '</li>';
        } else {
            echo '<li><a href="' . esc_url($c['url']) . '">' . esc_html($c['name']) . '</a></li>';
        }
    }
    echo '</ol></nav>';
    return ob_get_clean();
}

/** „Chips" z najważniejszymi parametrami (tylko obecne wartości). */
function polea_highlight_chips($m) {
    $chips = array();
    $add = static function ($k, $v) use (&$chips) {
        if ($v !== '' && $v !== null) {
            $chips[] = '<li class="polea-chip"><span class="polea-chip__k">' . esc_html($k) . '</span> '
                     . '<span class="polea-chip__v">' . esc_html($v) . '</span></li>';
        }
    };
    $add('Rok', !empty($m['rok_produkcji']) ? (string) (int) $m['rok_produkcji'] : '');
    $add('Przebieg', polea_km($m['przebieg_km']));
    $add('Pojemność', !empty($m['pojemnosc_ccm']) ? (int) $m['pojemnosc_ccm'] . ' ccm' : '');
    $add('Moc', !empty($m['moc_km']) ? (int) $m['moc_km'] . ' KM' : '');
    $add('Paliwo', $m['paliwo'] ?? '');
    $add('Skrzynia', $m['skrzynia'] ?? '');
    return implode('', $chips);
}

/** Wiersz listy definicji <dt>/<dd> (pomija puste). */
function polea_info_row($label, $val) {
    if ($val === null || $val === '') {
        return '';
    }
    return '<dt>' . esc_html($label) . '</dt><dd>' . esc_html($val) . '</dd>';
}

/** Sekcja „Podobne motocykle" (internal linking). Cache per lot (transient) chroni TTFB. */
function polea_render_related($m) {
    $lot  = $m['lot_id'];
    $tkey = 'polea_rel_' . $lot;
    $html = get_transient($tkey);
    if ($html !== false) {
        return $html;
    }
    $rel = Polea_DB::related($lot, $m['marka'] ?? '', 6);
    if (!$rel) {
        set_transient($tkey, '', POLEA_CACHE_TTL);
        return '';
    }
    $ids    = array_map(static function ($r) { return $r['lot_id']; }, $rel);
    $thumbs = Polea_DB::first_images_map($ids);

    ob_start();
    echo '<aside class="polea-related" aria-labelledby="polea-h-rel">';
    echo '<h2 id="polea-h-rel" class="polea-h">Podobne motocykle</h2>';
    echo '<ul class="polea-grid" role="list">';
    foreach ($rel as $r) {
        $thumb = isset($thumbs[$r['lot_id']]) ? $thumbs[$r['lot_id']] : '';
        echo '<li>' . polea_render_card($r, $thumb) . '</li>';
    }
    echo '</ul>';
    echo polea_related_links($m);
    echo '</aside>';
    $html = ob_get_clean();
    set_transient($tkey, $html, POLEA_CACHE_TTL);
    return $html;
}

/** Linki do przefiltrowanych list (marka/rok/paliwo) — internal linking po istniejących filtrach. */
function polea_related_links($m) {
    $base  = polea_page_url();
    $links = array();
    if (!empty($m['marka'])) {
        $links[] = '<a href="' . esc_url(add_query_arg('polea_marka', rawurlencode($m['marka']), $base)) . '">Wszystkie: ' . esc_html($m['marka']) . '</a>';
    }
    if (!empty($m['rok_produkcji'])) {
        $links[] = '<a href="' . esc_url(add_query_arg('polea_rok', (int) $m['rok_produkcji'], $base)) . '">Rocznik ' . (int) $m['rok_produkcji'] . '</a>';
    }
    if (!empty($m['paliwo'])) {
        $links[] = '<a href="' . esc_url(add_query_arg('polea_paliwo', rawurlencode($m['paliwo']), $base)) . '">Paliwo: ' . esc_html($m['paliwo']) . '</a>';
    }
    if (!$links) {
        return '';
    }
    return '<nav class="polea-morelinks" aria-label="Powiązane kategorie"><span>Zobacz też:</span> ' . implode(' <span aria-hidden="true">·</span> ', $links) . '</nav>';
}
