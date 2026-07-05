"""
Dział 1 · POBIERANIE — ŹRÓDŁO **Copart** (odpowiednik listingi/szczegoly/zdjecia dla IAAI).

Jeden plik, 3 etapy (wybierane przez --stage), o tym samym „kontrakcie" wejścia/wyjścia
co moduły IAAI, żeby wpiąć się w istniejący pipeline (run_pipeline.py --source copart):

  --stage listingi  --base <URL/keyword> --mode full|live --max-pages N --out cards.jsonl
  --stage szczegoly --in cards.jsonl --out detail.jsonl
  --stage zdjecia   --in cards.jsonl --out images.jsonl

Wyjście = JSONL w TYM SAMYM kształcie co IAAI (klucz `salvage_id` = numer lotu Copart),
każdy rekord dostaje `source="copart"`. Dalsze działy (normalizacja→dedup→audyt→json)
są wspólne. Kolumnę `source` do bazy zapisuje json_agent (--source copart).

⚠ REALIA COPART (walidacja na VPS):
  • Silna ochrona anty-bot (Cloudflare/Incapsula). Zwykły requests bywa blokowany —
    na VPS może być potrzebny nagłówek/cookies z sesji przeglądarki albo Playwright.
  • Pełne dane i WSZYSTKIE zdjęcia często wymagają zalogowania na konto Member.
    Podaj sesję przez ENV:  COPART_COOKIES="name=val; name2=val2"  (skopiowane z zalogowanej
    przeglądarki) — dołączane do żądań. Bez tego część pól/zdjęć może być niedostępna.

Endpointy publiczne (bez gwarancji stałości — Copart bywa zmieniany):
  • szczegóły lotu: GET  https://www.copart.com/public/data/lotdetails/solr/{lot}
  • zdjęcia lotu:   GET  https://www.copart.com/public/data/lotdetails/solr/lotImages/{lot}
  • wyszukiwarka:   POST https://www.copart.com/public/lots/search-results  (JSON filtr)

Wymagania: pip install requests
"""
from __future__ import annotations
import argparse, json, os, sys, time
from pathlib import Path

import requests

BASE = "https://www.copart.com"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/125.0 Safari/537.36")


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Referer": BASE + "/",
        "X-Requested-With": "XMLHttpRequest",
    })
    # Sesja zalogowana (Member) — cookies z ENV, żeby dostać pełne dane/zdjęcia.
    cookies = os.environ.get("COPART_COOKIES", "").strip()
    if cookies:
        for part in cookies.split(";"):
            if "=" in part:
                k, v = part.strip().split("=", 1)
                s.cookies.set(k, v)
    return s


# ---- mapowanie pól Copart -> wspólny kształt (jak IAAI) --------------------
def _map_detail(d: dict) -> dict:
    """Copart lotDetails (klucze skrócone) -> nasz rekord. Best-effort; braki = None."""
    g = d.get
    def num(x):
        try:
            return int(float(x))
        except (TypeError, ValueError):
            return None
    return {
        "salvage_id":      num(g("ln")),                       # Lot number
        "source":          "copart",
        "vin":             g("fv") or g("vin"),
        "year":            num(g("lcy")),                      # year
        "make":            g("mkn"),                           # make name
        "model":           g("lmg") or g("mmod"),             # model group / model
        "series":          g("lm"),
        "body_style":      g("bstl"),
        "engine":          g("egn"),
        "cylinders":       num(g("cy")),
        "fuel_type":       g("ftd") or g("ft"),
        "transmission":    g("tmtp"),
        "drive_line":      g("drv"),
        "color":           g("clr"),
        "odometer":        num(g("orr")),                      # odometer reading
        "odometer_uom":    "mi",
        "odometer_brand":  g("ord"),                           # ACTUAL / NOT ACTUAL
        "primary_damage":  g("dd"),                            # primary damage
        "secondary_damage": g("sdd"),
        "loss":            g("lossType"),
        "title":           g("tzd") or g("td"),                # title/state
        "run_and_drive":   ("Run and Drive" if g("orgd") or g("rd") else None),
        "key_available":   ("Yes" if str(g("key")).lower() in ("y", "yes", "true", "1") else "No"),
        "selling_branch":  g("yn"),                            # yard name
        "buy_now":         g("bnp"),                           # buy now price
        "current_bid":     g("hb"),                            # high bid
        "detail_url":      f"{BASE}/lot/{g('ln')}",
    }


