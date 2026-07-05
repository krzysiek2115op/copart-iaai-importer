# Szczegółowe testy systemu — plugin + automatyzacja

Data: 2026-07-06 · wtyczka **v0.30.0** (dwa źródła: IAAI + Copart) · zakres: cały system
(WordPress plugin + scraper/ETL + wdrożenie).
Legenda: ✅ zweryfikowane · ⏳ wymaga środowiska docelowego (VPS/MySQL/żywe IAAI·Copart) · 🔒 test bezpieczeństwa.

> 🆕 **Sekcja G (na dole)** zbiera testy i AUDYT dodania drugiego źródła (Copart). Znaleziska
> audytu z tej rundy zostały naprawione w kodzie — patrz G.

---

## A. Testy jednostkowe (Python, bez sieci/bazy)
Komenda: `python -m unittest discover -s scraper/tests`
- Wynik (ta sesja): **27 testów — 16 przeszło, 11 pominiętych** (pominięte = brak zależności w dev:
  pymysql/requests/playwright; na VPS przejdą). ✅
- Pokrycie: `jednostki` (parsowanie przebiegu, sale_date, key_present), `vin` (maska/status),
  `match` (deduplikacja), `common` (prefiks tabel, hash), `pokrycie` (segmenty, krytyk kompletności),
  **`copart` (mapowanie pól + source), `json_agent` (kolumna source w upsert/upsert_image)**.

| # | Test | Oczekiwane | Status |
|---|------|-----------|--------|
| A1 | `parse_sale_date` numeryczny i tekstowy | ISO albo None (nieparsowalne) | ✅ |
| A2 | `key_present` „Not Available" | `False` (negacja przed „avail") | ✅ |
| A3 | VIN zamaskowany | `vin_status=masked`, nie grupowany w dedup | ✅ |
| A4 | `tbl()` prefiks tabel | dokłada `IAAI_DB_TABLE_PREFIX` | ✅ |
| A5 | krytyk pokrycia | wykrywa segment URWANY (got < ResultCount) | ✅ |
| A6 | `copart._map_detail` pełny rekord | klucze Copart→wspólny kształt, `source='copart'`, ln/lcy/orr→int | ✅ |
| A7 | `copart._map_detail` pusty/niepoprawny | brak wyjątku; `salvage_id=None`, `key='No'`, `source='copart'` | ✅ |
| A8 | `json_agent.ALL_COLS/_IMG_COLS` | zawierają `source` (poz. 1, zaraz po salvage_id) | ⏳ (pymysql) |
| A9 | `upsert`/`upsert_image` z atrapą kursora | przekazują `source`; `setdefault` nie nadpisuje jawnego | ⏳ (pymysql) |

## B. Testy wtyczki (runtime WordPress)
Środowisko testu tej sesji: WordPress (Studio/SQLite), motyw klasyczny „kredyt-kompas" + blokowy „Twenty Twenty-Five".

