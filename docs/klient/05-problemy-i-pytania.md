# Problemy i pytania (FAQ) + słowniczek

## Najczęstsze sytuacje

### Na stronie nie ma żadnych aut
1. Czy zrobiłeś **Etap 3**? Bez programu zbierającego baza jest pusta.
2. Odpal jeden cykl ręcznie i zobacz log:
   ```
   sudo systemctl start iaai-importer-live.service
   journalctl -u iaai-importer-live.service -n 60 --no-pager
   ```
3. Sprawdź, czy w bazie są auta:
   ```
   wp eval 'global $wpdb; echo $wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->prefix}iaai_vehicles");' --path=/var/www/html
   ```
   - Liczba > 0, a strona pusta → sprawdź krótki kod `[iaai_pojazdy]` na stronie (Etap 2).
   - Liczba = 0 → patrz log z punktu 2 (może blokada — patrz niżej).

### W logu widzę „BLOKADA"
Serwis IAAI chwilowo zablokował ruch. To normalne zabezpieczenie. System sam zwalnia i spróbuje
przy kolejnym cyklu. Jeśli powtarza się stale — zwiększ odstęp (Etap 4: częstotliwość) lub zawęź
zakres pobierania (zapytaj nas).

### Wtyczka się nie wgrała (Etap 1)
- Wysyłaj **plik ZIP**, nie folder.
- Brak opcji wgrania w panelu → wgraj folder `iaai-importer` przez FTP do `wp-content/plugins/`,
  potem włącz wtyczkę w **Wtyczki → Zainstalowane**.

### Instalator (Etap 3) przerwał z błędem
Komunikat podpowiada, czego brakuje:
- „Brak python3" / „Brak WP-CLI" → poproś dostawcę hostingu o instalację.
- „to nie katalog WordPressa" → podaj poprawną ścieżkę (gdzie jest `wp-config.php`).
- „hosting współdzielony" → potrzebny VPS (patrz [00-START-TUTAJ.md](00-START-TUTAJ.md)).

### Auta są, ale bez zdjęć
Zdjęcia ładują się z serwerów IAAI/Copart. Jeśli serwis usunął zdjęcie danego auta — nie
wyświetli się. To normalne dla aut już zdjętych z aukcji.

### Z Copart nic nie przychodzi (a IAAI działa)
To najczęściej **kwestia logowania**, nie błąd wtyczki:
- Copart zwykle oddaje pełne dane i zdjęcia dopiero **po zalogowaniu na konto Member**.
  Uruchom źródło `copart` z aktualnymi ciasteczkami sesji (`COPART_COOKIES`) — patrz
  [Etap 3 → „Drugie źródło — Copart"](03-uruchom-automatyzacje.md).
- Ciasteczka **wygasają** — jeśli Copart nagle przestał zwracać auta, odśwież je (zaloguj się
  ponownie i wklej nowe).
- Copart mocno filtruje automaty (Cloudflare). Puste wyniki bez ważnej sesji to **zachowanie
  serwisu**. Jeśli nie masz konta Copart — zostaw samo IAAI, strona działa normalnie.

### Aktualizuję istniejącą instalację (miałem tylko IAAI)
W wersji z drugim źródłem zmienił się **klucz główny bazy** (doszła kolumna „źródło").
- **Nowa/świeża instalacja albo demo:** nic nie robisz — tabele zakładają się poprawnie same.
- **Istniejąca baza z samym IAAI:** trzeba ją **jednorazowo zmigrować** (dodać kolumnę `source`
  z wartością `iaai` i przełożyć klucz na parę „źródło + numer aukcji"). Jeśli aktualizujesz
  działającą instalację — **napisz do nas przed aktualizacją**, podeślemy gotowe polecenie
  migracji dopasowane do Twojej bazy. Starych danych IAAI to nie usuwa.

---

## Słowniczek (proste tłumaczenia)
- **IAAI** — amerykański serwis aukcji samochodów (źródło danych nr 1).
- **Copart** — drugi amerykański serwis aukcji samochodów (źródło danych nr 2; wymaga konta
  Member i sesji logowania — `COPART_COOKIES`).
- **Konto Member / ciasteczka sesji** — dane zalogowania do Copart; pozwalają programowi pobrać
  pełne dane i zdjęcia. Wygasają — czasem trzeba je odświeżyć.
- **Wtyczka (plugin)** — dodatek do WordPress; tu: pokazuje auta na stronie.
- **Scraper / program zbierający** — program, który czyta auta z IAAI i wpisuje do bazy.
- **Baza danych** — „magazyn" danych Twojej strony (auta tam siedzą).
- **VPS** — Twój własny serwer, na którym można uruchamiać programy (potrzebny do Etapu 3).
- **SSH / terminal** — „czarne okno" do wpisywania poleceń na serwerze.
- **Krótki kod (shortcode)** — `[iaai_pojazdy]`; klocek, który pokazuje auta na stronie.
- **VIN** — numer nadwozia auta (bywa częściowo zakryty — to normalne).
- **Lot / salvage** — pojedyncza aukcja/sztuka auta w IAAI.
- **systemd / timer** — mechanizm serwera, który uruchamia program co jakiś czas (sam).

---

## Potrzebujesz pomocy?
Zbierz te informacje i wyślij do nas:
- co robiłeś (który Etap), pełną treść komunikatu błędu,
- wynik: `journalctl -u iaai-importer-live.service -n 60 --no-pager`.

Dla zaawansowanych / administratora: szczegóły techniczne w `deploy/README.md`,
opis całości w `STATUS.md`, audyt w `docs/AUDIT2.md`.
