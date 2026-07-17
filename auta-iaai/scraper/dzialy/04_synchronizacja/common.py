# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Importer Aukcji (IAAI + Copart).
# Licencja: GNU GPL v2 lub pozniejsza - pelny tekst w pliku LICENSE.
"""
Dział 4 · SYNCHRONIZACJA — wspólny moduł: połączenie z bazą, kolumny, hash.

Oryginał działu: docs/refs/mysql-upsert.md (INSERT ... ON DUPLICATE KEY UPDATE).
Sterownik: PyMySQL (działa z MySQL i MariaDB). Upsert w wersji PRZENOŚNEJ
(parametry podawane dwukrotnie) — bez aliasu `AS new` (MySQL 8.0.19+) ani
`VALUES()` (deprecyjne) — działa i na MySQL, i na MariaDB.
"""
from __future__ import annotations
import hashlib, json, os

import pymysql

# Kolumny DANYCH (1:1 z IAAI) — bez PK, bez metadanych (raw_hash/status/captured/updated)
DATA_COLS = [
    "stock_number", "item_id", "vin", "year", "make", "model", "series",
    "vehicle_type", "body_style", "engine", "cylinders", "fuel_type", "transmission",
    "drive_line", "color", "odometer", "odometer_uom", "odometer_brand",
    "primary_damage", "secondary_damage", "loss", "title", "run_and_drive",
    "key_available", "selling_branch", "branch_id", "sale_date", "lane", "aisle",
    "buy_now", "current_bid", "detail_url",
]


def tbl(name: str) -> str:
    """Nazwa tabeli z prefiksem WordPressa.

    DEV (przenośna MariaDB): IAAI_DB_TABLE_PREFIX puste -> `iaai_vehicles`.
    VPS klienta (ta sama baza co WP): IAAI_DB_TABLE_PREFIX=wp_ -> `wp_iaai_vehicles`,
    żeby Python pisał do TYCH SAMYCH tabel, które czyta wtyczka ({$wpdb->prefix}iaai_*).
    Wartość pochodzi z konfiguracji (nie od użytkownika) — bezpieczna w f-stringu SQL.
    """
    return os.environ.get("IAAI_DB_TABLE_PREFIX", "") + name


def connect():
    return pymysql.connect(
        host=os.environ.get("IAAI_DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("IAAI_DB_PORT", "3307")),
        user=os.environ.get("IAAI_DB_USER", "iaai"),
        password=os.environ.get("IAAI_DB_PASS", "iaai"),
        database=os.environ.get("IAAI_DB_NAME", "iaai"),
        charset="utf8mb4", autocommit=True,
    )


def to_db_row(rec: dict) -> dict:
    """Z bogatego rekordu (po normalizacji) wybiera tylko kolumny bazy."""
    row = {"salvage_id": rec.get("salvage_id")}
    for c in DATA_COLS:
        row[c] = rec.get(c)
    return row


def compute_hash(rec: dict) -> str:
    """SHA1 po polach danych (stabilny — sortowane klucze) do wykrywania zmian."""
    row = {c: rec.get(c) for c in DATA_COLS}
    blob = json.dumps(row, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()
