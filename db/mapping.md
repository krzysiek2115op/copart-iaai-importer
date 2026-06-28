# Mapowanie: rekord IAAI → nowa baza (wierna kopia)

Nowa baza odwzorowuje **rekord/kartę listingu IAAI 1:1**. Agenci łapią każdy nowy
pojazd pojawiający się live i wpisują dane + zdjęcia.

## Źródła (z analizy live, krok 1 + 3)
- **Wyniki wyszukiwania** `https://www.iaai.com/Search?...` — karty listingów renderowane
  server-side (~106 pojazdów/stronę). To realny punkt łapania **nowych live** listingów
  (strona szczegółów doładowuje dane skryptem — surowy HTML jest pusty).
- **Zdjęcia:** `https://vis.iaai.com/dimensions?imageKeys={salvageId}~SID` → `keys[]`;
  pełny obraz: `https://vis.iaai.com/resizer?imageKeys={K}&width=&height=`.

## `iaai_vehicles` ← karta/rekord IAAI
| Kolumna | Pole IAAI |
|---|---|
| salvage_id | ID lotu (`/VehicleDetail/{id}~US`) |
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

## Klucze (anty-duplikacja)
- **salvage_id** — pojazd już w bazie? sprawdź ten klucz.
- **image_key** (UNIQUE) — zdjęcie już pobrane? nie dubluj.

To jedyne dodatki ponad „surową" strukturę IAAI; reszta pól = jak u nich.
`captured_at` służy tylko do wykrywania, co jest nowe.
