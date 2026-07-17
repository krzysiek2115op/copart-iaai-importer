# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Importer Aukcji (IAAI + Copart).
# Licencja: GNU GPL v2 lub pozniejsza - pelny tekst w pliku LICENSE.
"""
Dział 1 · POBIERANIE — agent `szczegóły`  (+ krytyk `kompletność-pól`).

Pobiera pełne pola pojazdu ze strony szczegółów IAAI. Strona renderuje dane w DOM
przez JS (surowy HTTP jest pusty), więc używamy Playwright. Dane są w blokach
`.data-list__item` z etykietą w `.data-list__label` (np. "VIN (Status):",
"Odometer:", "Start Code:", "Drive Line Type:").

Strona szczegółów ma BOGATSZY zestaw niż karta listy, m.in.:
  - Odometer z marką, np. "142,447 mi (Actual)"
  - Secondary Damage, Start Code (Run & Drive), Airbags, Drive Line Type
Uwaga: VIN anonimowo jest MASKOWANY (np. WBAPL5G59BN****** ) — pełny wymaga konta.

Wymagania: pip install playwright  &&  playwright install chromium
Użycie:   python szczegoly.py 45574140
          python szczegoly.py --in out/listingi.jsonl --out out/szczegoly.jsonl
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from listingi import parse_title, parse_odometer, ZGODY  # ten sam pakiet (F2: dział 7)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# Etykiety ze strony SZCZEGÓŁÓW -> kolumny iaai_vehicles
DETAIL_MAP = {
    "Stock #": "stock_number", "Selling Branch": "selling_branch",
    "VIN (Status)": "vin", "VIN": "vin", "Loss": "loss",
    "Primary Damage": "primary_damage", "Secondary Damage": "secondary_damage",
    "Title/Sale Doc": "title", "Start Code": "run_and_drive", "Key": "key_available",
    "Odometer": "odometer_raw", "Vehicle": "vehicle_type", "Body Style": "body_style",
    "Engine": "engine", "Transmission": "transmission", "Drive Line Type": "drive_line",
    "Fuel Type": "fuel_type", "Cylinders": "cylinders", "Exterior Color": "color",
    "Color": "color",
    # M2 (#9): data sprzedaży/aukcji ze strony szczegółów (kilka wariantów etykiety
    # — potwierdzić na żywo). Surowy string -> `sale_date`, ISO robi dział 2.
    "Sale Date": "sale_date", "Auction Date": "sale_date",
    "Auction Date & Time": "sale_date", "Sale Date/Time": "sale_date",
    "Live Auction Date": "sale_date",
}
# Pola, których brak = rekord niekompletny (krytyk)
REQUIRED = ["year", "make", "model", "odometer", "primary_damage", "title", "selling_branch"]


def _clean_vin(val: str):
    """'WBAPL5G59BN****** (OK)' -> ('WBAPL5G59BN******', 'OK')."""
    status = re.search(r"\(([^)]+)\)\s*$", val)
    vin = re.sub(r"\s*\([^)]*\)\s*$", "", val).strip()
    return vin, (status.group(1) if status else None)


def parse_detail(html: str) -> dict:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    fields = {}
    for it in soup.select(".data-list__item"):
        lab = it.select_one(".data-list__label")
        if not lab or not lab.get_text(strip=True):
            continue
        label = lab.get_text(strip=True).rstrip(":")
        vspan = it.select_one(".data-list__value")
        if not vspan:
            others = [s for s in it.find_all("span") if s is not lab]
            vspan = others[-1] if others else None
        value = vspan.get_text(" ", strip=True) if vspan else ""
        if value:
            fields.setdefault(label, value)

    rec = {}
    for label, col in DETAIL_MAP.items():
        if fields.get(label):
            rec[col] = fields[label]
    if rec.get("vin"):
        rec["vin"], rec["vin_status"] = _clean_vin(rec["vin"])
        rec["vin_masked"] = "*" in rec["vin"]
    if rec.get("cylinders"):
        m = re.search(r"\d+", rec["cylinders"]); rec["cylinders"] = int(m.group()) if m else None
    if "odometer_raw" in rec:
        rec["odometer"], rec["odometer_uom"], rec["odometer_brand"] = parse_odometer(rec.pop("odometer_raw"))
    return rec


def fetch_detail(salvage_id, browser) -> dict:
    page = browser.new_context(user_agent=UA, locale="en-US").new_page()
    try:
        page.goto(f"https://www.iaai.com/VehicleDetail/{salvage_id}~US",
                  wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_selector(".data-list__item", timeout=30_000, state="attached")
        page.wait_for_timeout(1500)
        html = page.content()
        reason = ZGODY.detect_block(200, html)              # F2: detekcja blokady
        if reason:
            return {"salvage_id": int(salvage_id), "_blocked": reason}
        rec = parse_detail(html)
        # rok/marka/model z nagłówka strony
        heading = ""
        for sel in ("h1", "h2.heading-2", "title"):
            try:
                heading = page.locator(sel).first.text_content(timeout=2000) or ""
                if re.search(r"\d{4}\s+\w", heading):
                    break
            except Exception:
                continue
        y, mk, md = parse_title(re.sub(r"\s*\|.*$", "", heading).strip())
        rec.update(salvage_id=int(salvage_id), year=y, make=mk, model=md,
                   detail_url=f"https://www.iaai.com/VehicleDetail/{salvage_id}~US")
        return rec
    finally:
        page.context.close()


# ---- 🔴 KRYTYK: kompletność-pól -------------------------------------------
def krytyk_kompletnosc_pol(rec: dict) -> list[str]:
    issues = [f"brak wymaganego pola: {f}" for f in REQUIRED if not rec.get(f)]
    if rec.get("vin_masked"):
        issues.append("VIN zamaskowany (anonimowo) — pełny VIN wymaga konta IAAI")
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("salvage_id", nargs="?", help="pojedynczy lot, np. 45574140")
    ap.add_argument("--in", dest="infile", type=Path, help="JSONL z listingi (pole salvage_id)")
    ap.add_argument("--out", type=Path, default=Path("out/szczegoly.jsonl"))
    ap.add_argument("--delay", type=float, default=1.0)
    args = ap.parse_args()

    ids = []
    if args.salvage_id:
        ids = [args.salvage_id]
    elif args.infile:
        ids = [json.loads(l)["salvage_id"] for l in args.infile.read_text().splitlines() if l.strip()]
    else:
        ap.error("podaj salvage_id albo --in plik.jsonl")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    limiter = ZGODY.RateLimiter(min_interval=args.delay)    # F2: rate-limit (dotąd --delay był ignorowany)
    blocked = False
    with sync_playwright() as p, args.out.open("w", encoding="utf-8") as fh:
        browser = p.chromium.launch()
        for sid in ids:
            limiter.wait()
            rec = fetch_detail(sid, browser)
            if rec.get("_blocked"):                         # F2: blokada -> przerwij, nie młóć
                blocked = rec["_blocked"]
                print(f"  ⚠️ BLOKADA ({blocked}) przy {sid} — przerywam (backoff).")
                break
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            issues = krytyk_kompletnosc_pol(rec)
            status = "OK ✅" if not issues else "ZASTRZEŻENIA: " + "; ".join(issues)
            print(f"  {sid}: {rec.get('year')} {rec.get('make')} {rec.get('model')} "
                  f"| odo={rec.get('odometer')} {rec.get('odometer_brand')} | [{status}]")
        browser.close()
    print(f"[szczegóły] zapisano -> {args.out}")
    if blocked:                                         # F2: zgłoś blokadę orkiestratorowi
        print(f"[krytyk:blokady] BLOKADA ({blocked}) — pobieranie przerwane.")
        sys.exit(1)


if __name__ == "__main__":
    main()
