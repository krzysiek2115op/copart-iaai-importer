# Architektura (v0.30 — dwa źródła: IAAI + Copart)

> **Decyzja (aktualna):** Copart **przywrócony jako DRUGIE ŹRÓDŁO** obok IAAI. Nowa baza ma
> kolumnę `source` (`iaai` / `copart`), klucz główny to para `(source, salvage_id)`; wtyczka
> pokazuje plakietkę źródła i filtr. Copart mocniej broni się przed automatami (Cloudflare),
> a pełne dane/zdjęcia zwykle wymagają **konta Member** — sesja przez zmienną `COPART_COOKIES`;
> realne, ciągłe pobieranie walidujemy na VPS (tak jak IAAI). Bez konta system działa na samym
> IAAI. (Wcześniejsza decyzja „v0.2 — Copart usunięty" jest nieaktualna; analiza w tagu `v0.1.0`.)

## Schemat (wg rysunku)

```
        STRONA INTERNETOWA W WORDPRESS
                    ⇅ json
                  PLUGIN
                    ⇅ json
                  DZIAŁY  ◄──── AJAX (live) ──── STARE BAZY: iaai.com + copart.com
                    ⇅                                      ⇅ JSON
              NOWA BAZA DANYCH ◄────────────────── (sync/import, --source iaai|copart)
        (rekordy z obu źródeł; kolumna source rozróżnia IAAI/Copart)
```

Kluczowe: **plugin łączy się tylko z DZIAŁAMI i ze stroną WordPress — NIE z bazą danych.**
Z **nową bazą** połączone są **DZIAŁY**. Oba źródła (IAAI, Copart) trafiają do **jednej** nowej
bazy; rozróżnia je kolumna `source`, a klucz `(source, salvage_id)` chroni przed kolizją numerów
lotów między serwisami.

## Komponenty i przepływ danych

| Komponent | Rola |
|---|---|
| **STARE BAZY (iaai.com + copart.com)** | Dwa źródła — dane i zdjęcia pojazdów pobierane z IAAI oraz Copart. Copart wymaga sesji Member (`COPART_COOKIES`). |
| **NOWA BAZA DANYCH** | Nasza docelowa baza. Zawiera dane z **obu** źródeł (kolumna `source`), zaimportowane i zbierane na bieżąco („live"). Klucz `(source, salvage_id)`. Połączona z **działami** (nie bezpośrednio z pluginem). |
| **DZIAŁY** | Centralny węzeł: pobiera dane **live** z IAAI i Copart (**AJAX**, osobny przebieg per źródło: `--source iaai\|copart`), czyta/zapisuje **nową bazę** i wymienia **JSON** z pluginem. |
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

## Przepływ: baza → strona WordPress (cel końcowy)
Po wpięciu wtyczki dane z bazy mają być widoczne na stronie klienta:

```
Agenci → wpis do bazy (wp_iaai_vehicles + wp_iaai_vehicle_images)
  → dział publikacja: rekord = wpis WordPressa (CPT „Pojazd")
    → dział front i media: szablon listy + szablon pojazdu + galeria (vis.iaai.com)
      → odwiedzający widzi auta na stronie (lista + szczegóły + filtry)
```

- **Lista pojazdów** — kafelki: zdjęcie + rok/marka/model, przebieg, Run & Drive, Buy Now.
- **Szczegóły pojazdu** — galeria zdjęć (URL z `vis.iaai.com/resizer`) + wszystkie pola.
- **Nowe auto live** → po przejściu działów pojawia się na stronie **automatycznie**.
- Spójnie z architekturą: **plugin łączy się z działami i stroną WP** (nie z bazą wprost);
  działy czytają bazę i podają pluginowi gotowe dane (JSON), plugin renderuje.

## Zakres zasilania nowej bazy (decyzja)
Nowa baza jest zasilana **dwojako**:
1. **Backfill (historia)** — jednorazowy zaciąg istniejących aukcji z IAAI na starcie.
2. **Live** — ciągłe łapanie nowych pojazdów pojawiających się na bieżąco.

Dział **pobieranie** ma więc dwa tryby: `full` (backfill) i `live`/`incremental`.

**Ustalono:** „historia" = **cała bieżąca oferta IAAI** — backfill (`full`) zaciąga
WSZYSTKIE aktualnie wystawione loty z publicznej wyszukiwarki, a potem `live`
dokłada nowe na bieżąco. **Bez płatnych API third-party.** (Głębokie archiwum
sprzedanych aut sprzed lat — świadomie poza zakresem; nie jest publiczne.)

## Otwarte pytania do doprecyzowania
- **„Działy"** — w jakiej technologii? (osobny serwis/backend automatyzacji, czy warstwa w obrębie WP?). Pełnią rolę warstwy pośredniej między IAAI/bazą a pluginem.
- Silnik **nowej bazy** — MySQL (natywny dla WP) czy osobna baza?
- Częstotliwość synchronizacji live (interwał AJAX / nasłuch SignalR).
