<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Audyt bezpieczeństwa — Plugin 2 (Importer motocykli poleasingowe.pl)

**Data:** 2026-07-09 · **Wersja wtyczki:** 0.7.0 · **Zakres:** wtyczka WordPress (`wp-plugin/motocykle-poleasingowe/`) + scraper Python (`scraper/`)
**Standardy odniesienia:** OWASP Top 10 (2021), WordPress Coding/Security Standards, PHP Security Best Practices.

Audytowano **każdy plik**: `motocykle-poleasingowe.php`, `includes/{security,class-db,shortcode,activation,admin}.php`, `uninstall.php`, `assets/front.css` oraz `scraper/{config,main,dzial1a,dzial1b,dzial2,dzial3,dzial4,dzial5,dzial7}.py`.

---

## 1. Model zagrożeń i powierzchnia ataku

Architektura celowo **minimalizuje powierzchnię ataku**:

- Wtyczka **tylko czyta** z osobnej bazy `polea_*` (read-only) — **nie** tworzy CPT/postów, **nie** przyjmuje uploadów, **nie** rejestruje REST/AJAX, **nie** uruchamia crona po stronie WP.
- Front renderowany **server-side** (shortcode) — brak JS przyjmującego dane → **brak DOM XSS**.
- Scraper parsuje HTML **wyłącznie regexem stdlib** (bez `lxml`/parsera XML) → **brak bomb XML/XXE**; brak `zipfile` → **brak bomb ZIP**.
- Sekrety (hasło bazy) **wyłącznie** w `wp-config.php` / zmiennych środowiskowych.

### Powierzchnie, które NIE występują (N/A — z uzasadnieniem)
| Obszar z checklisty | Status | Dlaczego |
|---|---|---|
| File Upload / `$_FILES` / `move_uploaded_file` | N/A | Wtyczka nie przyjmuje plików. |
| REST API (`register_rest_route`, `permission_callback`) | N/A | Brak endpointów REST. |
| AJAX (`wp_ajax_*`) | N/A | Brak akcji AJAX. |
| `$_REQUEST` / `$_COOKIE` / `php://input` | N/A | Nieużywane (tylko `$_GET`/`$_POST` w 2 miejscach). |
| `eval/exec/system/unserialize/create_function` (PHP) | N/A | Nie występują (zweryfikowane grepem). |
| `eval/exec/os.system/subprocess/pickle` (Python) | N/A | Nie występują (zweryfikowane grepem). |
| Parsowanie XML / ZIP / CSV | N/A | Scraper używa regexu; brak deserializacji formatów. |
| Application Passwords / sesje / cookies | N/A | Wtyczka nie zarządza uwierzytelnianiem. |

---

## 2. Znaleziska i poprawki

Legenda poziomu: 🟥 wysoki · 🟧 średni · 🟨 niski · 🟩 informacyjny / już bezpieczne.

### NAPRAWIONE

