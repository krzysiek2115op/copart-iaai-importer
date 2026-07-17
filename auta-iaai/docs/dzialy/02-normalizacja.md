# Dział 2 · NORMALIZACJA — dokumentacja działu

> Jeden dział = jedna dokumentacja. 1 agent : 1 krytyk.

Cel: ujednolicić i zwalidować surowe dane z działu „pobieranie" przed dalszym
przetwarzaniem — VIN i jednostki/formaty.

Oryginał techniczny: [`docs/refs/vin-nhtsa.md`](../refs/vin-nhtsa.md)
(ISO 3779 / FMVSS 565 + NHTSA vPIC API).

## Agenci i krytycy

### 🔵 `VIN` → 🔴 `poprawność-VIN`  ✅ zaimplementowany
Kod: [`scraper/dzialy/02_normalizacja/vin.py`](../../scraper/dzialy/02_normalizacja/vin.py).
- **Agent:** waliduje format (17 znaków, bez I/O/Q), liczy **cyfrę kontrolną** (ISO 3779,
  tylko pełne VIN-y), wykrywa **maskowanie** (`...******`), dekoduje przez **vPIC** →
  kanoniczne `make/model/year/body/fuel/cylinders/drive` i krzyżowo sprawdza ze scrapem.
- **Klucz:** vPIC dekoduje **nawet zamaskowany VIN** (maska psuje tylko numer seryjny).
  Zweryfikowane: `WBAPL5G59BN******` → BMW 335i, 2011, Sedan, 6 cyl, AWD.
- **Krytyk `poprawność-VIN`:** format ok, cyfra kontrolna (pełne VIN), flaga maski,
  zgodność marki scrap↔vPIC, błędy dekodowania.

### 🔵 `jednostki` → 🔴 `jakość-jednostek`  ✅ zaimplementowany
Kod: [`scraper/dzialy/02_normalizacja/jednostki.py`](../../scraper/dzialy/02_normalizacja/jednostki.py).
- **Agent:** przebieg mi/km → dokłada `odometer_km`; ceny „$1,300 USD" → `1300.0`
  (buy_now, current_bid); data „Mon Jun 29…" → ISO `YYYY-MM-DD` (sale_date);
  tytuł „SALVAGE (Missouri)" → `title_brand` + `title_state`; klucz → `key_present` (bool).
  Zweryfikowane: 142447 mi → 229246 km; SALVAGE/Missouri; key_present=true.
- **Krytyk `jakość-jednostek`:** przebieg ma jednostkę i przeliczenie km; ceny są liczbami;
  `sale_date` w formacie ISO.

## Przepływ
`pobieranie` (JSONL) → `VIN` → `jednostki` → dalej do działu 3 (deduplikacja).
Każdy agent czyta JSONL i zapisuje wzbogacony JSONL (podpięcie do bazy = technikalia na potem).