| # | Test | Kroki | Oczekiwane | Status |
|---|------|-------|-----------|--------|
| B1 | Aktywacja | Wtyczki → Włącz | brak błędów; wpis aktywny | ✅ |
| B2 | Tabele bazy | po aktywacji | `{prefix}iaai_vehicles`, `{prefix}iaai_vehicle_images` istnieją | ✅ |
| B3 | Auto-podstrona | po aktywacji | strona „Nasze auta" (`/nasze-auta`), status publish | ✅ (id 13) |
| B4 | CPT + meta | publikacja | wpisy „Pojazd" z meta (make/model/rok/odo/…); title „ROK MARKA MODEL" | ✅ (6/6) |
| B5 | Siatka kart | otwórz podstronę | zdjęcie 4:3, tytuł-link, cena Buy Now, przebieg km(mi), uszkodzenie, skrzynia | ✅ |
| B6 | Plakietki | karta | „Run & Drive" / „Key Available" gdy dane na to wskazują | ✅ |
| B7 | Responsywność | zwężanie okna | kolumny zwijają się 4→2→1 | ✅ |
| B8 | Paginacja | > `ile` aut | „‹ n z N ›", `?iaai_str=`, zachowuje filtry | ✅ |
| B9 | Filtry | marka/rok/uszkodzenie/sort | lista zawęża się; opcje z realnych danych | ✅ |
| B10 | Dziedziczenie motywu | różne motywy | kolory/fonty z motywu (jasny/ciemny) | ✅ |
| B11 | Menu — klasyczny | motyw z menu WP | „Nasze auta" dodane automatycznie | ✅ |
| B12 | Menu — blokowy | TT5 (page-list) | „Nasze auta" widoczne w pasku | ✅ |
| B13 | Menu — „na sztywno" | motyw z hardkodem | JS-fallback dokleja link do nawigacji | ✅ |
| B14 | Strona pojazdu | klik w auto | tabela danych + galeria; wygląd wg motywu | ✅ |
| B15 | Zdjęcia hotlink | tryb domyślny | ładowane z hosta IAAI (0 miejsca na dysku) | ✅ |
| B16 | Znikanie sold/removed | status≠active + publikacja | wpis przechodzi w szkic (znika ze strony) | ⏳ (logika ✅; potwierdzić na danych) |
| B17 | SEO | źródło strony auta | JSON-LD `@type:Car`, meta description, OG (gdy brak wtyczki SEO) | ✅ |
| B18 | Sitemapa | /wp-sitemap.xml | CPT „pojazd" obecny (public+show_in_rest) | ⏳ |

## C. Testy automatyzacji (scraper + wdrożenie)
| # | Test | Kroki | Oczekiwane | Status |
|---|------|-------|-----------|--------|
| C1 | Pipeline backfill | `run_pipeline.py --mode full` | pobiera ofertę → normalizacja → dedup → diff → audyt → upsert do bazy | ⏳ (E2E na dev: [docs/TEST-SYSTEMU.md](TEST-SYSTEMU.md)) |
| C2 | Pipeline live | `run_pipeline.py --mode live` | dokłada nowe (inkrement po `raw_hash`) | ⏳ |
| C3 | Publikacja do WP | `wp eval 'iaai_publish_all_active();'` | rekordy bazy → wpisy CPT (mutex, batch, log) | ⏳ (MySQL) |
| C4 | Reconcile | pełny feed + `--reconcile` | znikłe z IAAI → status sold/removed | ⏳ |
| C5 | Idempotencja | dwukrotny upsert | brak duplikatów (PK salvage_id, UNIQUE image_key) | ✅ (logika + E2E) |
| C6 | Harmonogram live | `iaai-importer-live.timer` | cykl co ~15 min, `Persistent` nadrabia po restarcie; brak nakładania | ⏳ (systemd na VPS) |
| C7 | Harmonogram backfill | `iaai-importer-backfill.timer` | pełny przebieg + reconcile o 03:30 | ⏳ |
| C8 | Most danych | `deploy/iaai-env.sh` | czyta DB z `wp-config.php`; Python i WP piszą do TYCH SAMYCH tabel | ✅ (prefiks) / ⏳ (VPS) |
| C9 | Zgodność (dział 7) | rate-limit + detekcja blokad | throttling działa; blokada zgłaszana | ✅ (test) |
| C10 | Instalator | `sudo bash deploy/install.sh /var/www/html` | venv + zależności + playwright + usługi | ⏳ (VPS) |

