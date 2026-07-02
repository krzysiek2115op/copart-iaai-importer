<?php
/**
 * Dział 9 · FRONT I MEDIA — agenci `front` + `media`, krytyk `render`.
 *
 * `media`: tryb zdjęć (decyzja projektu: HOTLINK). Domyślnie zdjęcia są pokazywane
 *          bezpośrednio z vis.iaai.com po URL-ach z {$wpdb->prefix}iaai_vehicle_images
 *          (0 miejsca na dysku). Opcjonalny tryb „download" sideloaduje do mediów WP.
 * `front`: renderuje listę i stronę pojazdu (dane escapowane przez dział 6).
 *
 * Oryginał: docs/refs/wordpress-media.md (media_sideload_image + szablony).
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/* ====================================================================
 * 🔵 AGENT `media` — zdjęcia pojazdu
 * ==================================================================== */

/**
 * Tryb zdjęć: 'hotlink' (domyślny, decyzja projektu) lub 'download'.
 * Można nadpisać filtrem: add_filter('iaai_image_mode', fn() => 'download');
 */
function iaai_image_mode() : string {
	$mode = apply_filters( 'iaai_image_mode', 'hotlink' );
	return in_array( $mode, array( 'hotlink', 'download' ), true ) ? $mode : 'hotlink';
}

/** Górny limit zdjęć renderowanych na pojazd (ochrona przed nadmiarem / DoS). */
const IAAI_MAX_IMAGES = 40;

/**
 * Adresy zdjęć pojazdu prosto z nowej bazy (hotlink z vis.iaai.com).
 * Każdy URL przechodzi przez allowlist hosta IAAI (SSRF / podstawione URL-e odrzucone).
 * @return string[] bezpieczne URL-e w kolejności seq.
 */
function iaai_get_image_urls( int $salvage_id, int $limit = 0 ) : array {
	global $wpdb;
	$table = $wpdb->prefix . 'iaai_vehicle_images';
	$cap   = $limit > 0 ? min( absint( $limit ), IAAI_MAX_IMAGES ) : IAAI_MAX_IMAGES;
	$urls  = $wpdb->get_col( $wpdb->prepare(
		"SELECT url FROM {$table} WHERE salvage_id = %d AND url IS NOT NULL ORDER BY seq ASC LIMIT %d",
		$salvage_id,
		$cap
	) );
	$safe = array();
	foreach ( (array) $urls as $u ) {
		$s = iaai_safe_image_url( (string) $u );   // dział 6: tylko host IAAI, https/http
		if ( '' !== $s ) {
			$safe[] = $s;
		}
	}
	return $safe;
}

/**
 * F3 — czytelny przebieg z jednostką + przeliczeniem na km (baza pozostaje wierną
 * kopią IAAI: km liczymy przy wyświetlaniu, nie zapisujemy własnej kolumny).
 * "169594" + "mi" -> "169 594 km (105 380 mi)". Gdy uom=km, pokazujemy km bez przeliczeń.
 * @return string już bezpieczny (esc_html w środku) tekst HTML.
 */
function iaai_format_odometer( $value, string $uom = 'mi' ) : string {
	$value = (int) $value;
	if ( $value <= 0 ) {
		return '';
	}
	$uom = strtolower( $uom ?: 'mi' );
	if ( 'km' === $uom ) {
		return esc_html( number_format_i18n( $value ) . ' km' );
	}
	$km = (int) round( $value * 1.609344 );          // mi -> km
	return esc_html( number_format_i18n( $km ) . ' km (' . number_format_i18n( $value ) . ' mi)' );
}

/**
 * Sideloaduje zdjęcia pojazdu do mediów WP (lazy — tylko raz). Pierwsze zdjęcie =
 * miniatura (featured), reszta = galeria (meta iaai_gallery).
 * @return int liczba zaimportowanych załączników.
 */
