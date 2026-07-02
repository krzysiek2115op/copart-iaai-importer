========================================================================
  📘  INSTRUKCJA OD A DO Z  —  IMPORTER AUT Z IAAI DO WORDPRESS
  Przeczytaj mnie NAJPIERW.  Pisane prostym językiem — nie musisz być
  informatykiem. Rób kroki po kolei, od 1 w dół.
========================================================================

Witaj! Trzymasz komplet do uruchomienia systemu, który **sam pobiera samochody
z serwisu aukcyjnego iaai.com i pokazuje je na Twojej stronie WordPress** — przez
całą dobę, bez Twojego udziału.

Ta instrukcja przeprowadzi Cię przez wszystko krok po kroku: co gdzie kliknąć,
jak wgrać wtyczkę, jak sprawdzić, że działa, oraz co zrobić, gdy coś pójdzie nie tak.
Na końcu jest **FAQ** (pytania i odpowiedzi) i **słowniczek** trudnych słów.

Spokojnie — samo wgranie wtyczki i pokazanie aut na stronie to głównie klikanie.


────────────────────────────────────────────────────────────────────────
CZĘŚĆ I — CO TO JEST I JAK DZIAŁA (2 minuty czytania)
────────────────────────────────────────────────────────────────────────

W skrócie, cały system to trzy elementy:

   IAAI.com  ──►  PROGRAM ZBIERAJĄCY  ──►  BAZA DANYCH  ──►  TWOJA STRONA
   (źródło aut)     (działa sam 24/7)        (auta)         (klienci widzą auta)

