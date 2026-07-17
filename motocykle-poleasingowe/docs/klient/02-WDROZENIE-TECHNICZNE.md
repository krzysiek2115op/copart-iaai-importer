<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Wdrozenie techniczne — Importer Motocykli (poleasingowe.pl)

Dokument dla osoby technicznej (administrator WordPress / hosting / DevOps).
Opisuje pelne wdrozenie w dwoch wariantach:

- WARIANT 1 — pelny self-hosting: klient uruchamia u siebie tez scraper (VPS).
- WARIANT 2 — scraper hostujemy my; klient wdraza tylko wtyczke WP + dostep do bazy.

Czesci A i B (wtyczka + baza) sa wspolne dla obu wariantow. Czesc C dotyczy tylko
WARIANTU 1. Sekcja „Wariant 2" opisuje uproszczony rozdzial obowiazkow.

## Architektura (3 warstwy)

```
[ poleasingowe.pl ]  --(scraper Python, Dzialy 1-7)-->  [ MySQL: polea_* ]  --(odczyt RO)-->  [ Wtyczka WP ]
        zrodlo                 VPS / cron                    osobna baza                      strona klienta
```

- Scraper (Python 3, tylko stdlib + leniwie requests/PyMySQL) crawluje zrodlo,
  normalizuje, audytuje, deduplikuje i robi upsert do osobnej bazy MySQL.
- Wtyczka WordPress czyta te baze **tylko do odczytu** (mysqli) i renderuje
  podstrone „Nasze motory". Nie uzywa `wpdb` — zla baza nie moze ubic strony.
- Zdjecia sa **hotlinkowane** (nie kopiowane na serwer klienta).

## Wymagania

| Warstwa | Wymaganie |
|---|---|
| WordPress | 6.0+ , PHP 7.4+ (rozszerzenie mysqli) |
| Baza | MySQL 5.7+ lub MariaDB 10.2+ , InnoDB , utf8mb4 |
| Scraper (Wariant 1) | Python 3.8+ , dostep sieciowy do poleasingowe.pl |
| Przyjazne odnosniki | Wlaczone (Ustawienia -> Bezposrednie odnosniki), dla ladnych URL-i |

## CZESC A — Wtyczka WordPress (oba warianty)

### A1. Instalacja
1. Panel WP: Wtyczki -> Dodaj nowa -> Wyslij wtyczke na serwer -> `motocykle-poleasingowe.zip` -> Zainstaluj -> Wlacz.
   (Alternatywnie rozpakuj katalog `motocykle-poleasingowe/` do `wp-content/plugins/`.)
2. Po aktywacji wtyczka sama tworzy strone „Nasze motory" (`[motocykle]`) i wpina ja w menu
   (motyw blokowy: `wp_navigation`; klasyczny: menu location `primary` lub pierwsze).

### A2. Poswiadczenia bazy (wp-config.php)
Dodaj powyzej linii „That's all, stop editing":

```
define('POLEA_DB_HOST', '127.0.0.1');   // lub host zdalnej bazy
define('POLEA_DB_NAME', 'polea');
define('POLEA_DB_USER', 'polea_ro');     // ZALECANE: uzytkownik TYLKO-ODCZYT
define('POLEA_DB_PASSWORD', 'silne-haslo');
// opcjonalnie: define('POLEA_DB_PORT', 3306);
```

Zasada najmniejszych uprawnien: wtyczka potrzebuje wylacznie `SELECT`. Uzyj
osobnego uzytkownika `polea_ro` (GRANT nizej), nie tego, ktorym pisze scraper.

### A3. Weryfikacja
- Ustawienia -> Motocykle: powinno byc „Polaczono. Motocykli w bazie: N".
- Wejdz na podstrone „Nasze motory" — lista + widok pojedynczy.
- Po wdrozeniu z ladnymi URL-ami odswiez raz: Ustawienia -> Bezposrednie odnosniki -> Zapisz
  (przebudowuje reguly przepisan; inaczej `/nasze-motory/<lot_id>/` moze dawac 404).

## CZESC B — Baza MySQL (oba warianty)

### B1. Utworzenie bazy i schematu
```
CREATE DATABASE polea CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
mysql -u root -p polea < db/schema.sql
```
Szczegoly tabel i kolumn opisuje osobny dokument „03 — Schemat bazy".

### B2. Uzytkownicy (rozdzial uprawnien)
```
-- Scraper: zapis (INSERT/UPDATE/DELETE + SELECT)
CREATE USER 'polea'@'%' IDENTIFIED BY 'silne-haslo-zapisu';
GRANT SELECT, INSERT, UPDATE, DELETE ON polea.* TO 'polea'@'%';

-- Wtyczka WP: tylko odczyt
CREATE USER 'polea_ro'@'%' IDENTIFIED BY 'silne-haslo-odczytu';
GRANT SELECT ON polea.* TO 'polea_ro'@'%';
FLUSH PRIVILEGES;
```
Ogranicz `@'%'` do konkretnych adresow (host WP / host scrapera), gdy to mozliwe.
Do zdalnego polaczenia wlacz TLS (`POLEA_DB_SSL_CA`).

## CZESC C — Scraper na VPS (tylko WARIANT 1)

