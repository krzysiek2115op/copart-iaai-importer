# STATUS PROJEKTU — Importer IAAI → WordPress

Master-dokument: cel, jak działa, co mamy, czego brakuje. Stan: **2026-06-30, v0.28.0**
(bloki A/B/C: kod gotowy; audyt A–Z + naprawy F1–F3 — [docs/AUDIT2.md](docs/AUDIT2.md)).
(Szczegóły techniczne: [docs/PIPELINE.md](docs/PIPELINE.md), [docs/AUDIT.md](docs/AUDIT.md),
[docs/dzialy/](docs/dzialy/), [docs/refs/](docs/refs/).)

---

## 1. CEL PROJEKTU
Wtyczka **WordPress**, która automatycznie pobiera dane i zdjęcia pojazdów z **iaai.com**
do **nowej bazy danych** i wyświetla je na stronie klienta.
- **Backfill** — zaciąga całą bieżącą ofertę IAAI.
- **Live** — dokłada nowe pojazdy na bieżąco.
- Klient po otrzymaniu wtyczki (ZIP) wpina ją do swojego WordPressa; tabele zakładają się
  same (`dbDelta`), a pojazdy pojawiają się na stronie jako wpisy typu „Pojazd".
- **Copart usunięty z zakresu** (cała domena za Imperva Incapsula — brak legalnego, anonimowego
  dostępu). Projekt = **tylko IAAI**.

### ⚙️ WYMÓG NADRZĘDNY: automatyzacja ciągła (always-on)
System ma **działać cały czas sam**, nie po ręcznym odpaleniu komendy. Gdy na IAAI pojawia się
nowe auto → agenci **same je wyłapują** → dane + zdjęcia trafiają do bazy → auto pokazuje się na
stronie klienta. **Bez ingerencji operatora.** Ręczne `run_pipeline.py` to tylko tryb
testowy/backfill — docelowo pipeline `live` chodzi w pętli jako **usługa/harmonogram**
(daemon / systemd / cron / wp-cron). To jest warunek spełnienia celu, nie opcja.

**MODEL WDROŻENIA (ustalony):** wszystko na **jednym VPS klienta**, tam gdzie hostuje stronę:
WordPress + MySQL już są; **scraper Python** chodzi jako usługa na tym samym serwerze i pisze do
**TEJ SAMEJ bazy MySQL** co WordPress (`IAAI_DB_*` = baza WP klienta, połączenie lokalne).
Harmonogram: **systemd timer / cron** odpala `live` w pętli; publikacja do CPT przez **WP-CLI**
(`wp eval 'iaai_publish_all_active();'`) lub bezpośrednio z bazy. Brak osobnego hostingu na scraper.

## 2. JAK TO DZIAŁA (architektura)
Pipeline **wieloagentowy**: 9 działów, w każdym **agenci** (🔵 wykonują) i **krytyk** (🔴 sprawdza).
Zasada: **1 agent : 1 krytyk**. Każdy dział ma **jedną oryginalną dokumentację** (w `docs/refs/`).

Dwie technologie:
- **Python (działy 1–5, 7)** — scraping + ETL → zapis do nowej bazy.
- **Wtyczka WordPress / PHP (działy 6, 8, 9)** — czyta bazę i renderuje na stronie.

```
IAAI ─> [1 pobieranie] ─> [2 normalizacja] ─> [3 deduplikacja] ─> [4a diff] ─> [5 audyt]
        ─> [4b json: upsert pojazdów+zdjęć (+reconcile)] ─> NOWA BAZA (MySQL/MariaDB)
   ▲ (7 zgodność: robots/rate-limit)
WordPress <─ [9 front i media] <─ [8 publikacja CPT] <─ [6 bezpieczeństwo] <─ NOWA BAZA
(klient widzi auta)
```

