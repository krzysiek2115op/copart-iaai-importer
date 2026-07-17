# SPDX-License-Identifier: GPL-2.0-or-later
"""Dzial 5 — Audyt: reguly twarde (blokuja publikacje) i miekkie (tylko flaga)."""
from datetime import datetime

HARD = "hard"
SOFT = "soft"
_STATUSY = ("aktywna", "zakonczona", "usunieta")


def audit(rec):
    """Zwraca (ok, errors). ok=False gdy zlamana regula twarda."""
    errors = []
    if not rec.get("lot_id"):
        errors.append((HARD, "brak lot_id"))
    if not rec.get("cena_pln") or rec["cena_pln"] <= 0:
        errors.append((HARD, "cena_pln <= 0"))
    if not rec.get("marka"):
        errors.append((HARD, "brak marki"))
    rok = rec.get("rok_produkcji")
    if rok is not None and not (1950 <= rok <= datetime.now().year + 1):
        errors.append((HARD, f"rok poza zakresem: {rok}"))
    if rec.get("status") not in _STATUSY:
        errors.append((HARD, f"nieznany status: {rec.get('status')}"))

    if rec.get("vin") and not rec.get("vin_valid"):
        errors.append((SOFT, "VIN niepoprawny"))
    if not rec.get("images"):
        errors.append((SOFT, "brak zdjec"))
    if not rec.get("termin_zakonczenia"):
        errors.append((SOFT, "brak terminu"))

    ok = not any(sev == HARD for sev, _ in errors)
    return ok, errors
