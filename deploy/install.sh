#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Importer Aukcji (IAAI + Copart).
# Licencja: GNU GPL v2 lub pozniejsza - pelny tekst w pliku LICENSE.
# =====================================================================
#  install.sh — INSTALATOR „NA TACY" automatyzacji IAAI na serwerze klienta.
#
#  Robi za Ciebie najtrudniejszy etap (scraper always-on):
#    1) sprawdza wymagania (python3, wp-cli),
#    2) tworzy środowisko Pythona + instaluje zależności + przeglądarkę,
#    3) wpina wtyczkę do WordPressa i ją włącza (tabele zakładają się same),
#    4) konfiguruje i włącza usługi systemd (live co 15 min + backfill 03:30).
#
#  UŻYCIE (na serwerze, w katalogu z rozpakowaną paczką):
#     sudo bash deploy/install.sh /sciezka/do/wordpressa
#  np. sudo bash deploy/install.sh /var/www/html
#
#  Wszystko jest opisane krok po kroku w docs/klient/03-uruchom-automatyzacje.md.
# =====================================================================
set -euo pipefail

WP_PATH="${1:-}"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WP_CLI="$(command -v wp || true)"
PY="$(command -v python3 || true)"

say()  { printf '\n\033[1;36m== %s\033[0m\n' "$*"; }
ok()   { printf '   \033[1;32m✔\033[0m %s\n' "$*"; }
die()  { printf '\n\033[1;31m✘ %s\033[0m\n' "$*" >&2; exit 1; }

say "0/5  Sprawdzam wymagania"
[ -n "$WP_PATH" ]      || die "Podaj ścieżkę do WordPressa, np.:  sudo bash deploy/install.sh /var/www/html"
[ -f "$WP_PATH/wp-config.php" ] || die "W $WP_PATH nie ma wp-config.php — to nie katalog WordPressa."
[ -n "$PY" ]           || die "Brak python3. Zainstaluj Pythona 3.10+ (poproś hosting/administratora)."
[ -n "$WP_CLI" ]       || die "Brak WP-CLI (komenda 'wp'). Instrukcja: https://wp-cli.org/#installing"
ok "WordPress: $WP_PATH"
ok "python3:   $PY"
ok "wp-cli:    $WP_CLI"

say "1/5  Środowisko Pythona + zależności (to potrwa kilka minut)"
"$PY" -m venv "$REPO_DIR/.venv"
"$REPO_DIR/.venv/bin/pip" -q install --upgrade pip
for r in "$REPO_DIR"/scraper/dzialy/*/requirements.txt; do
	"$REPO_DIR/.venv/bin/pip" -q install -r "$r"
done
"$REPO_DIR/.venv/bin/playwright" install chromium
# G2: biblioteki systemowe headless chromium (libnss3/libatk...). Na czystym VPS bez nich
# przeglądarka nie startuje. Na dystrybucjach nie-apt polecenie może nie zadziałać -> nie przerywaj.
"$REPO_DIR/.venv/bin/playwright" install-deps chromium || \
	echo "   (uwaga: install-deps pominięte — jeśli chromium nie startuje, doinstaluj biblioteki systemowe ręcznie)"
ok "Zależności i przeglądarka zainstalowane"

say "2/5  Wtyczka WordPress (kopiuję i włączam)"
PLUG_DST="$WP_PATH/wp-content/plugins/iaai-importer"
mkdir -p "$PLUG_DST"
cp -a "$REPO_DIR/wp-plugin/iaai-importer/." "$PLUG_DST/"
"$WP_CLI" plugin activate iaai-importer --path="$WP_PATH" --allow-root || \
	die "Nie udało się włączyć wtyczki — włącz ją ręcznie w panelu WordPress (Wtyczki)."
ok "Wtyczka włączona (tabele wp_iaai_* założone przez dbDelta)"

say "3/5  Konfiguracja usług (środowisko)"
ENV_FILE="/etc/iaai-importer.env"
if [ ! -f "$ENV_FILE" ]; then
	sed -e "s#^WP_PATH=.*#WP_PATH=$WP_PATH#" \
	    -e "s#^WP_CLI=.*#WP_CLI=$WP_CLI#" \
	    -e "s#^SCRAPER_DIR=.*#SCRAPER_DIR=$REPO_DIR/scraper#" \
	    -e "s#^PYTHON=.*#PYTHON=$REPO_DIR/.venv/bin/python#" \
	    "$REPO_DIR/deploy/iaai-importer.env.example" > "$ENV_FILE"
	ok "Utworzono $ENV_FILE"
else
	ok "$ENV_FILE już istnieje — zostawiam bez zmian"
fi

say "4/5  Usługi systemd (automatyzacja always-on)"
# Podmień ścieżkę ExecStart na realny katalog repo:
for unit in iaai-importer-live.service iaai-importer-backfill.service; do
	sed "s#^ExecStart=.*#ExecStart=$REPO_DIR/deploy/iaai-live-cycle.sh#" \
		"$REPO_DIR/deploy/$unit" > "/etc/systemd/system/$unit"
done
cp "$REPO_DIR/deploy/iaai-importer-live.timer" "$REPO_DIR/deploy/iaai-importer-backfill.timer" \
	/etc/systemd/system/
chmod +x "$REPO_DIR/deploy/iaai-live-cycle.sh" "$REPO_DIR/deploy/iaai-env.sh"
systemctl daemon-reload
systemctl enable --now iaai-importer-live.timer
systemctl enable --now iaai-importer-backfill.timer
ok "Timery włączone (live co 15 min, backfill 03:30)"

say "5/5  GOTOWE ✅"
cat <<EOF

Co dalej:
  • Pierwsze auta pojawią się po pierwszym cyklu (do ~15 min). Możesz odpalić od razu:
        sudo systemctl start iaai-importer-live.service
  • Podgląd logu:
        journalctl -u iaai-importer-live.service -n 40 --no-pager
  • Pokaż auta na stronie: wstaw na dowolnej stronie WordPress krótki kod:
        [iaai_pojazdy ile="12"]
  • Pełna instrukcja obsługi: docs/klient/00-START-TUTAJ.md
EOF