## 3. NOWA BAZA DANYCH
Wierna kopia rekordu IAAI. Schemat: [db/schema.sql](db/schema.sql) (MySQL 5.7+/MariaDB 10.3+, utf8mb4).
- `iaai_vehicles` — pola 1:1 jak listing IAAI (salvage_id PK, VIN, year/make/model, odometer+brand,
  damage, title, run&drive, key, branch, lane/aisle, buy_now/current_bid, …) + metadane sync
  (`raw_hash`, `status` active/sold/removed, `captured_at`, `updated_at`).
- `iaai_vehicle_images` — zdjęcia (image_key UNIQUE, seq, W/H, url).
- Mapowanie pól: [db/mapping.md](db/mapping.md). Uruchomienie/podgląd: [db/SETUP.md](db/SETUP.md).
- **Instancja deweloperska** (postawiona): przenośna MariaDB 11.4.4 w `~/iaai-mariadb`,
  `127.0.0.1:3307`, baza `iaai`, user `iaai/iaai`. Sterowanie: `~/iaai-mariadb/{start,stop,connect}-db.sh`.

---

## 4. CO JUŻ MAMY (gotowe)

### Wszystkie 9 działów zaimplementowane
| # | Dział | Agenci → krytyk | Oryginał (refs) | Tech | Stan |
|---|-------|-----------------|-----------------|------|------|
| 1 | pobieranie | listingi, szczegóły, zdjęcia → kompletność | playwright-python.md | Python | ✅ testowany na żywo |
| 2 | normalizacja | VIN, jednostki → poprawność-VIN, jakość | vin-nhtsa.md | Python | ✅ testowany |
| 3 | deduplikacja | match → fałszywe-trafienia | (logika własna) | Python | ✅ testowany |
| 4 | synchronizacja | diff, json → spójność, poprawność-json | mysql-upsert.md | Python+DB | ✅ testowany na żywej bazie |
| 5 | audyt | walidacja → poprawność | json-schema.md | Python | ✅ testowany |
| 6 | bezpieczeństwo | sanityzacja, nonce → podatności | wordpress-security.md | PHP/WP | ⚠️ statycznie |
| 7 | zgodność | zgody → blokady | robots-rfc9309.md | Python | ✅ testowany |
| 8 | publikacja | CPT, meta → poprawność | wordpress-cpt.md | PHP/WP | ⚠️ statycznie |
| 9 | front i media | front, media → render | wordpress-media.md | PHP/WP | ⚠️ statycznie |

Kod Python: [scraper/dzialy/](scraper/dzialy/) · Wtyczka WP: [wp-plugin/iaai-importer/](wp-plugin/iaai-importer/).

### Orkiestrator (jedna komenda)
[scraper/run_pipeline.py](scraper/run_pipeline.py) — spina cały łańcuch Pythona end-to-end:
```bash
python scraper/run_pipeline.py --mode full --base "https://www.iaai.com/Search"   # backfill
python scraper/run_pipeline.py --mode live --base "https://www.iaai.com/Search"   # nowe
# --limit N do testów (ogranicza szczegóły/zdjęcia; reconcile wtedy pomijany)
```
Krok WP (osobno, w WordPressie): `wp eval 'iaai_publish_all_active();'`.

### Audyt + naprawy (zrobione)
Raport: [docs/AUDIT.md](docs/AUDIT.md). Test integracyjny E2E przeszedł (realne Ferrari → baza).
- ✅ **H1** — zdjęcia trafiają do bazy (`json --images`).
- ✅ **H2** — audyt odsiewa przed zapisem (`json` pomija `_audit_ok=false`); kolejność diff→audyt→json.
- ✅ **M1** — bezpieczna `sale_date` (nieparsowalna → None).
- ✅ **M3** — wykrywanie `sold/removed` (`json --reconcile` po pełnym feedzie).
- ✅ **M4** — orkiestrator + udokumentowany most do WP.

