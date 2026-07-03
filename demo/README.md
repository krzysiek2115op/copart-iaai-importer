# Kredyt Kompas — demo wtyczki **IAAI Importer**

To repozytorium hostuje **działające demo** wtyczki. Klient klika w jeden link i w swojej
przeglądarce uruchamia się WordPress ze stylem strony **oraz wtyczką IAAI Importer**, która
sama tworzy podstronę **„Nasze auta"** z ofertą pojazdów (zdjęcia, filtry marka/rok/uszkodzenie,
karty, paginacja). Nic nie trzeba instalować — działa w przeglądarce (technologia *WordPress Playground*).

## ▶ Zobacz demo (kliknij)

**[► Otwórz demo „Nasze auta"](https://playground.wordpress.net/?blueprint-url=https://raw.githubusercontent.com/krzysiek2115op/iaai-importer-demo/main/blueprint.json)**

> Pełny link do wysłania klientowi:
> ```
> https://playground.wordpress.net/?blueprint-url=https://raw.githubusercontent.com/krzysiek2115op/iaai-importer-demo/main/blueprint.json
> ```

## Co widać w demie
- Podstrona **„Nasze auta"** utworzona automatycznie po włączeniu wtyczki i dodana do menu.
- **Karty pojazdów** ze zdjęciem, ceną „Buy Now", przebiegiem (km + mi), rodzajem uszkodzenia
  i plakietkami *Run & Drive* / *Key Available*.
- **Pasek filtrów** (marka, rok, uszkodzenie, sortowanie) + **paginacja**.
- Wygląd **dziedziczy motyw** strony (kolory/czcionki) — u klienta dopasuje się do jego szablonu.

## Ważne (to tylko prezentacja)
- Dane aut są **przykładowe** (atrapa), zdjęcia z `placehold.co` — żeby pokazać układ.
- Wersja w przeglądarce jest **tymczasowa**: po odświeżeniu strony demo startuje od nowa.
- W prawdziwym wdrożeniu auta pobiera automat (scraper) z **iaai.com**, a zdjęcia idą z serwerów IAAI.

## Zawartość repo
| Plik | Rola |
|------|------|
| `blueprint.json` | scenariusz startowy Playground (motyw + wtyczka + dane demo) |
| `iaai-importer.zip` | wtyczka WordPress (ta sama, którą dostaje klient) |
| `iaai-demo-seed.php` | mu-plugin: wstawia przykładowe auta i zezwala na obrazki demo |

---
*Demo generowane z prywatnego repo produktu. Kod źródłowy i dokumentacja wdrożeniowa — osobno.*