function iaai_import_images( int $salvage_id, int $post_id ) : int {
	if ( get_post_meta( $post_id, '_iaai_media_done', true ) ) {
		return 0;                                   // już zaimportowane
	}
	require_once ABSPATH . 'wp-admin/includes/media.php';
	require_once ABSPATH . 'wp-admin/includes/file.php';
	require_once ABSPATH . 'wp-admin/includes/image.php';

	global $wpdb;
	$table = $wpdb->prefix . 'iaai_vehicle_images';
	$rows  = $wpdb->get_results(
		$wpdb->prepare(
			"SELECT url FROM {$table} WHERE salvage_id = %d AND url IS NOT NULL ORDER BY seq ASC LIMIT %d",
			$salvage_id,
			IAAI_MAX_IMAGES
		),
		ARRAY_A
	);
	$gallery = array();
	foreach ( $rows as $i => $r ) {
		$src = iaai_safe_image_url( (string) $r['url'] );   // SSRF: tylko host IAAI
		if ( '' === $src ) {
			iaai_log( 'media: pominięto niedozwolony URL zdjęcia dla lotu ' . $salvage_id, 'warn' );
			continue;
		}
		$att = media_sideload_image( $src, $post_id, null, 'id' );
		if ( is_wp_error( $att ) ) {
			iaai_log( 'media: sideload nieudany (' . $att->get_error_code() . ') lot ' . $salvage_id, 'warn' );
			continue;
		}
		// Upewnij się, że pobrany załącznik to OBRAZ (blokuje podmianę na inny typ pliku).
		if ( 0 !== strpos( (string) get_post_mime_type( $att ), 'image/' ) ) {
			wp_delete_attachment( (int) $att, true );
			continue;
		}
		if ( empty( $gallery ) ) {
			set_post_thumbnail( $post_id, $att );   // miniatura = pierwsze poprawne zdjęcie
		}
		$gallery[] = (int) $att;
	}
	update_post_meta( $post_id, 'iaai_gallery', $gallery );
	update_post_meta( $post_id, '_iaai_media_done', 1 );
	return count( $gallery );
}

/* ====================================================================
 * Style frontu — minimalny CSS, DZIEDZICZY MOTYW (dział 9).
 * Wczytywany TYLKO tam, gdzie potrzebny: strona/archiwum pojazdu albo
 * strona z shortcode [iaai_pojazdy]. Zero obciążenia reszty witryny.
 * ==================================================================== */
add_action( 'wp_enqueue_scripts', 'iaai_enqueue_styles' );
function iaai_enqueue_styles() : void {
	wp_register_style( 'iaai-importer', IAAI_IMPORTER_URL . 'assets/iaai.css', array(), IAAI_IMPORTER_VERSION );

	$need = is_singular( IAAI_CPT ) || is_post_type_archive( IAAI_CPT );
	if ( ! $need && is_singular() ) {
		$post = get_post();
		if ( $post instanceof WP_Post && has_shortcode( (string) $post->post_content, 'iaai_pojazdy' ) ) {
			$need = true;
		}
	}
	if ( $need ) {
		wp_enqueue_style( 'iaai-importer' );
	}
}

/* ====================================================================
 * AUTO-MENU (front-end) — wstawia „Nasze auta" na górny pasek NA KAŻDYM motywie.
 *
 * Preferowana droga to menu WP / blok Nawigacja (activation.php). Ten skrypt to
 * SIATKA BEZPIECZEŃSTWA dla motywów z paskiem „na sztywno" (gotowce/page-buildery),
 * gdzie nie ma menu WordPressa. Heurystyka: znajduje w <header> największą listę
 * linków = główne menu i dokleja pozycję dopasowaną stylem do sąsiadów.
 * NIE duplikuje (gdy link już jest w menu — pomija). Wyłączenie:
 *   add_filter('iaai_auto_menu','__return_false');
 * ==================================================================== */