### Infrastruktura
- Repo prywatne **krzysiek2115op/copart-iaai-importer** (GitHub). Wersjonowanie: auto commit+push+tag
  po każdej zmianie (v0.1.0 → **v0.20.0**, releasy na GitHub).
- Folder projektu: `~/zlecenie plugin 1 ` (UWAGA: spacja na końcu nazwy).
- Token w `~/.git-credentials` (fine-grained, scope: to repo). NIE w repo.

---

## 5. CO JESZCZE DO ZROBIENIA

### A. Wysoki priorytet (do działającej całości u klienta)
> **Blok A — kod GOTOWY (v0.24.0), zostaje test na realnym VPS.** Zob. `deploy/README.md`.

1. **🔴 Automatyzacja ciągła (always-on) — RDZEŃ projektu.** ✅ **Zaimplementowane (kod):**
   usługi systemd `iaai-importer-live.timer` (co 15 min od zakończenia, `Persistent` — nadrabia po
   restarcie) + `iaai-importer-backfill.timer` (`full`+reconcile 03:30). Cykl
   `deploy/iaai-live-cycle.sh` = pipeline `live` → publikacja do WP. Inkrement już był (`diff`
   `raw_hash` + `reconcile`). Rate-limit/zgodność: dział 7.  ⏳ **Zostaje:** odpalić i potwierdzić na VPS.
2. **Runtime wtyczki w prawdziwym WordPressie** — ⏳ wpiąć `wp-plugin/iaai-importer/` do instalacji WP,
   przetestować: zakładanie tabel (`dbDelta`), CPT, meta, import zdjęć, front. (Działy 6/8/9 +
   `activation.php` dotąd weryfikowane statycznie — brak PHP/WP w dev. Procedura: `deploy/README.md`.)
3. **Aktywacja wtyczki + `dbDelta()`** — ✅ **Zrobione:** `includes/activation.php`
   (`register_activation_hook` + `iaai_maybe_upgrade_db`) zakłada `{$wpdb->prefix}iaai_*` samo.
4. **Konfiguracja połączenia z bazą** — ✅ **Zrobione:** `deploy/iaai-env.sh` czyta dane z
   `wp-config.php` (WP-CLI) → `IAAI_DB_*` + `IAAI_DB_TABLE_PREFIX`. **Prefiks tabel** dodany w
   `common.tbl()` i wpięty w `json_agent`/`diff` → Python pisze do TYCH SAMYCH `wp_iaai_*` co wtyczka.
5. **Most Python → WP** — ✅ **Zrobione:** cykl kończy się `wp eval 'iaai_publish_all_active();'`.

