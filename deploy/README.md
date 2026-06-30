# Wdrożenie na VPS klienta — automatyzacja always-on

Cel: scraper Python chodzi **sam, cały czas** na tym samym VPS co WordPress klienta,
wyłapuje nowe auta z IAAI, zapisuje do **bazy WordPressa** i publikuje je na stronie —
bez udziału operatora. (Patrz STATUS.md sekcja 1: wymóg always-on + model wdrożenia.)

```
VPS klienta:
  WordPress + MySQL  ──┐
  wtyczka iaai-importer │  (czyta wp_iaai_* -> CPT „pojazd" -> front)
  scraper Python (usługa) ┘  systemd timer -> cykl live -> pisze do wp_iaai_* -> wp eval publish
```

## Wymagania VPS
- WordPress z dostępem do shella (nie „shared hosting") + **WP-CLI** (`wp`).
- **Python 3.10+**, możliwość instalacji **Playwright + Chromium** (`playwright install chromium`).
- Dostęp do bazy MySQL/MariaDB WordPressa (lokalnie, po `localhost`).
- systemd (standard na większości VPS z Linuksem).

## Instalacja (skrót)
```bash
# 1. Kod na serwer (przykładowo do /opt/iaai-importer):
sudo git clone <repo> /opt/iaai-importer
cd /opt/iaai-importer

# 2. Środowisko Pythona + zależności (wszystkie działy) + przeglądarka:
python3 -m venv .venv
for r in scraper/dzialy/*/requirements.txt; do .venv/bin/pip install -r "$r"; done
.venv/bin/playwright install chromium

# 3. Wtyczka WordPress — skopiuj i aktywuj (tabele wp_iaai_* założą się SAME przez dbDelta):
cp -r wp-plugin/iaai-importer /var/www/html/wp-content/plugins/
wp plugin activate iaai-importer --path=/var/www/html

# 4. Konfiguracja środowiska usług:
sudo cp deploy/iaai-importer.env.example /etc/iaai-importer.env
sudo nano /etc/iaai-importer.env      # ustaw WP_PATH, WP_CLI, SCRAPER_DIR, PYTHON

# 5. Usługi systemd (live co 15 min + backfill raz na dobę):
sudo cp deploy/iaai-importer-*.service deploy/iaai-importer-*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now iaai-importer-live.timer
sudo systemctl enable --now iaai-importer-backfill.timer
```

## Jak to spina się z resztą
- **Baza:** `deploy/iaai-env.sh` czyta dane dostępowe z `wp-config.php` przez WP-CLI i ustawia
  `IAAI_DB_*` + `IAAI_DB_TABLE_PREFIX` (= `table_prefix`, np. `wp_`). Dzięki temu agenci Pythona
  piszą do **tych samych** tabel (`wp_iaai_vehicles`, `wp_iaai_vehicle_images`), które czyta wtyczka.
  Hasła są tylko w `wp-config.php` — nie duplikujemy ich.
- **Cykl:** `deploy/iaai-live-cycle.sh` = `run_pipeline.py --mode live` → `wp eval 'iaai_publish_all_active();'`.
- **Harmonogram:** `iaai-importer-live.timer` (co 15 min od zakończenia poprzedniego, `Persistent`),
  `iaai-importer-backfill.timer` (`full` + reconcile o 03:30).

## Test po instalacji
```bash
sudo systemctl start iaai-importer-live.service     # jednorazowy cykl od ręki
journalctl -u iaai-importer-live.service -n 50 --no-pager
systemctl list-timers 'iaai-importer-*'             # kiedy następne odpalenie
wp eval 'global $wpdb; var_dump($wpdb->get_var("SELECT COUNT(*) FROM {$wpdb->prefix}iaai_vehicles"));' --path=/var/www/html
```

## Dostrojenie
- **Interwał live:** `OnUnitInactiveSec` w `iaai-importer-live.timer` (domyślnie 15 min).
- **Zakres oferty:** `IAAI_BASE` w `/etc/iaai-importer.env` (można zawęzić filtrami wyszukiwarki).
- **Rate-limit / zgodność:** dział 7 (zgody) pilnuje robots + tempa; przy blokadach krytyk zgłasza.
- **Uwaga prawna:** scraping `/Search` IAAI to decyzja biznesowo-prawna (ToS) właściciela projektu.
