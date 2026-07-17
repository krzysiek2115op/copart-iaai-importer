# Kredyt Kompas — demo wtyczki **IAAI Importer**

To repozytorium hostuje **działające demo**. Klient klika w jeden link i w swojej przeglądarce
uruchamia się strona **Kredyt Kompas** (Start, Kredyty hipoteczne, Kalkulator, O nas, FAQ, Kontakt)
z wtyczką **IAAI Importer** — w górnym menu pojawia się podstrona **„Nasze auta"** z ofertą pojazdów
(zdjęcia, filtry marka/rok/uszkodzenie, karty, paginacja). Nic nie trzeba instalować — działa
w przeglądarce (technologia *WordPress Playground*).

## ▶ Zobacz demo (kliknij)

**[► Otwórz demo Kredyt Kompas](https://playground.wordpress.net/?blueprint-url=https://raw.githubusercontent.com/krzysiek2115op/iaai-importer-demo/main/blueprint.json)**

> Pełny link do wysłania klientowi:
> ```
> https://playground.wordpress.net/?blueprint-url=https://raw.githubusercontent.com/krzysiek2115op/iaai-importer-demo/main/blueprint.json
> ```

## Co widać w demie
- **Strona Kredyt Kompas** z prawdziwymi podstronami, stroną główną „Start".
- W **górnym menu** podstrona **„Nasze auta"** utworzona przez wtyczkę — klikalna.
- **Karty pojazdów** ze zdjęciem, ceną „Buy Now", przebiegiem (km + mi), rodzajem uszkodzenia
  i plakietkami *Run & Drive* / *Key Available*.
- **Pasek filtrów** (marka, rok, uszkodzenie, sortowanie) + **paginacja**.

## Ważne (to tylko prezentacja)
- Dane aut są **przykładowe** (atrapa), zdjęcia z `placehold.co` — żeby pokazać układ.
- Wygląd renderuje czysty motyw blokowy (Twenty Twenty-Five); u klienta wtyczka dopasuje się do jego motywu.
- Wersja w przeglądarce jest **tymczasowa**: po odświeżeniu demo startuje od nowa.
- W prawdziwym wdrożeniu auta pobiera automat (scraper) z **iaai.com**, a zdjęcia idą z serwerów IAAI.

## Zawartość repo
| Plik | Rola |
|------|------|
| `blueprint.json` | scenariusz startowy Playground (motyw + wtyczka + treści + dane demo) |
| `iaai-importer.zip` | wtyczka WordPress (ta sama, którą dostaje klient) |
| `iaai-demo-seed.php` | mu-plugin: odtwarza strony Kredyt Kompas, menu, auta |
| `kredyt-kompas-content.php` | treści podstron Kredyt Kompas |

---
*Demo generowane z prywatnego repo produktu. Kod źródłowy i dokumentacja wdrożeniowa — osobno.*
