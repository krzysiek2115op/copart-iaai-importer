#!/usr/bin/env bash
# =====================================================================
#  iaai-env.sh — MOST KONFIGURACJI: scraper Python pisze do TEJ SAMEJ
#  bazy MySQL, której używa WordPress klienta (blok A, pkt 3/4).
#
#  Czyta dane dostępowe z wp-config.php przez WP-CLI (`wp config get`)
#  i eksportuje zmienne IAAI_DB_*, których używają agenci (common.connect()).
#  Dzięki temu nie duplikujemy haseł — jedno źródło prawdy = wp-config.php.
#
#  Użycie:   source /sciezka/deploy/iaai-env.sh
#  Wymaga:   zainstalowanego WP-CLI (`wp`) i dostępu do katalogu WordPressa.
# =====================================================================

# --- KONFIGURACJA (dostosuj na VPS klienta) --------------------------
: "${WP_PATH:=/var/www/html}"          # katalog instalacji WordPressa
: "${WP_CLI:=wp}"                      # ścieżka/komenda WP-CLI

wp_get() { "$WP_CLI" config get "$1" --path="$WP_PATH" 2>/dev/null; }

DB_NAME="$(wp_get DB_NAME)"
DB_USER="$(wp_get DB_USER)"
DB_PASS="$(wp_get DB_PASSWORD)"
DB_HOST_RAW="$(wp_get DB_HOST)"
TABLE_PREFIX="$(wp_get table_prefix)"

if [ -z "$DB_NAME" ]; then
	echo "[iaai-env] BŁĄD: nie odczytano DB_NAME z wp-config (WP_PATH=$WP_PATH, WP_CLI=$WP_CLI)." >&2
	return 1 2>/dev/null || exit 1
fi

# DB_HOST w WordPressie bywa "localhost", "127.0.0.1:3306" albo gniazdo.
# Rozdziel na host + port; gniazdo unix -> użytkownik ustawia ręcznie.
DB_PORT="3306"
DB_HOST="$DB_HOST_RAW"
case "$DB_HOST_RAW" in
	*:*)
		DB_HOST="${DB_HOST_RAW%%:*}"
		_suffix="${DB_HOST_RAW##*:}"
		case "$_suffix" in
			''|*[!0-9]*) : ;;            # nie-numeryczne (gniazdo) — zostaw port domyślny
			*) DB_PORT="$_suffix" ;;     # numeryczne -> port
		esac
		;;
esac
# PyMySQL nie lubi "localhost" przez gniazdo — wymuś TCP loopback.
[ "$DB_HOST" = "localhost" ] && DB_HOST="127.0.0.1"

export IAAI_DB_HOST="$DB_HOST"
export IAAI_DB_PORT="$DB_PORT"
export IAAI_DB_USER="$DB_USER"
export IAAI_DB_PASS="$DB_PASS"
export IAAI_DB_NAME="$DB_NAME"
export IAAI_DB_TABLE_PREFIX="$TABLE_PREFIX"   # np. "wp_" -> Python pisze do wp_iaai_*

echo "[iaai-env] baza: $IAAI_DB_USER@$IAAI_DB_HOST:$IAAI_DB_PORT/$IAAI_DB_NAME prefiks='$IAAI_DB_TABLE_PREFIX'"
