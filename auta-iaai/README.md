<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Importer Aukcji — auta (IAAI + Copart)

Wtyczka WordPress pokazująca na stronie klienta pojazdy z aukcji **IAAI** oraz **Copart**
(podstrona **„Nasze auta"**, CPT „Pojazd"). Dane i zdjęcia wkłada do bazy osobny scraper
w Pythonie; wtyczka czyta je z tabel `{prefix}iaai_vehicles` / `iaai_vehicle_images`
(kolumna `source` = `iaai`/`copart`) i prezentuje z plakietką i filtrem źródła.

> **Dwuźródłowość:** klucz `(source, salvage_id)` w pojazdach i zdjęciach — ten sam numer
> lotu w IAAI i Copart nie koliduje. Bazy sprzed wersji dwuźródłowej migrują PK automatycznie
> (`iaai_migrate_source_pk`).

## Zawartość
- `wp-plugin/iaai-importer/` — wtyczka WordPress (to wgrywasz do WP). Wersja: patrz
  nagłówek `iaai-importer.php` / `readme.txt`.
- `scraper/` — pipeline Pythona (działy 01–05 + orkiestrator `run_pipeline.py`,
  `--source iaai|copart`).
- `deploy/` — instalator + systemd (live + backfill), `iaai-importer.env.example`.
- `db/` — `schema.sql` (referencyjny; wtyczka i tak zakłada tabele przez dbDelta).
- `docs/klient/` — instrukcje krok po kroku (PDF).

## Start
1. Wgraj `wp-plugin/iaai-importer/` do WordPressa i włącz (tabele + podstrona „Nasze auta"
   utworzą się same).
2. Poświadczenia bazy w `wp-config.php` (`IAAI_DB_*`).
3. Uruchom scraper na VPS wg `deploy/README.md` i `docs/klient/`.

Zdjęcia są hotlinkowane (0 miejsca na dysku). SEO: Schema.org „Car", meta/OG/Twitter jako
fallback (bez konfliktu z Yoast/Rank Math/AIOSEO/SEOPress), CPT w sitemap.xml rdzenia WP.
