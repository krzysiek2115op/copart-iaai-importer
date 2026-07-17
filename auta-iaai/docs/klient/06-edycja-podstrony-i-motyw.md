# Etap 6 — Edycja podstrony „Nasze auta" i dopasowanie do motywu

Podstrona z autami powstaje sama, ale **możesz ją swobodnie edytować** i dostroić
wygląd do swojej strony. Tu masz jak, krok po kroku — bez programowania.

---

## 1. Gdzie jest podstrona i jak ją edytować
**Strony → Wszystkie strony → „Nasze auta" → Edytuj.**

Zobaczysz zwykłą stronę WordPress z jednym „klockiem" — **krótkim kodem**:
```
[iaai_pojazdy ile="24"]
```
- **Nie usuwaj** tego kodu — to on wyświetla auta.
- Możesz **dopisać własny tekst** nad albo pod nim (nagłówek, opis, telefon…).
- Możesz zmienić **tytuł strony** i jej adres.

## 2. Ile aut na stronie
W krótkim kodzie zmień liczbę:
```
[iaai_pojazdy ile="12"]     ← 12 aut na stronę (mniej = szybciej)
[iaai_pojazdy ile="48"]     ← maksymalnie 48
```
Pod siatką jest **paginacja** („‹ 1 z N ›") — reszta aut jest na kolejnych stronach.

## 3. Wygląd dopasowuje się SAM do motywu
Karty, filtry i paginacja **dziedziczą kolory i fonty** Twojego motywu (jasny/ciemny),
więc od razu pasują do strony. Nie musisz nic ustawiać.

## 4. Chcesz dostroić kolory/odstępy? (opcjonalnie)
Bez ruszania kodu wtyczki — przez **Dodatkowy CSS**:
**Wygląd → Dostosuj → Dodatkowy CSS** (motyw klasyczny) lub
**Wygląd → Edytor → Style → Dodatkowy CSS** (motyw blokowy). Wklej np.:
```css
.iaai-pojazdy{
  --iaai-accent:#c0392b;   /* kolor akcentu (przyciski, plakietki) */
  --iaai-radius:6px;       /* zaokrąglenie rogów kart */
}
```
Inne dostępne pokrętła: `--iaai-border` (kolor ramek), `--iaai-tint` (tło kart),
`--iaai-muted` (kolor drobnego tekstu).

## 5. Dodanie strony do górnego menu
Wtyczka próbuje sama (motywy klasyczne i blokowe). Jeśli Twój motyw ma menu
„na sztywno" (gotowce premium / page-buildery), dodaj raz ręcznie:
- **Klasyczny:** Wygląd → Menu → zaznacz „Nasze auta" → Dodaj do menu → Zapisz.
- **Blokowy:** Wygląd → Edytor → Nawigacja → „+" → dodaj link do „Nasze auta".
Szczegóły i wyjątki: [02-pokaz-auta-na-stronie.md](02-pokaz-auta-na-stronie.md).

## 6. Strona pojedynczego auta
Każde auto ma własny adres (`/pojazdy/...`) z tabelą danych i galerią zdjęć.
Wygląda zgodnie z Twoim motywem. To wpis typu „Pojazd" — zwykle nie trzeba nic
zmieniać; zaawansowany deweloper może nadpisać szablon w motywie (`single-pojazd.php`).

## 7. Rzeczy, których lepiej NIE robić
- Nie kasuj krótkiego kodu `[iaai_pojazdy]` — strona przestanie pokazywać auta.
- Nie zmieniaj ręcznie wpisów „Pojazd" — są nadpisywane przy każdej synchronizacji
  ze źródłem IAAI/Copart (to jest zamierzone: dane mają być wierną kopią aukcji).
- Nie usuwaj wtyczki, jeśli chcesz zachować auta (dane są w bazie; dezaktywacja
  ukrywa je, usunięcie wtyczki nie kasuje bazy).

Problemy i pytania: **[05-problemy-i-pytania.md](05-problemy-i-pytania.md)**.
