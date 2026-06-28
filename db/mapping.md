# Mapowanie pól: IAAI → nowa baza

Źródła danych (z kroku 1, patrz [../research/report.md](../research/report.md)):
- **`#ProductDetailsVM.inventory`** (osadzony JSON w `VehicleDetail/{salvageId}~US`)
- **`vis.iaai.com/dimensions?imageKeys={salvageId}~SID`** → `keys[]` (zdjęcia)

## `iaai_vehicles` ← `inventory`
| Kolumna | Pole źródłowe |
|---|---|
| salvage_id | `salvageId` |
| item_id | `itemId` |
| stock_number | `stockNumber` |
| vin | `vin` |
| year / make / model / series | `year` / `make` / `model` / `series` |
| body_style | `bodyStyleName` |
| engine_info / engine_size | `engineInfo` / `engineSize` |
| cylinders | `cylinders` |
| fuel_type | `fuelTypeDesc` |
| transmission | `transmissionDesc` |
| drive_line | `driveLineTypeDesc` |
| drives | `drives` |
| color / interior_color | `colorDesc` / `interiorColor` |
| odometer_value / _uom / _brand | `odoValue` / `odoUoM` / `odoBrand` |
| primary_damage / secondary_damage | `primaryDamageDesc` / `secondaryDamageDesc` |
| loss_type | `lossTypeDesc` |
| title_brand / title_state | `titleBrand` / `certState` |
| keys_present / key_fob | `keys` / `keyFOB` |
| airbags_count / airbag_state | `noOfAirbags` / `airbagState` |
| branch_id | `branchId` |
| src_created_at / src_modified_at | `createdDateTime` / `modifiedDateTime` |
| src_version_id | `versionId` |

## `iaai_branches` ← `inventory` (pola lokalizacji)
`branchId, branchNumber, locName/name, address, city, state, zip, phone, locLatitude, locLongitude, isOffsite`

## `iaai_vehicle_images` ← `dimensions.keys[]`
| Kolumna | Pole |
|---|---|
| image_key | `K` |
| seq | `IN` |
| width / height | `W` / `H` |
| is_360 | z `Image360Ind` / `Videos` |

Pełny obraz pobierany na żądanie: `https://vis.iaai.com/resizer?imageKeys={K}&width=&height=`.

## `iaai_auctions` ← `inventory` + live (SignalR `/timedauctionhub`)
`auctionId, timedAuctionIndicator, timedAuctionCloseDateTime, buyNowIndicator, buyNowSold` + `current_bid`/`bid_count` aktualizowane live.

## Uwagi
- `raw_hash` = SHA1 całego `#ProductDetailsVM` — wykrywanie zmian (dział **synchronizacja**) bez porównywania pól.
- `iaai_raw_payloads` trzyma surowy JSON — pozwala działowi **audyt** wykryć błędy mapowania i ponownie przetworzyć dane bez ponownego pobierania z IAAI.
- `status` (active/sold/removed) ustawiany przez dział **synchronizacja** na podstawie obecności lotu w kolejnych pobraniach.
- Wiele pól w teście kroku 1 było `null` (lot zamknięty) — przy aktywnym locie są wypełnione; typy kolumn to uwzględniają (NULL-able).
