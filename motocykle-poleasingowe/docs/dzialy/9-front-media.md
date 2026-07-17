<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Dział 9 · FRONT I MEDIA (WordPress)

**Cel:** render listy i strony motocykla + galeria zdjęć. Auto-podstrona i motyw → wydzielone do [Działu 10](10-podstrona-motyw.md).

## Agenci
### agent: front
- **Zadanie:** grid kart (lista) + strona pojedynczego motocykla; filtry marka/rok/cena/paliwo (sanityzowane, **allowlist** pól/meta); paginacja; wszystkie dane escapowane; cache `transient` (kilka min).

### agent: media
- **Zadanie:** galeria zdjęć **hotlink** z `poleasingowe.pl/images`; lazy-load; `alt` = marka+model; łagodny fallback gdy brak zdjęć / 404.

## Krytyk
### krytyk: render
Odrzuca gdy: filtr wpuszcza dowolne meta/SQL (brak allowlist); N+1 zapytań o zdjęcia (brak mapy zdjęć); niepoprawny/niresponsywny HTML; hotlink nie degraduje łagodnie przy 404.
