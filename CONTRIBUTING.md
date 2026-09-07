# Praca w tym repo

Monorepo z dwiema wtyczkami WordPressa i dwoma scraperami w Pythonie. Konkrety
wynikające z tego, że **połowa systemu nie działa na WordPressie**, tylko na VPS-ie.

## Co gdzie mieszka

```
<podprojekt>/
  wp-plugin/<wtyczka>/   wtyczka WordPress (PHP) — TO wgrywa klient
  scraper/               program zbierający (Python) — TO stoi na VPS
  deploy/                instalacja, systemd/cron, .env.example
  db/schema.sql          osobna baza ofert
  docs/klient/           instrukcje dla osoby nietechnicznej (PDF)
```

**Wtyczka nigdy nie pobiera danych.** Czyta bazę tylko do odczytu. Jeśli poprawka
polega na tym, że „wtyczka ma coś ściągnąć" — poprawka jest w złym miejscu:
WP-cron nie uruchomi Pythona ani Playwrighta.

## Zanim cokolwiek zmienisz

```bash
cd <podprojekt>/scraper && pip install pytest pymysql jsonschema requests && pytest -q
find */wp-plugin -name '*.php' -print0 | xargs -0 -n1 php -l
```

To dokładnie to, co robi CI. Kody wyjścia sprawdzaj **bez potoku** —
`pytest -q | tail` maskuje kod wyjścia.

## Workflow

```
branch → commit(y) → push → PR → CI zielone → merge → tag
```

Nazwy gałęzi: `fix/<opis>`, `feat/<opis>`, `docs/<opis>`.

## Wersjonowanie — dwie osie, nie mylić

| Co | Gdzie | Przykład |
|---|---|---|
| Wersja **repozytorium** (kolejny krok pracy) | tag `vX.Y.Z` | `v0.79.0` |
| Wersja **wtyczki** (to widzi WordPress) | `Version:` w nagłówku pliku wtyczki | `0.30.6` |

Te dwie liczby **nie są tym samym i nie muszą się zgadzać**. WordPress decyduje
o aktualizacji po `Version:` z nagłówka — podbicie taga repo bez podbicia nagłówka
znaczy, że klient nie dostanie poprawki, którą właśnie wydałeś.

**Każdy tag jest anotowany i niesie opis** (`git tag -a`). Z tych opisów powstaje
[`CHANGELOG.md`](CHANGELOG.md) — tag bez opisu to dziura w historii projektu.

## Konwencja commitów

**Temat opisuje SKUTEK, nie czynność** — jedno zdanie, po polsku.

Dobrze:

```
Podstrona "Nasze auta" wpina sie w motywy z menu na sztywno
Relist tego samego pojazdu przestaje tworzyc duplikat
```

Źle: `fix`, `poprawki`, `update scraper`.

## Czego nie robimy

- **Nie hotlinkujemy przez własny serwer.** Zdjęcia idą prosto ze źródła —
  to dlatego dysk klienta zajmuje 0 MB niezależnie od wielkości oferty.
- **Nie trzymamy danych dostępowych w repo.** `.env.example` opisuje, co ma być
  ustawione; prawdziwe wartości żyją na VPS-ie i w `wp-config.php`.
- **Nie mieszamy baz dwóch wtyczek.** Osobne bazy to powód, dla którego obie
  mogą stać na jednej stronie bez kolizji.
