# Krok 1 — Analiza źródeł danych: IAAI i Copart

**Data analizy:** 2026-06-27
**Cel:** ustalić, czy iaai.com i copart.com udostępniają API / JSON / GraphQL / WebSocket / inne źródła danych o pojazdach, opisać zabezpieczenia i wskazać **legalne** drogi pozyskania danych (dane pojazdów + zdjęcia) do nowej bazy.

> ⚠️ Analiza oparta wyłącznie na **rzeczywistym ruchu sieciowym** (curl) i kodzie stron, nie na domysłach. Wszystkie próbki odpowiedzi w katalogu [`samples/`](samples/).

---

## 0. Metodyka

- Pobranie realnych odpowiedzi HTTP (`curl`) ze strony szczegółów pojazdu IAAI, strony głównej Copart oraz znanych endpointów JSON.
- Analiza HTML pod kątem osadzonego JSON, listy skryptów, hostów CDN obrazów, użycia SignalR/WebSocket.
- Test endpointów obrazów i API (status, content-type, treść).
- Sprawdzenie `robots.txt` obu serwisów.
- Rozeznanie oficjalnych/licencjonowanych źródeł danych (WebSearch).

---

## 1. IAAI (iaai.com) — DOSTĘPNE ✅

Strona testowa: `https://www.iaai.com/VehicleDetail/45293605~US` → **HTTP 200**, 357 KB, renderowanie **server-side** (dane wbudowane w HTML).
Uwaga: ten konkretny lot jest **zamknięty/pusty** (pola pojazdu wyzerowane), ale **zdjęcia nadal istnieją**, a schemat danych jest kompletny.

### 1.1. Dane pojazdu — osadzony JSON w HTML (główne źródło)

W HTML znajdują się bloki `<script type="application/json">`:

| id bloku | zawartość |
|---|---|
| **`#ProductDetailsVM`** | **pełny model pojazdu** (obiekt `inventory`): VIN, marka, model, rok, przebieg (odoValue/odoUoM/odoBrand), szkody (primary/secondaryDamage), tytuł (title/titleBrand), kluczyki (keys/keyFOB), liczba poduszek, lokalizacja (branchId, city, state, zip, lat/long), aukcja (auctionId, timedAuction...), linki do zdjęć (`keyImageLink`, `hdImageLinks`, `standardImageLinks`, `link360`, `engineSoundLink`), daty. Pełny zrzut schematu: [`samples/iaai_ProductDetailsVM_full.json`](samples/iaai_ProductDetailsVM_full.json) |
| `#GTMGABiddingEcommerceEventData` | dane e-commerce / licytacji do Google Tag Manager |
| `#GTMReportClickEventData`, `#GTMVisitRBClickEventData` | dane zdarzeń kliknięć |
| `#medalliaProps` | konfiguracja ankiet Medallia |

➡️ **Wniosek:** szczegóły pojazdu można pobrać **bez osobnego API** — wystarczy pobrać stronę `VehicleDetail/{id}~US` i sparsować `#ProductDetailsVM`.

### 1.2. Zdjęcia — publiczny serwis obrazów `vis.iaai.com` ✅

Hidden field `#hdnVisRootUrl` = `https://vis.iaai.com/`.

**a) Lista zdjęć (JSON):**
```
GET https://vis.iaai.com/dimensions?imageKeys={salvageId}~SID
```
Zwraca JSON: `DeepZoomInd`, `Image360Ind`/`Image360Url`, `Videos[]`, oraz tablicę `keys[]`, gdzie każdy element to jeden obraz:
`{"K":"45293605~SID~B518~S1~I1~RW2576~H1932~TH0","W":2576,"H":1932,"SID":45293605,"IN":1,...}`
Pełna próbka: [`samples/iaai_dimensions_45293605.json`](samples/iaai_dimensions_45293605.json) (ten lot ma kilkanaście zdjęć 2576×1932).

