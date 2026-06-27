# Importer aukcji Copart / IAAI → nowa baza (wtyczka WordPress)

Projekt: wtyczka WordPress importująca dane i zdjęcia pojazdów z **copart.com** i
**iaai.com** do nowej, wspólnej bazy danych, z zasilaniem danymi **live** i
prezentacją na stronie klienta.

## Status: krok 1 — analiza źródeł danych (v0.1.0)

Wykonano rozpoznanie API/źródeł danych obu serwisów. Pełne wyniki:
- [research/report.md](research/report.md) — dokumentacja: endpointy, zabezpieczenia, ocena prawna, szacunki rekordów
- [research/samples/](research/samples/) — realne próbki odpowiedzi
- [research/scraper/](research/scraper/) — kod scrapera (IAAI: Playwright; Copart: szkielet + rekomendacje legalne)

### Skrót ustaleń
- **IAAI** — dane pojazdu osadzone server-side w HTML (`#ProductDetailsVM`); zdjęcia przez `vis.iaai.com`; live przez SignalR `/timedauctionhub`.
- **Copart** — całość za Imperva Incapsula (brak dostępu anonimowego); legalnie: oficjalny CSV "Sales Data" lub licencjonowane API third-party.

> ⚠️ Techniczna dostępność ≠ zgoda prawna. Przed produkcją zweryfikować ToS serwisów.

## Wersjonowanie
Repo prywatne. Każdy większy krok = commit + tag (semver). Bieżący: `v0.1.0`.
