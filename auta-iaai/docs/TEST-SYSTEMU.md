# Test całego systemu — raport

Data: 2026-06-30, stan **v0.29.0**. Zakres: maksymalny możliwy w środowisku dev
(bez PHP/WP i bez łączenia na żywo z IAAI). Środowisko: przenośna MariaDB `127.0.0.1:3307`,
Python w venv (pymysql, jsonschema).

## Wynik zbiorczy: ✅ PRZESZŁO
Cała ścieżka danych Pythona (normalizacja → dedup → diff → audyt → zapis do bazy + zdjęcia)
przetestowana end-to-end na danych syntetycznych. Zapis działa też z prefiksem `wp_` (ścieżka VPS).

## Co przetestowano

### 1. Statyka
- Kompilacja 14/14 plików Pythona — OK.
- Testy jednostkowe `scraper/tests` — 12 pass / 7 skip (deps spoza bazowego Pythona) / 0 fail.
- Składnia wszystkich skryptów `deploy/*.sh` — OK.

### 2. End-to-end ścieżki danych (2 syntetyczne auta: pełny + maskowany VIN)
| Etap | Wynik |
|------|-------|
| Normalizacja (jednostki) | mi→km OK (50000mi→80467km); `sale_date` tekstowy „Mon Jun 29"→2026-06-29 **i** bez roku „Jul 2"→2026-07-02 (L13) |
| **L12 key_present** | „Not Available"→**False**, „Present"→**True** ✅ (naprawiony bug) |
| Dedup (match) | 2 unikalne; maskowany VIN **nie** grupowany ✅ |
| Diff | 1. przebieg `new=2`; ponowny `unchanged=2` (idempotencja po `raw_hash`) ✅ |
| Audyt (walidacja) | poprawnych=2, niepoprawnych=0 ✅ |
| Zapis (json_agent) | wstawiono=2, zdjęcia=3 (FK OK); odczyt zwrotny krytyka OK ✅ |
| `item_id`/`sale_date` w bazie | zapisane (F4 + łańcuch sale_date) ✅ |
| **Reconcile (F1/M3)** | feed tylko z autem 1 → auto 2 → `status=removed`, auto 1 zostaje `active` ✅ |

### 3. Ścieżka VPS — prefiks `wp_`
- Z `IAAI_DB_TABLE_PREFIX=wp_` pojazdy zapisały się do **`wp_iaai_vehicles`**, zdjęcia do
  **`wp_iaai_vehicle_images`** (3/3) ✅ — dowód, że Python pisze do tych samych tabel, które
  czyta wtyczka na WordPressie.
- Uwaga techniczna: `db/schema.sql` ma nazwany klucz obcy `fk_image_vehicle`; przy ręcznym
  klonowaniu schematu pod inny prefiks w TEJ SAMEJ bazie nazwa FK się powtarza (kolizja). Na
  realnym WP nie występuje — `activation.php` (dbDelta) tworzy tabele **bez** FK. (Tylko dla
  świadomości przy ręcznych testach.)

## Czego NIE dało się przetestować tutaj (wymaga realnego środowiska)
- **Runtime PHP/WP** (działy 6/8/9 + `activation.php`, shortcode, hotlink) — brak PHP/WP w dev.
- **Pobieranie na żywo z IAAI** (Playwright + rate-limit + detekcja blokad w praktyce) — nie
  młócimy serwisu z dev; logika zweryfikowana statycznie i jednostkowo.
- Domknięcie tych dwóch = test na realnym VPS wg `docs/klient/03-uruchom-automatyzacje.md`.

## Wniosek
Rdzeń (ETL + zapis do bazy, w tym ścieżka `wp_` dla WordPressa) działa poprawnie i jest spójny.
Pozostały do potwierdzenia wyłącznie elementy wymagające realnego WordPressa/VPS.
