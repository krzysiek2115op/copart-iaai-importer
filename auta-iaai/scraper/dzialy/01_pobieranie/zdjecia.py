# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Importer Aukcji (IAAI + Copart).
# Licencja: GNU GPL v2 lub pozniejsza - pelny tekst w pliku LICENSE.
"""
Dział 1 · POBIERANIE — agent `zdjęcia`  (+ krytyk `kompletność-zdjęć`).

Pobiera listę zdjęć pojazdu z serwisu obrazów IAAI i buduje rekordy do
`iaai_vehicle_images`. Zwykły HTTP (requests) — vis.iaai.com to bezpośrednie API,
bez przeglądarki.

Źródło (zweryfikowane, krok 1):
  - lista:  GET https://vis.iaai.com/dimensions?imageKeys={salvage_id}~SID  -> JSON keys[]
  - obraz:  GET https://vis.iaai.com/resizer?imageKeys={K}&width=&height=   -> JPEG

Decyzja 4: zdjęcia pobierane do nas (import do mediów WP) w rozsądnej rozdzielczości
(domyślnie ~1024px). Pobieranie jest opcjonalne (--download) — domyślnie budujemy
rekordy z gotowymi URL-ami (lazy: plik ściągamy, gdy auto wchodzi do publikacji).

Wymagania: pip install requests
Użycie:   python zdjecia.py 45293605
          python zdjecia.py --in out/listingi.jsonl --out out/zdjecia.jsonl [--download media/]
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path

import requests

VIS = "https://vis.iaai.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
DEF_W, DEF_H = 1024, 768


def resizer_url(key: str, width: int = DEF_W, height: int = DEF_H) -> str:
    return f"{VIS}/resizer?imageKeys={key}&width={width}&height={height}"


def fetch_image_list(salvage_id, session: requests.Session) -> dict:
    r = session.get(f"{VIS}/dimensions", params={"imageKeys": f"{salvage_id}~SID"}, timeout=30)
    r.raise_for_status()
    return r.json()


def build_records(salvage_id, data: dict, width: int = DEF_W, height: int = DEF_H) -> list[dict]:
    recs = []
    for img in data.get("keys", []):
        k = img["K"]
        recs.append({
            "salvage_id": int(salvage_id),
            "image_key": k,
            "seq": img.get("IN"),
            "width": img.get("W"),
            "height": img.get("H"),
            "url": resizer_url(k, width, height),
        })
    return recs


def download_images(records: list[dict], out_dir: Path, session: requests.Session, delay: float = 0.3):
    d = out_dir / str(records[0]["salvage_id"]) if records else out_dir
    d.mkdir(parents=True, exist_ok=True)
    for rec in records:
        r = session.get(rec["url"], timeout=60)
        if r.ok and r.headers.get("content-type", "").startswith("image"):
            # P3: nazwa pliku wyłącznie z int(seq) — twardo odcina path traversal, gdyby
            # seq zawierał '../' czy separatory (dotyczy tylko trybu dev --download).
            fname = d / f"{int(rec['seq'])}.jpg"
            fname.write_bytes(r.content)
            rec["local_path"] = str(fname)
        time.sleep(delay)


# ---- 🔴 KRYTYK: kompletność-zdjęć -----------------------------------------
def krytyk_kompletnosc_zdjec(data: dict, records: list[dict], session: requests.Session) -> list[str]:
    issues = []
    expected = len(data.get("keys", []))
    if len(records) != expected:
        issues.append(f"zapisano {len(records)}/{expected} zdjęć")
    keys = [r["image_key"] for r in records]
    if len(keys) != len(set(keys)):
        issues.append("duplikaty image_key")
    # próbka: pierwszy URL musi zwrócić obraz
    if records:
        try:
            h = session.get(records[0]["url"], timeout=30, stream=True)
            ct = h.headers.get("content-type", "")
            if not (h.ok and ct.startswith("image")):
                issues.append(f"próbka URL nie zwróciła obrazu (HTTP {h.status_code}, {ct})")
        except Exception as e:
            issues.append(f"próbka URL błąd: {e}")
    elif expected == 0:
        issues.append("brak zdjęć dla lotu (0 keys)")
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("salvage_id", nargs="?", help="pojedynczy lot, np. 45293605")
    ap.add_argument("--in", dest="infile", type=Path, help="JSONL z listingi (pole salvage_id)")
    ap.add_argument("--out", type=Path, default=Path("out/zdjecia.jsonl"))
    ap.add_argument("--download", metavar="DIR", type=Path, help="pobierz pliki do katalogu")
    ap.add_argument("--width", type=int, default=DEF_W)
    ap.add_argument("--height", type=int, default=DEF_H)
    ap.add_argument("--delay", type=float, default=0.5)
    args = ap.parse_args()

    ids = []
    if args.salvage_id:
        ids = [args.salvage_id]
    elif args.infile:
        ids = [json.loads(l)["salvage_id"] for l in args.infile.read_text().splitlines() if l.strip()]
    else:
        ap.error("podaj salvage_id albo --in plik.jsonl")

    session = requests.Session(); session.headers["User-Agent"] = UA
    args.out.parent.mkdir(parents=True, exist_ok=True)
    rc = 0
    with args.out.open("w", encoding="utf-8") as fh:
        for sid in ids:
            data = fetch_image_list(sid, session)
            recs = build_records(sid, data, args.width, args.height)
            if args.download and recs:
                download_images(recs, args.download, session)
            for r in recs:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            issues = krytyk_kompletnosc_zdjec(data, recs, session)
            status = "OK ✅" if not issues else "ZASTRZEŻENIA: " + "; ".join(issues)
            extra = " (+360°)" if data.get("Image360Ind") else ""
            print(f"  {sid}: {len(recs)} zdjęć{extra} | [{status}]")
            if issues:
                rc = 1
            time.sleep(args.delay)
    print(f"[zdjęcia] zapisano -> {args.out}")
    sys.exit(rc)


if __name__ == "__main__":
    main()