add_action( 'wp_footer', 'iaai_auto_menu_script' );
function iaai_auto_menu_script() : void {
	if ( is_admin() || ! apply_filters( 'iaai_auto_menu', true ) ) {
		return;
	}
	$pid = (int) get_option( 'iaai_page_id' );
	if ( ! $pid ) {
		return;
	}
	$url = get_permalink( $pid );
	if ( ! $url ) {
		return;
	}
	$data = wp_json_encode( array(
		'url'       => esc_url_raw( $url ),
		'label'     => get_the_title( $pid ),
		'selectors' => array_values( (array) apply_filters( 'iaai_auto_menu_selectors', array(
			'.wp-block-navigation__container', 'header nav ul', 'nav ul.menu',
			'#site-navigation ul', '.main-navigation ul', 'header nav', 'header ul',
		) ) ),
	) );
	?>
<script>(function(){try{
var D=<?php echo $data; // już zescapowane przez wp_json_encode ?>;
var path=new URL(D.url,location.href).pathname;
var cand=[];
D.selectors.forEach(function(s){document.querySelectorAll(s).forEach(function(n){cand.push(n);});});
var hdr=document.querySelector('header')||document.body;
hdr.querySelectorAll('ul,nav').forEach(function(n){cand.push(n);});
var nav=null,best=-1;
cand.forEach(function(el){var c=el.querySelectorAll('a').length;if(c>best){best=c;nav=el;}});
if(!nav||best<1)return;
var as=nav.querySelectorAll('a'),i;
for(i=0;i<as.length;i++){try{if(new URL(as[i].href).pathname===path)return;}catch(e){}}
var sample=nav.querySelector('li');
if(sample){var li=sample.cloneNode(true);li.querySelectorAll('ul').forEach(function(u){u.remove();});
li.className=sample.className.replace(/current[-_][a-z-]+/g,'');
var a=li.querySelector('a')||document.createElement('a');a.setAttribute('href',D.url);a.textContent=D.label;
if(!a.parentNode)li.appendChild(a);nav.appendChild(li);}
else{var a2=document.createElement('a');a2.href=D.url;a2.textContent=D.label;
if(nav.tagName==='UL'){var l=document.createElement('li');l.appendChild(a2);nav.appendChild(l);}else nav.appendChild(a2);}
}catch(e){}})();</script>
	<?php
}

/* ====================================================================
 * 🔵 AGENT `front` — render listy i strony pojazdu (escapowane!)
 * ==================================================================== */

/** [iaai_pojazdy ile="12"] — siatka pojazdów (styl zbliżony do IAAI) + paginacja.
 * `ile` = liczba aut na stronę. Wynik cache'owany (Transient API). */
