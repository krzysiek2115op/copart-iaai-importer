# Audyt bezpieczeństwa wtyczki IAAI Importer

Data: 2026-06-30 · wtyczka **v0.16.0** · zakres: cały kod PHP wtyczki
(`wp-plugin/iaai-importer/`) + powiązana integracja (scraper Python, baza).
Traktowane jak produkt komercyjny: odporność na ataki, błędy, awarie i złe dane.

## Ocena końcowa: **9 / 10**
Wtyczka po utwardzeniu jest solidna: pełna sanityzacja wejścia, escapowanie wyjścia,
wyłącznie zapytania `$wpdb->prepare`, brak własnych endpointów REST/AJAX (mała powierzchnia
ataku), allowlista hostów zdjęć (anty-SSRF), mutex importu, batch, cache, nagłówki, logowanie.
Do „10" brakuje rzeczy z poziomu **serwera/wdrożenia** (CSP/HSTS, blokada PHP w `uploads`) —
poza kontrolą wtyczki; opisane w „Hardening".

---

## 1. Ważne ustalenie o architekturze (powierzchnia ataku)
Wtyczka **nie ma własnych endpointów REST, AJAX ani zadań WP-Cron**. Scraping i import
robi osobny proces **Python/systemd**, a publikacja do CPT idzie przez **WP-CLI**
(`wp eval 'iaai_publish_all_active();'`). Dlatego klasyczne wektory „REST bez
permission_callback", „AJAX bez nonce", „formularz bez CSRF" **nie istnieją** — nie
dodajemy ich sztucznie. Pomocnicze funkcje nonce/uprawnień są gotowe, gdyby w przyszłości
doszedł panel admina.

