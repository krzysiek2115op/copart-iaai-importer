# Importer aukcji Copart / IAAI → nowa baza (wtyczka WordPress)

Projekt: import danych i zdjęć pojazdów z **iaai.com** do nowej bazy danych,
z zasilaniem danymi **live** i prezentacją na stronie klienta przez wtyczkę WordPress.

> **Zmiana zakresu (v0.2):** Copart **usunięty z planu** — cała domena jest za
> Imperva Incapsula (brak legalnego, anonimowego dostępu). Skupiamy się na IAAI.
> Architektura: [docs/architecture.md](docs/architecture.md).

## 📋 Pełny status projektu: [STATUS.md](STATUS.md)
Cel, architektura, co gotowe, co do zrobienia, ustalenia — wszystko w jednym miejscu.

## 🧑‍💻 Instrukcja dla klienta (od A do Z, nietechniczna): [docs/klient/00-START-TUTAJ.md](docs/klient/00-START-TUTAJ.md)
Wgranie wtyczki, pokazanie aut na stronie, uruchomienie automatyzacji (instalator
[deploy/install.sh](deploy/install.sh)), obsługa, FAQ — krok po kroku.

## Status: wszystkie 9 działów zbudowane + audyt/naprawy (v0.20.0)

Cały pipeline IAAI → WordPress rozpisany i zaimplementowany. Jak działa całość:
**[docs/PIPELINE.md](docs/PIPELINE.md)**. Działy: [docs/dzialy/](docs/dzialy/) ·
oryginalne dokumentacje: [docs/refs/](docs/refs/) · wtyczka WP: [wp-plugin/iaai-importer/](wp-plugin/iaai-importer/).

### (historyczne) krok 1 — analiza źródeł danych (v0.1.0)

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