**b) Pobranie pełnego zdjęcia (JPEG):** — przetestowane, **HTTP 200, image/jpeg, ~218 KB**:
```
GET https://vis.iaai.com/resizer?imageKeys={K}&width=1024&height=768
```
gdzie `{K}` to wartość pola `K` z listy. Można podać dowolne width/height (oryginał to W×H z listy).

### 1.3. Dane LIVE (licytacja w czasie rzeczywistym) — SignalR ✅

Strona ładuje `microsoft-signalr 3.1.7` i łączy się z hubem:
```
WebSocket/SignalR hub: https://www.iaai.com/timedauctionhub
```
(plik `productDetailsSubscription.js`). To kanał aktualizacji licytacji na żywo (ceny/odliczanie). Do nasłuchu „live" w naszej automatyzacji.

### 1.4. Zabezpieczenia IAAI

- **Imperva Incapsula** obecny (`/_Incapsula_Resource`, skrypt o losowej nazwie), ale **przepuścił** zwykłe żądania `curl` z normalnym User-Agent — challenge JS **nie** został wymuszony. Realne ryzyko: rate-limiting / okresowe wymuszenie challenge przy większym wolumenie.
- TrustArc (zgody cookie), Evergage, Medallia, Kampyle — narzędzia marketingowe, bez znaczenia dla danych.

### 1.5. `robots.txt` IAAI
```
User-agent: *
Disallow: /MyAuctionCenter/
Disallow: /Login/*
Disallow: /Search
Disallow: /Marketing/Search
```
➡️ **`/VehicleDetail/` NIE jest zabronione** w robots.txt; **`/Search` jest zabronione**. (To nie zwalnia z ToS — patrz §3.)

---

## 2. Copart (copart.com) — ZABLOKOWANE 🚫

Strona główna i wszystkie endpointy: **HTTP 403 / 302** → **Imperva Incapsula** (`_Incapsula_Resource`, cookie `visid_incap_*`, `incap_ses_*`, obfuskowany skrypt `/vpwarding-...`). Blokowany jest nawet **`/robots.txt`** (403). Próbka challenge: [`samples/copart_incapsula_403.html`](samples/copart_incapsula_403.html).

### 2.1. Istniejące endpointy API (za WAF-em)

Front-end Copart to SPA zasilane JSON-em. Endpointy **istnieją**, ale wszystkie zwracają challenge Incapsula:

| endpoint | metoda | wynik anonimowo |
|---|---|---|
| `/public/data/lotdetails/solr/{lotNumber}` | GET | **302** → interstitial „Loading" (Incapsula) |
| `/public/lots/search-results` | POST (JSON) | **403** → iframe challenge Incapsula |

Bez przejścia challenge JS (realna przeglądarka + ciasteczka) lub logowania — **brak danych**.

### 2.2. Zabezpieczenia Copart

**Imperva Incapsula** w trybie agresywnym: JS challenge na każdym żądaniu anonimowym, ciasteczka sesyjne, obfuskowane skrypty, blokada `NOINDEX,NOFOLLOW`. Omijanie tego mechanizmu jest sprzeczne z ToS i potencjalnie z prawem (CFAA w USA) — **nie robimy tego**.

### 2.3. Legalne źródła danych Copart (bez omijania zabezpieczeń)

- **Oficjalny eksport CSV „Sales Data"** dla zalogowanych członków: `copart.com/content/us/en/buyer/sales/download-sales-data` — historia sprzedaży do pobrania po zalogowaniu na konto członkowskie. To **oficjalna, legalna** droga (wymaga konta).
- Brak publicznego, oficjalnego API REST/GraphQL.

---

## 3. Ocena legalności i rekomendacje

| | IAAI | Copart |
|---|---|---|
| Dane dostępne anonimowo | tak (server-side JSON + vis.iaai.com) | nie (Incapsula) |
| Oficjalne API | brak publicznego | brak publicznego |
| Oficjalny feed | – | CSV Sales Data (po zalogowaniu) |
| robots.txt dla detali | dozwolone (`/VehicleDetail/`) | niedostępny (403) |
| Zabezpieczenia | Incapsula (łagodny) | Incapsula (agresywny) |

