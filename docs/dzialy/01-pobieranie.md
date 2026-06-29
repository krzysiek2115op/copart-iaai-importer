# Dział 1 · POBIERANIE — dokumentacja działu

> **Zasada:** jeden dział = **jedna** dokumentacja (ten plik). 1 agent : 1 krytyk.

Cel: zaciągnąć z IAAI **całą bieżącą ofertę** (`full`) i potem **nowe pojazdy live**
(`live`) — dane + zdjęcia — i zapisać do nowej bazy (`iaai_vehicles`, `iaai_vehicle_images`).

## Agenci i krytycy

### 🔵 `listingi` → 🔴 `kompletność-listy`
- **Agent:** iteruje wyniki wyszukiwarki IAAI (server-side, ~106 lotów/stronę), zbiera
  `salvage_id` + `detail_url` + pola karty (rok/marka/model, odometer, Buy Now, Run & Drive, Key);
  `full` = cała oferta, `live` = tylko nowe od ostatniego przejścia. Wynik: kolejka ID + upsert pól.
- **Krytyk:** paginacja doszła do końca, brak luk i duplikatów ID; brakujące strony → ponów.

### 🔵 `szczegóły` → 🔴 `kompletność-pól`  ✅ zaimplementowany
Kod: [`scraper/dzialy/01_pobieranie/szczegoly.py`](../../scraper/dzialy/01_pobieranie/szczegoly.py).
- **Agent:** renderuje `/VehicleDetail/{id}` przez **Playwright** (surowy HTML pusty — dane
  wstrzykiwane JS w DOM) i czyta bloki `.data-list__item` (etykiety: „VIN (Status)",
  „Odometer", „Start Code", „Drive Line Type"…). Daje **bogatszy** zestaw niż karta:
  m.in. `secondary_damage`, `odometer_brand` („Actual"), `drive_line`, pełny `engine`, `loss`.
  Zweryfikowane na żywo (lot 45574140 → 2011 BMW 335I XDRIVE, 18+ pól).
- **Krytyk `kompletność-pól`:** wymagane pola niepuste (year, make, model, odometer,
  primary_damage, title, selling_branch); osobno flaguje **VIN zamaskowany** (anonimowo
  IAAI zwraca `...******`; pełny VIN wymaga konta).

### 🔵 `zdjęcia` → 🔴 `kompletność-zdjęć`
- **Agent:** `GET vis.iaai.com/dimensions?imageKeys={id}~SID` → `keys[]`; zapis do
  `iaai_vehicle_images` (`image_key` UNIQUE), `url` = resizer.
- **Krytyk:** liczba zdjęć = `len(keys[])`; próbka URL-i → HTTP 200 `image/jpeg`; brak duplikatów.

## Stan implementacji agenta `listingi` (zweryfikowany na żywym IAAI)
Kod: [`scraper/dzialy/01_pobieranie/listingi.py`](../../scraper/dzialy/01_pobieranie/listingi.py).
- **Parser działa** (potwierdzone na realnym HTML): listing = wiersz `.table-row-border`
  z `h4.heading-7 > a[name=salvage_id]`; pola w `.data-list__item`, gdzie etykieta jest
  w atrybucie `title="Etykieta: wartość"`. Poprawnie wyciąga ~25 pól/lot.
- ⚠️ **VIN jest MASKOWANY anonimowo** (`WBABD33454P******`, „Please log in as a buyer").
  Pełny VIN wymaga **konta IAAI** — przy obecnej decyzji (anonimowo) listingi dają VIN
  częściowy. Flaga `vin_masked`. Do decyzji: czy pełny VIN jest wymagany (→ konto), czy OK.
- ✅ **Paginacja ROZWIĄZANA (Playwright).** Wyszukiwarka IAAI to Knockout.js — strony
  ładowane przez POST `/Search` (nie `&page=N`). Agent steruje paginacją przeglądarką:
  liczy liczbę stron z ukrytego `ResultCount` (np. 7877 → 79 stron), klika numer strony
  (`#PageNumber{n}`) / „Next", czeka aż lista się zmieni. Zweryfikowane: 4 strony =
  400 unikalnych lotów, bez zapętleń (`str.1/79 → str.4/79`).
- 🔴 Krytyk `kompletność-listy` porównuje zebrane `total` z `ResultCount` IAAI i flaguje
  braki/luki/zapętlenia. (W teście z `--max-pages 4` słusznie zgłasza niekompletność.)
- ⚠️ Otwarte dla „całego IAAI": pojedyncze zapytanie zwraca tyle, ile `ResultCount` dla
  tego zapytania; jeśli IAAI ma twardy limit stron na zapytanie, pełne pokrycie wymaga
  iteracji po filtrach (np. po stanach/markach). Paginacja w obrębie zapytania — pewna.

## Źródła techniczne (wewnętrzne, z krok 1)
Endpointy i zachowanie IAAI: patrz [`research/report.md`](../../research/report.md) i
[`db/mapping.md`](../../db/mapping.md). IAAI **nie ma** oficjalnej dokumentacji API.

---

## 📄 ORYGINALNA dokumentacja potrzebna dla tych agentów

Wszyscy trzej agenci to **agenci scrapujący** — wspólny silnik techniczny to
**Playwright** (sterowanie przeglądarką: nawigacja, paginacja, render `#ProductDetailsVM`,
przechwyt sieci). To jest **ta jedna oryginalna dokumentacja**, na której opieramy dział:

- **Oficjalna dokumentacja Playwright (Python)** — pobrana i zapisana jako referencja:
  [`docs/refs/playwright-python.md`](../refs/playwright-python.md)
  (wersja **1.61.0**, źródło playwright.dev, stan 2026-06-29).

Kod agentów `listingi/szczegóły/zdjęcia` budujemy na tej referencji (sync API).

> Osobno (decyzje biznesowe, nie „dokumentacja"): zakres oferty (całe IAAI vs filtry),
> konto IAAI (anon/login), lista wymaganych pól, wymagania co do zdjęć. To ustalenia,
> nie oryginalny dokument — podasz w rozmowie.