## D. Testy bezpieczeństwa 🔒
Pełny raport: [docs/SECURITY-AUDIT.md](SECURITY-AUDIT.md) (ocena 9/10). Sweep w tej sesji:
| # | Wektor | Kontrola | Wynik |
|---|--------|---------|-------|
| D1 | SQL Injection | wszystkie zapytania danych przez `$wpdb->prepare`; kolumny filtrów z allowlisty | ✅ brak |
| D2 | XSS | całe wyjście `esc_html/esc_attr/esc_url`; brak surowego echo zmiennych | ✅ brak |
| D3 | SSRF | zdjęcia przez `iaai_safe_image_url()` + allowlista `*.iaai.com` | ✅ aktywne |
| D4 | Wejście GET | `iaai_make/year/dmg/sort/str` sanityzowane (sanitize_text_field/absint/sanitize_key) | ✅ |
| D5 | Niebezpieczne funkcje | brak `eval/exec/system/shell_exec/…` | ✅ brak |
| D6 | SSL | `sslverify` nigdzie nie wyłączony (PHP i Python) | ✅ |
| D7 | Sekrety | brak tokenów/haseł w kodzie i paczce | ✅ brak |
| D8 | Direct access | `ABSPATH` guard w każdym pliku z kodem; `index.php` w każdym katalogu | ✅ |
| D9 | DoS | clamp shortcode 1–48 + Transient cache + mutex publikacji | ✅ |

## E. Audyt paczki i weryfikacja ZIP
| # | Kontrola | Wynik |
|---|----------|-------|
| E1 | `require` → pliki istnieją | ✅ 5/5 |
| E2 | Wersje spójne (nagłówek/stała/readme) | ✅ 0.30.0 |
| E3 | Python kompiluje się | ✅ wszystkie |
| E4 | `vehicle.schema.json` poprawny | ✅ |
| E5 | Plugin ZIP | ✅ 11 plików, 0 śmieci, komplet includes+assets+readme |
| E6 | Paczka dostawy | ✅ 0-PRZECZYTAJ + PDF + iaai-importer.zip + scraper/deploy/docs; 0 niepożądanych; brak sekretów |

## F. Wydajność (optymalizacje)
| # | Optymalizacja | Efekt | Status |
|---|---------------|-------|--------|
| F1 | Zdjęcia listy: N+1 → 1 zapytanie (`iaai_first_images_map`) | mniej zapytań przy siatce | ✅ |
| F2 | `update_post_term_cache=false` | brak grzania cache termów (CPT bez taksonomii) | ✅ |
| F3 | Transient cache 5 min per (filtry+strona), bump wersji przy publikacji | odciąża bazę | ✅ |
| F4 | Lazy-load zdjęć (`loading="lazy"`), limit zdjęć/kart | szybsze ładowanie | ✅ |
| F5 | CSS/JS ładowane tylko tam, gdzie potrzebne | brak narzutu na resztę witryny | ✅ |

## G. Dwa źródła — Copart (audyt + testy dual-source) 🆕
Zakres: kolumna `source` (iaai/copart), klucz `(source, salvage_id)`, plakietka + filtr źródła,
osobny przebieg scrapera per źródło (`--source`), sesja Member Copart (`COPART_COOKIES`).

### G.1 Znaleziska AUDYTU (naprawione w tej rundzie)
| # | Waga | Znalezisko | Skutek | Naprawa |
|---|------|-----------|--------|---------|
| G-A1 | 🔴 błąd | `iaai_get_image_urls()` (galeria szczegółów) odpytywała po samym `salvage_id` | przy tym samym numerze lotu w IAAI i Copart galeria mieszała zdjęcia z obu źródeł | dodany parametr `$source` + `AND source = %s`; wywołanie pobiera źródło z meta `iaai_source` |
| G-A2 | 🔴 błąd | `iaai_krytyk_render()` liczył `COUNT(*)` zdjęć po samym `salvage_id` | fałszywy alarm/licznik przy kolizji numerów | `COUNT(*) ... AND source = %s` + `get_image_urls(..., $source)` |
| G-A3 | 🟡 migracja | dbDelta **nie przebudowuje** istniejącego PRIMARY KEY | świeża instalacja OK; stara baza IAAI zostaje na kluczu `(salvage_id)` — dwa źródła z tym samym lotem by kolidowały | dodane wykrywanie `iaai_check_source_pk()` (log ostrzegawczy, bez ryzykownego auto-ALTER) + instrukcja migracji w docs/klient/05 |