add_shortcode( 'iaai_pojazdy', 'iaai_render_list' );
function iaai_render_list( $atts ) : string {
	$a   = shortcode_atts( array( 'ile' => 12 ), $atts, 'iaai_pojazdy' );
	// Clamp 1..48 — ochrona przed [iaai_pojazdy ile="999999"] (DoS / ciężkie zapytanie).
	$ile = max( 1, min( 48, absint( $a['ile'] ) ) );

	// Fallback: gdy shortcode użyty poza wykrytą stroną (widget/blok) — dołóż styl.
	if ( ! wp_style_is( 'iaai-importer', 'enqueued' ) ) {
		wp_enqueue_style( 'iaai-importer' );
	}

	// Filtry z adresu (GET) — walidowane; puste = brak filtra.
	$sel = array(
		'make' => isset( $_GET['iaai_make'] ) ? sanitize_text_field( wp_unslash( $_GET['iaai_make'] ) ) : '',
		'year' => isset( $_GET['iaai_year'] ) ? absint( $_GET['iaai_year'] ) : 0,
		'dmg'  => isset( $_GET['iaai_dmg'] ) ? sanitize_text_field( wp_unslash( $_GET['iaai_dmg'] ) ) : '',
		'sort' => isset( $_GET['iaai_sort'] ) ? sanitize_key( wp_unslash( $_GET['iaai_sort'] ) ) : '',
	);
	// Numer strony — własny parametr, by nie kolidować z paginacją treści strony WP.
	$paged = isset( $_GET['iaai_str'] ) ? max( 1, absint( wp_unslash( $_GET['iaai_str'] ) ) ) : 1;

	// Cache 5 min; klucz = wersja + liczba + strona + odcisk filtrów.
	$cache_key = 'iaai_list_' . iaai_list_cache_version() . '_' . $ile . '_' . $paged
		. '_' . substr( md5( maybe_serialize( $sel ) ), 0, 8 );
	$cached = get_transient( $cache_key );
	if ( false !== $cached ) {
		return $cached;
	}

	$args = array(
		'post_type'           => IAAI_CPT,
		'posts_per_page'      => $ile,
		'paged'               => $paged,
		'post_status'         => 'publish',
		'ignore_sticky_posts' => true,
	);
	$meta = array();
	if ( '' !== $sel['make'] ) { $meta[] = array( 'key' => 'iaai_make', 'value' => $sel['make'] ); }
	if ( $sel['year'] > 0 )    { $meta[] = array( 'key' => 'iaai_year', 'value' => $sel['year'], 'type' => 'NUMERIC' ); }
	if ( '' !== $sel['dmg'] )  { $meta[] = array( 'key' => 'iaai_primary_damage', 'value' => $sel['dmg'] ); }
	if ( $meta ) {
		$meta['relation']    = 'AND';
		$args['meta_query']  = $meta;
	}
	switch ( $sel['sort'] ) {
		case 'price_asc':  $args['meta_key'] = 'iaai_buy_now';  $args['orderby'] = 'meta_value_num'; $args['order'] = 'ASC';  break;
		case 'price_desc': $args['meta_key'] = 'iaai_buy_now';  $args['orderby'] = 'meta_value_num'; $args['order'] = 'DESC'; break;
		case 'odo_asc':    $args['meta_key'] = 'iaai_odometer'; $args['orderby'] = 'meta_value_num'; $args['order'] = 'ASC';  break;
		default:           $args['orderby'] = 'date'; $args['order'] = 'DESC';
	}

	$q       = new WP_Query( $args );
	$filters = iaai_render_filters( $sel );

	if ( ! $q->have_posts() ) {
		$out = '<div class="iaai-pojazdy" id="iaai">' . $filters
			. '<p class="iaai-empty">' . esc_html__( 'Brak pojazdów dla wybranych filtrów.', 'iaai-importer' ) . '</p></div>';
		set_transient( $cache_key, $out, 5 * MINUTE_IN_SECONDS );
		return $out;
	}
	$out = '<div class="iaai-pojazdy" id="iaai">' . $filters . '<div class="iaai-grid">';
	while ( $q->have_posts() ) {
		$q->the_post();
		$out .= iaai_render_card( (int) get_the_ID() );
	}
	$out .= '</div>';
	$out .= iaai_render_pager( $paged, (int) $q->max_num_pages );
	$out .= '</div>';
	wp_reset_postdata();

	set_transient( $cache_key, $out, 5 * MINUTE_IN_SECONDS );
	return $out;
}

/** Distinct wartości pola ze źródłowej tabeli (opcje filtrów). Kolumna z allowlisty. */
function iaai_distinct_meta( string $col, int $limit = 300 ) : array {
	$allowed = array( 'make', 'model', 'year', 'primary_damage', 'transmission', 'fuel_type' );
	if ( ! in_array( $col, $allowed, true ) ) {
		return array();
	}
	global $wpdb;
	$table = $wpdb->prefix . 'iaai_vehicles';
	$order = 'year' === $col ? "{$col} DESC" : "{$col} ASC";
	return (array) $wpdb->get_col( $wpdb->prepare(
		"SELECT DISTINCT {$col} FROM {$table} WHERE status = %s AND {$col} IS NOT NULL AND {$col} <> '' ORDER BY {$order} LIMIT %d",
		'active',
		$limit
	) );
}

