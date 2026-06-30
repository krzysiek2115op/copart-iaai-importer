# AUDYT A–Z (debug) — przed pakowaniem do ZIP

Data: 2026-06-30, stan **v0.27.0**. Audyt całego systemu: kompilacja, testy,
parytet danych, wpięcia, cykl życia rekordu. Wynik: rdzeń spójny; znaleziono
**7 ustaleń** (F1–F7) do Twojej decyzji — żadne nie blokuje, część ważna dla produkcji.

---

## 1. CO ZWERYFIKOWANO ✅ (przeszło)
- **Kompilacja:** wszystkie 14 plików Pythona kompilują się bez błędu.
- **Testy:** `scraper/tests/test_pure.py` — 12 przechodzi, 7 skip (brak deps w bazowym
  Pythonie; wykonają się na produkcji z venv). Zero failów.
- **Parytet kolumn ścieżki ZAPISU (krytyczne):** 32 kolumny **identyczne** w trzech źródłach:
  `db/schema.sql` ↔ `common.DATA_COLS` ↔ `activation.php` (dbDelta na WP). Brak rozjazdu →
  brak cichej utraty danych przy zapisie do bazy.
- **Audyt danych (dział 5):** schema JSON `additionalProperties:true`, `required:[salvage_id]`,
  `odometer_uom`/`status` z enumami — nie odrzuca błędnie rekordów wzbogaconych.
- **Łańcuch `sale_date`:** etykieta (listingi/szczegóły) → `sale_date` → ISO (jednostki) → kolumna
  w bazie — domknięty (po blokach B/C).

## 2. USTALENIA (F1–F7) — do decyzji

> **STATUS NAPRAW (v0.28.0):** F1 ✅, F2 ✅, F3 ✅ (zrobione). F4–F7 pozostają wg opisu niżej.