1. **Program zbierający** („scraper") pilnuje serwisu IAAI i pobiera nowe auta
   (zdjęcia + dane: rok, marka, model, przebieg, uszkodzenia itd.).
2. **Baza danych** przechowuje te auta (to ta sama baza, na której stoi Twój WordPress).
3. **Wtyczka WordPress** bierze auta z bazy i **pokazuje je na stronie**.

Gdy na aukcji pojawia się nowe auto → trafia na stronę. Gdy auto znika z aukcji →
znika też u Ciebie (wpis zostaje ukryty, historia się nie kasuje). **Wszystko dzieje
się samo.**

Co dostajesz w tej paczce (ZIP):
   • wp-plugin/iaai-importer/  → WTYCZKA do WordPress (pokazuje auta)
   • scraper/                  → PROGRAM ZBIERAJĄCY (pobiera auta z IAAI)
   • deploy/                   → INSTALATOR automatyzacji (install.sh) + ustawienia
   • docs/klient/             → instrukcje (ten plik + rozbite na etapy)

Czego potrzebujesz:
   ✔ WordPress na własnym hostingu (Twoja strona).
   ✔ Do PEŁNEJ automatyzacji: serwer typu **VPS** z dostępem do „terminala" (SSH).
     ⚠ Najtańszy „hosting współdzielony" NIE wystarczy do programu zbierającego.
     Jeśli nie wiesz co masz — zapytaj dostawcę: „Czy mam VPS z dostępem SSH
     i mogę uruchamiać Pythona?".

> Ważne rozróżnienie:
>   • CZĘŚĆ 1 (wgranie wtyczki i pokazanie aut) → zrobisz sam, to klikanie.
>   • CZĘŚĆ 2 (automatyzacja na serwerze) → bardziej techniczna; jest gotowy
>     instalator „jednym poleceniem", ale jeśli nie czujesz się pewnie, poproś
>     administratora hostingu — to dla niego 10 minut pracy.


────────────────────────────────────────────────────────────────────────
CZĘŚĆ II — INSTALACJA WTYCZKI KROK PO KROKU (to zrobisz sam)
────────────────────────────────────────────────────────────────────────

KROK 1 — Rozpakuj otrzymaną paczkę
------------------------------------------------------------------------
Kliknij prawym przyciskiem na otrzymany plik ZIP → „Wyodrębnij/Rozpakuj".
Powstanie folder z zawartością wypisaną wyżej.


KROK 2 — Przygotuj plik wtyczki do wgrania
------------------------------------------------------------------------
WordPress wgrywa wtyczki jako plik ZIP. Spakuj SAM folder wtyczki:

   • Wejdź do folderu `wp-plugin/`.
   • Kliknij prawym na folder `iaai-importer` → „Wyślij do" →
     „Folder skompresowany (ZIP)" (Windows) / „Kompresuj" (Mac).
   • Powstanie plik `iaai-importer.zip`.  ← ten plik wgrasz do WordPress.

> Jeśli w paczce jest już gotowy `iaai-importer.zip` — użyj go i pomiń ten krok.


KROK 3 — Zaloguj się do panelu WordPress
------------------------------------------------------------------------
W przeglądarce wejdź na adres swojego panelu, zwykle:

   https://twojastrona.pl/wp-admin

Zaloguj się swoim loginem i hasłem administratora.


KROK 4 — Wgraj wtyczkę
------------------------------------------------------------------------
W menu po lewej: **Wtyczki → Dodaj nową wtyczkę**.

   ┌──────────────────────────────┐
   │  Kokpit                      │
   │  Wpisy / Media / Strony      │
   │ ▸ Wtyczki        ← kliknij   │
   │     • Zainstalowane wtyczki  │
   │     • Dodaj nową wtyczkę  ←  │
   └──────────────────────────────┘

Na górze kliknij **„Wyślij wtyczkę na serwer"** (ang. *Upload Plugin*).

   [ Dodaj wtyczki ]   [ Wyślij wtyczkę na serwer ]  ← kliknij

Kliknij **„Wybierz plik"**, wskaż **`iaai-importer.zip`**, potem
**„Zainstaluj teraz"**.


KROK 5 — Włącz wtyczkę
------------------------------------------------------------------------
Po chwili pojawi się przycisk **„Włącz wtyczkę"** (ang. *Activate Plugin*).
Kliknij go.

✅ W tym momencie dzieje się AUTOMATYCZNIE (nic nie klikasz):
   • wtyczka zakłada w bazie potrzebne tabele,
   • tworzy gotową podstronę **„Nasze auta"**, dopasowaną do wyglądu Twojego
     motywu i działającą na telefonie,
   • próbuje dodać tę podstronę do głównego menu strony.


KROK 6 — Sprawdź, że się udało
------------------------------------------------------------------------
   • **Wtyczki → Zainstalowane wtyczki** → na liście jest „IAAI Importer" (aktywna).
   • W menu po lewej pojawia się nowa pozycja **„Pojazdy"** (tu trafiają auta).
   • **Strony → Nasze auta** → istnieje nowa strona (adres: `.../nasze-auta`).

> Na razie strona „Nasze auta" będzie pusta — auta wypełnią ją dopiero po
> uruchomieniu automatyzacji (Część III). To normalne.


KROK 7 — (Jeśli menu nie dodało się samo) dodaj stronę do menu
------------------------------------------------------------------------
Wtyczka próbuje zrobić to sama, ale jeśli Twój motyw nie ma jeszcze ustawionego
menu, dodaj ręcznie (30 sekund):

   **Wygląd → Menu** → zaznacz „Nasze auta" → „Dodaj do menu" → „Zapisz menu".


KROK 8 — (Opcjonalnie) własna, dodatkowa strona z autami
------------------------------------------------------------------------
Chcesz pokazać auta też w innym miejscu? Użyj „krótkiego kodu":

   1. Strony → Dodaj nową stronę, wpisz tytuł np. „Oferta".
   2. Kliknij „+”, wyszukaj blok „Krótki kod" (ang. *Shortcode*).
   3. Wklej dokładnie:   [iaai_pojazdy ile="24"]
      (liczba 24 = ile aut pokazać; możesz zmienić).
   4. Opublikuj.


────────────────────────────────────────────────────────────────────────
CZĘŚĆ III — URUCHOMIENIE AUTOMATYZACJI (część techniczna / dla admina)
────────────────────────────────────────────────────────────────────────

To sprawia, że auta zaczynają się POJAWIAĆ i AKTUALIZOWAĆ same. Wykonuje się to
raz, na serwerze VPS (przez „terminal"/SSH). Jest gotowy instalator — jedno
polecenie ustawia wszystko.

Jeśli nie czujesz się pewnie w terminalu — **przekaż ten rozdział administratorowi
hostingu**. Dla niego to rutyna.

KROK 9 — Wgraj folder projektu na serwer i uruchom instalator
------------------------------------------------------------------------
Na serwerze, w terminalu (SSH), przejdź do folderu projektu i uruchom:

   sudo bash deploy/install.sh /var/www/html

   (zamień `/var/www/html` na katalog, gdzie stoi Twój WordPress).

Instalator sam: zainstaluje potrzebne programy (Python, przeglądarkę do zbierania),
połączy się z bazą Twojego WordPressa (odczyta dane z `wp-config.php`), włączy
usługę, która co kilkanaście minut sprawdza IAAI i publikuje nowe auta.

Szczegółowy opis krok po kroku (co wpisać, co powinno się wyświetlić) jest w:
   docs/klient/03-uruchom-automatyzacje.md


KROK 10 — Sprawdź, że auta się pojawiają
------------------------------------------------------------------------
Po pierwszym przebiegu (kilka–kilkanaście minut) wejdź na stronę „Nasze auta" —
powinny pojawić się pierwsze pojazdy ze zdjęciami. W panelu, w zakładce „Pojazdy",
zobaczysz je również jako wpisy.

✅ GOTOWE. Od tej chwili system działa SAM — nie musisz nic robić na co dzień.


────────────────────────────────────────────────────────────────────────
CZĘŚĆ IV — CO MOŻE PÓJŚĆ NIE TAK (i jak to naprawić)
────────────────────────────────────────────────────────────────────────

▸ „Wtyczka nie mogła zostać zainstalowana"
   Przyczyna: wysłałeś rozpakowany folder zamiast pliku ZIP.
   Napraw: wgraj plik `iaai-importer.zip` (patrz KROK 2), nie sam folder.

▸ Brak przycisku „Wyślij wtyczkę na serwer"
   Przyczyna: część hostingów blokuje wgrywanie wtyczek z panelu.
   Napraw: wgraj folder `iaai-importer` przez FTP do `wp-content/plugins/`,
   potem włącz wtyczkę w panelu (Wtyczki → Zainstalowane wtyczki → Włącz).

▸ Plik ZIP jest za duży / błąd „przekroczono limit wgrywania"
   Napraw: wgraj wtyczkę przez FTP (jak wyżej) albo poproś hosting o zwiększenie
   limitu „upload_max_filesize".

▸ Strona „Nasze auta" nie powstała
   Napraw: wejdź do panelu i odśwież (wtyczka tworzy ją też przy pierwszym wejściu
   do panelu). Jeśli dalej nie ma — utwórz ręcznie stronę z kodem [iaai_pojazdy].

▸ Podstrona nie dodała się do menu
   To normalne, gdy motyw nie ma jeszcze menu. Dodaj ręcznie — patrz KROK 7.

▸ Auta się nie pokazują (strona pusta)
   • Jeśli NIE zrobiłeś Części III — to oczekiwane; auta pojawią się po
     uruchomieniu automatyzacji.
   • Jeśli automatyzacja działa, a jest pusto — daj jej kilkanaście minut na
     pierwszy przebieg; potem sprawdź logi (opis w 03/05).

▸ Zdjęcia się nie ładują
   Zdjęcia są pokazywane wprost z serwerów IAAI. Sprawdź, czy masz połączenie
   z internetem po stronie serwera i czy IAAI nie jest chwilowo niedostępne.

▸ Strona wygląda „inaczej niż reszta witryny"
   Wtyczka celowo dziedziczy wygląd Twojego motywu (kolory, fonty). Jeśli chcesz
   inaczej — motyw/CSS możesz dostroić; auta są w neutralnej siatce kart.

▸ Automatyzacja nie działa / nie mam VPS
   Program zbierający wymaga serwera VPS z dostępem SSH. Na hostingu współdzielonym
   nie uruchomisz go — rozważ VPS albo poproś dostawcę o odpowiedni plan.

Więcej i dokładniej: docs/klient/05-problemy-i-pytania.md


────────────────────────────────────────────────────────────────────────
CZĘŚĆ V — FAQ (najczęstsze pytania)
────────────────────────────────────────────────────────────────────────

P: Czy muszę coś robić codziennie?
O: Nie. Po uruchomieniu system działa sam 24/7 — pobiera nowe auta i aktualizuje stronę.

P: Czy zdjęcia zajmują miejsce na moim hostingu?
O: Nie. Domyślnie zdjęcia są pokazywane bezpośrednio z serwerów IAAI (0 miejsca
   na dysku). Jest też opcjonalny tryb pobierania zdjęć do WordPressa, jeśli wolisz.

P: Skąd biorą się dane aut?
O: Z publicznie widocznych ofert na iaai.com. System kopiuje je 1:1 do Twojej bazy.

P: Czy auta same znikają, gdy schodzą z aukcji?
O: Tak. Wpis jest wtedy ukrywany (przechodzi w „szkic") — nie kasujemy historii.

P: Czy to jest zoptymalizowane pod Google (SEO)?
O: Tak. Każde auto ma dane strukturalne (Schema.org „Car"), opis, podgląd do
   udostępniania (Open Graph) i opisowe zdjęcia. Auta trafiają też do mapy strony
   (sitemap) WordPressa. Jeśli masz wtyczkę SEO (Yoast/Rank Math) — nie kłócą się.

P: Mam już wtyczkę SEO (Yoast/Rank Math). Będzie konflikt?
O: Nie. Wtedy tytuły/opisy zostawiamy Twojej wtyczce SEO, a sami dokładamy tylko
   dane strukturalne pojazdu, których wtyczki SEO nie generują.

P: Czy mogę zmienić, ile aut pokazuje strona?
O: Tak — w „krótkim kodzie" zmień liczbę, np. [iaai_pojazdy ile="12"].

P: Czy mogę przenieść/zmienić nazwę strony „Nasze auta"?
O: Tak. To zwykła strona WordPress — edytuj ją, przenieś w menu, dodaj własny tekst.

P: Czy wtyczka jest bezpieczna?
O: Tak. Przeszła audyt bezpieczeństwa (ocena 9/10): zabezpieczenia przed
   SQL injection, XSS, SSRF, kontrola wgrywanych zdjęć, brak sekretów w kodzie.

P: Aktualizacja wtyczki w przyszłości — stracę dane?
O: Nie. Dane aut są w bazie; podmiana plików wtyczki ich nie usuwa.

P: Nie mam VPS — co robić?
O: Sama wtyczka (pokazywanie aut) działa na zwykłym WordPressie. Automatyzacja
   pobierania wymaga VPS — załóż VPS albo poproś dostawcę hostingu o taki plan.


────────────────────────────────────────────────────────────────────────
CZĘŚĆ VI — SŁOWNICZEK (proste tłumaczenia)
────────────────────────────────────────────────────────────────────────

• Wtyczka (plugin) — mały dodatek do WordPressa, który dokłada nową funkcję.
• Shortcode („krótki kod") — gotowy „klocek" w [nawiasach], który wstawiasz na
  stronę, a on sam coś wyświetla (u nas: siatkę aut).
• CPT / „Pojazdy" — specjalny typ wpisów WordPressa; tu trafiają auta.
• VPS — Twój prywatny serwer, na którym można uruchamiać własne programy.
• SSH / terminal — sposób łączenia się z serwerem i wpisywania poleceń tekstem.
• FTP — sposób przesyłania plików na serwer (np. programem FileZilla).
• Baza danych — magazyn, w którym WordPress trzyma treści; tu też trzymamy auta.
• Hotlink — pokazywanie zdjęcia wprost z cudzego serwera (bez kopiowania na dysk).
• SEO — optymalizacja pod wyszukiwarki (żeby Google lepiej pokazywał Twoje auta).


────────────────────────────────────────────────────────────────────────
GDY UTKNIESZ
────────────────────────────────────────────────────────────────────────

1. Zajrzyj do CZĘŚCI IV (co może pójść nie tak) i FAQ powyżej.
2. Szczegółowe instrukcje etapami są w folderze docs/klient/:
     00-START-TUTAJ.md · 01-instalacja-wtyczki.md · 02-pokaz-auta-na-stronie.md
     03-uruchom-automatyzacje.md · 04-jak-dziala-i-obsluga.md · 05-problemy-i-pytania.md
3. Część techniczną (Część III) możesz spokojnie przekazać administratorowi
   hostingu — wystarczy, że pokażesz mu rozdział „Uruchomienie automatyzacji".

Powodzenia! Po wgraniu wtyczki i uruchomieniu automatyzacji nie musisz już
robić nic — auta pojawią się i będą aktualizować się same.
========================================================================
