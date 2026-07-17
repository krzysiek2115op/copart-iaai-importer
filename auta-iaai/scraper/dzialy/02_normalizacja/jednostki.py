# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Importer Aukcji (IAAI + Copart).
# Licencja: GNU GPL v2 lub pozniejsza - pelny tekst w pliku LICENSE.
"""
Dział 2 · NORMALIZACJA — agent `jednostki`  (+ krytyk `jakość-jednostek`).

Ujednolica jednostki i formaty (niezależne od źródła, reguły wewnętrzne):
  - przebieg: mi/km -> dokłada `odometer_km` (1 mi = 1.609344 km)
  - ceny: "$1,300 USD" -> 1300.00 (buy_now, current_bid)
  - daty: "Mon Jun 29, 8:30am CDT" -> ISO `YYYY-MM-DD` (sale_date)
  - tytuł: "SALVAGE (Missouri)" -> title_brand + title_state
  - klucz: "Key Available"/"Present" -> key_present (bool)

Wymagania: brak (stdlib)
Użycie:   python jednostki.py --in out/norm_vin.jsonl --out out/norm_jedn.jsonl
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

MI_TO_KM = 1.609344
MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}


def parse_price(val) -> float | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    m = re.search(r"([\d,]+(?:\.\d+)?)", str(val))
    return float(m.group(1).replace(",", "")) if m else None


def parse_sale_date(val: str) -> str | None:
    """Data sprzedaży/aukcji IAAI -> 'YYYY-MM-DD' (best-effort). Obsługuje:
       - tekst: 'Mon Jun 29, 8:30am CDT' / 'Fri Jun 26, 1:20am CDT',
       - numeryczny: '6/29/2026 1:00:00 AM +00:00' (M/D/RRRR)."""
    if not val:
        return None
    from datetime import date
    # 1) numeryczny M/D/RRRR (np. z ProductDetailsVM)
    n = re.search(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b", val)
    if n:
        mo, dy, yr = int(n.group(1)), int(n.group(2)), int(n.group(3))
        try:
            return date(yr, mo, dy).isoformat()
        except ValueError:
            return None
    # 2) tekstowy 'Mon Jun 29[, ...][ 2026]'
    m = re.search(r"\b([A-Z][a-z]{2})\s+(\d{1,2})\b", val)
    if not m or m.group(1) not in MONTHS:
        return None
    month, day = MONTHS[m.group(1)], int(m.group(2))
    yr = re.search(r"\b(20\d{2})\b", val)
    if yr:
        year = int(yr.group(1))
    else:
        # L13: brak roku -> wybierz rok dający datę NAJBLIŻSZĄ dziś (aukcje bywają tuż po
        # przełomie roku), zamiast sztywno bieżącego.
        today = date.today()
        cands = []
        for y in (today.year - 1, today.year, today.year + 1):
            try:
                cands.append(date(y, month, day))
            except ValueError:
                pass
        year = min(cands, key=lambda d: abs((d - today).days)).year if cands else today.year
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def split_title(val: str):
    """'SALVAGE (Missouri)' -> ('SALVAGE', 'Missouri')."""
    if not val:
        return None, None
    st = re.search(r"\(([^)]+)\)\s*$", val)
    brand = re.sub(r"\s*\([^)]*\)\s*$", "", val).strip()
    return (brand or None), (st.group(1) if st else None)


def normalize(rec: dict) -> dict:
    out = dict(rec)
    # przebieg -> km
    if out.get("odometer") is not None:
        uom = (out.get("odometer_uom") or "mi").lower()
        out["odometer_km"] = round(out["odometer"] * MI_TO_KM) if uom == "mi" else int(out["odometer"])
    # ceny
    for f in ("buy_now", "current_bid"):
        if f in out:
            out[f] = parse_price(out[f])
    # data sprzedaży — ZAWSZE ISO albo None (M1: nie wpuszczaj surowego stringa do DATETIME)
    if out.get("sale_date"):
        raw = out["sale_date"]
        parsed = parse_sale_date(raw)
        out["sale_date"] = parsed                 # None gdy nie da się sparsować
        if parsed is None:
            out["sale_date_raw"] = raw            # zachowaj oryginał do diagnozy (nie idzie do bazy)
    # tytuł
    if out.get("title"):
        out["title_brand"], out["title_state"] = split_title(out["title"])
    # klucz (L12): normalizacja niespójnych wartości ("Present"/"Available"/"Not Available"/...).
    # UWAGA: najpierw negacja — "Not Available" zawiera "avail", więc naiwne wyszukanie dałoby True.
    if out.get("key_available"):
        kv = str(out["key_available"]).strip().lower()
        if re.search(r"\b(not|no|without|missing|absent)\b", kv) or kv in ("none", "n/a", "-"):
            out["key_present"] = False
        else:
            out["key_present"] = bool(re.search(r"avail|present|yes", kv))
    return out


# ---- 🔴 KRYTYK: jakość-jednostek ------------------------------------------
def krytyk_jakosc_jednostek(rec: dict) -> list[str]:
    issues = []
    if rec.get("odometer") is not None:
        if not rec.get("odometer_uom"):
            issues.append("przebieg bez jednostki (mi/km)")
        if rec.get("odometer_km") is None:
            issues.append("nie przeliczono przebiegu na km")
    for f in ("buy_now", "current_bid"):
        if f in rec and rec[f] is not None and not isinstance(rec[f], (int, float)):
            issues.append(f"{f} nie jest liczbą")
    if rec.get("sale_date") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(rec["sale_date"])):
        issues.append(f"sale_date nie w ISO: {rec['sale_date']}")
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("out/norm_jedn.jsonl"))
    args = ap.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    rc = 0
    with args.out.open("w", encoding="utf-8") as fh:
        for line in args.infile.read_text().splitlines():
            if not line.strip():
                continue
            rec = normalize(json.loads(line))
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            issues = krytyk_jakosc_jednostek(rec)
            status = "OK ✅" if not issues else "; ".join(issues)
            print(f"  {rec.get('salvage_id')}: odo={rec.get('odometer')}{rec.get('odometer_uom')}"
                  f"->{rec.get('odometer_km')}km | sale={rec.get('sale_date')}"
                  f" | title={rec.get('title_brand')}/{rec.get('title_state')} | [{status}]")
            if issues:
                rc = 1
    print(f"[jednostki] zapisano -> {args.out}")
    sys.exit(rc)


if __name__ == "__main__":
    main()
