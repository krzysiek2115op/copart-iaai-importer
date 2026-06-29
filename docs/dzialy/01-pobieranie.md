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

### 🔵 `szczegóły` → 🔴 `kompletność-pól`
- **Agent:** dla każdego `salvage_id` pobiera pełne pola i uzupełnia `iaai_vehicles`.
  ⚠️ Surowy HTML `/VehicleDetail` jest pusty (dane doładowywane JS) → render przeglądarką.
- **Krytyk:** wymagane pola niepuste (VIN, make, model, year, odometer, damage, title); braki → ponów.

### 🔵 `zdjęcia` → 🔴 `kompletność-zdjęć`
- **Agent:** `GET vis.iaai.com/dimensions?imageKeys={id}~SID` → `keys[]`; zapis do
  `iaai_vehicle_images` (`image_key` UNIQUE), `url` = resizer.
- **Krytyk:** liczba zdjęć = `len(keys[])`; próbka URL-i → HTTP 200 `image/jpeg`; brak duplikatów.

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
