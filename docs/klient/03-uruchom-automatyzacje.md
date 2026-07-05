# Etap 3 — Uruchom automatyzację (program zbierający auta)

Cel: uruchomić na serwerze program, który **sam, całą dobę** pobiera auta z IAAI (i opcjonalnie
z Copart) do bazy. To najbardziej „techniczny" etap — ale przygotowaliśmy **instalator**, który
robi wszystko za Ciebie jednym poleceniem. Wystarczy kopiuj-wklej.

> ℹ️ Domyślnie automatyzacja startuje na **IAAI** (działa od razu). **Copart** to drugie,
> opcjonalne źródło — włączasz je osobno, bo wymaga konta (patrz sekcja „Drugie źródło — Copart"
> niżej).

> ⚠️ Ten etap wymaga **serwera VPS z dostępem do terminala (SSH)**. Jeśli masz tylko zwykły
> hosting współdzielony — napisz do dostawcy: *„Potrzebuję VPS z dostępem SSH i możliwością
> uruchomienia Pythona oraz usług systemd"*. Bez tego program nie ruszy (sama strona z Etapów
> 1–2 będzie działać, ale nie będzie skąd brać aut).

---

## Co musi być na serwerze (poproś hosting, jeśli czegoś brak)
- **Python 3.10+** (sprawdzenie: `python3 --version`)
- **WP-CLI** — narzędzie `wp` ([instrukcja](https://wp-cli.org/#installing))
- **Dostęp `sudo`** (uprawnienia administratora serwera)

---

## Krok po kroku

**1. Połącz się z serwerem przez SSH.**
Z komputera (Windows: program „PowerShell" lub „PuTTY"; Mac/Linux: „Terminal"):
```
ssh uzytkownik@adres-twojego-serwera
```
(dane logowania dostajesz od dostawcy VPS).

**2. Wgraj paczkę na serwer.** Najłatwiej:
```
# będąc w terminalu serwera, w swoim katalogu:
git clone <ADRES-REPO> iaai-importer
cd iaai-importer
```
Jeśli nie używasz git — wgraj rozpakowaną paczkę przez program FTP (np. FileZilla) do katalogu
na serwerze, a potem wejdź do niego: `cd /sciezka/do/iaai-importer`.

**3. Uruchom instalator** — podaj ścieżkę do swojego WordPressa
(zwykle `/var/www/html`; jeśli nie wiesz — zapytaj hosting):
```
sudo bash deploy/install.sh /var/www/html
```

Instalator sam:
- sprawdzi wymagania,
- zainstaluje program zbierający i przeglądarkę,
- wgra i włączy wtyczkę (założy tabele),
- ustawi automatyczne uruchamianie (co 15 minut „nowe auta" + raz dziennie „pełna synchronizacja").

Na końcu zobaczysz **„GOTOWE ✅”**.

**4. (Opcjonalnie) Odpal pierwsze pobranie od razu**, nie czekając 15 minut:
```
sudo systemctl start iaai-importer-live.service
```

✅ **Gotowe.** Od tej chwili auta z IAAI same trafiają na stronę i same z niej znikają.

---

## Drugie źródło — Copart (opcjonalnie)

Copart to **drugie źródło** aut. Działa tak samo jak IAAI (te same dane, zdjęcia, plakietka
„Copart" i filtr na liście), ale ma dwie różnice, o których warto wiedzieć:

1. **Silniejsza ochrona przed automatami** (Cloudflare). Anonimowo Copart często oddaje
   niepełne dane.
2. **Pełne dane i zdjęcia zwykle wymagają zalogowania na konto Member.** Dlatego Copart
   uruchamiamy z **ciasteczkami sesji** zalogowanego konta (zmienna `COPART_COOKIES`).

**Jak włączyć Copart (gdy masz konto Copart Member):**
```
# 1) Zaloguj się na copart.com w przeglądarce, skopiuj ciasteczka sesji
#    (Narzędzia deweloperskie → Application/Storage → Cookies) do jednej linii.
# 2) Uruchom przebieg dla źródła "copart" z tymi ciasteczkami:
COPART_COOKIES="tu-wklej-ciasteczka" \
  python3 scraper/run_pipeline.py --source copart --mode live
```
Ten sam program obsługuje oba źródła — dla IAAI uruchamiasz go z `--source iaai` (to robi
instalator automatycznie), dla Copart z `--source copart`. Dane z obu źródeł trafiają do
**tej samej bazy** (rozróżnia je kolumna „źródło") i na **tę samą stronę**.

> ⚠️ **Ważne (uczciwie):** moduł Copart jest gotowy od strony programu, ale — z uwagi na
> ochronę Cloudflare i wymóg logowania — **realne, ciągłe pobieranie z Copart trzeba
> potwierdzić na Twoim serwerze VPS** (tak samo jak przy IAAI: tam też walidujemy na żywo).
> Bez ważnej sesji Member Copart potrafi zwracać puste wyniki — to zachowanie serwisu, nie błąd
> wtyczki. Jeśli nie masz konta Copart — po prostu zostaw samo IAAI; strona działa normalnie.

---

## Skąd wiem, że działa?
```
# podgląd na żywo (Ctrl+C aby wyjść):
journalctl -u iaai-importer-live.service -n 40 --no-pager

# kiedy następne automatyczne uruchomienie:
systemctl list-timers 'iaai-importer-*'
```
Po chwili wejdź na stronę z Etapu 2 — powinny pojawić się auta.

## Ważne (zgodność / prawo)
Pobieranie danych z serwisu zewnętrznego podlega jego regulaminowi (ToS). Decyzja o uruchomieniu
i zakresie pobierania należy do Ciebie jako właściciela strony. Program respektuje ograniczenia
tempa i wykrywa blokady (gdy serwis zacznie blokować — sam zwalnia/odpuszcza).

Następnie: **[Etap 4 — jak to działa i obsługa →](04-jak-dziala-i-obsluga.md)**.
