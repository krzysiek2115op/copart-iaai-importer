# Pipeline — jak działa cały system (IAAI → WordPress)

System pobiera pojazdy z **iaai.com**, przetwarza je przez 9 działów (każdy: agenci 🔵
robią, krytyk 🔴 sprawdza, zasada **1 agent : 1 krytyk**) i pokazuje na **stronie WordPress**.

Dwie technologie:
- **Działy 1–5 + 7 = Python** (scraping i ETL → zapis do nowej bazy).
- **Działy 6, 8, 9 = wtyczka WordPress (PHP)** (`wp-plugin/iaai-importer/`) — czyta bazę i renderuje.

```
IAAI ─> [1 pobieranie] ─> [2 normalizacja] ─> [3 deduplikacja] ─> [4a diff] ─> [5 audyt] ─> [4b json: upsert pojazdów+zdjęć] ─> NOWA BAZA
   ▲ (7 zgodność: robots/rate-limit przy pobieraniu)
   │
WordPress <─ [9 front i media] <─ [8 publikacja CPT] <─ [6 bezpieczeństwo] <─ NOWA BAZA (MySQL/MariaDB)
(odwiedzający)        (wtyczka PHP czyta NOWĄ BAZĘ i wyświetla pojazdy)
```
> Kolejność zapisu (po audycie v0.18): `diff` liczy status → **`audyt` odsiewa** niepoprawne
> → `json` zapisuje do bazy **tylko `_audit_ok≠false`** (pojazdy **oraz zdjęcia**, `--images`).

## Przepływ krok po kroku

| # | Dział | Agenci 🔵 | Krytyk 🔴 | Co robi | Tech |
|---|-------|-----------|-----------|---------|------|
| 1 | **pobieranie** | listingi, szczegóły, zdjęcia | kompletność (×3) | przechodzi wyszukiwarkę IAAI (paginacja Playwright), pobiera pełne pola pojazdu i listę zdjęć | Python |
| 2 | **normalizacja** | VIN, jednostki | poprawność-VIN, jakość-jednostek | waliduje/dekoduje VIN (NHTSA vPIC, działa też dla zamaskowanych), ujednolica mi→km, ceny, daty, tytuł | Python |
| 3 | **deduplikacja** | match | fałszywe-trafienia | usuwa duplikaty po `salvage_id`; relist po pełnym VIN; nie łączy różnych aut | Python |
| 4 | **synchronizacja** | diff, json | spójność, poprawność-json | wykrywa zmiany (`raw_hash`) i robi **upsert do bazy** (new/changed/unchanged) | Python+DB |
| 5 | **audyt danych** | walidacja | poprawność | JSON Schema + reguły biznesowe — odrzuca rekordy niepoprawne | Python |
| 6 | **bezpieczeństwo** | sanityzacja, nonce | podatności | sanityzuje wejście, escapuje wyjście, chroni akcje (nonce), SQL przez `prepare` | PHP/WP |
| 7 | **zgodność** | zgody | blokady | respektuje robots.txt (RFC 9309), rate-limit, wykrywa blokady (Incapsula/429) | Python |
| 8 | **publikacja** | CPT, meta | poprawność-CPT, poprawność-meta | tworzy wpisy WordPressa typu „pojazd" + meta z rekordów bazy | PHP/WP |
| 9 | **front i media** | front, media | render | importuje zdjęcia do mediów WP (miniatura+galeria), renderuje listę i strony pojazdów | PHP/WP |

## Co przepływa
- **Działy 1–5 (Python):** rekord pojazdu jako JSONL między agentami, a w dziale 4 wpada
  do **nowej bazy** (`iaai_vehicles`, `iaai_vehicle_images`; schemat: `db/schema.sql`).
- **Wtyczka (PHP):** czyta nową bazę (`$wpdb->prepare`), publikuje jako CPT „pojazd" + meta,
  importuje zdjęcia, renderuje na stronie. **Plugin nie łączy się z bazą bezpośrednio na
  froncie** — działy (CPT/meta/front) pośredniczą; odwiedzający widzi gotowe wpisy WP.

## Tryby zasilania
- **Backfill (`full`)** — cała bieżąca oferta IAAI (dział 1 przechodzi wszystkie strony).
- **Live (`incremental`)** — nowe pojazdy na bieżąco; dział 4 wykrywa zmiany i dokłada.

## Oryginalne dokumentacje (jedna na dział, w `docs/refs/`)
Playwright (1) · NHTSA vPIC/ISO 3779 (2) · [logika własna] (3) · MySQL upsert (4) ·
JSON Schema (5) · WordPress Security (6) · RFC 9309 robots (7) · WordPress CPT (8) ·
WordPress media (9).

## Stan i ograniczenia (świadome, „technikalia na potem")
- Działy Python **przetestowane na żywym IAAI i realnej bazie MariaDB**.
- Działy PHP/WP **zweryfikowane statycznie** (brak PHP/WordPress w środowisku) — runtime po
  wpięciu do instalacji WP.
- **VIN maskowany anonimowo** — pełny wymaga konta IAAI (make/model/rok mamy z vPIC mimo maski).
- **`/Search` zabronione w robots.txt** — decyzja o scrapingu jest biznesowo-prawna (ToS).
- **Pełne pokrycie „całego IAAI"** może wymagać iteracji po filtrach (limit wyników na zapytanie).
- Podpięcie agentów Python→baza działa (dział 4); spięcie crona/kolejki dla pełnej automatyzacji — do zrobienia.
