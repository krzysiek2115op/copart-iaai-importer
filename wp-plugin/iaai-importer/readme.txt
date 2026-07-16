=== Importer Aukcji (IAAI + Copart) ===
Contributors: iaai-importer
Tags: iaai, copart, vehicles, auctions, import, cpt
Requires at least: 6.0
Tested up to: 6.6
Requires PHP: 7.4
Stable tag: 0.30.4
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Import danych i zdjęć pojazdów z aukcji IAAI oraz Copart do WordPressa (CPT „Pojazd") —
z automatyczną podstroną, plakietką źródła, filtrem źródła i wyglądem dziedziczącym motyw.

== Description ==

Wtyczka pokazuje na stronie WordPress pojazdy z serwisów aukcyjnych IAAI oraz Copart. Dane
i zdjęcia wkłada do bazy osobny program zbierający (Python/systemd, dział 1–5, po jednym
źródle na przebieg: --source iaai|copart); wtyczka odczytuje je z tych samych tabel
({prefix}iaai_vehicles, z kolumną `source`) i prezentuje jako wpisy typu „Pojazd" z plakietką
źródła (IAAI/Copart) i filtrem źródła.

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

= 0.30.4 =
* Motywy z menu „na sztywno" (bez menu WP / page-list, np. „Kredyt Kompas" przez
  filtr `kk_menu_items`): podstrona „Nasze auta" wpina się teraz automatycznie —
  wcześniej takie motywy trzeba było uzupełniać ręcznie. Na pozostałych motywach hak
  jest bezczynny (fallback: menu klasyczne / blok Nawigacja bez duplikatu z page-list).

= 0.30.3 =
* Utwardzenie na skalę (po re-audycie): publikacja przetwarza tylko loty ZMIENIONE od
  ostatniego przebiegu (watermark po updated_at + nowy indeks idx_updated, schemat 1.2.0) —
  koszt cyklu zależy od rozmiaru zmian, nie od rozmiaru całej oferty; `iaai_publish_all_active(200,true)`
  wymusza pełną publikację (np. po zmianie szablonu). Cache listy: filtry przycinane do realnych
  wartości z bazy (koniec zapychania transientów przez dowolne ?iaai_make), klucz zawiera kontekst
  strony (poprawne linki pagera, gdy shortcode jest na wielu stronach), rozkłady filtrów cache'owane.
* Deploy: skrypt cyklu bierze mutex (flock) na czas przebiegu Pythona — live i backfill nie nałożą
  się na zapis do bazy.

