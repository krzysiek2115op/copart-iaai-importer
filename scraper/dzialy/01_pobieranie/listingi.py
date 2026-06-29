"""
Dział 1 · POBIERANIE — agent `listingi`  (+ krytyk `kompletność-listy`).

Decyzje: 1) całe IAAI  2) anonimowo  3) pełne szczegóły (osobny agent)
4) zdjęcia pobierane do nas (osobny agent).

PAGINACJA (rozwiązana): wyszukiwarka IAAI to aplikacja Knockout.js — strony są
przeładowywane przez POST /Search (nie przez &page=N). Niezawodnie sterujemy tym
**przeglądarką (Playwright)**: klikamy „Next", czekamy aż lista się zmieni, czytamy DOM.
Kompletność weryfikujemy po ukrytym polu `ResultCount` (łączna liczba wyników).

Parser (zweryfikowany na żywo): listing = wiersz `.table-row-border`,
tytuł `h4.heading-7 > a[name=salvage_id]`, pola w `.data-list__item`
(etykieta w atrybucie `title="Etykieta: wartość"`).

Wymagania: pip install beautifulsoup4 playwright  &&  playwright install chromium
Użycie:    python listingi.py --base "https://www.iaai.com/Search?Keyword=BMW" --mode full
           python listingi.py --mode full --max-pages 80 --out out/listingi.jsonl
"""
from __future__ import annotations
import argparse, json, math, re, sys, time
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

LABEL_MAP = {
    "Stock #": "stock_number", "VIN": "vin", "Odometer": "odometer_raw",
    "Primary Damage": "primary_damage", "Secondary Damage": "secondary_damage",
    "Loss": "loss", "Vehicle Type": "vehicle_type", "Body Style": "body_style",
    "Engine": "engine", "Cylinder": "cylinders", "Fuel Type": "fuel_type",
    "Exterior Color": "color", "Branch": "selling_branch", "Title/Sale Doc": "title",
    "Lane/Run#": "lane", "Aisle/Stall": "aisle", "Transmission": "transmission",
    "Driveline Type": "drive_line", "Key": "key_available",
}
RUNDRIVE_VALUES = {"run & drive", "runs & drives", "engine start program",
                   "stationary", "non runner", "does not run"}


def parse_title(title: str):
    parts = title.split()
    year = int(parts[0]) if parts and re.fullmatch(r"\d{4}", parts[0]) else None
    make = parts[1] if len(parts) > 1 else None
    model = " ".join(parts[2:]) if len(parts) > 2 else None
    return year, make, model


def parse_odometer(raw: str):
    if not raw:
        return None, None, None
    num = re.search(r"([\d,]+)", raw)
    value = int(num.group(1).replace(",", "")) if num else None
    uom = "km" if re.search(r"\bkm\b", raw, re.I) else ("mi" if re.search(r"\bmi\b", raw, re.I) else None)
    brand = re.search(r"\(([^)]+)\)", raw)
    return value, uom, (brand.group(1) if brand else None)


def _item_label_value(it):
    spans = it.find_all("span")
    lab_span = it.select_one(".data-list__label")
    val_span = it.select_one(".data-list__value") or (spans[-1] if spans else None)
    if lab_span and lab_span.get_text(strip=True):
        return lab_span.get_text(strip=True).rstrip(":"), (val_span.get_text(" ", strip=True) if val_span else "")
    title = (val_span.get("title") if val_span else "") or ""
    label = title.split(":", 1)[0].strip() if ":" in title else ""
    return label, (val_span.get_text(" ", strip=True) if val_span else "")