### ✅ F1 (NAPRAWIONE) — znikłe auta zostają opublikowane na stronie
`iaai_publish_all_active()` publikuje **tylko** rekordy `status='active'`. Gdy reconcile oznaczy
lot jako `sold`/`removed`, jego wpis WP **nie jest cofany** (zostaje „publish"). Efekt: strona
pokazuje auta, których już nie ma w ofercie.
**Zrobione:** `iaai_unpublish_inactive()` (wołane z `iaai_publish_all_active()`) przestawia wpisy
sold/removed na `draft` (nie kasuje — historia zostaje) i zapisuje meta `iaai_status`. Re-list
wraca na `publish`. Wtyczka v0.15.0.

### ✅ F2 (NAPRAWIONE) — dział 7 (rate-limit + detekcja blokad) nie wpięty w orkiestrator
`run_pipeline.py` robi tylko jednorazowy `compliance_note()` (sprawdzenie robots). Właściwy
`RateLimiter`/`detect_block()` z `07_zgodnosc/zgody.py` **nie jest** używany w przebiegu. Jedyny
throttle to `--delay` (1 s/stronę) w `listingi`. Przy always-on + pełnym pokryciu (wiele segmentów)
to ryzyko blokady IAAI.
**Zrobione:** `listingi` i `szczegóły` importują dział 7 (`zgody.py`): `RateLimiter` (odstęp między
żądaniami — w `szczegóły` `--delay` był wcześniej **ignorowany**) + `detect_block()` (Incapsula/
CAPTCHA/403/429) → przy blokadzie pobieranie przerywa się (backoff), krytyk/exit code to zgłasza.
Flaga `blocked` propagowana też przez `pokrycie` do krytyka. (`zdjęcia` = requests do CDN
vis.iaai.com, niższe ryzyko — poza zakresem F2.)

### ✅ F3 (NAPRAWIONE) — pola WYLICZANE, ale niezapisywane
`odometer_km`, `key_present`, `title_brand`, `title_state`, `vin_status` są liczone w normalizacji,
ale `to_db_row()` bierze tylko `DATA_COLS` → nie trafiają do bazy.
**Decyzja + zrobione:** baza MA POZOSTAĆ **wierną kopią rekordu IAAI** — nie dodajemy własnych
kolumn. Realny skutek dla klienta (km nie docierał, front na sztywno „mi") naprawiony w warstwie
WYŚWIETLANIA: `iaai_format_odometer()` liczy km przy renderze i honoruje `odometer_uom`
(„169 594 km (105 380 mi)"). Pozostałe pola wyliczane zostają **diagnostyczne** (logi/krytycy),
zgodnie z zasadą wiernej kopii.

### 🟡 F4 (niskie) — meta WP nie wystawia `item_id` ani `branch_id`
W bazie są (zapisywane), ale `iaai_meta_keys()` ich nie publikuje (30 z 32 pól). `branch_id` i tak
jest by-design null (L11); `item_id` (Item #) jest realny i można go pokazać.
**Opcje:** dodać `item_id` (ew. `branch_id`) do meta, jeśli ma być widoczny.

### 🟡 F5 (niskie, kosmetyka) — dwie definicje schematu
`db/schema.sql` ma `status ENUM(...)` (dla dev MariaDB), `activation.php` ma `status varchar(10)`
(dbDelta nie lubi ENUM). To celowe, ale dwa źródła = ryzyko rozjazdu przy zmianach. Wartości
zgodne (active/sold/removed). **Opcja:** opisać w `db/` że WP-autorytatywny jest `activation.php`.

### 🔵 F6 (info, znane z bloku B) — do potwierdzenia na żywym IAAI
Konkretne **segmenty pokrycia** (parametr filtra po stanie/branch) i dokładna **etykieta `sale_date`**
na karcie — do potwierdzenia przy pierwszym przebiegu na żywo (mamy szablon + warianty defensywne).

### 🔵 F7 (info) — PHP/WP nieuruchamiane w dev
Działy 6/8/9 + `activation.php` weryfikowane statycznie (brak PHP/WP w środowisku). Runtime
domyka się przy teście na realnym WordPress/VPS (blok A „⏳”).

---

## 3. PROCES SYSTEMU — jak to działa (A→Z)
```
[IAAI.com]
   │  (Playwright; robots/ToS = decyzja właściciela)
   ▼
DZIAŁ 1 POBIERANIE
   ├─ pokrycie  → iteruje segmenty (filtry), scala unikalne po salvage_id   [#6]
   ├─ listingi  → karty wyników (paginacja Knockout), ~32 pola
   ├─ szczegóły → strona lotu (render JS), uzupełnia pola
   └─ zdjęcia   → vis.iaai.com (lista keys + URL-e)
   ▼ (merge karta+szczegóły po salvage_id)
DZIAŁ 2 NORMALIZACJA
   ├─ VIN       → format/cyfra kontrolna, maska, vPIC (make/model/rok), vin_status
   └─ jednostki → mi→km, ceny→liczby, sale_date→ISO, tytuł→brand/stan, key_present
   ▼
DZIAŁ 3 DEDUPLIKACJA  → exact po salvage_id; relist po PEŁNYM VIN; miękcy kandydaci (nie auto-merge)
   ▼
DZIAŁ 4a DIFF  → raw_hash → new/changed/unchanged
   ▼
DZIAŁ 5 AUDYT  → JSON Schema + reguły; znakuje _audit_ok (H2: odrzucone nie idą do bazy)
   ▼
DZIAŁ 4b JSON  → upsert pojazdów + zdjęć do bazy (prefiks wp_), reconcile sold/removed
   ▼
[NOWA BAZA = wp_iaai_vehicles + wp_iaai_vehicle_images]   (ta sama baza co WordPress)
   ▼
DZIAŁ 6 BEZPIECZEŃSTWO  → sanitize/escape/nonce/prepare (wejście do WP)
DZIAŁ 8 PUBLIKACJA      → CPT „pojazd" + meta (z bazy)            [F1: brak cofania removed]
DZIAŁ 9 FRONT I MEDIA   → lista + strona pojazdu, zdjęcia HOTLINK z vis.iaai.com
   ▼
[STRONA WordPress klienta]  — klient widzi auta

Spina to: DZIAŁ 7 ZGODNOŚĆ (robots/rate-limit/blokady)  [F2: rate-limit nie wpięty do pętli]
Always-on: systemd live.timer (15 min) + backfill.timer (full 03:30) → cykl → publish (WP-CLI)
```

## 4. REKOMENDACJA KOLEJNOŚCI (do Twojej decyzji)
1. **F1** (znikłe auta → cofnij publikację) — najbardziej widoczne dla klienta.
2. **F2** (rate-limit do pętli) — ważne dla stabilności always-on przy skali.
3. **F3** (zapis km/title_brand/…) — jeśli mają być w bazie/na stronie.
4. **F4/F5** — drobne/kosmetyka. **F6/F7** — domknięcie na żywym IAAI/VPS.

Nic z powyższego nie blokuje spakowania ZIP — to ulepszenia jakości/produkcyjności.
