# SPDX-License-Identifier: GPL-2.0-or-later
"""Konfiguracja scrapera. Wartosci wrazliwe (baza) czytane ze zmiennych srodowiskowych."""
import os
from urllib.parse import urlsplit

BASE_URL = "https://poleasingowe.pl"
CATEGORY_PATH = "/pl/auctions/list/pub/all/ecr_motorcycles"

# Allowlista hostow (anty-SSRF): pobieramy WYLACZNIE z domeny zrodla.
# Przekierowania i odnosniki poza ta liste sa odrzucane (Dzial 7 / Fetcher).
_BASE_HOST = (urlsplit(BASE_URL).hostname or "").lower()
ALLOWED_HOSTS = {h for h in (_BASE_HOST, "www." + _BASE_HOST) if h and h != "www."}

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
MAX_REDIRECTS = int(os.environ.get("POLEA_MAX_REDIRECTS", "3"))  # limit przekierowan (anty-SSRF)
MAX_RESPONSE_BYTES = int(os.environ.get("POLEA_MAX_BYTES", str(8 * 1024 * 1024)))  # 8 MB (anty-DoS/bomba)
LOCK_PATH = os.environ.get("POLEA_LOCK", "/tmp/polea_import.lock")  # pojedyncza instancja (cron)

# Baza (osobna MySQL) — Dzial 4. NIGDY nie wpisywac hasla na sztywno.
DB = {
    "host": os.environ.get("POLEA_DB_HOST", "127.0.0.1"),
    "port": int(os.environ.get("POLEA_DB_PORT", "3306")),
    "user": os.environ.get("POLEA_DB_USER", "polea"),
    "password": os.environ.get("POLEA_DB_PASSWORD", ""),
    "database": os.environ.get("POLEA_DB_NAME", "polea"),
}
