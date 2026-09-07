<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Importery aukcji do WordPressa — auta (IAAI/Copart) + motocykle (poleasingowe.pl)

*[English version →](README.en.md)*

Monorepo z **dwiema niezależnymi wtyczkami WordPress**, zbudowanymi na tej samej
architekturze. Każda pokazuje na stronie klienta ofertę z aukcji i odświeża ją
automatycznie. Wtyczki są **kompatybilne obok siebie** na jednej stronie (osobne bazy,
brak kolizji, każda dziedziczy wygląd aktywnego motywu).

| Podprojekt | Co robi | Źródło danych | Wersja |
|---|---|---|---|
| [`auta-iaai/`](auta-iaai/) | Podstrona **„Nasze auta"** — samochody z aukcji | **IAAI + Copart** (dwa źródła, kolumna `source`) | wtyczka 0.30.6 |
| [`motocykle-poleasingowe/`](motocykle-poleasingowe/) | Podstrona **„Nasze motory"** — motocykle | **poleasingowe.pl** | wtyczka 0.12.6 |

## Jak to działa (obie tak samo)

```
[ scraper Python na VPS ]  --(cron/systemd)-->  [ baza MySQL ]  <--(read-only)--  [ wtyczka WordPress ]
      pobiera ofertę,                              dane + zdjęcia                     pokazuje na stronie,
      normalizuje, audytuje                                                          SEO, filtry, cache
```

- **Wtyczka (PHP)** to część na WordPressie: tworzy podstronę, czyta bazę i renderuje ofertę
  (SEO/Schema.org, filtry, paginacja, cache). Sama wtyczka nie pobiera danych.
- **Scraper (Python)** działa na **serwerze VPS** (cron albo systemd timer) — to on „wybudza"
  pobieranie: crawl → normalizacja → deduplikacja → audyt → zapis do bazy. WP‑cron tego nie robi
  (nie uruchomi Pythona/Playwrighta).
- **Zdjęcia** są **hotlinkowane** (0 miejsca na dysku klienta).

## Struktura podprojektu (identyczna w obu)

```
<podprojekt>/
  wp-plugin/<wtyczka>/   # wtyczka WordPress (PHP) — TO wgrywasz do WP
  scraper/               # program zbierający (Python) — na VPS
  deploy/                # instalacja + automatyzacja (systemd/cron) + .env.example
  db/                    # schema.sql (osobna baza ofert)
  docs/                  # dokumentacja, w tym docs/klient/ (instrukcje krok po kroku, PDF)
  README.md
```

## Szybki start

1. **WordPress:** spakuj katalog `wp-plugin/<wtyczka>/` do ZIP i wgraj przez *Wtyczki → Dodaj nową
   → Wyślij wtyczkę*, włącz. Podstrona utworzy się sama i wepnie w menu.
2. **Baza:** załóż osobną bazę z `db/schema.sql`, dane dostępu wpisz do `wp-config.php`
   (stałe `POLEA_DB_*` / `IAAI_DB_*`).
3. **Automatyzacja:** uruchom scraper na VPS wg `deploy/README.md` i `docs/klient/`.

Instrukcje krok po kroku (dla osoby nietechnicznej, PDF) są w `docs/klient/` każdego podprojektu.

## Licencja

GPL‑2.0‑or‑later — patrz [LICENSE](LICENSE).
