# szczegoly.md — agent „szczegóły" (dział pobieranie)

> Status: **szkielet** — uzupełnić oryginałem (pkt 3 z README działu: lista pól).

## Co już wiemy
- Pełny rekord IAAI to obiekt `inventory` (z `#ProductDetailsVM`) — schemat w `db/mapping.md`.
- ⚠️ Surowy HTML `/VehicleDetail/{id}` jest **pusty** (dane doładowywane JS).
  Dwie drogi pozyskania kompletu pól:
  - **(a)** z karty wyszukiwarki — ma większość pól, bez przeglądarki, szybkie.
  - **(b)** render przeglądarką (Playwright) → `#ProductDetailsVM` — pełne pola, wolniejsze.

## Czego potrzebuję od Ciebie (oryginał)
- **Które pola są wymagane** dla klienta (data dictionary / lista pól) — to definiuje,
  co krytyk uzna za „kompletne", i przesądza wybór drogi (a)/(b).

## Krytyk „kompletność-pól"
- Wymagane pola niepuste (np. VIN, make, model, year, odometer, damage, title).
- Braki → flaga do ponowienia (ew. przełączenie na drogę (b) dla danego lotu).