/** Pasek filtrów nad siatką (marka / rok / uszkodzenie / sortowanie). GET, działa bez JS. */
function iaai_render_filters( array $sel ) : string {
	$makes = iaai_distinct_meta( 'make' );
	$years = iaai_distinct_meta( 'year' );
	$dmgs  = iaai_distinct_meta( 'primary_damage' );
	if ( ! $makes && ! $years && ! $dmgs ) {
		return '';
	}
	$mk_select = static function ( string $name, array $vals, $current, string $ph ) {
		$h = '<select name="' . esc_attr( $name ) . '" onchange="this.form.submit()">'
			. '<option value="">' . esc_html( $ph ) . '</option>';
		foreach ( $vals as $v ) {
			$h .= '<option value="' . esc_attr( $v ) . '"' . selected( (string) $current, (string) $v, false )
				. '>' . esc_html( $v ) . '</option>';
		}
		return $h . '</select>';
	};
	$sorts = array(
		''           => __( 'Sortuj: najnowsze', 'iaai-importer' ),
		'price_asc'  => __( 'Cena: rosnąco', 'iaai-importer' ),
		'price_desc' => __( 'Cena: malejąco', 'iaai-importer' ),
		'odo_asc'    => __( 'Przebieg: rosnąco', 'iaai-importer' ),
	);
	$sortsel = '<select name="iaai_sort" onchange="this.form.submit()">';
	foreach ( $sorts as $k => $lab ) {
		$sortsel .= '<option value="' . esc_attr( $k ) . '"' . selected( $sel['sort'], $k, false ) . '>' . esc_html( $lab ) . '</option>';
	}
	$sortsel .= '</select>';

	$has   = ( '' !== $sel['make'] || $sel['year'] > 0 || '' !== $sel['dmg'] || '' !== $sel['sort'] );
	$clear = esc_url( remove_query_arg( array( 'iaai_make', 'iaai_year', 'iaai_dmg', 'iaai_sort', 'iaai_str' ) ) );

	$html = '<form class="iaai-filters" method="get">';
	if ( $makes ) { $html .= $mk_select( 'iaai_make', $makes, $sel['make'], __( 'Marka', 'iaai-importer' ) ); }
	if ( $years ) { $html .= $mk_select( 'iaai_year', $years, $sel['year'] ?: '', __( 'Rok', 'iaai-importer' ) ); }
	if ( $dmgs )  { $html .= $mk_select( 'iaai_dmg', $dmgs, $sel['dmg'], __( 'Uszkodzenie', 'iaai-importer' ) ); }
	$html .= $sortsel;
	$html .= '<button type="submit">' . esc_html__( 'Filtruj', 'iaai-importer' ) . '</button>';
	if ( $has ) {
		$html .= '<a class="iaai-filters__clear" href="' . $clear . '">' . esc_html__( 'Wyczyść', 'iaai-importer' ) . '</a>';
	}
	return $html . '</form>';
}

