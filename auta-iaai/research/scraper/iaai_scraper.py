"""
IAAI VehicleDetail scraper (Playwright) — krok 1 / proof-of-concept.

Pobiera dla danego salvageId:
  - dane pojazdu z osadzonego w HTML bloku JSON  #ProductDetailsVM  (obiekt `inventory`)
  - listę zdjęć z  https://vis.iaai.com/dimensions?imageKeys={salvageId}~SID
  - (opcjonalnie) pełne zdjęcia JPEG z  https://vis.iaai.com/resizer

UWAGA PRAWNA: robots.txt IAAI nie zabrania /VehicleDetail/, ale ToS może zakazywać
automatycznego pobierania. Używać odpowiedzialnie, z rozsądnym rate-limitem.
To kod poglądowy do kroku 1 — nie jest to wersja produkcyjna.

Wymagania:  pip install playwright requests  &&  playwright install chromium
Użycie:     python iaai_scraper.py 45293605 [--images out_dir]
"""
from __future__ import annotations
import argparse, json, re, sys, time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright

VIS_ROOT = "https://vis.iaai.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def fetch_vehicle(salvage_id: str) -> dict:
    """Pobiera stronę VehicleDetail przez realną przeglądarkę i parsuje #ProductDetailsVM."""
    url = f"https://www.iaai.com/VehicleDetail/{salvage_id}~US"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=UA, locale="en-US")
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=45_000)
        # blok JSON jest renderowany server-side, więc jest w DOM od razu
        raw = page.locator('script#ProductDetailsVM').first.text_content(timeout=15_000)
        browser.close()
    if not raw:
        raise RuntimeError("Nie znaleziono #ProductDetailsVM — strona mogła zwrócić challenge.")
    data = json.loads(raw)
    return data.get("inventory", data)


def fetch_image_list(salvage_id: str) -> dict:
    """Lista zdjęć (JSON) z serwisu obrazów vis.iaai.com."""
    r = requests.get(f"{VIS_ROOT}/dimensions",
                     params={"imageKeys": f"{salvage_id}~SID"},
                     headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    return r.json()


def download_images(image_list: dict, out_dir: Path, width: int = 1024, height: int = 768):
    out_dir.mkdir(parents=True, exist_ok=True)
    for img in image_list.get("keys", []):
        k = img["K"]
        r = requests.get(f"{VIS_ROOT}/resizer",
                         params={"imageKeys": k, "width": width, "height": height},
                         headers={"User-Agent": UA}, timeout=60)
        if r.ok and r.headers.get("content-type", "").startswith("image"):
            (out_dir / f"{img.get('IN', k.split('~')[0])}.jpg").write_bytes(r.content)
            print(f"  zapisano zdjęcie IN={img.get('IN')}  ({len(r.content)} B)")
        time.sleep(0.4)  # rate-limit – bądź grzeczny dla serwera


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("salvage_id", help="np. 45293605")
    ap.add_argument("--images", metavar="DIR", help="pobierz zdjęcia do katalogu")
    args = ap.parse_args()

    print(f"[IAAI] pobieram dane pojazdu {args.salvage_id} ...")
    vehicle = fetch_vehicle(args.salvage_id)
    keep = {k: v for k, v in vehicle.items()
            if k in ("vin", "year", "make", "model", "odoValue", "odoUoM",
                     "primaryDamageDesc", "secondaryDamageDesc", "titleBrand",
                     "city", "state", "zip", "branchId", "auctionId", "salvageId")}
    print(json.dumps(keep, indent=2, ensure_ascii=False))

    print(f"[IAAI] pobieram listę zdjęć ...")
    images = fetch_image_list(args.salvage_id)
    print(f"  zdjęć: {len(images.get('keys', []))}, 360°: {images.get('Image360Ind')}, "
          f"wideo: {len(images.get('Videos', []))}")

    if args.images:
        download_images(images, Path(args.images))

    # tu w kolejnym kroku: zapis `vehicle` + `images` do nowej bazy danych
    return {"vehicle": vehicle, "images": images}


if __name__ == "__main__":
    main()
