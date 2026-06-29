"""
Dział 1 · POBIERANIE — agent `listingi`  (+ krytyk `kompletność-listy`).

Decyzje (ustalone): 1) całe IAAI  2) anonimowo  3) pełne szczegóły (osobny agent)
4) zdjęcia pobierane do nas (osobny agent). Ten agent zbiera z wyszukiwarki IAAI
listę lotów: salvage_id, year/make/model, detail_url + pola z karty.

Źródło (zweryfikowane, krok 1):
  - wyniki: https://www.iaai.com/Search?...&page=N  (server-side HTML, ~100 lotów/stronę)
  - tytuł:  h4.heading-7 > a[href*="VehicleDetail"]  (name = salvage_id)
  - pola:   .data-list__item > (.data-list__label, .data-list__value)

Referencja techniczna działu: docs/refs/playwright-python.md
(tu wystarcza requests — strona jest renderowana server-side; Playwright dla `szczegóły`).

Wymagania: pip install requests beautifulsoup4
Użycie:   python listingi.py --mode full --out out/listingi.jsonl
          python listingi.py --mode live --base "https://www.iaai.com/Search?Keyword=BMW"
"""
from __future__ import annotations
import argparse, json, re, sys, time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# Etykiety z karty IAAI (atrybut title="Etykieta: wartość") -> kolumny iaai_vehicles
LABEL_MAP = {
    "Stock #": "stock_number", "VIN": "vin", "Odometer": "odometer_raw",
    "Primary Damage": "primary_damage", "Secondary Damage": "secondary_damage",
    "Loss": "loss", "Vehicle Type": "vehicle_type", "Body Style": "body_style",
    "Engine": "engine", "Cylinder": "cylinders", "Fuel Type": "fuel_type",
    "Exterior Color": "color", "Branch": "selling_branch", "Title/Sale Doc": "title",
    "Lane/Run#": "lane", "Aisle/Stall": "aisle", "Transmission": "transmission",
    "Driveline Type": "drive_line", "Key": "key_available",
}
# Wartości wskazujące status Run & Drive (etykieta na karcie bywa pusta)
RUNDRIVE_VALUES = {"run & drive", "runs & drives", "engine start program",
                   "stationary", "non runner", "does not run"}


def _item_label_value(it):
    """Z jednego .data-list__item zwraca (etykieta, wartość). Etykieta: z .data-list__label
    albo z atrybutu title='Etykieta: wartość' na wartości."""
    spans = it.find_all("span")
    lab_span = it.select_one(".data-list__label")
    val_span = it.select_one(".data-list__value") or (spans[-1] if spans else None)
    if lab_span and lab_span.get_text(strip=True):
        return lab_span.get_text(strip=True).rstrip(":"), (val_span.get_text(" ", strip=True) if val_span else "")
    title = (val_span.get("title") if val_span else "") or ""
    label = title.split(":", 1)[0].strip() if ":" in title else ""
    return label, (val_span.get_text(" ", strip=True) if val_span else "")


def parse_title(title: str):
    """'2004 BMW 325CI' -> (2004, 'BMW', '325CI')."""
    parts = title.split()
    year = int(parts[0]) if parts and re.fullmatch(r"\d{4}", parts[0]) else None
    make = parts[1] if len(parts) > 1 else None
    model = " ".join(parts[2:]) if len(parts) > 2 else None
    return year, make, model


def parse_odometer(raw: str):
    """'169,594 mi (Not Required/Exempt)' -> (169594, 'mi', 'Not Required/Exempt')."""
    if not raw:
        return None, None, None
    num = re.search(r"([\d,]+)", raw)
    value = int(num.group(1).replace(",", "")) if num else None
    uom = "km" if re.search(r"\bkm\b", raw, re.I) else ("mi" if re.search(r"\bmi\b", raw, re.I) else None)
    brand = re.search(r"\(([^)]+)\)", raw)
    return value, uom, (brand.group(1) if brand else None)