/** Jedna karta pojazdu: zdjęcie, tytuł-link, cena, kluczowe dane, plakietki. */
function iaai_render_card( int $id ) : string {
	$title = get_the_title( $id );
	$link  = get_permalink( $id );
	$m     = static function ( string $k ) use ( $id ) {
		return trim( (string) get_post_meta( $id, 'iaai_' . $k, true ) );
	};

	$dmg   = $m( 'primary_damage' );
	$trans = $m( 'transmission' );
	$odo   = iaai_format_odometer( $m( 'odometer' ), $m( 'odometer_uom' ) ?: 'mi' );
	$buy   = (float) $m( 'buy_now' );
	$bid   = (float) $m( 'current_bid' );

	// Zdjęcie (hotlink 1. z bazy albo miniatura WP; brak → placeholder).
	if ( 'hotlink' === iaai_image_mode() ) {
		$sid   = (int) get_post_meta( $id, 'iaai_salvage_id', true );
		$first = $sid ? iaai_get_image_urls( $sid, 1 ) : array();
		$img   = $first
			? '<img loading="lazy" src="' . esc_url( $first[0] ) . '" alt="'
				. esc_attr( $title . ( $dmg ? ' – ' . $dmg : '' ) ) . '" />'
			: '<span class="iaai-noimg" aria-hidden="true"></span>';
	} else {
		$img = get_the_post_thumbnail( $id, 'medium' ) ?: '<span class="iaai-noimg" aria-hidden="true"></span>';
	}

	// Cena.
	$price = '';
	if ( $buy > 0 ) {
		$price = 'Buy Now: USD ' . number_format_i18n( $buy );
	} elseif ( $bid > 0 ) {
		$price = esc_html__( 'Aktualna oferta', 'iaai-importer' ) . ': USD ' . number_format_i18n( $bid );
	}

	// Wiersze danych (odo już zescapowane w iaai_format_odometer).
	$rows = '';
	if ( '' !== $price ) { $rows .= '<span class="iaai-price">' . esc_html( $price ) . '</span>'; }
	if ( '' !== $odo )   { $rows .= '<span class="iaai-odo">' . $odo . '</span>'; }
	if ( '' !== $dmg )   { $rows .= '<span class="iaai-dmg">' . esc_html( $dmg ) . '</span>'; }
	if ( '' !== $trans ) { $rows .= '<span class="iaai-trans">' . esc_html( $trans ) . '</span>'; }

	// Plakietki.
	$badges = '';
	$rd = strtolower( $m( 'run_and_drive' ) );
	if ( false !== strpos( $rd, 'run' ) || false !== strpos( $rd, 'drive' ) ) {
		$badges .= '<span class="iaai-badge iaai-badge--rd">' . esc_html__( 'Run &amp; Drive', 'iaai-importer' ) . '</span>';
	}
	$key = strtolower( $m( 'key_available' ) );
	if ( '' !== $key && false === strpos( $key, 'no' )
		&& ( false !== strpos( $key, 'yes' ) || false !== strpos( $key, 'avail' ) || false !== strpos( $key, 'key' ) ) ) {
		$badges .= '<span class="iaai-badge iaai-badge--key">' . esc_html__( 'Key Available', 'iaai-importer' ) . '</span>';
	}

	return '<article class="iaai-card">'
		. '<a class="iaai-card__media" href="' . esc_url( $link ) . '">' . $img . '</a>'
		. '<div class="iaai-card__body">'
		. '<a class="iaai-card__title" href="' . esc_url( $link ) . '">' . esc_html( $title ) . '</a>'
		. ( $rows ? '<div class="iaai-card__rows">' . $rows . '</div>' : '' )
		. ( $badges ? '<div class="iaai-card__badges">' . $badges . '</div>' : '' )
		. '</div></article>';
}

/** Pager „‹  n z N  ›" pod siatką (paginacja przez ?iaai_str=N). */
function iaai_render_pager( int $paged, int $max ) : string {
	if ( $max <= 1 ) {
		return '';
	}
	$base = remove_query_arg( 'iaai_str' );
	$mk   = static function ( int $p, string $label ) use ( $base ) {
		$url = $p <= 1 ? $base : add_query_arg( 'iaai_str', $p, $base );
		return '<a class="iaai-pager__btn" href="' . esc_url( $url ) . '#iaai">' . $label . '</a>';
	};
	$prev = $paged > 1 ? $mk( $paged - 1, '‹' ) : '<span class="iaai-pager__btn is-disabled">‹</span>';
	$next = $paged < $max ? $mk( $paged + 1, '›' ) : '<span class="iaai-pager__btn is-disabled">›</span>';
	/* translators: 1: bieżąca strona, 2: liczba stron */
	$info = '<span class="iaai-pager__info">' . sprintf( esc_html__( '%1$d z %2$d', 'iaai-importer' ), $paged, $max ) . '</span>';
	return '<nav class="iaai-pager" aria-label="Paginacja">' . $prev . $info . $next . '</nav>';
}

/** Wersja cache list (bump = unieważnienie wszystkich stron). */
function iaai_list_cache_version() : int {
	return (int) get_option( 'iaai_list_cv', 1 );
}

/** Czyści cache list po publikacji/zmianach (woła to dział 8) — bump wersji. */
function iaai_flush_list_cache() : void {
	update_option( 'iaai_list_cv', time() );
}

