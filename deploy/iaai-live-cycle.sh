#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Importer Aukcji (IAAI + Copart).
# Licencja: GNU GPL v2 lub pozniejsza - pelny tekst w pliku LICENSE.
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

# G4: tylko JEDEN przebieg naraz (live vs backfill). Chroni zapis Pythona do bazy przed
# nałożeniem się (reconcile z full na insert z live). Zajęty lock = pomijamy ten cykl.
LOCKFILE="${STATE_DIRECTORY:-/tmp}/iaai-importer.lock"
exec 9>"$LOCKFILE"
if command -v flock >/dev/null 2>&1 && ! flock -n 9; then
	echo "[cykl] inny przebieg trwa (lock $LOCKFILE) — pomijam."
	exit 0
fi

# 1) konfiguracja bazy = baza WordPressa klienta
# shellcheck source=/dev/null
source "$HERE/iaai-env.sh"

echo "[cykl] start $(date -Is)  mode=$IAAI_MODE base=$IAAI_BASE"

# 2) pipeline (zapis do bazy WP). reconcile włącza się sam tylko dla full bez limitu.
# G1: workdir ABSOLUTNY. Pod systemd = $STATE_DIRECTORY (/var/lib/iaai-importer, zapisywalny
# jako www-data); ręcznie = pipeline_out obok scrapera. Bez tego CWD=/ i zapis padał.
WORKDIR="${STATE_DIRECTORY:-$SCRAPER_DIR/pipeline_out}"
"$PYTHON" "$SCRAPER_DIR/run_pipeline.py" --mode "$IAAI_MODE" --base "$IAAI_BASE" --workdir "$WORKDIR"

# 3) most do WP — publikacja aktywnych pojazdów do CPT „pojazd"
"${WP_CLI:-wp}" eval 'iaai_publish_all_active();' --path="${WP_PATH:-/var/www/html}"

echo "[cykl] koniec $(date -Is)"