| # | Lokalizacja | Problem | Ryzyko | CVSS 3.1 | Poziom | Poprawka |
|---|---|---|---|---|---|---|
| F1 | `scraper/dzial7_zgodnosc.py` → `Fetcher.get()` | **SSRF przez przekierowanie / brak allowlisty hostów.** `requests` domyślnie podążał za redirectami (do 30) bez walidacji celu — złośliwa/zmanipulowana odpowiedź mogła przekierować pobieranie na `localhost` / `169.254.169.254` (metadane chmury) / adres wewnętrzny. | SSRF do zasobów wewnętrznych VPS | `AV:N/AC:H/PR:N/UI:N/S:C/C:H/I:N/A:N` ≈ **6.8** | 🟧 średni | Allowlista hostów (`ALLOWED_HOSTS`), `allow_redirects=False` + **ręczna walidacja każdego skoku** (host + blokada IP prywatnych/loopback/link-local/reserved), limit skoków `MAX_REDIRECTS=3`, wymuszony schemat `http(s)`. |
| F2 | `scraper/dzial7_zgodnosc.py` → `Fetcher.get()` | **DoS / bomba dekompresyjna.** `return r.text` wczytywał całą odpowiedź do pamięci bez limitu; spreparowany gzip mógł rozwinąć się do GB. | wyczerpanie pamięci procesu | `AV:N/AC:H/PR:N/UI:N/S:U/C:N/I:N/A:H` ≈ **5.3** | 🟧 średni | Czytanie strumieniowe `iter_content` z twardym limitem `MAX_RESPONSE_BYTES=8 MB` (liczonym **po** dekompresji). |
| F3 | `scraper/main.py` → `main()` | **Cron: brak blokady pojedynczej instancji** → nakładające się uruchomienia (race na reconcile, marnowanie zasobów). | spójność importu / mini-DoS na źródło | `AV:L/AC:H/PR:L/UI:N/S:U/C:N/I:L/A:L` ≈ **3.1** | 🟨 niski | `flock(LOCK_EX\|LOCK_NB)` na `LOCK_PATH`; drugi proces kończy się kodem 1. Flaga `--no-lock` do testów. |
| F4 | `wp-plugin/.../includes/security.php` → `polea_sanitize_filters()` | **Brak limitu długości/zakresu** wejścia filtrów (`$_GET`). Bez wpływu na SQL (prepared), ale obrona w głąb. | nadmiarowe wejście | — | 🟨 niski | `mb_substr(...,0,64)` na polach tekstowych, zakres roku 1900–2100, cena ≥ 0, `paged ≤ 100000`. |
| F5 | `scraper/requirements.txt` | **Przestarzałe minimalne wersje** zależności z publicznymi CVE. | podatne komponenty | — | 🟨 niski | `requests>=2.32.2` (CVE-2024-35195), `urllib3>=2.2.2` (CVE-2024-37891), `PyMySQL>=1.1.1`. |

#### Kod przed / po — F1 (SSRF) — fragment kluczowy
```python
# PRZED
def get(self, url):
    if not self.allowed(url):
        raise BlockedError(...)
    ...
    r = self.s.get(url, timeout=config.TIMEOUT)   # allow_redirects=True (domyślnie), brak walidacji hosta
    ...
    return r.text

# PO
def url_allowed(url, resolve=True):
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"): return False, "niedozwolony schemat"
    if (parts.hostname or "").lower() not in config.ALLOWED_HOSTS: return False, "host spoza allowlisty"
    if resolve and _host_is_private(parts.hostname): return False, "adres prywatny/lokalny"
    return True, ""

def get(self, url):
    self._check(url)                      # allowlist + anty-SSRF + robots
    ...
    r = self.s.get(current, timeout=config.TIMEOUT, allow_redirects=False, stream=True)
    if code in _REDIRECT_CODES:
        nxt = urljoin(current, r.headers.get("Location",""))
        self._check(nxt)                  # KAŻDY skok walidowany
        ...
    return self._read_capped(r)           # limit bajtów
```

#### Kod przed / po — F2 (limit rozmiaru)
```python
# PRZED:  return r.text
# PO:
def _read_capped(self, r):
    limit = config.MAX_RESPONSE_BYTES; chunks, total = [], 0
    for chunk in r.iter_content(chunk_size=65536):
        total += len(chunk)
        if total > limit: raise BlockedError(f"Odpowiedz przekracza limit {limit} B: {r.url}")
        chunks.append(chunk)
    enc = r.encoding or r.apparent_encoding or "utf-8"
    return b"".join(chunks).decode(enc, errors="replace")
```

### ZWERYFIKOWANE JAKO BEZPIECZNE (bez zmian — 🟩)

