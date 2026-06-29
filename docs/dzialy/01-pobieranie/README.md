# Dział 1 · POBIERANIE — agenci i krytycy

Cel działu: zaciągnąć z IAAI **całą bieżącą ofertę** (tryb `full`) i potem **nowe
pojazdy live** (tryb `live`) — dane + zdjęcia — i zapisać do nowej bazy.
Zasada: **1 agent : 1 krytyk**.

Dokumentacja działu: [`dostep.md`](dostep.md) · [`listingi.md`](listingi.md) ·
[`szczegoly.md`](szczegoly.md) · [`zdjecia.md`](zdjecia.md)

---

## 🔵 Agent `listingi` → 🔴 Krytyk `kompletność-listy`
**Agent robi:**
- Iteruje strony wyszukiwarki IAAI (renderowane server-side, ~106 lotów/stronę).
- Z każdej karty wyciąga `salvage_id`, `detail_url` i pola podstawowe (rok/marka/model,
  odometer, Buy Now, Run & Drive, Key).
- Obsługuje paginację do końca; w trybie `full` przechodzi całość, w `live` tylko nowe
  (po nowych ID / dacie sprzedaży od ostatniego przejścia).
- Wynik: kolejka `salvage_id` do dalszego przetworzenia + upsert pól podstawowych do `iaai_vehicles`.

**Krytyk sprawdza:**
- Czy paginacja doszła do końca (liczba stron × rozmiar ≈ deklarowana liczba wyników).
- Brak luk i duplikatów ID; jeśli luka → zleca ponowienie brakujących stron.

## 🔵 Agent `szczegóły` → 🔴 Krytyk `kompletność-pól`
**Agent robi:**
- Dla każdego `salvage_id` pobiera **pełne** pola pojazdu i uzupełnia `iaai_vehicles`.
- ⚠️ Z analizy (krok 1): surowy HTML `/VehicleDetail` jest pusty (dane doładowywane JS).
  Dwie drogi — do potwierdzenia oryginałem/decyzją (patrz [`szczegoly.md`](szczegoly.md)):
  (a) brać komplet z karty wyszukiwarki (ma większość pól), (b) renderować stronę
  przeglądarką (Playwright), by dostać `#ProductDetailsVM`.

**Krytyk sprawdza:**
- Czy wymagane pola (VIN, make, model, year, odometer, damage, title) są niepuste.
- Rekordy z brakami flaguje do ponowienia.

## 🔵 Agent `zdjęcia` → 🔴 Krytyk `kompletność-zdjęć`
**Agent robi:**
- `GET https://vis.iaai.com/dimensions?imageKeys={salvage_id}~SID` → `keys[]`.
- Zapis do `iaai_vehicle_images` (`image_key`, `seq`, `width`, `height`, `url` = resizer).
- Opcjonalnie pobranie plików / import do mediów WP (zależnie od decyzji, patrz [`zdjecia.md`](zdjecia.md)).

**Krytyk sprawdza:**
- Czy liczba zapisanych zdjęć = `len(keys[])`; próbka URL-i zwraca HTTP 200 `image/jpeg`.
- Brak duplikatów `image_key`.

---

## 📄 Jakiej ORYGINALNEJ dokumentacji potrzebuję od Ciebie (dla tego działu)
Każdy plik `dok` powinien opierać się na oryginale — niżej co konkretnie potrzebne.
Pozycje oznaczone „(sam zdobędę)" pobiorę samodzielnie.

1. **Zakres oferty** (do `listingi.md`): czy łapiemy **całe IAAI**, czy filtrujemy
   (marki / stany / typ aukcji / tylko z Buy Now)? Jeśli filtry — lista/parametry.
2. **Konto IAAI** (do `dostep.md`): czy działamy **anonimowo**, czy masz **konto IAAI**
   (część danych/cen bywa za logowaniem)? Jeśli konto — jak ma być używane.
3. **Lista pól** (do `szczegoly.md`): które pola pojazdu są **wymagane** dla klienta
   (data dictionary / lista pól) — żeby krytyk wiedział, co jest „kompletne".
4. **Wymagania co do zdjęć** (do `zdjecia.md`): ile zdjęć, jaka rozdzielczość,
   **pobierać i trzymać u nas** czy linkować z `vis.iaai.com`?
5. **Oficjalna dokumentacja IAAI**, jeśli ją masz (dane dostępowe/umowa/ToS).
6. *(sam zdobędę)* oficjalny **WordPress Plugin Handbook** (CPT, media, nonce) —
   to do późniejszych działów, nie musisz dostarczać.

> Daj oryginały do pkt 1–5, a uzupełnię `dostep.md / listingi.md / szczegoly.md /
> zdjecia.md` ich treścią i dopnę kod agenta `listingi`.
