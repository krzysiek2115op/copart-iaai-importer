=== IAAI Importer ===
Contributors: iaai-importer
Tags: iaai, vehicles, auctions, import, cpt
Requires at least: 6.0
Tested up to: 6.6
Requires PHP: 7.4
Stable tag: 0.18.0
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Import danych i zdjęć pojazdów z IAAI do WordPressa (CPT „Pojazd") — z automatyczną
podstroną, responsywnym wyglądem dziedziczącym motyw i optymalizacją SEO.

== Description ==

Wtyczka pokazuje na stronie WordPress pojazdy z serwisu aukcyjnego IAAI. Dane i zdjęcia
wkłada do bazy osobny program zbierający (Python/systemd, dział 1–5); wtyczka odczytuje je
z tych samych tabel ({prefix}iaai_vehicles) i prezentuje jako wpisy typu „Pojazd".

Główne cechy:

* Po aktywacji SAMA tworzy tabele (dbDelta) oraz podstronę „Nasze auta" z shortcode
  [iaai_pojazdy] i próbuje dopiąć ją do głównego menu.
* Responsywna siatka kart dziedzicząca wygląd aktywnego motywu (kolory, fonty).
* Zdjęcia domyślnie hotlinkowane z serwerów IAAI (0 miejsca na dysku); opcjonalny tryb
  pobierania do mediów WP (filtr iaai_image_mode).
* SEO: dane strukturalne Schema.org „Car" (JSON-LD), meta description + Open Graph +
  Twitter Card (fallback, bez konfliktu z Yoast/Rank Math/AIOSEO/SEOPress/TSF),
  opisowe atrybuty alt; CPT trafia do sitemap.xml rdzenia WP.
* Bezpieczeństwo (audyt 9/10): $wpdb->prepare wszędzie, sanityzacja wejścia i escapowanie
  wyjścia, allowlista hostów zdjęć (anty-SSRF), mutex importu (GET_LOCK), publikacja
  partiami, nagłówki bezpieczeństwa, logowanie bez wycieku do użytkownika.

== Installation ==

1. Wgraj wtyczkę: Wtyczki → Dodaj nową → Wyślij wtyczkę na serwer → wybierz iaai-importer.zip.
2. Kliknij „Włącz wtyczkę". Tabele i podstrona „Nasze auta" utworzą się same.
3. Aby auta zaczęły się pojawiać, uruchom program zbierający na serwerze (VPS) — patrz
   docs/klient/ (instrukcja krok po kroku) oraz deploy/install.sh.

Pełna instrukcja dla osoby nietechnicznej: docs/klient/PRZECZYTAJ-MNIE-NAJPIERW.md

== Frequently Asked Questions ==

= Czy zdjęcia zajmują miejsce na hostingu? =
Nie — domyślnie są pokazywane bezpośrednio z serwerów IAAI.

= Czy muszę mieć wtyczkę SEO? =
Nie. Jeśli masz (Yoast/Rank Math), wtyczka nie dubluje tytułów/opisów, dokłada tylko
dane strukturalne pojazdu.

= Czy potrzebuję VPS? =
Sama wtyczka działa na zwykłym WordPressie. Automatyzacja pobierania aut wymaga VPS z SSH.

== Changelog ==

= 0.18.0 =
* SEO: JSON-LD Schema.org „Car", meta description, Open Graph/Twitter (fallback), opisowe alt.

= 0.17.0 =
* Auto-podstrona „Nasze auta" po aktywacji + wpięcie do menu + responsywny CSS dziedziczący motyw.

= 0.16.0 =
* Utwardzenie bezpieczeństwa (audyt 9/10): anty-SSRF, mutex, batch, cache, nagłówki, logowanie.