| Obszar | Lokalizacja | Ustalenie |
|---|---|---|
| **SQL Injection (PHP)** | `class-db.php` | Wszystkie zapytania to **prepared statements** (`mysqli_prepare` + `bind_param`); nazwa kolumny w `distinct()` z **allowlisty**; klauzula `IN(...)` budowana z `?`. Brak konkatenacji wejścia. |
| **SQL Injection (Python)** | `dzial4_synchronizacja.py` | `cur.execute(sql, params)` — parametryzowane; `NOT IN (%s,%s,...)` z listą bindów; kolumny z listy stałej `_FIELDS`. |
| **XSS (output escaping)** | `shortcode.php`, `admin.php` | Każde wyjście: `esc_html` / `esc_attr` / `esc_url` / `selected()` / rzutowania `(int)`. Link do aukcji: `esc_url` + `rel="noopener nofollow"`. |
| **CSRF** | `admin.php` | `wp_nonce_field('polea_flush_cache')` + `check_admin_referer('polea_flush_cache')` przed akcją zapisu. |
| **Autoryzacja** | `admin.php` | `add_options_page(..., 'manage_options', ...)` + dodatkowo `current_user_can('manage_options')` (defense in depth). Najmniejsze potrzebne uprawnienie dla operacji administracyjnej. |
| **Direct access** | wszystkie `*.php` | `defined('ABSPATH') || exit;`; `uninstall.php` → `WP_UNINSTALL_PLUGIN`. |
| **Sekrety** | `class-db.php`, `config.py` | Poświadczenia wyłącznie ze stałych `POLEA_DB_*` (wp-config) / env. Brak sekretów w kodzie i w repo. |
| **Odporność połączenia** | `class-db.php` | `@mysqli_connect` + `mysqli_report(MYSQLI_REPORT_OFF)` → błąd bazy **nie** wywołuje `wp_die` i **nie** wywala strony klienta. Błędy nie trafiają do klienta. |
| **Error handling** | całość | Brak `var_dump`/`print_r`/`echo $e`/stack trace na produkcji. |
| **Nonce na formularzu filtra** | `shortcode.php` | Formularz filtrów to **GET nawigacyjny** (odczyt, bez zmiany stanu) — celowo bez nonce (nonce w publicznym GET łamałby cache i wygasał). Poprawne. |

---

## 3. Zgodność z OWASP Top 10 (2021)

| Kategoria | Status | Uwagi |
|---|---|---|
| A01 Broken Access Control | ✅ | `current_user_can` + capability na stronie admina; brak innych operacji uprzywilejowanych. |
| A02 Cryptographic Failures | ✅ | Brak przechowywania sekretów/PII przez wtyczkę; źródło po HTTPS. Zalecane TLS do bazy (pkt 5). |
| A03 Injection | ✅ | Prepared statements (PHP+Python); wyjście escapowane; brak `eval`. |
| A04 Insecure Design | ✅ | Read-only front, allowlista źródła, rate-limit, limity rozmiaru/paginacji, blokada instancji. |
| A05 Security Misconfiguration | ✅ | ABSPATH wszędzie; brak debug output; sekrety poza kodem. |
| A06 Vulnerable Components | ✅ | Zależności podniesione (F5); PHP korzysta tylko z API WP core. |
| A07 Identification & Auth Failures | ✅ (N/A) | Wtyczka nie zarządza uwierzytelnianiem/sesjami. |
| A08 Software & Data Integrity | ✅ | Brak deserializacji niezaufanych danych (JSON zamiast pickle/`unserialize`). |
| A09 Logging & Monitoring | ✅ | Logi bez haseł/tokenów/PII; logowane tylko URL/marka/model/liczniki. |
| A10 SSRF | ✅ | Naprawione (F1): allowlista hostów, walidacja redirectów, blokada IP prywatnych. |

---

## 4. Dependency Security

| Komponent | Wersja min. | CVE / uwaga | Akcja |
|---|---|---|---|
| PHP (wtyczka) | — | Brak zależności zewnętrznych (tylko WordPress core ≥ 6.0, PHP ≥ 7.4). | OK |
| `requests` | 2.32.2 | CVE-2024-35195 | ✅ podniesione |
| `urllib3` | 2.2.2 | CVE-2024-37891 | ✅ przypięte |
| `PyMySQL` | 1.1.1 | — | ✅ podniesione |

---

## 5. Rekomendacje poza kodem wtyczki (poziom serwera/wdrożenia)

