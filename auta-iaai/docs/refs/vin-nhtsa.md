# Referencja: VIN — oryginał dla działu „normalizacja"

> Standard VIN: **ISO 3779 / FMVSS Part 565**. Dekodowanie: oficjalne, darmowe
> **NHTSA vPIC API** (https://vpic.nhtsa.dot.gov/api/). Stan: 2026-06-29.

## Struktura VIN (17 znaków)
- Dozwolone znaki: `A–Z` i `0–9`, **bez I, O, Q** (by nie mylić z 1/0).
- Pozycje 1–3: **WMI** (producent), 4–9: **VDS** (opis, poz. 9 = cyfra kontrolna),
  10: rok modelowy, 11: zakład, 12–17: numer seryjny.

## Cyfra kontrolna (pozycja 9) — walidacja pełnego VIN
1. Transliteracja liter na liczby: A=1,B=2,C=3,D=4,E=5,F=6,G=7,H=8, J=1,K=2,L=3,M=4,
   N=5,P=7,R=9, S=2,T=3,U=4,V=5,W=6,X=7,Y=8,Z=9; cyfry = ich wartość.
2. Wagi pozycji 1–17: `8,7,6,5,4,3,2,10,0,9,8,7,6,5,4,3,2`.
3. `suma(wartość*waga) mod 11`. Wynik 10 → znak `X`. Musi równać się znakowi na poz. 9.

## Dekodowanie (NHTSA vPIC) — działa też dla VIN częściowych/zamaskowanych
```
GET https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/{VIN}?format=json&modelyear={ROK}
```
- `{VIN}` może być **częściowy** — brakujące znaki jako `*` (nasze zamaskowane VIN-y!).
- Zwraca m.in.: `Make`, `Model`, `ModelYear`, `BodyClass`, `FuelTypePrimary`,
  `DisplacementL`, `EngineCylinders`, `DriveType`, `ErrorCode`, `ErrorText`.
- ⚠️ Maska psuje tylko numer seryjny — **WMI+VDS (marka/model/rok/typ) dekodują się i tak**.
  Zweryfikowane: `WBAPL5G59BN******` + `modelyear=2011` → BMW 335i, 2011, Sedan.
  (Przy masce `ErrorText` zgłasza „Check Digit … does not calculate" — to normalne.)

## Zastosowanie w agentach
- **VIN:** walidacja formatu/długości/cyfry kontrolnej (pełne VIN-y), wykrycie maski,
  dekodowanie vPIC → kanoniczne `make/model/year/body` (krzyżowa kontrola ze scrapem).
- **jednostki:** osobny agent (przebieg mi/km, daty sprzedaży, ceny $ → liczby).
