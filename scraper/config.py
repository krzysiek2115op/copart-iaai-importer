# SPDX-License-Identifier: GPL-2.0-or-later
"""Konfiguracja scrapera. Wartosci wrazliwe (baza) czytane ze zmiennych srodowiskowych."""
import os

BASE_URL = "https://poleasingowe.pl"
CATEGORY_PATH = "/pl/auctions/list/pub/all/ecr_motorcycles"

USER_AGENT = os.environ.get(
    "POLEA_USER_AGENT",
    "PoleasingoweImporter/0.1 (+kontakt)",
)

# Rate-limit i sie (Dzial 7)
REQUEST_DELAY = float(os.environ.get("POLEA_DELAY", "2.0"))    # sekundy miedzy zadaniami
REQUEST_JITTER = float(os.environ.get("POLEA_JITTER", "1.0"))
MAX_RETRIES = int(os.environ.get("POLEA_RETRIES", "3"))
TIMEOUT = int(os.environ.get("POLEA_TIMEOUT", "30"))
MAX_PAGES = int(os.environ.get("POLEA_MAX_PAGES", "50"))       # bezpiecznik paginacji

# Baza (osobna MySQL) — Dzial 4. NIGDY nie wpisywac hasla na sztywno.
DB = {
    "host": os.environ.get("POLEA_DB_HOST", "127.0.0.1"),
    "port": int(os.environ.get("POLEA_DB_PORT", "3306")),
    "user": os.environ.get("POLEA_DB_USER", "polea"),
    "password": os.environ.get("POLEA_DB_PASSWORD", ""),
    "database": os.environ.get("POLEA_DB_NAME", "polea"),
}
