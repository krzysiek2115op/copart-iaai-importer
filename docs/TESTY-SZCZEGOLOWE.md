# Szczegółowe testy systemu — plugin + automatyzacja

Data: 2026-07-03 · wtyczka **v0.24.0** · zakres: cały system (WordPress plugin + scraper/ETL + wdrożenie).
Legenda: ✅ zweryfikowane · ⏳ wymaga środowiska docelowego (VPS/MySQL/żywe IAAI) · 🔒 test bezpieczeństwa.

---

## A. Testy jednostkowe (Python, bez sieci/bazy)
Komenda: `python -m unittest discover -s scraper/tests`
- Wynik (ta sesja): **19 testów — 12 przeszło, 7 pominiętych** (pominięte = brak zależności w dev; na VPS przejdą). ✅
- Pokrycie: `jednostki` (parsowanie przebiegu, sale_date, key_present), `vin` (maska/status),
  `match` (deduplikacja), `common` (prefiks tabel, hash), `pokrycie` (segmenty, krytyk kompletności).

| # | Test | Oczekiwane | Status |
|---|------|-----------|--------|
| A1 | `parse_sale_date` numeryczny i tekstowy | ISO albo None (nieparsowalne) | ✅ |
| A2 | `key_present` „Not Available" | `False` (negacja przed „avail") | ✅ |
| A3 | VIN zamaskowany | `vin_status=masked`, nie grupowany w dedup | ✅ |
| A4 | `tbl()` prefiks tabel | dokłada `IAAI_DB_TABLE_PREFIX` | ✅ |
| A5 | krytyk pokrycia | wykrywa segment URWANY (got < ResultCount) | ✅ |

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
| E2 | Wersje spójne (nagłówek/stała/readme) | ✅ 0.24.0 |
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

---

## Jak samodzielnie powtórzyć testy wtyczki
Instrukcja krok po kroku z gotowym seedem: [dev-test/INSTRUKCJA-TEST-LOCAL.md](../dev-test/INSTRUKCJA-TEST-LOCAL.md)
(uwaga: folder `dev-test/` to narzędzia deweloperskie — NIE trafia do paczki klienta).

## Pozostałe do potwierdzenia na środowisku docelowym (⏳)
Runtime na prawdziwym MySQL/WordPressie i żywym IAAI: C1–C4, C6–C8, C10, B16, B18.
Procedura wdrożenia i uruchomienia: [deploy/README.md](../deploy/README.md) oraz [docs/klient/](klient/).
