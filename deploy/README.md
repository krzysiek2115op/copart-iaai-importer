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
