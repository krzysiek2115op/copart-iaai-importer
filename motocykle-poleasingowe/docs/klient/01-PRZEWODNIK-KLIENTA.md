<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Przewodnik dla Klienta — wtyczka „Nasze motory"

Ten dokument jest napisany prostym jezykiem, bez terminow technicznych.
Wyjasnia, co robi wtyczka, jak ja wlaczyc i jak z niej korzystac na co dzien.
Jesli w ktoryms kroku pojawi sie cokolwiek trudnego — przekaz ten plik swojej
osobie technicznej albo napisz do nas (kontakt na koncu).

## Co robi ta wtyczka

Wtyczka dodaje do Twojej strony now podstrone **„Nasze motory"**, na ktorej
automatycznie wyswietlaja sie aktualne aukcje motocykli z serwisu poleasingowe.pl.

- Odwiedzajacy widzi **liste motocykli** ze zdjeciem, cena, rokiem i przebiegiem.
- Moze **filtrowac** po marce, paliwie, roku i cenie.
- Po kliknieciu w motocykl otwiera sie **strona szczegolow**: galeria zdjec,
  pelna tabela danych technicznych i przycisk do aukcji zrodlowej.
- Wszystko **dopasowuje sie do wygladu Twojej strony** (kolory i czcionki motywu)
  oraz **dziala na telefonie, tablecie i komputerze**.

Dane odswiezaja sie **same** — nie musisz nic wpisywac ani aktualizowac recznie.

## Co jest w paczce, ktora dostajesz

- Plik wtyczki: **motocykle-poleasingowe.zip** (to wgrywasz do WordPressa)
- Ten przewodnik (dla Ciebie)
- Dokument techniczny (dla osoby technicznej / hostingu)
- Plik bazy danych: **schema.sql** (potrzebny osobie technicznej raz, przy starcie)

## Instalacja krok po kroku (dla osoby nietechnicznej)

### Krok 1 — Wgraj wtyczke do WordPressa
1. Zaloguj sie do panelu WordPress (adres zwykle konczy sie na **/wp-admin**).
2. W menu po lewej wejdz w **Wtyczki → Dodaj nowa wtyczke**.
3. Na gorze kliknij **Wyslij wtyczke na serwer**.
4. Kliknij **Wybierz plik**, wskaz plik **motocykle-poleasingowe.zip** i kliknij **Zainstaluj teraz**.
5. Po chwili kliknij **Wlacz wtyczke**.

Gotowe — podstrona „Nasze motory" utworzy sie **sama** i pojawi w menu strony.

### Krok 2 — Polacz wtyczke z baza danych (jednorazowo)
Wtyczka czyta motocykle z osobnej bazy danych. Trzeba jej raz podac **4 dane
dostepowe**. To jedyny moment, w ktorym potrzebna moze byc pomoc technika lub
hostingu — zajmuje 2 minuty.

1. Wejdz w **Ustawienia → Motocykle**.
2. Jesli zobaczysz zielony komunikat „Polaczono" — **gotowe, nic nie robisz**.
3. Jesli zobaczysz komunikat na zolto — poproszaj osobe techniczna/hosting o
   dopisanie do pliku **wp-config.php** czterech linijek (dostaniesz je od nas):

```
define('POLEA_DB_HOST', '127.0.0.1');
define('POLEA_DB_NAME', 'polea');
define('POLEA_DB_USER', 'polea');
define('POLEA_DB_PASSWORD', 'haslo-ktore-dostaniesz');
```

Po zapisaniu tego pliku wroc do **Ustawienia → Motocykle** i odswiez — powinno
byc juz „Polaczono. Motocykli w bazie: ...".

### Krok 3 — Sprawdz efekt
- Wejdz na strone i znajdz w menu pozycje **„Nasze motory"**.
- Powinna pokazac sie lista motocykli. Kliknij dowolny — otworzy sie szczegoly.

## Codzienne korzystanie

Na co dzien **nie musisz robic nic**. Lista aktualizuje sie automatycznie.
Panel **Ustawienia → Motocykle** daje Ci tylko dwie rzeczy:

| Element | Do czego sluzy |
|---|---|
| Status bazy | Zielony = wszystko dziala. Zolty = zadzwon do technika. |
| Wyczysc cache | Odswieza liste od razu, gdy chcesz zobaczyc najnowsze dane. |

## Najczestsze pytania

- **Skad sa te motocykle?** Z serwisu aukcyjnego poleasingowe.pl. Wtyczka je
  tylko pokazuje na Twojej stronie.
- **Jak czesto sie aktualizuja?** Automatycznie, zwykle raz dziennie (dokladny
  harmonogram ustawia osoba techniczna).
- **Czy zdjecia zajmuja miejsce na moim serwerze?** Nie. Zdjecia sa pokazywane
  bezposrednio ze zrodla — nie obciazaja Twojego hostingu.
- **Widze „Brak motocykli" — co robic?** Zwykle to chwilowa sytuacja (brak
  aktywnych aukcji lub trwa aktualizacja). Jesli utrzymuje sie dluzej —
  sprawdz status w Ustawienia → Motocykle i, w razie zoltego komunikatu,
  skontaktuj sie z nami.
- **Czy moge zmienic wyglad?** Strona sama przejmuje kolory i czcionki Twojego
  motywu. Wieksze zmiany wygladu zglos nam — dopasujemy.

## Czego lepiej NIE robic

- Nie usuwaj podstrony „Nasze motory" i nie kasuj z niej wpisu `[motocykle]`
  (to on wyswietla liste). Gdyby zniknal — wpisz go z powrotem albo wlacz
  wtyczke ponownie, a podstrona odtworzy sie sama.
- Nie zmieniaj danych dostepowych do bazy bez kontaktu z nami.

## Kontakt / wsparcie

W razie pytan lub problemow napisz do nas — podaj adres swojej strony i (jesli
jest) tresc komunikatu z **Ustawienia → Motocykle**. Postaramy sie pomoc szybko.