### G.2 Zweryfikowane OK (spójność `source`)
| # | Element | Oczekiwane | Status |
|---|---------|-----------|--------|
| G1 | Schemat 1.1.0 | PK `(source,salvage_id)`; obrazy UNIQUE `(source,image_key)`, KEY `(source,salvage_id,seq)` | ✅ (świeża inst.) |
| G2 | Publikacja | `iaai_publish_vehicle/find_post_by_salvage/publish_all/unpublish_inactive` operują na parze (source, salvage_id) | ✅ (przegląd) |
| G3 | Front: miniatury listy | `iaai_first_images_map` łączy po `(source = %s AND salvage_id = %d)` (OR-grupy), klucz `source|salvage_id` | ✅ |
| G4 | Front: plakietka + filtr | badge IAAI/Copart (`esc_attr/esc_html`); filtr „Źródło" tylko gdy >1 źródło | ✅ |
| G5 | Import zdjęć (download) | `iaai_import_images` bierze `source` z meta i filtruje `AND source = %s` | ✅ |
| G6 | Sanityzacja | `source` z whitelisty `{iaai,copart}` (inaczej `iaai`) — brak SQLi/śmieci | ✅ |
| G7 | Anty-SSRF zdjęć | allowlista hostów obejmuje `copart.com` + `*.copart.com` (i IAAI) | ✅ |
| G8 | Scraper copart | `_map_detail` → `source='copart'`; zdjęcia `image_key='copart-{lot}-{i}'`, `seq` | ✅ (A6–A7) |
| G9 | json_agent | `source` w `upsert`/`upsert_image`; reconcile ograniczony `AND v.source = %s` (per źródło) | ✅ (przegląd; A8–A9 na VPS) |
| G10 | Copart live (żywe dane) | pełne dane/zdjęcia po zalogowaniu (`COPART_COOKIES`); anty-bot Cloudflare | ⏳ (walidacja na VPS, jak IAAI) |

### G.3 Testy wtyczki dual-source (runtime WP — do potwierdzenia na danych 2 źródeł)
| # | Test | Oczekiwane | Status |
|---|------|-----------|--------|
| G-B1 | Dwa źródła na liście | auta IAAI i Copart obok siebie, każde z plakietką źródła | ⏳ (demo statyczne ✅: 9 IAAI + 3 Copart) |
| G-B2 | Filtr źródła | wybór „Copart" zawęża listę do Copart; „IAAI" do IAAI | ⏳ (demo ✅) |
| G-B3 | Galeria per źródło | ten sam numer lotu w obu źródłach → galeria pokazuje TYLKO zdjęcia właściwego źródła (regresja G-A1) | ⏳ (MySQL) |
| G-B4 | Kolizja numeru lotu | rekord IAAI i Copart z identycznym `salvage_id` współistnieją (PK na parze) | ⏳ (MySQL, świeża inst.) |

---

## Jak samodzielnie powtórzyć testy wtyczki
Instrukcja krok po kroku z gotowym seedem: [dev-test/INSTRUKCJA-TEST-LOCAL.md](../dev-test/INSTRUKCJA-TEST-LOCAL.md)
(uwaga: folder `dev-test/` to narzędzia deweloperskie — NIE trafia do paczki klienta).

## Pozostałe do potwierdzenia na środowisku docelowym (⏳)
Runtime na prawdziwym MySQL/WordPressie i żywym IAAI: C1–C4, C6–C8, C10, B16, B18.
Dual-source (Copart): A8–A9 (pymysql), G-B1–G-B4, G10 (żywy Copart — wymaga konta Member i sesji
`COPART_COOKIES`; anty-bot Cloudflare — walidacja na VPS, jak przy IAAI).
Procedura wdrożenia i uruchomienia: [deploy/README.md](../deploy/README.md) oraz [docs/klient/](klient/).
