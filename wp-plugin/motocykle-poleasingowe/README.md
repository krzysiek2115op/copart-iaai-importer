<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Importer Motocykli (poleasingowe.pl) — wtyczka WordPress

Wyświetla motocykle z aukcji poleasingowe.pl na podstronie **„Nasze motory"**, automatycznie dopasowanej do motywu klienta. Dane czytane **tylko do odczytu** z osobnej bazy MySQL (`polea_*`), którą zasila [scraper](../../scraper/).

## Architektura (Działy 6, 8, 9, 10)
- **6 Bezpieczeństwo** — połączenie z bazą przez `mysqli` z obsługą błędów (nie `wpdb` → brak ryzyka `wp_die`); wszystkie zapytania prepared; wyjście escapowane; nonce+capability w adminie.
- **8 Repo** — `Polea_DB` (odczyt `polea_motocykle` / `polea_zdjecia`). *Świadoma rewizja: brak CPT/postów WP — aukcje są czasowe, scraper jest właścicielem danych.*
- **9 Front i media** — shortcode `[motocykle]`: siatka + szczegóły + filtry (marka/paliwo/rok/cena) + paginacja + cache (5 min); zdjęcia **hotlink**.
- **10 Podstrona i motyw** — auto-tworzenie „Nasze motory" + wpięcie w menu (block: `wp_navigation`, classic: menu location); styl dziedziczy fonty/kolory motywu (`currentColor`, `color-mix`).
- **10 SEO** (`includes/seo.php`) — ładne URL-e pojedynczego motocykla `/<podstrona>/<lot_id>/`; per motocykl unikalny `<title>` (H1 = nazwa pojazdu przez filtr `the_title`), meta description, canonical, Open Graph, **Twitter Cards**; `noindex` dla widoków filtrowanych/paginowanych i aukcji zakończonych; sitemap XML aktywnych ofert (WP core). Gdy aktywna jest wtyczka SEO (Yoast/Rank Math/SEOPress/AIOSEO), moduł **ustępuje** jej miejsca dla title/meta/OG/canonical (bez dublowania), zawsze zostawiając JSON-LD.
- **Dane strukturalne + treść** — JSON-LD `@graph` (w stopce, poza `wpautop`): pojedynczy = `Product`+`Motorcycle`+`Offer` + `BreadcrumbList` + `FAQPage`; lista = `WebSite`+`Organization`+`CollectionPage`+`BreadcrumbList`+`ItemList`. Widok pojazdu: breadcrumbs (HTML+schema), auto-generowany opis, „chips" parametrów, tabela danych (`<caption>`), informacje (`<time>`/`<address>`), FAQ (`<details>`), CTA do aukcji, sekcja „Podobne motocykle" + linki po marce/roczniku/paliwie (internal linking). Semantyka HTML5, jedno H1, ARIA, `focus-visible`, `prefers-reduced-motion`, obrazy `lazy`/`decoding=async`/`aspect-ratio` (CLS), pierwszy obraz `fetchpriority=high` (LCP). Bez JS.

## Instalacja
1. Wgraj katalog `motocykle-poleasingowe/` do `wp-content/plugins/` i aktywuj.
2. Dodaj poświadczenia osobnej bazy do `wp-config.php`:
   ```php
   define('POLEA_DB_HOST', '127.0.0.1');
   define('POLEA_DB_NAME', 'polea');
   define('POLEA_DB_USER', 'polea');
   define('POLEA_DB_PASSWORD', 'TWOJE_HASLO');
   // opcjonalnie: define('POLEA_DB_PORT', 3306);
   ```
3. Status połączenia sprawdzisz w **Ustawienia → Motocykle**.

Podstrona „Nasze motory" tworzy się sama przy aktywacji. Pojedynczy motocykl: ładny adres `/<podstrona>/<lot_id>/` (przy włączonych przyjaznych odnośnikach; w innym razie `?motocykl=<lot_id>`) — w obrębie tej samej (motywowanej) strony.

> Po aktualizacji do wersji z ładnymi URL-ami odśwież raz przyjazne odnośniki: **Ustawienia → Bezpośrednie odnośniki → Zapisz** (albo dezaktywuj/aktywuj wtyczkę) — przebudowuje reguły przepisań.