### C1. Rozmieszczenie
```
sudo useradd -r -s /usr/sbin/nologin polea
sudo mkdir -p /opt/polea /var/log/polea /opt/polea/run
# skopiuj katalog scraper/ (i db/) do /opt/polea/
sudo python3 -m venv /opt/polea/venv
/opt/polea/venv/bin/pip install requests PyMySQL
sudo chown -R polea:polea /opt/polea /var/log/polea
```

### C2. Konfiguracja (env)
```
sudo cp deploy/polea.env.example /etc/polea.env
sudo chmod 600 /etc/polea.env      # zawiera haslo — tylko root
# w /etc/polea.env ustaw POLEA_DB_USER=polea (uzytkownik ZAPISU) i haslo
```

### C3. Pierwsze uruchomienie (test)
```
cd /opt/polea
set -a; . /etc/polea.env; set +a
# suchy przebieg bez zapisu (kilka lotow):
venv/bin/python3 -m scraper.main --limit 5 --dry-run -v
# realny zapis do bazy:
venv/bin/python3 -m scraper.main -v
```
Flagi: `--limit N` (test), `--dry-run` (bez zapisu), `--no-lock` (pomin blokade), `-v`.

### C4. Harmonogram — systemd (zalecane)
Pliki gotowe w `deploy/systemd/`:
```
sudo cp deploy/systemd/polea-import.service /etc/systemd/system/
sudo cp deploy/systemd/polea-import.timer   /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now polea-import.timer
systemctl list-timers polea-import.timer    # kontrola
journalctl -u polea-import.service -n 50    # logi ostatniego przebiegu
```
Usluga jest utwardzona (NoNewPrivileges, ProtectSystem=strict, PrivateTmp,
RestrictAddressFamilies) i ma limit czasu 1800 s. Timer: co ~4 h z jitterem.

### C4-alt. Harmonogram — cron (alternatywa)
```
sudo cp deploy/cron/polea-import.cron /etc/cron.d/polea-import
```
Wpis uruchamia import co 4 h, ladujac `/etc/polea.env` i logujac do `/var/log/polea/import.log`.

### C5. Kopie zapasowe i rotacja logow
```
sudo cp deploy/logrotate/polea /etc/logrotate.d/polea
# backup bazy (przyklad w deploy/backup/polea-backup.sh) — podepnij pod cron/systemd
```

### C6. Bezpiecznik importu (reconcile)
Scraper nie zamyka masowo aukcji, gdy pojedynczy crawl „widzi" mniej niz
`POLEA_RECONCILE_MIN_RATIO` (domyslnie 0.5) dotychczas aktywnych — chroni przed
urwanym przebiegiem. W logu pojawi sie wtedy „Reconcile POMINIETY".

## WARIANT 2 — scraper hostujemy my

Podzial obowiazkow, gdy zasilanie bazy bierzemy na siebie:

| Obszar | Kto |
|---|---|
| Scraper (crawl, cron, VPS) | My — po naszej stronie |
| Baza MySQL (polea_*) | Do ustalenia: nasz host albo baza klienta z dostepem RO dla WP |
| Wtyczka WP + wp-config | Klient / jego technik (Czesc A) |

Wariant 2 = klient robi tylko **Czesc A** (wtyczka) i dostaje od nas:
poswiadczenia **tylko-do-odczytu** (`polea_ro`) oraz host/port bazy (najlepiej
przez TLS). Czesci B/C stawiamy my. Jesli baza jest u nas — klient poda tylko
te 4 stale w wp-config i ma gotowa podstrone.

## Aktualizacja wtyczki
1. Wgraj nowa wersje (nadpisujac katalog wtyczki) lub przez panel.
2. Jesli zmienily sie reguly URL: Ustawienia -> Bezposrednie odnosniki -> Zapisz.
3. Wersja bumpuje cache CSS automatycznie (staly `POLEA_VERSION`).

## Diagnostyka — typowe problemy

| Objaw | Przyczyna / rozwiazanie |
|---|---|
| „Brak stalych POLEA_DB_*" | Brak define w wp-config.php (Czesc A2). |
| „Nie udalo sie polaczyc" | Zly host/login/haslo lub firewall/port; sprawdz z hosta WP. |
| „brak tabeli polea_motocykle" | Nie zaladowano schema.sql (Czesc B1). |
| Podstrona „Brak motocykli" | Baza pusta lub wszystkie aukcje `zakonczona`; uruchom scraper. |
| `/nasze-motory/<id>/` = 404 | Odswiez przyjazne odnosniki (A3). |
| Sitemap ofert pusta | Wymaga wlaczonych ladnych URL-i + istniejacej podstrony. |
| Dublujace sie meta OG/JSON-LD | Motyw wstrzykuje wlasne meta — zawez w motywie do `is_front_page()`. |

## Bezpieczenstwo (podsumowanie)

- Wtyczka: prepared statements, escapowanie wyjscia, nonce+capability w adminie,
  mysqli z timeoutami (nie `wpdb`), `LOCAL INFILE` wylaczone, brak sekretow w kodzie.
- Scraper: allowlista hosta + anty-SSRF (odrzuca adresy prywatne/metadanych,
  rewalidacja kazdego przekierowania), limity rozmiaru/czasu odpowiedzi, rate-limit,
  `LOCAL INFILE` off, poswiadczenia tylko z env, lock pojedynczej instancji.
- Rozdziel uzytkownikow bazy: `polea` (zapis) dla scrapera, `polea_ro` (odczyt) dla WP.
- `/etc/polea.env` z haslem: `chmod 600`, nigdy w repozytorium.
