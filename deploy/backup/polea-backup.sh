#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Kopia zapasowa bazy polea + rotacja. Poświadczenia z /etc/polea.env (POLEA_DB_*).
# Hasło przekazujemy przez MYSQL_PWD (NIE w argv -> niewidoczne w `ps`).
# Uruchamianie: z crona/systemd, na koncie z prawem SELECT (np. polea_ro) do bazy.
set -euo pipefail

# Wczytaj env, jeśli podany (domyślnie /etc/polea.env).
ENV_FILE="${POLEA_ENV_FILE:-/etc/polea.env}"
if [ -f "$ENV_FILE" ]; then
    set -a; . "$ENV_FILE"; set +a
fi

: "${POLEA_DB_HOST:=127.0.0.1}"
: "${POLEA_DB_PORT:=3306}"
: "${POLEA_DB_USER:?POLEA_DB_USER wymagane}"
: "${POLEA_DB_PASSWORD:?POLEA_DB_PASSWORD wymagane}"
: "${POLEA_DB_NAME:=polea}"

DEST="${POLEA_BACKUP_DIR:-/var/backups/polea}"
KEEP="${POLEA_BACKUP_KEEP:-14}"          # ile ostatnich kopii zostawić

umask 077
mkdir -p "$DEST"
chmod 700 "$DEST"

ts="$(date +%F_%H%M%S)"
out="$DEST/polea_${ts}.sql.gz"

# --single-transaction: spójny snapshot InnoDB bez blokad; --no-tablespaces: bez prawa PROCESS.
export MYSQL_PWD="$POLEA_DB_PASSWORD"
mysqldump --single-transaction --quick --no-tablespaces --default-character-set=utf8mb4 \
    -h "$POLEA_DB_HOST" -P "$POLEA_DB_PORT" -u "$POLEA_DB_USER" "$POLEA_DB_NAME" \
    | gzip -c > "$out"
unset MYSQL_PWD

# Rotacja: usuń kopie starsze niż $KEEP najnowszych.
ls -1t "$DEST"/polea_*.sql.gz 2>/dev/null | tail -n +"$((KEEP + 1))" | xargs -r rm -f

echo "Backup OK: $out ($(du -h "$out" | cut -f1))"
