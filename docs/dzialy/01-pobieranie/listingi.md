# listingi.md — agent „listingi" (dział pobieranie)

> Status: **szkielet** — uzupełnić oryginałem (pkt 1 z README działu: zakres oferty).

## Co już wiemy
- Strona wyników wyszukiwarki: ~106 lotów/stronę, każda karta ma `salvage_id`,
  `detail_url` + pola podstawowe (rok/marka/model, odometer, Buy Now, Run & Drive, Key).
- Paginacja przez parametry URL wyszukiwarki.

## Czego potrzebuję od Ciebie (oryginał)
- **Zakres:** całe IAAI czy filtry? (marki / stany / typ aukcji / tylko Buy Now / inne).
- Jeśli filtry — dokładne wartości/parametry, które mają trafić do zapytania wyszukiwarki.

## Logika agenta (do dopisania kodu po ustaleniu zakresu)
- `full`: iteruj wszystkie strony zakresu → zbierz `salvage_id` → upsert pól podstawowych.
- `live`: tylko nowe ID od ostatniego przejścia (kursor po dacie/ID).

## Krytyk „kompletność-listy"
- Liczba stron × rozmiar ≈ deklarowana liczba wyników; brak luk/duplikatów ID;
  brakujące strony → ponowienie.
