<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Architektura — Importer Motocykli (poleasingowe.pl → WordPress)

Adaptacja sprawdzonego schematu działów/agentów/krytyków z importera IAAI+Copart,
uproszczona do **jednego źródła** (poleasingowe.pl), **PL**, **motocykle** (`ecr_motorcycles`).

**Zasada:** 1 agent = wykonuje zadanie · 1 krytyk = sprawdza wynik · 1 dokumentacja na dział.
Kolejność prac: **najpierw baza** (Etap 1 ✅), potem scraper (Część 1), potem wtyczka (Część 2).

## Czym różni się od IAAI+Copart (świadome uproszczenia)

- **Jedno źródło** → brak „łączenia strumieni JSONL", brak podwójnego Działu 1, brak kolumny `source`.
- **Server-side HTML** → **brak Playwright**. Dział 1 = zwykły HTTP GET (`requests`) + parser HTML. AJAX/żądania idą do serwera poleasingowe.pl (paginacja `?page=N`).
- **Normalizacja lżejsza** — dane już PL/PLN/km. Odpada mile→km i tłumaczenie stanu z US.
- **vPIC/NHTSA opcjonalne** — marka/model są u źródła; VIN tylko walidujemy (17 znaków, cyfra kontrolna), nie musimy odpytywać NHTSA.
- **Osobna baza MySQL** (`polea_*`), nie tabele wewnątrz WordPressa.
- **Zdjęcia z jednego hosta** — `poleasingowe.pl/images/sgallery_<UUID>_75.png` (hotlink).

---

## ŹRÓDŁO · poleasingowe.pl
Ich baza — brak dostępu; czytamy przez publiczne strony (HTTP).
- Listing: `/pl/auctions/list/pub/all/ecr_motorcycles?page=N`
- Szczegóły: `/pl/auctions/details/<slug>/<lot_id>`
- Zdjęcia: `/images/sgallery_<UUID>_75.png`
- robots.txt: dozwolone `/pl/auctions/list/` i `/pl/auctions/details/`; blokuje bidder-panel, files, calc-commission, autodna.

---

## CZĘŚĆ 1 — SCRAPER (Python): zbiera dane i zapisuje do bazy `polea_*`

### DZIAŁ 1 · POBIERANIE — dok: `poleasingowe-html.md`
Kanał HTTP do serwera poleasingowe.pl (server-side HTML, bez JS).
| Agent | Zadanie | Krytyk |
|---|---|---|
| pokrycie | przejście całej kategorii `ecr_motorcycles` po stronach (`?page=N`) → cała oferta | kompletność-pokrycia |
| listingi | karty wyników + paginacja; **odfiltrowanie reklam partnerów** (~2/stronę) | kompletność-listy |
| szczegóły | strona `/details/<slug>/<lot_id>`, wszystkie pola z kontraktu danych | kompletność-pól |
| zdjęcia | `sgallery_<UUID>` → `image_key` + URL-e, kolejność | kompletność-zdjęć |

### DZIAŁ 7 · ZGODNOŚĆ — dok: `robots-rfc9309.md`
| Agent | Zadanie | Krytyk |
|---|---|---|
| zgody | respektuje robots.txt, rate-limit (import co kilka godzin + odstęp między żądaniami), User-Agent, wykrywa blokady/429 | blokady |

### DZIAŁ 2 · NORMALIZACJA — dok: `normalizacja-pl.md`
| Agent | Zadanie | Krytyk |
|---|---|---|
| VIN | format 17 znaków + cyfra kontrolna, maska (bez odpytywania NHTSA) | poprawność-VIN |
| jednostki | `"17 460 PLN"`→liczba, `"3708 km"`→int, `"76 KM"`→int, `"754 ccm"`→int, daty→ISO, `"10 godzin (2026-07-08)"`→`termin_zakonczenia` DATETIME | jakość-jednostek |

### DZIAŁ 3 · DEDUPLIKACJA — dok: `dedup.md`
| Agent | Zadanie | Krytyk |
|---|---|---|
| match | usuwa duplikaty po `lot_id`; wykrywa relist po **pełnym VIN** (ten sam motocykl, nowy `lot_id`) | fałszywe-trafienia |

### DZIAŁ 4 · SYNCHRONIZACJA — dok: `mysql-upsert.md`
| Agent | Zadanie | Krytyk |
|---|---|---|
| diff | `raw_hash`: new / changed / unchanged | spójność |
| zapis | upsert do `polea_*` (PyMySQL) + reconcile: aukcje zniknięte/po terminie → `status` (zakonczona/usunieta) | poprawność-zapisu |

### DZIAŁ 5 · AUDYT — dok: `walidacja.md`
| Agent | Zadanie | Krytyk |
|---|---|---|
| walidacja | reguły pól (VIN 17 znaków, `cena_pln`>0, `rok_produkcji` sensowny, wymagane pola) | poprawność |

### → NOWA BAZA · `polea_*` · klucz `lot_id` (osobna baza MySQL)
Zapis SQL upsert (PyMySQL). Wtyczka WordPress czyta tę bazę (osobne połączenie).

---

## CZĘŚĆ 2 — WORDPRESS (wtyczka PHP): pokazuje motocykle z bazy na stronie

### DZIAŁ 6 · BEZPIECZEŃSTWO — dok: `wordpress-security.md`
| Agent | Zadanie | Krytyk |
|---|---|---|
| sanityzacja | escape/prepare danych wchodzących do WP; bezpieczne przechowanie poświadczeń osobnej bazy | podatności |
| nonce | ochrona akcji admina (CSRF), capability checks | podatności |

### DZIAŁ 8 · PUBLIKACJA — dok: `wordpress-cpt.md`
| Agent | Zadanie | Krytyk |
|---|---|---|
| CPT | typ treści `motocykl` w WordPress | poprawność-publikacji |
| meta | pola (VIN, rok, cena, przebieg, pojemność, moc, paliwo, lokalizacja, termin…) | poprawność-publikacji |

### DZIAŁ 9 · FRONT I MEDIA — dok: `wordpress-media.md`
| Agent | Zadanie | Krytyk |
|---|---|---|
| front | lista + strona motocykla (dane escapowane), filtry marka/rok/cena; **podstrona „Nasze motory" auto-tworzona i dopasowana do motywu** (block + classic) | render |
| media | zdjęcia hotlink z `poleasingowe.pl/images` | render |

### → STRONA WORDPRESS → klienci widzą motocykle

---

## Mapa dokumentacji (do uzupełnienia w Etapie 3–4)
- `poleasingowe-html.md` — endpointy, selektory HTML, paginacja, filtr reklam
- `robots-rfc9309.md` — zasady zgodności, rate-limit
- `normalizacja-pl.md` — parsowanie PL (PLN, km, KM, ccm, daty, terminy)
- `dedup.md` — logika lot_id + relist po VIN
- `mysql-upsert.md` — upsert + reconcile
- `walidacja.md` — reguły audytu pól
- `wordpress-security.md`, `wordpress-cpt.md`, `wordpress-media.md` — warstwa WP