/** Strona pojedynczego pojazdu: dokleja tabelę danych + galerię do treści. */
add_filter( 'the_content', 'iaai_render_single' );
function iaai_render_single( string $content ) : string {
	if ( ! is_singular( IAAI_CPT ) || ! in_the_loop() || ! is_main_query() ) {
		return $content;
	}
	$id     = get_the_ID();
	$fields = array(
		'stock_number' => 'Stock #', 'item_id' => 'Item #',
		'vin' => 'VIN', 'year' => 'Rok', 'make' => 'Marka', 'model' => 'Model',
		'odometer' => 'Przebieg', 'primary_damage' => 'Uszkodzenie', 'title' => 'Tytuł',
		'run_and_drive' => 'Run & Drive', 'key_available' => 'Kluczyk', 'buy_now' => 'Buy Now',
	);
	$rows = '';
	foreach ( $fields as $key => $label ) {
		$val = get_post_meta( $id, 'iaai_' . $key, true );
		if ( $val === '' ) {
			continue;
		}
		// F3: przebieg z przeliczeniem na km (już zescapowany); reszta przez esc_html.
		if ( 'odometer' === $key ) {
			$cell = iaai_format_odometer( $val, (string) get_post_meta( $id, 'iaai_odometer_uom', true ) );
		} else {
			$cell = esc_html( $val );
		}
		$rows .= '<tr><th>' . esc_html( $label ) . '</th><td>' . $cell . '</td></tr>';
	}
	// Galeria: hotlink (URL-e z bazy, vis.iaai.com) albo załączniki WP (tryb download).
	$imgs = '';
	if ( 'hotlink' === iaai_image_mode() ) {
		$sid = (int) get_post_meta( $id, 'iaai_salvage_id', true );
		$n   = 0;
		foreach ( $sid ? iaai_get_image_urls( $sid ) : array() as $u ) {
			$n++;
			$alt   = get_the_title() . ' – zdjęcie ' . $n;   // unikalny, opisowy alt (SEO)
			$imgs .= '<img class="iaai-gallery-img" loading="lazy" src="' . esc_url( $u )
				. '" alt="' . esc_attr( $alt ) . '" />';
		}
	} else {
		foreach ( (array) get_post_meta( $id, 'iaai_gallery', true ) as $att ) {
			$imgs .= wp_get_attachment_image( (int) $att, 'large', false, array( 'class' => 'iaai-gallery-img' ) );
		}
	}
	return $content
		. '<table class="iaai-specs">' . $rows . '</table>'
		. ( $imgs ? '<div class="iaai-gallery">' . $imgs . '</div>' : '' );
}

/* ---------- 🔴 KRYTYK `render` ------------------------------------------- *
 * media (hotlink): pojazd ze zdjęciami w bazie ma niepuste URL-e do hotlinka.
 * media (download): post ma miniaturę i liczba załączników == liczba zdjęć w bazie.
 * front: całe wyjście przez esc_html/esc_url/esc_attr/wp_get_attachment_image
 *        (brak surowego echo) — brak XSS. */
function iaai_krytyk_render( int $salvage_id, int $post_id ) : array {
	global $wpdb;
	$issues = array();
	$table  = $wpdb->prefix . 'iaai_vehicle_images';
	$db     = (int) $wpdb->get_var( $wpdb->prepare(
		"SELECT COUNT(*) FROM {$table} WHERE salvage_id = %d", $salvage_id ) );

	if ( 'hotlink' === iaai_image_mode() ) {
		if ( $db > 0 && count( iaai_get_image_urls( $salvage_id ) ) < $db ) {
			$issues[] = "render(media/hotlink): brak URL-i do hotlinka dla części z {$db} zdjęć";
		}
		return $issues;
	}
	// tryb download
	if ( ! has_post_thumbnail( $post_id ) ) {
		$issues[] = "render(media): post {$post_id} bez miniatury";
	}
	$got = count( (array) get_post_meta( $post_id, 'iaai_gallery', true ) );
	if ( $db && $got < $db ) {
		$issues[] = "render(media): zaimportowano {$got}/{$db} zdjęć";
	}
	return $issues;
}
