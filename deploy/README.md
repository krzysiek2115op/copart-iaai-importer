<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Wdrożenie scrapera na VPS

Cykliczny import motocykli (`python3 -m scraper.main`) uruchamiany z harmonogramu.
Zalecany wariant: **systemd timer** (czytelne logi w journalu, kontrola kodu wyjścia).
Wariant alternatywny: **cron**.

Założenia przykładów: kod w `/opt/polea` (katalog zawiera podkatalog `scraper/`),
dedykowany użytkownik systemowy `polea`, poświadczenia bazy w `/etc/polea.env`.

## 1. Przygotowanie
```bash
sudo useradd --system --home /opt/polea --shell /usr/sbin/nologin polea
sudo mkdir -p /opt/polea /opt/polea/run /var/log/polea
sudo cp -r scraper /opt/polea/
sudo python3 -m venv /opt/polea/venv
sudo /opt/polea/venv/bin/pip install -r /opt/polea/scraper/requirements.txt
sudo cp deploy/polea.env.example /etc/polea.env   # UZUPEŁNIJ hasło, chmod 600
sudo chmod 600 /etc/polea.env
sudo chown -R polea:polea /opt/polea /var/log/polea
```

## 2a. systemd (zalecane)
```bash
sudo cp deploy/systemd/polea-import.service /etc/systemd/system/
sudo cp deploy/systemd/polea-import.timer   /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now polea-import.timer
systemctl list-timers polea-import.timer        # podgląd następnego uruchomienia
journalctl -u polea-import.service -n 50         # logi ostatniego przebiegu
```
Niezerowy kod wyjścia (np. **2** = wykryta zmiana formatu źródła, patrz Dział 5) oznacza
przebieg jako `failed` — łatwe do wyłapania przez monitoring (`systemctl is-failed`).

## 2b. cron (alternatywa)
```bash
sudo cp deploy/cron/polea-import.cron /etc/cron.d/polea-import
sudo cp deploy/logrotate/polea /etc/logrotate.d/polea
```

## Kody wyjścia
| Kod | Znaczenie |
|---|---|
| 0 | OK |
| 1 | inny import już działa (flock) — normalne przy nakładaniu przebiegów |
| 2 | >60% rekordów odrzuconych — prawdopodobna zmiana formatu źródła; zapis wstrzymany |

Blokada pojedynczej instancji (`flock`) jest wbudowana — bezpiecznie nakładające się terminy.

## Bezpieczeństwo serwera (zalecane, poza kodem)

Pełny opis: `docs/SECURITY-AUDIT.md` (Iteracja 3, pkt C). Skrót:

- **MySQL least privilege — dwa konta.** Scraper: `SELECT, INSERT, UPDATE` na `polea.*` (bez `DELETE/DROP/GRANT/FILE`). Wtyczka WP: **tylko `SELECT`** (czyta wyłącznie):
  ```sql
  CREATE USER 'polea_ro'@'10.0.0.%' IDENTIFIED BY '...';
  GRANT SELECT ON polea.* TO 'polea_ro'@'10.0.0.%';
  ```
  W `wp-config.php`: `define('POLEA_DB_USER','polea_ro');`
- **TLS do bazy** przy połączeniu zdalnym: scraper → `POLEA_DB_SSL_CA`; MySQL → `require_secure_transport=ON`.
- **Firewall egress na VPS** (mitygacja DNS-rebinding/SSRF): blok ruchu do sieci wewnętrznych i `169.254.169.254`.
- **Nagłówki HTTP na serwerze WWW** (dla całej witryny): `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-Frame-Options: SAMEORIGIN`, oraz `Content-Security-Policy` z **dozwolonym `img-src https://poleasingowe.pl`** (hotlink zdjęć).
- **Sekrety:** `/etc/polea.env` z `chmod 600`, poza repo (`.gitignore` blokuje `*.env`).

## Kopia zapasowa i odzyskiwanie

Skrypt `deploy/backup/polea-backup.sh` robi `mysqldump` (spójny snapshot InnoDB, bez blokad) + rotację.
Hasło idzie przez `MYSQL_PWD` (niewidoczne w `ps`). Wystarczy konto z prawem `SELECT` (np. `polea_ro`).

```bash
sudo install -m 700 deploy/backup/polea-backup.sh /opt/polea/polea-backup.sh
# codziennie 03:30, log do dziennika crona:
echo '30 3 * * *  polea  POLEA_BACKUP_DIR=/var/backups/polea /opt/polea/polea-backup.sh >> /var/log/polea/backup.log 2>&1' \
  | sudo tee /etc/cron.d/polea-backup
```
Zmienne: `POLEA_BACKUP_DIR` (domyślnie `/var/backups/polea`), `POLEA_BACKUP_KEEP` (domyślnie 14 kopii).
**Odtworzenie:** `gunzip -c /var/backups/polea/polea_<ts>.sql.gz | mysql -u <user> -p polea`.

## Monitoring importu

- **systemd:** stan ostatniego przebiegu `systemctl is-failed polea-import.service`; alert przez `OnFailure=` (własna jednostka powiadamiająca) lub `systemctl --failed` w monitoringu.
- **cron:** dodaj `MAILTO=ops@twojadomena.pl` na górze `/etc/cron.d/polea-import` — niezerowy kod wyjścia (2 = zmiana formatu źródła, 1 = już działa) trafi mailem.
- Kod wyjścia importu jest znaczący (patrz tabela wyżej) — nadaje się do dowolnego zewnętrznego monitoringu (Healthchecks.io, Zabbix, itp.).
