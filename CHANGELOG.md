# Dziennik zmian

Zapis wydań obu wtyczek. Powstał **z anotowanych tagów gita** — każdy z 126 tagów
w tym repo niesie własny opis, więc historia nie musiała być odtwarzana z pamięci
ani zmyślona. Odtworzenie tej listy:

```sh
git tag -l --format='%(creatordate:short) %(refname:short) %(contents:subject)' --sort=-creatordate
```

Numeracja: `vX.Y.Z` to wersja **repozytorium** (kolejny krok pracy), a `p2-vX.Y.Z`
— wydania drugiej wtyczki z okresu, gdy pracowała na własnej gałęzi. Wersje samych
wtyczek (`Version:` w nagłówku pliku) idą osobno i są podane w temacie taga tam,
gdzie się zmieniały.

> **Uwaga o Releases na GitHubie.** Opisane są tam tylko cztery pierwsze wydania
> (v0.1.0–v0.4.0, czerwiec 2026); potem praca szła dalej, ale wydania przestały
> powstawać. Ten plik jest kompletniejszy od zakładki Releases i to on jest
> źródłem prawdy o historii projektu.

---

## Repozytorium (`v*`)

97 tagów — główna oś pracy, obie wtyczki.

- **`v0.79.0`** · 2026-07-17 — Konsolidacja: branche plugin-1/plugin-2 scalone do main (-s ours), branche zachowane
- **`v0.78.0`** · 2026-07-17 — Monorepo: main = obie wtyczki (auta-iaai + motocykle-poleasingowe) + prawdziwy README
- **`v0.77.0`** · 2026-07-17 — iaai v0.30.6: auto-migracja PK dual-source (item5) + uninstall.php (item4)
- **`v0.76.0`** · 2026-07-16 — Domkniecie audytu plugin-2 (5x P3): relist dedup + cache-gen + sitemap paginacja (v0.12.6)
- **`v0.75.0`** · 2026-07-16 — Domkniecie audytu plugin-1 (P1/P2/P3): reconcile prog + Copart paginacja + keep-going + prune zdjec (v0.30.5)
- **`v0.74.0`** · 2026-07-16 — iaai: wpiecie "Nasze auta" w motywy z menu "na sztywno" (filtr kk_menu_items) (v0.30.4)
- **`v0.73.0`** · 2026-07-16 — Fix menu: guard page-list (koniec duplikatu "Nasze motory") + wpiecie w motyw "na sztywno" (v0.12.5)
- **`v0.72.0`** · 2026-07-16 — Re-audyt P2 (subagent-audytor): naprawa 2 bugow + hardening backupu
- **`v0.71.0`** · 2026-07-16 — Utwardzenie na skale (opcja A po re-audycie): W1+G4+S1+#13 (v0.30.3)
- **`v0.70.0`** · 2026-07-15 — Re-audyt P1 (subagent-audytor): naprawa 9 defektow dual-source/produkcja (v0.30.2)
- **`v0.69.0`** · 2026-07-15 — Audyt P1: domkniecie spojnosci dual-source + odpornosc importu (v0.30.1)
- **`v0.68.0`** · 2026-07-07 — Licencja GPL-2.0-or-later dla automatyzacji (LICENSE + SPDX)
- **`v0.67.0`** · 2026-07-07 — Audyt wtyczki + dual-source w tekstach klienta (v0.30.1)
- **`v0.66.0`** · 2026-07-07 — Demo Playground: fix blueprint (meta) + wyglad marki
- **`v0.65.0`** · 2026-07-07 — CI fix: mysqldump --column-statistics=0 (MariaDB) w vps-automatyzacja
- **`v0.64.0`** · 2026-07-06 — Diagram: rozdzielone pobieranie per zrodlo (1 AJAX = 1 dzial)
- **`v0.63.0`** · 2026-07-06 — Instrukcja konta Member Copart (dla laika) + branding etapow
- **`v0.62.0`** · 2026-07-06 — Diagram architektury 2 zrodla + narzedzie testowe Copart
- **`v0.61.0`** · 2026-07-06 — Audyt PDF/tekstow: Copart w kazdej sekcji (2 zrodla 1:1 z systemem)
- **`v0.60.0`** · 2026-07-06 — Skad-pochodza-dane: swiezy zrzut Copart jako 2. zrodlo
- **`v0.59.0`** · 2026-07-06 — Audyt dual-source + instrukcje/testy na 2 zrodla (IAAI + Copart)
- **`v0.58.0`** · 2026-07-05 — Demo + diagramy na 2 zrodla (IAAI + Copart)
- **`v0.57.0`** · 2026-07-05 — Drugie zrodlo: Copart obok IAAI (baza + wtyczka + scraper)
- **`v0.56.0`** · 2026-07-04 — Diagramy: rozbudowa bez duplikacji instrukcji (4 strony)
- **`v0.55.0`** · 2026-07-04 — Instrukcje: rozdzielenie na 2 PDF (dowod + diagram) + diagram bardziej szczegolowy, pierwsze w paczce
- **`v0.54.0`** · 2026-07-04 — Instrukcja: dodatek 'Skad pochodza dane' — dowod (2 zrzuty) + diagram przeplywu
- **`v0.53.0`** · 2026-07-03 — Demo Pages: 'Nasze auta' — hero jak w motywie + prawdziwe zdjecia aut
- **`v0.52.0`** · 2026-07-03 — Statyczna migawka Kredyt Kompas + Nasze auta (GitHub Pages)
- **`v0.51.0`** · 2026-07-03 — Demo: prawdziwa strona Kredyt Kompas + wtyczka + 'Nasze auta' w menu
- **`v0.50.0`** · 2026-07-03 — Demo dla klienta: WordPress Playground (blueprint + seed aut + zip wtyczki)
- **`v0.49.0`** · 2026-07-03 — Paczka: kolejnosc Zacznij tutaj -> 1-Instrukcje -> reszta (prefiks folderu)
- **`v0.48.0`** · 2026-07-03 — Paczka: 'Zacznij tutaj' jako ladny PDF na wierzchu zamiast pliku .md
- **`v0.47.0`** · 2026-07-03 — Paczka: usuniety komplet-PDF (duplikat folderu Instrukcje-PDF)
- **`v0.46.0`** · 2026-07-03 — Czysta paczka dostawy: usuniete zbedne pliki dla klienta
- **`v0.45.0`** · 2026-07-03 — Kazdy etap instrukcji jako osobny ladny PDF (docs/klient/pdf/)
- **`v0.44.0`** · 2026-07-03 — PDF instrukcji: dodana sekcja edycji podstrony + dopasowania do motywu (6 stron)
- **`v0.43.0`** · 2026-07-03 — Debug + optymalizacja wtyczki, docs edycji/motywu, szczegolowe testy (wtyczka 0.24.0)
- **`v0.42.0`** · 2026-07-02 — Wyglad listy dziedziczy motyw klienta zamiast narzuconej palety (wtyczka 0.23.0)
- **`v0.41.0`** · 2026-07-02 — Pasek filtrow nad lista aut: marka/rok/uszkodzenie/sortowanie (wtyczka 0.22.0)
- **`v0.40.0`** · 2026-07-02 — Ladniejsza, szczegolowa lista aut w stylu IAAI + paginacja (wtyczka 0.21.0)
- **`v0.39.0`** · 2026-07-02 — Auto-menu na froncie: 'Nasze auta' na gornym pasku na kazdym motywie (wtyczka 0.20.0)
- **`v0.38.0`** · 2026-07-02 — Instrukcja klienta: uwaga o motywach z menu 'na sztywno' (Elementor/Divi/gotowce)
- **`v0.37.0`** · 2026-07-02 — Auto-dodawanie podstrony do menu takze w motywach blokowych (wtyczka 0.19.0)
- **`v0.36.0`** · 2026-07-02 — Test reczny wtyczki na lokalnym WP: instrukcja + seed + mu-plugin
- **`v0.35.0`** · 2026-07-02 — Ladny PDF instrukcji klienta + domkniecie audytu paczki (wtyczka 0.18.0)
- **`v0.34.0`** · 2026-07-02 — Pelna instrukcja klienta A-Z w jednym pliku (PRZECZYTAJ-MNIE-NAJPIERW)
- **`v0.33.0`** · 2026-07-02 — Dzial 5: schemat audytu wyciagniety do vehicle.schema.json (artefakt w repo)
- **`v0.32.0`** · 2026-07-02 — SEO auto-podstrony i stron pojazdow (wtyczka 0.18.0)
- **`v0.31.0`** · 2026-07-02 — Auto-podstrona 'Nasze auta' po aktywacji + menu + responsywny CSS motywu (wtyczka 0.17.0)
- **`v0.30.0`** · 2026-06-30 — Audyt bezpieczenstwa + utwardzenie wtyczki (produkt komercyjny) v0.16.0
- **`v0.29.7`** · 2026-06-30 — Diagram: AJAX idzie z serwera/bazy IAAI wprost do Dzialu 1
- **`v0.29.6`** · 2026-06-30 — Diagram: rozdzielenie zrodla — AJAX startuje z BAZY IAAI
- **`v0.29.5`** · 2026-06-30 — Diagram architektury: dodano zrodlo IAAI (AJAX/Playwright), etykiety json miedzy dzialami, wyjasnienie jednej bazy
- **`v0.29.4`** · 2026-06-30 — Diagram architektury (dzialy/agenci/krytycy/dokumentacja) — SVG + generator
- **`v0.29.3`** · 2026-06-30 — Diagram systemu jako SVG (zrodlo PDF dla klienta)
- **`v0.29.2`** · 2026-06-30 — Diagram systemu dla klienta (docs/klient/diagram-systemu.md)
- **`v0.29.1`** · 2026-06-30 — Test calego systemu (E2E na dev MariaDB) — raport docs/TEST-SYSTEMU.md
- **`v0.29.0`** · 2026-06-30 — F4+F5 + instalator + instrukcja klienta A-Z
- **`v0.28.0`** · 2026-06-30 — Audyt: naprawa F1+F2+F3
- **`v0.27.1`** · 2026-06-30 — Audyt A-Z (debug) v2: docs/AUDIT2.md
- **`v0.27.0`** · 2026-06-30 — Blok C: dopiecia L10-L14 + testy jednostkowe
- **`v0.26.0`** · 2026-06-30 — Blok B decyzje: zdjecia=HOTLINK (#8), bez konta IAAI (#7)
- **`v0.25.0`** · 2026-06-30 — Blok B: silnik pokrycia (#6) + sale_date (#9/M2)
- **`v0.24.0`** · 2026-06-30 — Blok A: automatyzacja always-on (kod gotowy)
- **`v0.23.0`** · 2026-06-29 — Model wdrozenia: wszystko na jednym VPS klienta
- **`v0.22.0`** · 2026-06-29 — Wymóg: automatyzacja ciągła (always-on) jako rdzeń projektu
- **`v0.21.0`** · 2026-06-29 — v0.21.0 — STATUS.md (master-dokument projektu)
- **`v0.20.0`** · 2026-06-29 — v0.20.0 — M4: orkiestrator pipeline
- **`v0.19.0`** · 2026-06-29 — v0.19.0 — M3: wykrywanie sold/removed
- **`v0.18.1`** · 2026-06-29 — v0.18.1 — M1: bezpieczna sale_date
- **`v0.18.0`** · 2026-06-29 — v0.18.0 — naprawa H1 (zdjęcia w bazie) + H2 (audyt przed zapisem)
- **`v0.17.0`** · 2026-06-29 — v0.17.0 — audyt systemu (raport AUDIT.md)
- **`v0.16.0`** · 2026-06-29 — v0.16.0 — pełny opis pipeline'u (docs/PIPELINE.md)
- **`v0.15.0`** · 2026-06-29 — v0.15.0 — dział FRONT I MEDIA; wszystkie 9 działów gotowe
- **`v0.14.0`** · 2026-06-29 — v0.14.0 — dział PUBLIKACJA (CPT + meta)
- **`v0.13.0`** · 2026-06-29 — v0.13.0 — dział ZGODNOŚĆ
- **`v0.12.0`** · 2026-06-29 — v0.12.0 — dział BEZPIECZEŃSTWO (wtyczka WP)
- **`v0.11.0`** · 2026-06-29 — v0.11.0 — dział AUDYT DANYCH
- **`v0.10.0`** · 2026-06-29 — v0.10.0 — dział SYNCHRONIZACJA (diff + json, realna baza)
- **`v0.9.0`** · 2026-06-29 — v0.9.0 — dział DEDUPLIKACJA (match)
- **`v0.8.0`** · 2026-06-29 — v0.8.0 — dział NORMALIZACJA (VIN + jednostki)
- **`v0.7.3`** · 2026-06-29 — v0.7.3 — agent zdjęcia; dział POBIERANIE kompletny
- **`v0.7.2`** · 2026-06-29 — v0.7.2 — agent szczegóły + krytyk kompletność-pól
- **`v0.7.1`** · 2026-06-29 — v0.7.1 — niezawodna paginacja IAAI (Playwright)
- **`v0.7.0`** · 2026-06-29 — v0.7.0 — agent listingi + krytyk kompletność-listy (zweryfikowane na żywo)
- **`v0.6.2`** · 2026-06-29 — v0.6.2 — oryginał Playwright pobrany (referencja działu pobieranie)
- **`v0.6.1`** · 2026-06-29 — v0.6.1 — jeden dział = jedna dokumentacja; oryginał = Playwright
- **`v0.6.0`** · 2026-06-29 — v0.6.0 — dział pobieranie: agenci/krytycy + szkielety dokumentacji
- **`v0.5.0`** · 2026-06-29 — v0.5.0 — schemat wieloagentowy (1 agent : 1 krytyk) + przepływ baza->strona
- **`v0.4.4`** · 2026-06-29 — v0.4.4 — historia = bieżąca oferta IAAI (zakres domknięty)
- **`v0.4.3`** · 2026-06-29 — v0.4.3 — zakres zasilania bazy: historia (backfill) + live
- **`v0.4.2`** · 2026-06-29 — v0.4.2 — przenośna instancja MariaDB (lokalny podgląd bazy)
- **`v0.4.1`** · 2026-06-29 — v0.4.1 — instrukcja uruchomienia/podglądu bazy (MySQL/WP)
- **`v0.4.0`** · 2026-06-29 — v0.4.0 — nowa baza jako wierna kopia rekordu IAAI
- **`v0.3.0`** · 2026-06-29 — v0.3.0 — krok 3: nowa baza danych + mapowanie
- **`v0.2.0`** · 2026-06-27 — v0.2.0 — krok 2: tylko IAAI + architektura
- **`v0.1.0`** · 2026-06-27 — v0.1.0 — krok 1: analiza źródeł danych IAAI/Copart

## Wtyczka 2 na własnej gałęzi (`p2-v*`)

29 tagów z okresu, gdy `motocykle-poleasingowe` rozwijały się osobno.

- **`p2-v0.12.12`** · 2026-07-15 — Dokumentacja klienta plugin-2: 3 dokumenty (nietechniczny/techniczny/schema) + fix generatora PDF
- **`p2-v0.12.11`** · 2026-07-15 — Testy: dodaj test_edge_extra (22 testy brzegowe/regresyjne pipeline'u)
- **`p2-v0.12.10`** · 2026-07-15 — Fix sitemap ofert: poprawna nazwa funkcji WP + nazwa providera bez podkreslnika (v0.12.4)
- **`p2-v0.12.9`** · 2026-07-15 — Front: hardening responsywnosci (tabela, anty-overflow, filtry mobile)
- **`p2-v0.12.8`** · 2026-07-13 — Front: wlasny wysrodkowany kontener .polea-wrap (responsywnosc niezalezna od motywu)
- **`p2-v0.12.7`** · 2026-07-13 — Scraper: parsowanie najnizsza_cena_30d (Omnibus) — potwierdzone na zywym HTML
- **`p2-v0.12.6`** · 2026-07-12 — Instrukcja testow recznych jako PDF (generator MD->SVG->PDF)
- **`p2-v0.12.5`** · 2026-07-12 — Testy reczne: srodowisko Docker (styl VPS) + przewodnik
- **`p2-v0.12.4`** · 2026-07-12 — Optymalizacja: helper polea_vehicle_name (DRY, bez zmiany zachowania)
- **`p2-v0.12.3`** · 2026-07-12 — Diagramy plugin-2 jako PDF (nietechniczny/techniczny/schemat + scalony)
- **`p2-v0.12.2`** · 2026-07-12 — Diagramy draw.io: nietechniczny + techniczny + schemat bazy (ERD)
- **`p2-v0.12.1`** · 2026-07-12 — Testy integracyjne scrapera (+24, 43/43): reconcile/upsert/Fetcher.get/main.run/SSRF; CI discover
- **`p2-v0.12.0`** · 2026-07-11 — Domkniecie luk audytu: CI (php -l + testy), obserwowalnosc DB (WP_DEBUG), backup/monitoring, TZ doc
- **`p2-v0.11.1`** · 2026-07-11 — Hardening iteracja 3: TLS verify + Content-Type (scraper), .gitignore secrets, dokumentacja ryzyk serwera (headers/MySQL least-priv/DNS-rebind)
- **`p2-v0.11.0`** · 2026-07-11 — Podstrona: semantyka HTML5, breadcrumbs, JSON-LD @graph, FAQ, podobne oferty, CWV, dostępność, mobile-first
- **`p2-v0.10.0`** · 2026-07-11 — SEO podstrony: ładne URL-e, meta/OG/JSON-LD, sitemap, noindex; deferuje do wtyczek SEO
- **`p2-v0.9.0`** · 2026-07-11 — Naprawa audytu przedwdrozeniowego: #1-#6,#8,#10-#13 (production-ready)
- **`p2-v0.8.1`** · 2026-07-10 — Audyt i poprawki dokumentacji klienta (PDF)
- **`p2-v0.8.0`** · 2026-07-10 — Kompletna dokumentacja klienta (PDF)
- **`p2-v0.7.1`** · 2026-07-09 — Security hardening iteracja 2 (v0.7.1): DoS cache, timeouty, anty-SSRF env, limity wejscia
- **`p2-v0.7.0`** · 2026-07-09 — Hardening bezpieczenstwa (Dzial 6) + audyt: SSRF/DoS/cron/wejscie (v0.7.0)
- **`p2-v0.6.2`** · 2026-07-09 — Diagram: drugi lacznik AJAX (baza -> WordPress), symetryczny do zrodla
- **`p2-v0.6.1`** · 2026-07-09 — Diagram architektury: laczniki 'json' + lacznik AJAX zrodlo->pipeline
- **`p2-v0.6.0`** · 2026-07-09 — Dokumentacja PDF plugin-2: diagram architektury + skad-dane + jak-dziala
- **`p2-v0.5.0`** · 2026-07-09 — plugin-2 v0.5.0 — wtyczka WordPress
- **`p2-v0.4.0`** · 2026-07-08 — plugin-2 v0.4.0 — scraper Python
- **`p2-v0.3.0`** · 2026-07-08 — plugin-2 v0.3.0 — dokumentacja dzialow
- **`p2-v0.2.0`** · 2026-07-08 — plugin-2 v0.2.0 — schemat projektu
- **`p2-v0.1.0`** · 2026-07-08 — plugin-2 v0.1.0 — schemat bazy