## 2. Znalezione podatności i naprawy
| # | Podatność | Ryzyko | Status | Naprawa |
|---|-----------|--------|--------|---------|
| V1 | **SSRF / hotlink na obcy host** — `url` zdjęcia z bazy był renderowany i sideloadowany bez sprawdzenia hosta; podstawiony URL → pobranie/wyświetlenie z dowolnego serwera | **High** | ✅ naprawione | `iaai_safe_image_url()` + allowlista `*.iaai.com` (filtr `iaai_allowed_image_hosts`); użyte w hotlinku i przed `media_sideload_image` |
| V2 | **Równoległy import (race / double-run)** — dwa przebiegi publikacji mogły działać naraz | Medium | ✅ | MySQL **GET_LOCK** mutex (`iaai_db_lock`) w `iaai_publish_all_active` |
| V3 | **DoS przez shortcode** — `[iaai_pojazdy ile="999999"]` → ciężkie zapytanie | Medium | ✅ | clamp `ile` do 1–48 + **Transient cache** 5 min |
| V4 | **Wyczerpanie pamięci** — publikacja całego IAAI w jednej pętli | Medium | ✅ | **Batch** (partie po 200) + `wp_suspend_cache_addition` |
| V5 | **Podmiana typu pliku przy sideload** (download mode) | Low | ✅ | po pobraniu weryfikacja `mime` = `image/*`, inaczej `wp_delete_attachment` |
| V6 | **Listing katalogów wtyczki** | Low | ✅ | `index.php` („Silence is golden") w katalogach wtyczki |
| V7 | **Wyciek błędów do użytkownika** | Low | ✅ | `iaai_log()` → tylko `error_log`/plik; nic nie trafia do przeglądarki |
| V8 | **Brak nagłówków bezpieczeństwa** na stronach pojazdów | Low | ✅ | `nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy`, `Permissions-Policy` |

**Nie znaleziono**: SQL Injection (wszędzie `$wpdb->prepare`), XSS (całe wyjście escapowane),
sekretów w kodzie, wyłączonego SSL.

## 3. Weryfikacja wg listy wymagań
- **Sanityzacja wejścia** — `iaai_sanitize_vehicle()` (absint/sanitize_text_field/esc_url_raw/
  float, allowlista `status`); meta CPT z `sanitize_callback`. ✅
- **Escapowanie wyjścia** — `esc_html/esc_attr/esc_url` w całym `front.php`; brak surowego echo. ✅
- **SQL Injection** — 100% zapytań przez `$wpdb->prepare` z `%d/%s` (też `LIMIT/OFFSET` jako `%d`);
  nazwy tabel z `$wpdb->prefix` (zaufane). Zero konkatenacji wejścia. ✅
- **XSS** — dane z bazy/meta zawsze escapowane przy wyświetlaniu; URL-e zdjęć dodatkowo allowlistą. ✅
- **CSRF / nonce / uprawnienia** — brak formularzy/akcji web; helpery `iaai_nonce_field()`,
  `iaai_verify_admin_action()` (z `current_user_can`) gotowe na przyszłość; meta REST z
  `auth_callback` (`edit_posts`) do zapisu. ✅ (w zakresie istniejącej powierzchni)
- **REST** — brak własnych endpointów; automatyczny REST CPT to **odczyt** publicznych danych
  ogłoszeń; zapis meta chroniony `auth_callback`. ✅
- **AJAX** — brak. N/D.
- **HTTP do IAAI** — realne połączenia są po stronie Pythona: **timeouty** (30–60 s) na każdym
  żądaniu, **SSL nigdy nie wyłączony**, `raise_for_status` w dekoderze VIN; rate-limit i detekcja
  blokad (dział 7). PHP łączy się tylko przez WP HTTP API (sslverify domyślnie wł.). ✅
- **Importer odporny** — idempotentny upsert (PK `salvage_id`, UNIQUE `image_key`), `diff` po
  `raw_hash`, `reconcile`; mutex + batch po stronie publikacji. ✅
- **Cron lock** — `iaai-importer-live.timer` nie nakłada przebiegów (`OnUnitInactiveSec`), a
  publikacja ma **GET_LOCK**. ✅
- **Duplikaty** — `salvage_id` (PK), pełny VIN (relist), `image_key` (UNIQUE). ✅
- **Race condition** — mutex GET_LOCK + suspend cache. ✅
- **Logowanie** — `iaai_log()` (czas, liczba rekordów, pamięć, wyjątki); poziomy; nie do usera. ✅
- **Upload zdjęć** — domyślnie **hotlink** (brak uploadu). W trybie download: allowlista hosta,
  weryfikacja `image/*`, WP sanitizuje nazwę i nadaje unikalną. Blokada PHP w `uploads` =
  poziom serwera (patrz Hardening). ✅ (w zakresie wtyczki)
- **Direct access** — `ABSPATH` guard w każdym pliku PHP. ✅
- **Sekrety** — brak w kodzie/repo; dane bazy z `wp-config.php` (rdzeń WP); token GitHub poza repo. ✅
- **Cache** — Transient API dla list (5 min), unieważniany przy publikacji. ✅
- **Batch** — publikacja partiami. ✅
- **DoS** — clamp + cache + lock; rate-limit po stronie Pythona. ✅
- **JSON** — PHP nie parsuje zewnętrznego JSON-a; walidacja JSON Schema jest w dziale 5 (Python). ✅
- **UTF-8** — `utf8mb4` + `sanitize_text_field`. ✅
- **Nagłówki** — bezpieczny podzbiór wysyłany; CSP/HSTS = serwer (Hardening). ✅ częściowo

## 4. OWASP Top 10 — werdykt
| Kategoria | Status |
|-----------|--------|
| Injection (SQLi) | ✅ `$wpdb->prepare` wszędzie |
| XSS | ✅ całe wyjście escapowane |
| CSRF | ✅ brak formularzy; helpery gotowe |
| Broken Access Control | ✅ meta `auth_callback`; brak akcji web bez uprawnień |
| Security Misconfiguration | ✅ ABSPATH, index.php, brak debug do usera |
| Sensitive Data Exposure | ✅ brak sekretów; dane publiczne |
| **SSRF** | ✅ allowlista hostów zdjęć (V1) |
| Path Traversal / LFI / RFI | ✅ brak operacji na ścieżkach z wejścia; brak `include` z danych |
| XXE | ✅ brak parsowania XML |
| Insecure Deserialization | ✅ brak `unserialize` danych zewnętrznych |
| Command Injection | ✅ brak `exec/system/shell_exec` |
| Clickjacking / MIME sniffing | ✅ `X-Frame-Options`, `nosniff` |
| Open Redirect | ✅ brak przekierowań z wejścia |
| Dependency Vulnerabilities | ⚠️ brak zależności PHP (czysty WP API); Python: pinować wersje (Hardening) |

## 5. Wdrożone zabezpieczenia (skrót)
ABSPATH guard · `$wpdb->prepare` 100% · sanityzacja wejścia · escapowanie wyjścia ·
**allowlista hostów zdjęć (anty-SSRF)** · weryfikacja MIME przy sideload · **mutex GET_LOCK** ·
**batch publikacji** · `wp_suspend_cache_addition` · **Transient cache** list · clamp shortcode ·
limit liczby zdjęć · **logowanie** (bez wycieku do usera) · meta `auth_callback` ·
**nagłówki bezpieczeństwa** · `index.php` w katalogach · brak sekretów w kodzie.

## 6. Hardening — co jeszcze można utwardzić (poza kodem wtyczki)
1. **Serwer/uploads**: w trybie download dodać w `wp-content/uploads/` regułę blokującą
   wykonywanie PHP (`.htaccess`/Nginx `location`) — to poziom hostingu, nie wtyczki.
2. **CSP / HSTS**: ustawić globalnie na serwerze (HSTS musi obejmować całą domenę; CSP
   wymaga strojenia pod motyw). Wtyczka świadomie ich nie wymusza, by nie zepsuć strony.
3. **WAF / rate-limit na froncie** (np. Cloudflare) — dodatkowa warstwa anty-DoS.
4. **Python**: pinować wersje zależności (`requirements` z `==`), skan `pip-audit`; dodać
   jawne sprawdzanie `Content-Type`/długości odpowiedzi przy pobieraniu zdjęć (jest timeout;
   warto dodać walidację typu i rozmiaru przed zapisem URL-a).
5. **Klucz/rotacja**: token GitHub i dane bazy trzymać w menedżerze sekretów hostingu.

## 7. Uwaga o weryfikacji
Kod PHP weryfikowany **statycznie** (brak środowiska PHP/WP w dev — bilans składni równy,
przegląd ręczny). Pełny test runtime należy wykonać po wgraniu na WordPressa wg
`docs/klient/03-uruchom-automatyzacje.md`. Logika ETL i ścieżka zapisu do bazy przetestowane
end-to-end (`docs/TEST-SYSTEMU.md`).