Świadomie **nie** ustawiamy nagłówków HTTP z poziomu wtyczki wyświetlającej treść (CSP, X-Frame-Options, Permissions-Policy) — globalne nagłówki z jednej wtyczki potrafią popsuć inne części strony klienta. Zalecenie: ustawić na poziomie serwera/motywu:

- **HTTP:** `Content-Security-Policy` (z dopuszczeniem `img-src https://poleasingowe.pl` dla hotlinku), `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, `Referrer-Policy: strict-origin-when-cross-origin`.
- **Cookies WP:** `Secure`, `HttpOnly`, `SameSite=Lax` (konfiguracja WP/serwera).
- **Baza:** konto MySQL dla wtyczki z uprawnieniem **wyłącznie `SELECT`** na `polea_*`; scraper osobne konto z `INSERT/UPDATE`. TLS do MySQL, jeśli baza jest na innym hoście niż WP.
- **Cron:** wywołanie scrapera co kilka godzin z `--limit` w oknie testowym; monitoring czasu wykonania (timeout na poziomie systemd/cron).

---

## 6. Security Score (1–10)

| Obszar | Ocena | Uzasadnienie |
|---|---|---|
| Kod (ogólnie) | **9/10** | Prepared statements, pełne escapowanie, wąska powierzchnia. |
| WordPress Security | **9/10** | ABSPATH, nonce+capability, brak `wp_die`, uninstall czyści po sobie. |
| PHP Security | **9/10** | Brak niebezpiecznych funkcji; walidacja+sanityzacja wejścia. |
| REST API | **N/A** | Brak endpointów. |
| AJAX | **N/A** | Brak akcji AJAX. |
| Importer (scraper) | **8/10** | Po hardeningu: anty-SSRF, limit rozmiaru, robots, rate-limit. |
| Cron | **8/10** | Blokada instancji + backoff; brak zaawansowanego alertingu. |
| Baza danych | **9/10** | Parametryzacja pełna; zalecane konto tylko-SELECT + TLS. |
| File System | **10/10** | Brak operacji plikowych na wejściu użytkownika; brak LFI/RFI/traversal. |
| Sieć | **8/10** | Allowlista + walidacja redirectów + timeout; teoretyczny DNS-rebinding poza modelem. |
| **ŚREDNIA** | **≈ 8.7/10** | **Gotowe do produkcji** przy zaleceniach z pkt 5. |

---

## 7. Weryfikacja

- `python3 -m unittest scraper.tests.test_scraper` → **16/16 OK** (w tym 5 nowych testów bramki SSRF: obcy host, localhost, metadane chmury, zły schemat, host dozwolony).
- Zbalansowanie składni PHP: OK dla wszystkich 7 plików (regiony `<?php…?>`). `php -l` do wykonania w środowisku z PHP przed wysyłką (Etap 5 — demo).

---

# Iteracja 2 — dalszy hardening (v0.7.1, 2026-07-09)

Cel: z ~9/10 „tak wysoko, jak się da". Poniżej **nowe** utwardzenia (ponad F1–F5). Każde zweryfikowane (16/16 testów, PHP zbalansowany).

| # | Warstwa | Lokalizacja | Wektor / problem | Poziom | Poprawka |
|---|---|---|---|---|---|
| H1 | Wtyczka | `class-db.php` → `conn()` | **Zwis frontu przy awarii bazy** (brak timeoutu połączenia) + ryzyko `LOAD DATA LOCAL` ze złośliwego serwera MySQL. | 🟧 średni | `mysqli_init` + `MYSQLI_OPT_CONNECT_TIMEOUT=3` + `MYSQLI_OPT_READ_TIMEOUT=5` + **`MYSQLI_OPT_LOCAL_INFILE=false`** + `mysqli_real_connect`. |
| H2 | Wtyczka | `shortcode.php`, `security.php`, `class-db.php` | **Zalewanie cache transientów** (storage DoS): nieograniczona przestrzeń kluczy `md5(filtry)` z dowolnego `$_GET` (marka/cena/strona). | 🟧 średni | `polea_constrain_filters()` — marka/paliwo/rok tylko z **allowlisty z bazy**, cena **kubełkowana** co 500 z górnym limitem, `paged ≤ 500`. Listy wartości cache'owane (`distinct()` w transient). |
| H3 | Wtyczka | `shortcode.php` | Wyciek URL strony klienta do źródła (nagłówek `Referer` przy hotlinku obrazów). | 🟨 niski | `referrerpolicy="no-referrer"` na `<img>`. |
| H4 | Scraper | `dzial4_synchronizacja.py` → `connect()` | Zawieszony import przy niedostępnej bazie; brak TLS/limitu; ryzyko LOCAL INFILE. | 🟧 średni | `connect/read/write_timeout` (env), **`local_infile=False`**, opcjonalny **TLS** (`POLEA_DB_SSL_CA`). |
| H5 | Scraper | `dzial7_zgodnosc.py` → `Fetcher.__init__` | **SSRF przez zmienne środowiskowe** — złośliwy `HTTP(S)_PROXY`/`.netrc` mógł przekierować cały ruch. | 🟧 średni | `session.trust_env = False` (domyślnie; override `POLEA_TRUST_ENV=1`). |
| H6 | Scraper | `dzial1b_szczegoly.py`, `dzial2_normalizacja.py` | Niezaufany HTML → **znaki sterujące / przepełnienie kolumn / absurdalne liczby** (błędy zapisu, śmieci w bazie). | 🟨 niski | Usuwanie znaków sterujących C0, twarde limity długości pól (`_txt`, ≤255/32/64), górne limity liczb (`_capint`) i ceny (≤ 1e9). |
| H7 | Scraper | `dzial7_zgodnosc.py` → `__init__` | **Zwis inicjalizacji** na `robots.txt` (brak timeoutu, `RobotFileParser.read()`). | 🟨 niski | Pobranie z `timeout=TIMEOUT` + limit **512 KB** + `rp.parse()`. |
| H8 | Scraper | `dzial7_zgodnosc.py` → `_read_capped` | **Slow-loris** — serwer sączący bajty pod limitem read-timeout w nieskończoność. | 🟨 niski | Całkowity **budżet czasu** na odpowiedź `MAX_TOTAL_SECONDS=60`. |
| H9 | Repo | `scraper/.gitignore` | Ryzyko commitu sekretów/env/locka. | 🟨 niski | `.gitignore` na `.env`, `*.lock`, `__pycache__`, venv. |

### Zbieżność — świadomie NIE zmienione (żeby nie robić security theater)
- **Nagłówki HTTP (CSP/XFO/Permissions-Policy) z wtyczki** — globalne nagłówki z wtyczki wyświetlającej treść psują stronę klienta; poprawne miejsce to serwer/motyw (pkt 5).
- **DNS-rebinding** (host allowlisty rozwiązywany dwa razy) — poza modelem zagrożeń (źródło zaufane, allowlista + blokada IP prywatnych są głównym mechanizmem).
- **Hash-pinning `requirements.txt`** — nadmiarowe dla 2 zależności; utrzymujemy bezpieczne wersje minimalne.
- **Lock w `/tmp`** — na jednodostępnym VPS wystarcza; ścieżka konfigurowalna (`POLEA_LOCK`), zalecenie: katalog usługi z prawami 700 (pkt 5).
- **Bezpośredni `$wpdb->query` (transienty)** — statyczne LIKE bez wejścia; bezpieczne, zgodne z praktyką WP.

### Zaktualizowany Security Score

| Obszar | Iter. 1 | **Iter. 2** | Zmiana |
|---|---|---|---|
| Kod (ogólnie) | 9 | **9.5** | +walidacja allowlisty, mniej powierzchni |
| WordPress Security | 9 | **9.5** | +timeouty DB, brak zwisu frontu |
| PHP Security | 9 | **9.5** | +LOCAL INFILE off, limity wejścia |
| REST API / AJAX | N/A | N/A | brak |
| Importer (scraper) | 8 | **9** | +limity tekstu/liczb, robots timeout |
| Cron | 8 | **8** | bez zmian (lock już był) |
| Baza danych | 9 | **9.5** | +timeouty, TLS opcjonalny, local_infile off |
| File System | 10 | **10** | — |
| Sieć | 8 | **9** | +trust_env off, slow-loris, robots cap |
| **ŚREDNIA** | ≈ 8.7 | **≈ 9.3/10** | **maksimum sensownego hardeningu w tym modelu** |

**Wniosek:** dalsze podnoszenie oceny wymagałoby zmian **poza kodem** (nagłówki HTTP na serwerze, konto MySQL tylko-`SELECT`, TLS do bazy, monitoring) — opisane w pkt 5. W obrębie kodu projektu osiągnięto punkt zbieżności.

---

## Iteracja 3 (v0.11.x → hardening całości, po rozbudowie SEO/frontu)

Pełny ponowny przegląd całego brancha `plugin-2` (PHP, Python, SQL, HTML/CSS, cron/systemd, deploy, konfiguracje). **Bez zmian funkcjonalności** — wyłącznie utwardzenia i dokumentacja ryzyk resztkowych.

### A. Poprawki w kodzie (ta iteracja)

| # | Ryzyko | Podatność / CWE | Wpływ | Pliki | Zmiana | Dok.? |
|---|---|---|---|---|---|---|
| 1 | Niskie | Brak walidacji `Content-Type` odpowiedzi HTTP (CWE-20 / CWE-436) | Wrogi/zmanipulowany serwer źródła mógłby serwować binaria/nietypowe typy do parsera HTML (limit rozmiaru/czasu już chronił, brak twardej walidacji typu) | `scraper/dzial7_zgodnosc.py` | W `get()` po `raise_for_status()`: odrzuć odpowiedź, gdy `Content-Type` jest obecny i nie jest `text/*`/`*html*` | Nie |
| 2 | Niskie | Niejawna weryfikacja certyfikatu TLS (CWE-295) | `requests` domyślnie weryfikuje, ale poleganie na domyślnej wartości jest kruche | `scraper/dzial7_zgodnosc.py` | Jawne `self.s.verify = True` na sesji | Nie |
| 3 | Średnie | Realny plik `*.env` z hasłami mógł trafić do repo — `.gitignore` łapał tylko `.env`/`.env.*`, nie `polea.env` (CWE-312 / CWE-538) | Wyciek poświadczeń bazy przy przypadkowym `git add` | `.gitignore` | Dodano `*.env` + wyjątek `!*.env.example` (szablon nadal commitowalny) | Nie |

**Regresje:** scraper 19/19 testów OK; front — bez zmian ścieżek danych/API.

### B. Weryfikacja pentestowa nowego kodu (SEO/front, v0.8–v0.11) — bez nowych podatności

| Wektor (OWASP/CWE) | Miejsce | Status |
|---|---|---|
| XSS / HTML Injection (CWE-79) | `shortcode.php`, `seo.php` (breadcrumbs, chips, tabela, FAQ, opis, meta/OG/Twitter) | ✅ `esc_html`/`esc_attr`/`esc_url` na każdym wyjściu; `<title>`/H1 przez `wp_strip_all_tags` |
| JSON/Schema Injection (CWE-116) | JSON-LD `@graph` | ✅ `wp_json_encode(JSON_HEX_TAG\|JSON_HEX_AMP)` — brak wyjścia z `<script>` |
| SQL Injection (CWE-89) | `Polea_DB::related`, `active_lot_ids`, `query_list`, `distinct` | ✅ prepared statements; interpolowana tylko nazwa kolumny z allowlisty |
| Open Redirect (CWE-601) | generowanie URL (`polea_single_url`, pager, canonical) | ✅ brak `wp_redirect`; wszystkie URL przez `esc_url`; `get_permalink`/`home_url` zamiast danych żądania |
| Cache poisoning/stampede (CWE-524) | transient listy + `polea_rel_*` | ✅ klucz z allowlisty (skończona przestrzeń); flush obejmuje `polea_rel_*`; stampede = ryzyko resztkowe (pkt C) |
| CSRF (CWE-352) | panel admina (flush cache) | ✅ `check_admin_referer` + `current_user_can('manage_options')` |
| Rekurencja filtra `the_title` | breadcrumbs | ✅ `get_post_field` zamiast `get_the_title` |
| Ekspozycja błędów (CWE-209) | `Polea_DB` | ✅ `mysqli_report(OFF)`, błędy → `[]`/`null`, komunikaty ogólne |
| SSRF/redirecty (CWE-918) | rewrite/sitemap (tylko wewnętrzne URL) | ✅ wejście `lot_id` = regex `^[A-Za-z0-9]{1,32}$` |

**Potwierdzono brak:** REST/AJAX, uploadu, `eval/exec/system/shell_exec/proc_open/unserialize/extract`, deserializacji niezaufanych danych, `$_REQUEST/$_COOKIE`, dynamicznego `include/require`. `md5` **wyłącznie** jako klucz cache (nie kryptografia — CWE-328 nie dotyczy).

### C. Ryzyka resztkowe (poza kodem — konfiguracja środowiska)

1. **Nagłówki HTTP** — plugin celowo **nie** ustawia nagłówków globalnych (należą do serwera/motywu). Zalecane dla całej witryny:
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains` (po pełnym HTTPS)
   - `X-Content-Type-Options: nosniff`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Content-Security-Policy` — dostosować do motywu; w `img-src` **musi** być `https://poleasingowe.pl` (hotlink zdjęć)
   - `Permissions-Policy`, `Cross-Origin-Opener-Policy: same-origin`, `Cross-Origin-Resource-Policy`
   - `X-Frame-Options: SAMEORIGIN` (WP-admin już wysyła)
2. **MySQL — least privilege (CWE-250/CWE-269):** dwa konta do bazy `polea`:
   - **scraper** (VPS): `SELECT, INSERT, UPDATE` (bez `DELETE/DROP/GRANT/FILE`)
   - **wtyczka WP**: **tylko `SELECT`** (wtyczka wyłącznie czyta) → ogranicza skutki ewentualnego SQLi/przejęcia WP
   ```sql
   CREATE USER 'polea_ro'@'10.0.0.%' IDENTIFIED BY '...';
   GRANT SELECT ON polea.* TO 'polea_ro'@'10.0.0.%';
   ```
   W `wp-config.php`: `define('POLEA_DB_USER','polea_ro');`
3. **TLS do bazy** (połączenie zdalne): scraper honoruje `POLEA_DB_SSL_CA`; po stronie MySQL `require_secure_transport=ON`.
4. **DNS rebinding / TOCTOU (CWE-367):** host/IP walidowane przy sprawdzeniu, `requests` rozwiązuje DNS ponownie przy połączeniu (okno rebinding). Pełna ochrona = przypięcie IP (custom adapter) — świadomie niewprowadzone (ryzyko regresji). Mitygacja: firewall egress na VPS, blok `169.254.169.254`/sieci wewnętrznych.
5. **Cache stampede:** przy wygaśnięciu transientu równoległe żądania odbudują cache naraz — przy tej skali nieistotne; przy dużym ruchu obiektowy cache + blokada odbudowy.
6. **Sekrety:** wyłącznie env / stałe `wp-config.php`; `deploy/polea.env` (0600, poza repo, `.gitignore` utwardzony).
7. **PDF (`docs/klient/*.py`, `docs/*.gen.py`):** narzędzia **build-time**, nie działają na produkcji, nie przyjmują niezaufanego wejścia — poza powierzchnią ataku.

### D. Zgodność

OWASP Top 10 (A01–A10), ASVS L1/część L2, CWE Top 25 (79/89/352/22/78/918/434/502/601/295/312/367), WordPress/PHP/Python/MySQL Secure Coding. **W obrębie kodu: brak znanych podatności usuwalnych bez zmiany funkcjonalności.** Ocena ~9.3/10; pełne ~9.7–10 po wdrożeniu pkt C (serwer).
