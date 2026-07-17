# Dział 5 · AUDYT DANYCH — dokumentacja działu

> Jeden dział = jedna dokumentacja. 1 agent : 1 krytyk.

Cel: ostatnia bramka jakości przed publikacją — odrzucić rekordy niepoprawne
(złe typy/zakresy, brak wymaganych pól, bzdurne wartości).

Oryginał: [`docs/refs/json-schema.md`](../refs/json-schema.md) (JSON Schema draft 2020-12).

### 🔵 `walidacja` → 🔴 `poprawność`  ✅ zaimplementowany
Kod: [`scraper/dzialy/05_audyt/walidacja.py`](../../scraper/dzialy/05_audyt/walidacja.py).
Schemat (źródło prawdy, osobny plik):
[`scraper/dzialy/05_audyt/vehicle.schema.json`](../../scraper/dzialy/05_audyt/vehicle.schema.json)
— `walidacja.py` wczytuje go z dysku; można edytować reguły bez ruszania kodu
(gdy pliku brak/uszkodzony → minimalny schemat awaryjny + ostrzeżenie).
- **Agent:** waliduje rekord wg **JSON Schema** pojazdu (typy, zakresy: rok 1900–2027,
  przebieg 0–2 000 000, VIN regex z maską, status enum) + **reguły biznesowe**
  (rok ≤ bieżący+1, przebieg z jednostką). Oznacza `_audit_ok` + `_audit_errors`.
  `additionalProperties: true` — pola pomocnicze (vpic, odometer_km…) dozwolone.
- **Krytyk `poprawność`:** meta-kontrola — sprawdza, że walidator **wyłapuje** celowo
  błędny rekord i **przepuszcza** poprawny (audyt nie jest „ślepy").
- Zweryfikowane: poprawny przechodzi; błędny (`year:3000, odometer:-5, vin:IOQ`) złapany.

## Przepływ
`synchronizacja` → `walidacja` (odrzuca niepoprawne) → dział 6 (bezpieczeństwo).