def parse_listings(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    # każdy listing = jeden wiersz .table-row-border zawierający tytuł (pola kotwiczone w wierszu)
    for row in soup.select(".table-row-border"):
        a = row.select_one('h4.heading-7 a[href*="VehicleDetail"]')
        if not a:
            continue
        href = a.get("href", "")
        sid = a.get("name") or (re.search(r"VehicleDetail/(\d+)", href) or [None, None])[1]
        if not sid:
            continue
        year, make, model = parse_title(a.get_text(strip=True))
        fields = {}
        for it in row.select(".data-list__item"):
            label, value = _item_label_value(it)
            if value:
                fields.setdefault(label, value)
        rec = {
            "salvage_id": int(sid), "year": year, "make": make, "model": model,
            "detail_url": f"https://www.iaai.com/VehicleDetail/{sid}~US",
        }
        for label, col in LABEL_MAP.items():
            if fields.get(label):
                rec[col] = fields[label]
        # Run & Drive — etykieta bywa pusta, rozpoznaj po wartości
        for v in fields.values():
            if v.lower() in RUNDRIVE_VALUES:
                rec["run_and_drive"] = v
                break
        if rec.get("cylinders"):
            m = re.search(r"\d+", rec["cylinders"]); rec["cylinders"] = int(m.group()) if m else None
        if rec.get("vin"):
            rec["vin_masked"] = "*" in rec["vin"]      # anonimowo VIN jest maskowany
        if "odometer_raw" in rec:
            rec["odometer"], rec["odometer_uom"], rec["odometer_brand"] = parse_odometer(rec.pop("odometer_raw"))
        out.append(rec)
    return out


def run(base_url: str, mode: str, out_path: Path, max_pages: int, delay: float):
    sess = requests.Session()
    sess.headers["User-Agent"] = UA
    out_path.parent.mkdir(parents=True, exist_ok=True)
    seen, pages_meta = set(), []
    with out_path.open("w", encoding="utf-8") as fh:
        for page in range(1, max_pages + 1):
            sep = "&" if "?" in base_url else "?"
            url = f"{base_url}{sep}page={page}"
            r = sess.get(url, timeout=30)
            recs = parse_listings(r.text) if r.ok else []
            new = [x for x in recs if x["salvage_id"] not in seen]
            pages_meta.append({"page": page, "http": r.status_code, "count": len(recs), "new": len(new)})
            for x in new:
                seen.add(x["salvage_id"])
                fh.write(json.dumps(x, ensure_ascii=False) + "\n")
            print(f"  str.{page}: HTTP {r.status_code}, lotów {len(recs)} (nowych {len(new)})")
            if not recs:                       # koniec wyników
                break
            if not new and page > 1:           # paginacja się nie przesuwa (same loty) = stop
                print("  (brak nowych lotów — paginacja się nie przesuwa, stop)")
                break
            time.sleep(delay)
    return {"total": len(seen), "pages": pages_meta}


# ---- 🔴 KRYTYK: kompletność-listy ----------------------------------------
def krytyk_kompletnosc_listy(result: dict, page_size: int = 100) -> list[str]:
    """Zwraca listę zastrzeżeń; pusta = OK."""
    issues = []
    pages = result["pages"]
    for m in pages:
        if m["http"] != 200:
            issues.append(f"strona {m['page']}: HTTP {m['http']} (nie 200)")
    # każda strona poza ostatnią powinna być pełna
    for m in pages[:-1]:
        if m["count"] < page_size:
            issues.append(f"strona {m['page']}: tylko {m['count']}/{page_size} lotów — możliwa luka")
    if not pages or pages[-1]["count"] == page_size:
        issues.append("ostatnia strona pełna — paginacja mogła nie dojść do końca (zwiększ max_pages)")
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://www.iaai.com/Search",
                    help="bazowy URL wyszukiwarki (całe IAAI = domyślnie)")
    ap.add_argument("--mode", choices=["full", "live"], default="full")
    ap.add_argument("--out", default="out/listingi.jsonl", type=Path)
    ap.add_argument("--max-pages", type=int, default=50)
    ap.add_argument("--delay", type=float, default=1.0, help="opóźnienie między stronami (s)")
    args = ap.parse_args()

    print(f"[listingi] {args.mode} | {args.base}")
    result = run(args.base, args.mode, args.out, args.max_pages, args.delay)
    print(f"[listingi] zebrano {result['total']} lotów -> {args.out}")

    issues = krytyk_kompletnosc_listy(result)
    if issues:
        print("[krytyk:kompletność-listy] ZASTRZEŻENIA:")
        for i in issues:
            print("   -", i)
        sys.exit(1)
    print("[krytyk:kompletność-listy] OK ✅")


if __name__ == "__main__":
    main()