def parse_listings(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for row in soup.select(".table-row-border"):
        a = row.select_one('h4.heading-7 a[href*="VehicleDetail"]')
        if not a:
            continue
        sid = a.get("name") or (re.search(r"VehicleDetail/(\d+)", a.get("href", "")) or [None, None])[1]
        if not sid:
            continue
        year, make, model = parse_title(a.get_text(strip=True))
        fields = {}
        for it in row.select(".data-list__item"):
            label, value = _item_label_value(it)
            if value:
                fields.setdefault(label, value)
        rec = {"salvage_id": int(sid), "year": year, "make": make, "model": model,
               "detail_url": f"https://www.iaai.com/VehicleDetail/{sid}~US"}
        for label, col in LABEL_MAP.items():
            if fields.get(label):
                rec[col] = fields[label]
        for v in fields.values():
            if v.lower() in RUNDRIVE_VALUES:
                rec["run_and_drive"] = v
                break
        if rec.get("cylinders"):
            m = re.search(r"\d+", rec["cylinders"]); rec["cylinders"] = int(m.group()) if m else None
        if rec.get("vin"):
            rec["vin_masked"] = "*" in rec["vin"]
        if "odometer_raw" in rec:
            rec["odometer"], rec["odometer_uom"], rec["odometer_brand"] = parse_odometer(rec.pop("odometer_raw"))
        out.append(rec)
    return out


PAGE_SIZE = 100  # IAAI: PageSize w wynikach wyszukiwarki

def _first_id(page):
    return page.eval_on_selector_all(
        'h4.heading-7 a[href*="VehicleDetail"]',
        "els => els.length ? els[0].getAttribute('name') : null")


def _go_next(page, page_no, old_first_id) -> bool:
    """Przejdź na następną stronę: najpierw klik numeru (#PageNumber{n+1}),
    fallback na przycisk Next. Zwraca True, gdy lista realnie się zmieniła."""
    change = ("(old) => {const e=document.querySelector('h4.heading-7 a[href*=VehicleDetail]');"
              " return e && e.getAttribute('name')!==old;}")
    for sel in (f"#PageNumber{page_no + 1}", "button.btn-next"):
        loc = page.locator(sel).first
        if loc.count() == 0:
            continue
        try:
            loc.click(timeout=8_000, force=True)
            page.wait_for_function(change, arg=old_first_id, timeout=15_000)
            return True
        except Exception:
            continue
    return False


def run(base_url: str, mode: str, out_path: Path, max_pages: int, delay: float, headless: bool = True):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    seen, pages_meta, result_count = set(), [], None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_context(user_agent=UA, locale="en-US").new_page()
        page.goto(base_url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_selector('h4.heading-7 a[href*="VehicleDetail"]', timeout=30_000)
        # usuń ewentualne nakładki zgód (blokują kliknięcia paginacji)
        page.evaluate("""() => {for (const s of ['#truste-consent-track','.truste_overlay',
            '#onetrust-consent-sdk','.onetrust-pc-dark-filter']) {const e=document.querySelector(s); if(e) e.remove();}}""")
        try:
            result_count = int(page.locator("input[name=ResultCount]").first.get_attribute("value"))
        except Exception:
            pass
        total_pages = math.ceil(result_count / PAGE_SIZE) if result_count else None

        with out_path.open("w", encoding="utf-8") as fh:
            for page_no in range(1, max_pages + 1):
                recs = parse_listings(page.content())
                new = [x for x in recs if x["salvage_id"] not in seen]
                pages_meta.append({"page": page_no, "count": len(recs), "new": len(new)})
                for x in new:
                    seen.add(x["salvage_id"]); fh.write(json.dumps(x, ensure_ascii=False) + "\n")
                print(f"  str.{page_no}"
                      + (f"/{total_pages}" if total_pages else "")
                      + f": lotów {len(recs)} (nowych {len(new)}) | razem {len(seen)}"
                      + (f"/{result_count}" if result_count else ""))
                if total_pages and page_no >= total_pages:
                    break
                if mode == "live" and not new and page_no > 1:
                    break
                # poczekaj aż Knockout zainicjuje paginację (przyciski numerów stron)
                try:
                    page.wait_for_selector("[id^=PageNumber]", timeout=10_000)
                except Exception:
                    print("  (paginacja nie zainicjowana — stop)"); break
                old = _first_id(page)
                if not _go_next(page, page_no, old):
                    print("  (następna strona nie załadowała się — stop)"); break
                time.sleep(delay)
        browser.close()
    return {"total": len(seen), "result_count": result_count, "pages": pages_meta}


# ---- 🔴 KRYTYK: kompletność-listy ----------------------------------------
def krytyk_kompletnosc_listy(result: dict, page_size: int = 100) -> list[str]:
    issues = []
    rc, total, pages = result.get("result_count"), result["total"], result["pages"]
    # 1) zebrano tyle, ile deklaruje IAAI
    if rc and total < rc:
        issues.append(f"zebrano {total}/{rc} lotów — brakuje {rc - total} (paginacja nie dotarła do końca?)")
    # 2) strony pośrednie powinny być pełne
    for m in pages[:-1]:
        if m["count"] < page_size:
            issues.append(f"strona {m['page']}: tylko {m['count']}/{page_size} lotów — możliwa luka")
    # 3) duplikaty (nowych==0 na stronie >1 to znak zapętlenia)
    for m in pages[1:]:
        if m["count"] and m["new"] == 0:
            issues.append(f"strona {m['page']}: 0 nowych lotów — możliwe zapętlenie paginacji")
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://www.iaai.com/Search",
                    help="URL wyszukiwarki (całe IAAI = domyślnie)")
    ap.add_argument("--mode", choices=["full", "live"], default="full")
    ap.add_argument("--out", default="out/listingi.jsonl", type=Path)
    ap.add_argument("--max-pages", type=int, default=100)
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--headed", action="store_true", help="pokaż przeglądarkę (debug)")
    args = ap.parse_args()

    print(f"[listingi] {args.mode} | {args.base}")
    result = run(args.base, args.mode, args.out, args.max_pages, args.delay, headless=not args.headed)
    print(f"[listingi] zebrano {result['total']}"
          + (f"/{result['result_count']}" if result['result_count'] else "")
          + f" lotów -> {args.out}")

    issues = krytyk_kompletnosc_listy(result)
    if issues:
        print("[krytyk:kompletność-listy] ZASTRZEŻENIA:")
        for i in issues:
            print("   -", i)
        sys.exit(1)
    print("[krytyk:kompletność-listy] OK ✅")


if __name__ == "__main__":
    main()