### B. Średni priorytet (poprawność/skala produkcyjna)
6. **Pełne pokrycie „całego IAAI"** — ✅ **Silnik gotowy (kod):** agent `pokrycie`
   (`scraper/dzialy/01_pobieranie/pokrycie.py`) iteruje po SEGMENTACH (filtrach), scala
   unikalne po `salvage_id`; krytyk `kompletność-pokrycia` wykrywa segment URWANY
   (zebrano < ResultCount → „podziel drobniej"). Wpięte w orkiestrator: `--segments plik.json`.
   ⏳ **Zostaje:** ustalić konkretne segmenty (parametr filtra po stanie/branch) na żywym IAAI —
   `segments.example.json` to szablon; znany działający filtr to `?Keyword=`.
9. **M2 — `sale_date`** — ✅ **Zrobione (kod):** mapowanie etykiet daty (Sale/Auction Date,
   kilka wariantów) w `listingi`/`szczegóły` → `sale_date`; `jednostki.parse_sale_date` parsuje
   teraz format tekstowy I numeryczny (M/D/RRRR) → ISO; nieparsowalne → None (zabezpieczenie M1).
   ⏳ Potwierdzić dokładną etykietę na żywej karcie.

**Decyzje (PODJĘTE 2026-06-30):**
7. **Konto IAAI (pełny VIN)** — ❌ **NIE budujemy.** Zostaje VIN maskowany + dekodowanie vPIC
   (marka/model/rok). Bez konta, bez ryzyka prawnego. Stan obecny wystarcza.
8. **Składowanie zdjęć** — ✅ **HOTLINK z vis.iaai.com** (0 miejsca na dysku). Wtyczka renderuje
   zdjęcia bezpośrednio z URL-i w bazie (`iaai_image_mode()` = `hotlink`, domyślny). Tryb
   `download` (sideload do mediów WP) zostaje opcjonalnie pod filtrem `iaai_image_mode`.
   Wtyczka v0.14.0: lista i strona pojazdu hotlinkują (lazy `<img>`, escapowane).

### C. Niski priorytet (dopięcia — z audytu L1–L5) — ✅ ZROBIONE (v0.27.0)
10. ✅ **`vin_status`** — `vin.py` wyprowadza spójny status (masked/ok/invalid/unknown), gdy
    szczegóły nie podały go w nawiasie. (Pole diagnostyczne — nie idzie do bazy.)
11. ✅ **`branch_id`** — celowo NULL-owalny; źródłem prawdy jest `selling_branch` (tekst, jak na
    karcie IAAI anonimowo). Brak tabeli `iaai_branches` z założenia (płaska, wierna kopia). *By design.*
12. ✅ **`key_available`** — naprawiony błąd: „Not Available" zawiera „avail" → wcześniej dawało
    `key_present=True`. Teraz najpierw negacja (`not/no/without/...`) → poprawne `False`.
13. ✅ **`parse_sale_date`** — przy braku roku wybiera rok dający datę NAJBLIŻSZĄ dziś
    (aukcje bywają tuż po przełomie roku), nie sztywno bieżący.
14. ✅ **Testy automatyczne** — `scraper/tests/test_pure.py` (stdlib `unittest`, bez sieci/bazy):
    jednostki, vin, match, common(tbl/hash), pokrycie. Miękki import → moduł z brakującą
    zależnością jest pomijany, nie wywraca całości. Uruchom:
    `python -m unittest discover -s scraper/tests`.

### D. Dostawa dla klienta
15. **Paczka ZIP wtyczki** — spakować `wp-plugin/iaai-importer/` jako instalowalny plugin WP
    (z `readme.txt`, nagłówkiem, aktywacją). Część Python (scraper) jako osobny moduł/usługa
    zasilająca bazę. Do ustalenia model wdrożenia u klienta (gdzie działa scraper).

---

## 6. KLUCZOWE USTALENIA I OGRANICZENIA
- **IAAI = jedyne źródło** (Copart za Incapsula — poza zakresem).
- **Wyszukiwarka IAAI = Knockout.js**, paginacja przez POST `/Search` → sterowana Playwright
  (nie `&page=`). Strona szczegółów renderuje dane JS-em (surowy HTTP pusty) → też Playwright.
- **VIN maskowany anonimowo**; NHTSA vPIC dekoduje markę/model/rok nawet z maski.
- **`/Search` zabronione w robots.txt** IAAI — krytyk `blokady` to zgłasza; decyzja o scrapingu
  jest **biznesowo-prawna (ToS)** i należy do właściciela projektu, nie do kodu. `/VehicleDetail/` dozwolone.
- **PHP/WP nieuruchamiane lokalnie** — działy 6/8/9 zweryfikowane standardami; runtime po wpięciu do WP.
- Bezpieczeństwo: brak sekretów w repo; sanityzacja/escaping/`$wpdb->prepare`; token poza repo.

## 7. SZYBKI START (dev)
```bash
# baza dev:
~/iaai-mariadb/start-db.sh
# pipeline (test, 3 loty):
python "scraper/run_pipeline.py" --mode full --base "https://www.iaai.com/Search?Keyword=Ferrari" --limit 3
# podgląd bazy:
~/iaai-mariadb/connect-db.sh -e "SELECT salvage_id,year,make,model,status FROM iaai_vehicles;"
```
