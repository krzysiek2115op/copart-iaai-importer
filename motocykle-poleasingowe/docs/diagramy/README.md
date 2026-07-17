<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Diagramy plugin-2 (draw.io)

Pliki `.drawio` — format natywny [draw.io / diagrams.net](https://www.drawio.com). Edytowalne w:
- wtyczce **VS Code „Draw.io Integration"** (`hediet.vscode-drawio`) — wystarczy otworzyć plik,
- w przeglądarce na [app.diagrams.net](https://app.diagrams.net) (Otwórz → wskaż plik),
- w aplikacji desktop draw.io.

| Plik | Dla kogo | Zawartość |
|---|---|---|
| `plugin2-nietechniczny.drawio` | klient / osoby nietechniczne | prosty przepływ: portal → automat → baza → strona WWW |
| `plugin2-techniczny.drawio` | zespół techniczny | architektura: scraper (działy 1A–7) → MySQL `polea_*` → wtyczka WP; protokoły, cache, cron |
| `plugin2-schema-bazy.drawio` | baza danych | ERD: `polea_motocykle` 1:N `polea_zdjecia`, klucze, indeksy, ON DELETE CASCADE |

## Eksport do obrazu (PNG/SVG)
W wtyczce VS Code: otwórz plik → menu (trzy kropki) → **Export** → PNG/SVG.
W diagrams.net: **File → Export as → PNG/SVG**.