= 0.30.2 =
* Re-audyt (2. przejście, subagent-audytor) — naprawy: zdjęcia strony pojazdu w SEO
  (Open Graph/Twitter/JSON-LD) czytane z WŁAŚCIWEGO źródła (Copart nie dostawał już
  zdjęć IAAI); `sale_date` przestaje ginąć w sanitacji (meta `iaai_sale_date` zapisywane);
  `branch_id` eksponowany jako meta; wykrywanie zamaskowanego VIN tylko po gwiazdce
  (litera X jest legalna — koniec fałszywego maskowania w SEO i deduplikacji); reguła
  reconcile liczy obecność lotu w feedzie niezależnie od wyniku audytu (koniec fałszywego
  „removed"); górny limit rocznika w schemacie odsztywniony (koniec bomby zegarowej 2027).
* Deploy: usługi systemd dostają zapisywalny katalog stanu (StateDirectory) + absolutny
  --workdir — automatyzacja nie pada już przez CWD=/ jako www-data; instalator dokłada
  biblioteki systemowe chromium (playwright install-deps). Copart: pętle etapów odporne
  na pojedynczy błędny lot.

= 0.30.1 =
* Audyt P1 (spójność dual-source): agent `diff` porównuje raw_hash w obrębie właściwego
  `source` (koniec ryzyka odczytu cudzego wiersza, gdy ten sam numer lotu jest w IAAI i
  Copart); zapis do bazy odporny na pojedynczy błędny rekord (pomija i liczy `błędy=`,
  nie przerywa całego importu); instalator włącza wtyczkę także spod sudo (WP-CLI
  --allow-root). Bez zmian w danych i wyglądzie strony.

= 0.30.0 =
* DRUGIE ŹRÓDŁO — Copart. Baza: kolumna `source` (iaai/copart), klucz (source, salvage_id) w pojazdach i zdjęciach (dbDelta 1.1.0). Wtyczka: publikacja/wyszukiwanie/zdjęcia po parze (source, salvage_id), plakietka źródła (IAAI/Copart) i filtr źródła na liście, allowlist zdjęć Copart. Scraper: moduł 01_pobieranie/copart.py (listingi/szczegoly/zdjecia) + run_pipeline `--source iaai|copart` + json_agent zapis `source` i reconcile per źródło. Neutralna nazwa wtyczki „Importer Aukcji (IAAI + Copart)".
* AUDYT dual-source (naprawy): galeria szczegółów i krytyk zdjęć filtrują teraz po `source` (koniec kolizji zdjęć, gdy ten sam numer lotu występuje w IAAI i Copart); wykrywanie starego PRIMARY KEY po aktualizacji istniejącej bazy (iaai_check_source_pk — log ostrzegawczy zamiast ryzykownego auto-ALTER) z instrukcją migracji; leniwy import `requests` w copart.py (testowalność); testy jednostkowe dwóch źródeł (scraper/tests/test_copart.py). Instrukcje klienta i architektura zaktualizowane o Copart + uwagi (konto Member/COPART_COOKIES, migracja bazy).

= 0.24.0 =
* Optymalizacja: pierwsze zdjęcia listy jednym zapytaniem (N+1 → 1), wyłączony zbędny cache termów. Debug całości. Instrukcja edycji podstrony i dopasowania do motywu (docs/klient/06). Szczegółowe testy systemu (docs/TESTY-SZCZEGOLOWE.md).

= 0.23.0 =
* Wygląd listy DZIEDZICZY MOTYW klienta (kolory, fonty, jasny/ciemny) zamiast narzuconej palety — karta/filtry/paginacja wpasowują się w styl strony (currentColor/inherit/color-mix + akcent motywu). Zachowana profesjonalna struktura. Zmienne --iaai-* do dostrajania.

= 0.22.0 =
* Pasek filtrów nad listą aut: marka / rok / uszkodzenie / sortowanie (cena, przebieg). Działa serwerowo (GET), opcje budowane z realnych danych; ułatwia klientom wyszukiwanie.

= 0.21.0 =
* Ładniejsza, bardziej szczegółowa lista aut (styl zbliżony do IAAI): karta ze zdjęciem 4:3, tytuł-link, cena Buy Now, przebieg, uszkodzenie, skrzynia, plakietki Run & Drive / Key Available. Dodano paginację (?iaai_str).

= 0.20.0 =
* Auto-menu na froncie: „Nasze auta" pojawia się na górnym pasku także w motywach z menu „na sztywno" (gotowce/page-buildery) — skrypt dokleja link do głównej nawigacji, bez duplikatów; wyłączalny filtrem iaai_auto_menu.

= 0.19.0 =
* Auto-dodawanie podstrony „Nasze auta" do menu także w motywach BLOKOWYCH (blok Nawigacja/wp_navigation), nie tylko klasycznych. Motywy z nagłówkiem „na sztywno" (bez menu WP) trzeba uzupełnić ręcznie.

= 0.18.0 =
* SEO: JSON-LD Schema.org „Car", meta description, Open Graph/Twitter (fallback), opisowe alt.

= 0.17.0 =
* Auto-podstrona „Nasze auta" po aktywacji + wpięcie do menu + responsywny CSS dziedziczący motyw.

= 0.16.0 =
* Utwardzenie bezpieczeństwa (audyt 9/10): anty-SSRF, mutex, batch, cache, nagłówki, logowanie.
