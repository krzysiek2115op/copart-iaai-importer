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
