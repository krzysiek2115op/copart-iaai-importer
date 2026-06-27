# Architektura (v0.2 — tylko IAAI)

> **Decyzja:** Copart **usunięty z planu** — cała domena jest za Imperva Incapsula
> (brak legalnego, anonimowego dostępu). Pełna analiza Copart pozostaje w historii
> repo (tag `v0.1.0`, `research/`). Skupiamy się wyłącznie na **iaai.com**.

## Schemat (wg rysunku)

```
        STRONA INTERNETOWA W WORDPRESS
                    ⇅ json
                  PLUGIN
                    ⇅ json
                  DZIAŁY  ◄──── AJAX (live) ──── STARA BAZA DANYCH (iaai.com)
                    ⇅                                      ⇅ JSON
              NOWA BAZA DANYCH ◄────────────────── (sync/import)
        (nowe informacje z iaai.com)
```

Kluczowe: **plugin łączy się tylko z DZIAŁAMI i ze stroną WordPress — NIE z bazą danych.**
Z **nową bazą** połączone są **DZIAŁY**.

## Komponenty i przepływ danych

| Komponent | Rola |
|---|---|
| **STARA BAZA DANYCH (iaai.com)** | Źródło — dane i zdjęcia pojazdów pobierane z IAAI. |
| **NOWA BAZA DANYCH** | Nasza docelowa baza. Zawiera dane zaimportowane z IAAI **oraz** dane zbierane na bieżąco („live") przez automatyzację. Połączona z **działami** (nie bezpośrednio z pluginem). |
| **DZIAŁY** | Centralny węzeł: pobiera dane **live** z IAAI (**AJAX**), czyta/zapisuje **nową bazę** i wymienia **JSON** z pluginem. |
| **PLUGIN (WordPress)** | Most: łączy się **tylko** z działami (JSON) i ze stroną WP (JSON). **Nie ma dostępu do bazy bezpośrednio.** |
| **STRONA WORDPRESS** | Front klienta — wyświetla dane pojazdów (JSON z pluginu). |

### Przepływy
1. **IAAI ⇄ JSON ⇄ Nowa baza** — import początkowy + synchronizacja; automatyzacja dokłada dane live.
2. **IAAI → AJAX → Działy** — pobieranie danych na żywo (np. status licytacji, nowe loty).
3. **Działy ⇄ Nowa baza** — działy czytają/zapisują dane w nowej bazie.
4. **Działy ⇄ json ⇄ Plugin** — działy dostarczają dane pluginowi.
5. **Plugin ⇄ json ⇄ Strona WP** — prezentacja danych klientowi (plugin nie dotyka bazy).

## Techniczne źródła danych IAAI (z kroku 1)

- **Dane pojazdu:** strona `https://www.iaai.com/VehicleDetail/{salvageId}~US` → osadzony JSON `#ProductDetailsVM` (obiekt `inventory`).
- **Zdjęcia:** `GET https://vis.iaai.com/dimensions?imageKeys={salvageId}~SID` (lista) + `GET https://vis.iaai.com/resizer?imageKeys={K}&width=&height=` (pełny JPEG).
- **Live (licytacja):** SignalR hub `wss .../timedauctionhub` — kandydat do warstwy AJAX/live „Działy".

Szczegóły i próbki: [`../research/report.md`](../research/report.md).

## Otwarte pytania do doprecyzowania
- **„Działy"** — w jakiej technologii? (osobny serwis/backend automatyzacji, czy warstwa w obrębie WP?). Pełnią rolę warstwy pośredniej między IAAI/bazą a pluginem.
- Silnik **nowej bazy** — MySQL (natywny dla WP) czy osobna baza?
- Częstotliwość synchronizacji live (interwał AJAX / nasłuch SignalR).
