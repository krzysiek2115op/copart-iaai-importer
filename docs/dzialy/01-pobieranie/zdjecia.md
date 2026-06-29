# zdjecia.md — agent „zdjęcia" (dział pobieranie)

> Status: **szkielet** — uzupełnić oryginałem (pkt 4 z README działu: wymagania zdjęć).

## Co już wiemy (przetestowane, krok 1)
- Lista zdjęć: `GET https://vis.iaai.com/dimensions?imageKeys={salvage_id}~SID` → `keys[]`
  (każdy: `K`, `W`, `H`, `IN`).
- Pełny obraz: `GET https://vis.iaai.com/resizer?imageKeys={K}&width=&height=` → JPEG (HTTP 200).
- Zapis do `iaai_vehicle_images` (`image_key` UNIQUE → brak duplikatów).

## Czego potrzebuję od Ciebie (oryginał)
- Ile zdjęć na pojazd (wszystkie czy limit)? Jaka rozdzielczość?
- **Pobierać i trzymać u nas** (import do mediów WP) czy **linkować** z `vis.iaai.com`?
  (wpływa na miejsce na dysku, szybkość, ryzyko wygaśnięcia linków).

## Krytyk „kompletność-zdjęć"
- Liczba zapisanych = `len(keys[])`; próbka URL-i → HTTP 200 `image/jpeg`; brak duplikatów.
