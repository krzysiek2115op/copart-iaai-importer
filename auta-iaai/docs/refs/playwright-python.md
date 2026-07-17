# Referencja: Playwright (Python) — oryginał dla działu „pobieranie"

> Pobrane z oficjalnej dokumentacji **playwright.dev** (2026-06-29).
> Wersja: **playwright == 1.61.0** (PyPI, wyd. 2026-06-29). Python ≥ 3.8.
> Źródła: [intro](https://playwright.dev/python/docs/intro) ·
> [library](https://playwright.dev/python/docs/library) ·
> [locators](https://playwright.dev/python/docs/locators) ·
> [network](https://playwright.dev/python/docs/network)

To jest „jedna oryginalna dokumentacja" działu 1. Kod agentów `listingi/szczegóły/zdjęcia`
opieramy na poniższym API (sync).

## Instalacja
```bash
pip install playwright          # sama biblioteka (bez pytest)
playwright install chromium     # pobranie binarki przeglądarki
# aktualizacja:  pip install -U playwright  &&  playwright install chromium
```

## Bazowy szkielet (sync API) + custom UA/locale
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent="Mozilla/5.0 ...", locale="en-US")
    page = context.new_page()
    page.goto("https://www.iaai.com/Search?...", wait_until="domcontentloaded")
    # ... ekstrakcja ...
    browser.close()
```
- `wait_until`: `"domcontentloaded"` | `"load"` | `"networkidle"`.
- Playwright ma **auto-waiting** — zwykle nie trzeba ręcznych `sleep`.
- `headless=False` do podglądu w czasie developmentu.

## Lokatory i ekstrakcja danych (agent `listingi`/`szczegóły`)
```python
# liczba elementów
n = page.locator("div.search__result").count()

# iteracja po wszystkich pasujących + tekst/atrybut
for card in page.locator("div.search__result").all():
    title = card.locator("h4 a").text_content()
    href  = card.locator("h4 a").get_attribute("href")   # -> /VehicleDetail/{id}~US

# preferowane lokatory „user-facing":
page.get_by_role("listitem"); page.get_by_text("Buy Now"); page.get_by_label(...)

# masowa ekstrakcja przez JS:
texts = page.locator("li").evaluate_all("els => els.map(e => e.textContent)")
```
- ⚠️ Lokatory są **strict** — operacja rzuci wyjątek, gdy pasuje >1 element;
  używaj `.first`, `.nth(i)`, `.all()` albo filtrowania.

## Przechwytywanie odpowiedzi sieciowych (agent `szczegóły` → `#ProductDetailsVM`, `zdjęcia` → dimensions)
```python
# A) nasłuch wszystkich odpowiedzi
page.on("response", lambda r: print(r.status, r.url))

# B) czekaj na konkretną odpowiedź JSON wywołaną akcją/nawigacją
with page.expect_response("**/dimensions*") as info:
    page.goto(detail_url)
resp = info.value
data = resp.json()          # JSON prosto z API IAAI (lista zdjęć)

# C) wzorce: glob "**/...", regex, albo predykat
import re
with page.expect_response(re.compile(r"/dimensions")) as info:
    page.goto(detail_url)
```

## Zastosowanie w naszych agentach
- **listingi:** `goto` na wyszukiwarkę → `locator(...).all()` → `salvage_id`, `detail_url`, pola karty → paginacja.
- **szczegóły:** `goto` na `/VehicleDetail/{id}` (render JS) → odczyt `#ProductDetailsVM`
  (locator/`text_content`) **lub** `expect_response` na wewnętrzne API danych.
- **zdjęcia:** dla danych statycznych z `vis.iaai.com` wystarczy `requests` (HTTP);
  Playwright używamy tam, gdzie potrzebny render/JS lub przejście challenge.