**Uwaga prawna:** techniczna dostępność ≠ zgoda prawna. ToS obu serwisów zwykle zakazują automatycznego pobierania. Przed produkcją: weryfikacja ToS i ewentualna umowa/licencja. To jest decyzja biznesowa właściciela projektu.

**Rekomendowane drogi (od najbezpieczniejszej):**
1. **Licencjonowane API third-party** agregujące oba serwisy — legalne, gotowe, bez utrzymywania scraperów i walki z WAF:
   - auction-api.app, auctionsapi.com, apiauctions.io, carstat.dev, apibara.tech (Copart + IAAI: dane lotu, zdjęcia, historia sprzedaży po VIN).
2. **Copart:** oficjalny eksport CSV Sales Data z konta członkowskiego (jeśli mamy konto).
3. **IAAI:** własny scraper stron `VehicleDetail` (dozwolone w robots) + `vis.iaai.com` na zdjęcia — przy poszanowaniu rate-limit i ToS. Kod: [`scraper/iaai_scraper.py`](scraper/iaai_scraper.py).
4. **Copart przez przeglądarkę (Playwright):** technicznie możliwe (realna przeglądarka przechodzi challenge), ale **prawnie ryzykowne** (omijanie zabezpieczeń + ToS). Szkielet z ostrzeżeniem: [`scraper/copart_browser_skeleton.py`](scraper/copart_browser_skeleton.py) — **NIE uruchamiać produkcyjnie bez zgody prawnej**.

---

## 4. Szacunkowa liczba rekordów

- **Copart:** wg materiałów oficjalnych ~**400 000+** pojazdów dostępnych w danym momencie (globalnie).
- **IAAI:** rzędu **setek tysięcy** lotów; publiczny dzienny zrzut danych third-party (rebrowser/iaai-dataset) zawiera **667 681** rekordów dziennie.
- Historia sprzedaży (third-party API): zwykle **ostatnie ~3 lata** sprzedanych pojazdów po VIN.

(To szacunki na podstawie danych zewnętrznych; dokładnej liczby live nie da się policzyć bez przejścia paginacji/feedów, co jest ograniczane przez WAF/ToS.)

---

## 5. Lista endpointów (zwięźle)

```
# IAAI — dane pojazdu (server-side w HTML)
GET https://www.iaai.com/VehicleDetail/{salvageId}~US        -> HTML, blok #ProductDetailsVM (JSON)

# IAAI — zdjęcia
GET https://vis.iaai.com/dimensions?imageKeys={salvageId}~SID -> JSON (lista zdjęć, keys[])
GET https://vis.iaai.com/resizer?imageKeys={K}&width=W&height=H -> JPEG (pełne zdjęcie)

# IAAI — live (licytacja)
WSS  https://www.iaai.com/timedauctionhub                     -> SignalR hub (aktualizacje na żywo)

# Copart — istnieją, ale za Incapsula (403/302 anonimowo)
GET  https://www.copart.com/public/data/lotdetails/solr/{lotNumber}
POST https://www.copart.com/public/lots/search-results
# Copart — oficjalny feed (po zalogowaniu)
     https://www.copart.com/content/us/en/buyer/sales/download-sales-data  (CSV)
```

---

## 6. Następne kroki (propozycja)

1. **Decyzja biznesowo-prawna:** licencjonowane API third-party vs. własny scraping (ToS!).
2. Jeśli własny scraping IAAI: dopracować scraper o aktywny lot (z pełnymi danymi), zapis do nowej bazy + pobieranie zdjęć.
3. Copart: pozyskać konto członkowskie (CSV) lub wykupić API — bez omijania Incapsuli.
4. Zaprojektować schemat **nowej bazy** (wspólny dla IAAI+Copart) — mapowanie pól z `#ProductDetailsVM` i z feedu Copart.
5. Warstwa „live" (SignalR IAAI) → zasilanie nowej bazy na bieżąco.
