# Mapowanie: rekord IAAI / Copart → nowa baza (wierna kopia)

Nowa baza odwzorowuje **kartę listingu 1:1** — z **dwóch** źródeł: IAAI oraz Copart. Agenci łapią
każdy nowy pojazd pojawiający się live i wpisują dane + zdjęcia. Rekordy obu źródeł żyją w tych
samych tabelach; rozróżnia je kolumna **`source`** (`iaai` / `copart`), a klucz główny to para
**`(source, salvage_id)`** (numery lotów IAAI i Copart mogą się pokrywać — para chroni przed kolizją).

## Źródła (z analizy live, krok 1 + 3)
- **Wyniki wyszukiwania** `https://www.iaai.com/Search?...` — karty listingów renderowane
  server-side (~106 pojazdów/stronę). To realny punkt łapania **nowych live** listingów
  (strona szczegółów doładowuje dane skryptem — surowy HTML jest pusty).
- **Zdjęcia:** `https://vis.iaai.com/dimensions?imageKeys={salvageId}~SID` → `keys[]`;
  pełny obraz: `https://vis.iaai.com/resizer?imageKeys={K}&width=&height=`.

## `iaai_vehicles` ← karta/rekord IAAI lub Copart
| Kolumna | Pole IAAI |
|---|---|
| salvage_id | ID lotu (`/VehicleDetail/{id}~US`) |
| source | źródło: `iaai` / `copart` (część klucza głównego) |
| stock_number / item_id / vin | Stock # / Item # / VIN |
| year / make / model / series | nagłówek (np. „2010 BMW 335I") |
| vehicle_type / body_style | Vehicle Type / Body Style |
| engine / cylinders / fuel_type / transmission / drive_line / color | Engine / Cylinders / Fuel Type / Transmission / napęd / Color |
| odometer / odometer_uom / odometer_brand | Odometer (np. „169,594 mi (Not Required/Exempt)") |
| primary_damage / secondary_damage / loss / title | Primary Damage / Secondary Damage / Loss / Title |
| run_and_drive | Run & Drive |
| key_available | Key |
| selling_branch / branch_id | Selling Branch |
| sale_date / lane / aisle | Sale Date / Lane / Aisle |
| buy_now / current_bid | Buy Now / Current Bid |
| detail_url | URL listingu |

## `iaai_vehicle_images` ← `dimensions.keys[]`
| Kolumna | Pole |
|---|---|
| image_key | `K` |
| seq / width / height | `IN` / `W` / `H` |
| url | zbudowany z `resizer?imageKeys={K}` |

## Copart → te same kolumny
Rekord Copart (endpoint `lotdetails/solr/{lot}`, klucze skrócone: `ln`, `lcy`, `mkn`, `lmg`,
`orr`, `dd`, `bnp`, `hb`…) mapuje moduł `scraper/dzialy/01_pobieranie/copart.py` na **te same
kolumny** co IAAI, ustawiając `source="copart"`. Zdjęcia Copart: `image_key = copart-{lot}-{i}`,
`seq = i`. Dalsze działy (normalizacja→dedup→audyt→json) są wspólne dla obu źródeł.

## Klucze (anty-duplikacja)
- **(source, salvage_id)** — PRIMARY KEY pojazdu; ten sam numer lotu w IAAI i Copart to dwa różne rekordy.
- **(source, image_key)** (UNIQUE) — zdjęcie już pobrane dla danego źródła? nie dubluj.

To jedyne dodatki ponad „surową" strukturę listingu; reszta pól = jak u źródła.
`captured_at` służy tylko do wykrywania, co jest nowe.
