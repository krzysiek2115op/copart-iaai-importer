# Referencja: JSON Schema — oryginał dla działu „audyt danych"

> Z oficjalnej dokumentacji json-schema.org (Understanding JSON Schema). Aktualny
> draft: **2020-12**. Walidator (Python): biblioteka `jsonschema`. Stan: 2026-06-29.

## Kluczowe słowa walidacji
- `type` — typ (string, number, integer, object, array, boolean, null)
- `properties` — schematy pól obiektu
- `required` — pola wymagane
- `minimum` / `maximum` — zakres liczb
- `minLength` / `maxLength` — długość stringa
- `pattern` — regex dla stringa
- `enum` — dozwolony zbiór wartości
- `format` — walidacja semantyczna (date, uri, email…)

## Przykład
```json
{
  "type": "object",
  "properties": {
    "salvage_id": {"type": "integer", "minimum": 1},
    "year": {"type": ["integer", "null"], "minimum": 1900, "maximum": 2027},
    "odometer": {"type": ["integer", "null"], "minimum": 0},
    "status": {"enum": ["active", "sold", "removed"]}
  },
  "required": ["salvage_id"]
}
```

## Zastosowanie (dział audyt)
Agent `walidacja` sprawdza każdy rekord względem schematu pojazdu (typy, zakresy,
wymagane pola) + reguły biznesowe (rok ≤ bieżący+1, przebieg w sensownym zakresie).
`additionalProperties: true` — pola pomocnicze (vpic, odometer_km…) są dozwolone.
