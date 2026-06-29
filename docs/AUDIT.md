# Audyt systemu / pipeline — A do Z

Data: 2026-06-29. Zakres: wszystkie 9 działów (Python 1–5,7 + wtyczka WP 6,8,9),
schemat bazy, spójność między działami. Metoda: test integracyjny end-to-end na żywych
danych + przegląd statyczny kodu.

## ✅ Test integracyjny (przeszedł)
Przepuszczono realne loty Ferrari przez **cały łańcuch Pythona**:
`listingi → szczegóły → VIN → jednostki → match → diff → json(upsert) → audyt`.
- 2018 Ferrari California T i 1985 Ferrari 308 GTS **wylądowały w bazie** (status active).
- Wszyscy krytycy zielono; vPIC zdekodował **zamaskowany** VIN (Ferrari 308GTS, 1985).
- **Zero `KeyError`** → nazwy pól są spójne między działami; `DATA_COLS` == kolumny `schema.sql`.
- Upsert idempotentny, wykrywanie zmian (`raw_hash`) działa (zweryfikowane wcześniej).

## 🔴 Wysokie — ✅ NAPRAWIONE (v0.18.0)

> **H1 ✅** `json --images` upsertuje zdjęcia do `iaai_vehicle_images` (zweryfikowane: 37 szt.).
> **H2 ✅** `json` pomija `_audit_ok=false` (rekord odrzucony nie trafia do bazy — zweryfikowane).
> Kolejność zapisu: `diff → audyt → json`. Szczegóły niżej (kontekst pierwotny).

**H1. Zdjęcia nie trafiają do bazy.** Agent `zdjecia` produkuje rekordy (JSONL/pliki), ale
**żaden agent Pythona nie zapisuje do `iaai_vehicle_images`**; agent `json` (dział 4)
upsertuje tylko `iaai_vehicles`. Wtyczka WP (`media`) czyta `iaai_vehicle_images` — byłaby
**pusta** → brak miniatur i galerii na stronie.
→ *Fix:* dodać upsert zdjęć w dziale 4 (lub w `zdjecia`) — `INSERT … ON DUPLICATE KEY UPDATE`
po `image_key`.

**H2. Audyt jest PO zapisie do bazy.** Kolejność pipeline'u: dział 4 (zapis) → dział 5 (audyt).
Bramka jakości działa „po fakcie" — niepoprawne rekordy zdążą trafić do bazy. Brakuje też
**kroku odsiewającego** `_audit_ok=false` (walidacja tylko flaguje).
→ *Fix:* przenieść audyt PRZED `json`/upsert (5 przed 4) albo `json` ma pomijać `_audit_ok=false`.

## 🟠 Średnie

**M1. `sale_date`: nieparsowalna data idzie surowa do `DATETIME`.** `jednostki` przy nieudanym
parsowaniu zwraca string oryginalny (`… or out["sale_date"]`), a `DATA_COLS` zawiera `sale_date`
→ upsert wstawia nie-ISO string do kolumny `DATETIME` = błąd/obcięcie. Obecnie **utajone**
(żaden agent nie ustawia `sale_date`).
→ *Fix:* przy nieudanym parsowaniu ustawić `None`; albo `json` waliduje datę przed zapisem.

**M2. `sale_date` w praktyce nie jest zbierane.** Ani `listingi` (etykieta daty pusta), ani
`szczegóły` (brak „Sale Date" w `DETAIL_MAP`) nie mapują daty sprzedaży → zwykorzystywany
przy aukcjach `auction_close`/sale jest pusty.
→ *Fix:* dodać mapowanie daty (z karty/szczegółów) jeśli potrzebne biznesowo.

**M3. Status `sold`/`removed` niewykryty.** `diff` ustawia zawsze `active`; brak przebiegu
„feed-complete" oznaczającego loty nieobecne w nowym pobraniu jako sprzedane/usunięte.
→ *Fix:* po pełnym backfillu oznaczyć brakujące `salvage_id` jako `removed`.

**M4. Brak orkiestracji.** Działy uruchamiane ręcznie; brak jednego runnera/crona spinającego
1→…→9 oraz mostka Python→WP (publikacja po imporcie).
→ *Fix:* runner pipeline + harmonogram (to część „spraw technicznych").

## 🟡 Niskie

- **L1.** `szczegóły`: `vin_status` bywa `null` (nie wyłuskuje „(OK)") — niski wpływ (vin.py liczy sam).
- **L2.** `branch_id` i tabela `iaai_branches` nieużywane (mamy tylko `selling_branch` tekstem).
- **L3.** Niespójne wartości `key_available` („Present" vs „Key Available") — `key_present` to normalizuje.
- **L4.** `parse_sale_date` zakłada bieżący rok, gdy brak roku — ryzyko na przełomie roku.
- **L5.** Wtyczka PHP/WP **nie była uruchomiona** (brak PHP/WP w środowisku) — tylko weryfikacja statyczna.

## Bezpieczeństwo / zgodność (przegląd)
- Brak sekretów w repo (token tylko w `~/.git-credentials`, `.gitignore` chroni). ✅
- Dane do bazy/WP sanityzowane (dział 6), SQL przez `$wpdb->prepare`, wyjście escapowane.
- `/Search` zabroniony w robots.txt — krytyk `blokady` to zgłasza; decyzja prawna (ToS) po stronie właściciela. ⚠️
- VIN pełny wymaga konta IAAI (anonimowo maskowany).

## Ocena ogólna
Architektura spójna, łańcuch Pythona **realnie działa end-to-end z bazą**. Przed produkcją:
**H1 i H2** są kluczowe (zdjęcia w bazie + kolejność audytu). Reszta to dopięcia.
Lista naprawcza wchodzi w fazę „spraw technicznych".
