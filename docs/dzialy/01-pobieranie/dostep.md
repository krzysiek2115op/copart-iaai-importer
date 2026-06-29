# dostep.md — dostęp do IAAI (dział pobieranie)

> Status: **szkielet** — uzupełnić oryginałem (pkt 2 i 5 z README działu).

## Co już wiemy (z analizy, krok 1 — `research/report.md`)
- Wyszukiwarka: `https://www.iaai.com/Search?...` — wyniki renderowane server-side.
- Zdjęcia: `https://vis.iaai.com/dimensions?imageKeys={salvage_id}~SID` + `/resizer`.
- Zabezpieczenie: Imperva Incapsula — przy zwykłym User-Agent przepuszcza; ryzyko
  rate-limitu przy dużym wolumenie.
- `robots.txt`: `/VehicleDetail/` dozwolone, `/Search` zabronione dla crawlerów.

## Czego potrzebuję od Ciebie (oryginał)
- Czy działamy **anonimowo**, czy masz **konto IAAI** (login)? Jeśli konto — zasady użycia.
- Oficjalna dokumentacja/umowa IAAI, jeśli istnieje (limity, dozwolone użycie).

## Do ustalenia / zapisania tu po oryginale
- Nagłówki/User-Agent, polityka rate-limit (opóźnienia), obsługa ewentualnego challenge.
