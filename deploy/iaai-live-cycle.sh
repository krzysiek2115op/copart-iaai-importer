#!/usr/bin/env bash
# =====================================================================
#  iaai-live-cycle.sh — JEDEN CYKL automatyzacji always-on (blok A, pkt 1/5).
#
#  Wykonuje pełny przebieg dla nowych aut i publikuje je na stronie:
#    1) źródło danych (IAAI_DB_* z wp-config) — przez iaai-env.sh,
#    2) pipeline w trybie `live` (nowe loty -> baza WP),
#    3) most do WP: publikacja CPT „pojazd" z bazy (WP-CLI).
#
#  Uruchamiany cyklicznie przez systemd timer (patrz deploy/iaai-importer.timer).
#  Tryb pełny (full + reconcile) odpala osobny, rzadszy timer (backfill).
#
#  Zmienne (z env lub systemd): WP_PATH, WP_CLI, SCRAPER_DIR, IAAI_BASE, IAAI_MODE.
# =====================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${SCRAPER_DIR:=$(cd "$HERE/../scraper" && pwd)}"
: "${IAAI_BASE:=https://www.iaai.com/Search}"
: "${IAAI_MODE:=live}"                 # live (domyślnie) albo full (backfill)
: "${PYTHON:=python3}"

# 1) konfiguracja bazy = baza WordPressa klienta
# shellcheck source=/dev/null
source "$HERE/iaai-env.sh"

echo "[cykl] start $(date -Is)  mode=$IAAI_MODE base=$IAAI_BASE"

# 2) pipeline (zapis do bazy WP). reconcile włącza się sam tylko dla full bez limitu.
"$PYTHON" "$SCRAPER_DIR/run_pipeline.py" --mode "$IAAI_MODE" --base "$IAAI_BASE"

# 3) most do WP — publikacja aktywnych pojazdów do CPT „pojazd"
"${WP_CLI:-wp}" eval 'iaai_publish_all_active();' --path="${WP_PATH:-/var/www/html}"

echo "[cykl] koniec $(date -Is)"
