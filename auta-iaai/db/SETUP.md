# Uruchomienie nowej bazy (MySQL / WordPress) i podgląd

Schemat źródłowy: [`schema.sql`](schema.sql) (MySQL 5.7+/MariaDB 10.3+). Poniżej jak go
uruchomić lokalnie i obejrzeć tabele wizualnie.

---

## Wariant A (zalecany dla WordPressa) — „Local" by Flywheel/WP Engine
Najprostsze środowisko WP z MySQL + narzędziami bazodanowymi.

1. Pobierz i zainstaluj **Local**: https://localwp.com (darmowe).
2. *Create a new site* → nazwa np. `iaai` → poczekaj aż wstanie (daje WP + MySQL).
3. W oknie strony zakładka **Database** → otwórz **Adminer** (przycisk *Open Adminer*).
4. W Adminer: lewa kolumna → baza `local` (to baza WordPressa).
5. Zakładka **SQL command** → wklej całą zawartość `db/schema.sql` → **Execute**.
6. Tabele `iaai_vehicles` i `iaai_vehicle_images` pojawią się na liście — klikasz i przeglądasz dane jak w arkuszu.

> Wskazówka: w docelowej wtyczce te tabele będą zakładane automatycznie przy
> aktywacji (`dbDelta()`), z prefiksem instalacji, np. `wp_iaai_vehicles`.

---

## Wariant B — XAMPP (klasyczny Apache+MySQL+phpMyAdmin)
1. Zainstaluj **XAMPP**: https://www.apachefriends.org → uruchom **MySQL** w panelu.
2. Otwórz **phpMyAdmin**: http://localhost/phpmyadmin
3. *New* → utwórz bazę np. `iaai` (kodowanie `utf8mb4_unicode_ci`).
4. Zaznacz bazę → zakładka **Import** → wybierz plik `db/schema.sql` → **Go**.
5. Tabele widoczne po lewej; klik w `iaai_vehicles` → **Browse** = podgląd danych.

---

## Wariant C — wiersz poleceń (jeśli masz klienta `mysql`)
```bash
# utwórz bazę
mysql -u root -p -e "CREATE DATABASE iaai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
# załaduj schemat
mysql -u root -p iaai < db/schema.sql
# podejrzyj
mysql -u root -p iaai -e "SHOW TABLES; DESCRIBE iaai_vehicles;"
```

Do podglądu wizualnego bez phpMyAdmin: **DBeaver** (https://dbeaver.io) — łączysz się z MySQL i klikasz po tabelach.

---

## Wariant D — przenośna instancja (GOTOWA, postawiona bez sudo)
W `~/iaai-mariadb` stoi przenośna **MariaDB 11.4.4** z załadowanym `schema.sql`
i przykładowym rekordem. Nie wymaga sudo ani instalacji systemowej.

**Dane połączenia (GUI / DBeaver / aplikacja):**
| | |
|---|---|
| Host | `127.0.0.1` |
| Port | `3307` |
| Baza | `iaai` |
| User / hasło | `iaai` / `iaai` |

**Sterowanie (skrypty w `~/iaai-mariadb/`):**
```bash
~/iaai-mariadb/start-db.sh      # uruchom serwer (po restarcie komputera)
~/iaai-mariadb/stop-db.sh       # zatrzymaj
~/iaai-mariadb/connect-db.sh    # klient SQL prosto do bazy iaai
# np.: ~/iaai-mariadb/connect-db.sh -e "SELECT * FROM iaai_vehicles\G"
```
W DBeaver: *New Connection → MariaDB* → host `127.0.0.1`, port `3307`,
baza `iaai`, user `iaai`, hasło `iaai` → **Finish** → klikasz po tabelach.

> Uwaga: to instancja deweloperska. Docelowo w produkcji baza żyje w MySQL
> WordPressa (Warianty A–C), a tabele zakłada wtyczka przez `dbDelta()`.

## Szybki test z przykładowym rekordem
Po założeniu tabel możesz wrzucić jeden „złapany" listing, żeby zobaczyć dane:
```sql
INSERT INTO iaai_vehicles
  (salvage_id, vin, year, make, model, transmission, odometer, odometer_uom,
   odometer_brand, run_and_drive, key_available, buy_now, detail_url)
VALUES
  (45293605, 'WBAPM5C50AE000000', 2010, 'BMW', '335I', 'Automatic', 169594, 'mi',
   'Not Required/Exempt', 'Run & Drive', 'Available', 2100.00,
   'https://www.iaai.com/VehicleDetail/45293605~US');

INSERT INTO iaai_vehicle_images
  (salvage_id, image_key, seq, width, height, url)
VALUES
  (45293605, '45293605~SID~B518~S1~I1~RW2576~H1932~TH0', 1, 2576, 1932,
   'https://vis.iaai.com/resizer?imageKeys=45293605~SID~B518~S1~I1~RW2576~H1932~TH0&width=1024&height=768');
```
Następnie `SELECT * FROM iaai_vehicles;` — zobaczysz pojazd, a `url` ze zdjęcia
otworzysz w przeglądarce (realne zdjęcie z IAAI).