def _fetch_json(sess, url: str):
    r = sess.get(url, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code} dla {url} (możliwa blokada anty-bot / wymagane logowanie)")
    return r.json()


def stage_listingi(args):
    """Wyszukiwarka -> karty lotów (podstawowe pola). Zwraca JSONL (salvage_id + karta)."""
    sess = _session()
    kw = args.base
    payload = {"query": [kw] if kw else ["*"], "filter": {}, "watchListOnly": False,
               "freeFormSearch": True, "page": 0, "size": min(100, args.max_pages * 20),
               "sort": ["auction_date_type desc"]}
    out = []
    try:
        r = sess.post(f"{BASE}/public/lots/search-results", json=payload, timeout=30)
        data = r.json() if r.status_code == 200 else {}
        rows = (data.get("data", {}) or {}).get("results", {}).get("content", []) or []
        for it in rows:
            lot = it.get("lotNumberStr") or it.get("ln")
            if not lot:
                continue
            out.append({"salvage_id": int(str(lot).replace("*", "") or 0), "source": "copart",
                        "make": it.get("mkn"), "model": it.get("lmg"), "year": it.get("lcy"),
                        "buy_now": it.get("bnp"), "current_bid": it.get("hb"),
                        "detail_url": f"{BASE}/lot/{lot}"})
    except Exception as e:
        print(f"[copart:listingi] ⚠ {e}", file=sys.stderr)
    args.out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in out))
    print(f"[copart:listingi] kart={len(out)} -> {args.out}")


def stage_szczegoly(args):
    sess = _session()
    lots = [json.loads(l)["salvage_id"] for l in args.infile.read_text().splitlines() if l.strip()]
    out = []
    for lot in lots:
        try:
            d = _fetch_json(sess, f"{BASE}/public/data/lotdetails/solr/{lot}")
            ld = (d.get("data", {}) or {}).get("lotDetails") or d.get("lotDetails") or {}
            if ld:
                out.append(_map_detail(ld))
        except Exception as e:
            print(f"[copart:szczegoly] lot {lot}: {e}", file=sys.stderr)
        time.sleep(0.4)                                        # łagodnie dla serwera
    args.out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in out))
    print(f"[copart:szczegoly] szczegółów={len(out)} -> {args.out}")


def stage_zdjecia(args):
    sess = _session()
    lots = [json.loads(l)["salvage_id"] for l in args.infile.read_text().splitlines() if l.strip()]
    out = []
    for lot in lots:
        try:
            d = _fetch_json(sess, f"{BASE}/public/data/lotdetails/solr/lotImages/{lot}")
            imgs = (d.get("data", {}) or {}).get("imagesList", {}).get("FULL_IMAGE") \
                or (d.get("data", {}) or {}).get("imagesList", {}).get("HIGH_RESOLUTION_IMAGE") or []
            for i, im in enumerate(imgs, 1):
                url = im.get("url") if isinstance(im, dict) else im
                if not url:
                    continue
                out.append({"salvage_id": lot, "source": "copart",
                            "image_key": f"copart-{lot}-{i}", "seq": i,
                            "width": None, "height": None, "url": url})
        except Exception as e:
            print(f"[copart:zdjecia] lot {lot}: {e}", file=sys.stderr)
        time.sleep(0.4)
    args.out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in out))
    print(f"[copart:zdjecia] zdjęć={len(out)} -> {args.out}")


def main():
    ap = argparse.ArgumentParser(description="Copart — pobieranie (listingi/szczegoly/zdjecia)")
    ap.add_argument("--stage", required=True, choices=["listingi", "szczegoly", "zdjecia"])
    ap.add_argument("--base", default="")
    ap.add_argument("--mode", choices=["full", "live"], default="full")
    ap.add_argument("--max-pages", type=int, default=5)
    ap.add_argument("--in", dest="infile", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    {"listingi": stage_listingi, "szczegoly": stage_szczegoly, "zdjecia": stage_zdjecia}[args.stage](args)


if __name__ == "__main__":
    main()
