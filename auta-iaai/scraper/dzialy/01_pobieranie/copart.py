# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Importer Aukcji (IAAI + Copart).
# Licencja: GNU GPL v2 lub pozniejsza - pelny tekst w pliku LICENSE.
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

# `requests` importujemy LENIWIE w _session() (jedyne miejsce sieciowe), żeby czyste funkcje
# mapujące (_map_detail) dało się testować jednostkowo bez tej zależności. Adnotacje typów są
# odroczone przez `from __future__ import annotations`, więc `-> requests.Session` nie wymaga
# importu w czasie wczytywania modułu.

BASE = "https://www.copart.com"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/125.0 Safari/537.36")


def _session() -> requests.Session:
    import requests            # leniwy import ciężkiej zależności (patrz nagłówek)
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


_PAGE = 100          # rozmiar strony wyszukiwarki Copart


def stage_listingi(args):
    """Wyszukiwarka -> karty lotów. P2b: STRONICUJE po `page` (dotąd 1 strona ≤100 lotów →
    'full' był strukturalnie niekompletny). mode=live → tylko 1 strona najnowszych; mode=full
    → do --max-pages stron. Krytyk kompletności zwraca exit≠0 przy urwanym crawlu (0 kart)
    lub gdy limit stron przyciął zadeklarowany `totalElements` — chroni reconcile (patrz też
    próg RECONCILE_MIN_RATIO w json_agent)."""
    sess = _session()
    kw = args.base
    max_pages = 1 if args.mode == "live" else max(1, args.max_pages)
    out, total, page = [], None, 0
    while page < max_pages:
        payload = {"query": [kw] if kw else ["*"], "filter": {}, "watchListOnly": False,
                   "freeFormSearch": True, "page": page, "size": _PAGE,
                   "sort": ["auction_date_type desc"]}
        try:
            r = sess.post(f"{BASE}/public/lots/search-results", json=payload, timeout=30)
            data = r.json() if r.status_code == 200 else {}
        except Exception as e:
            print(f"[copart:listingi] ⚠ strona {page}: {e}", file=sys.stderr)
            break
        results = (data.get("data", {}) or {}).get("results", {}) or {}
        rows = results.get("content", []) or []
        if total is None:
            total = results.get("totalElements")
        for it in rows:
            try:                                    # P4: jeden nietypowy wiersz nie ubija etapu
                lot = it.get("lotNumberStr") or it.get("ln")
                if not lot:
                    continue
                out.append({"salvage_id": int(str(lot).replace("*", "") or 0), "source": "copart",
                            "make": it.get("mkn"), "model": it.get("lmg"), "year": it.get("lcy"),
                            "buy_now": it.get("bnp"), "current_bid": it.get("hb"),
                            "detail_url": f"{BASE}/lot/{lot}"})
            except (ValueError, TypeError):
                continue
        page += 1
        if len(rows) < _PAGE:                       # ostatnia strona
            break
        time.sleep(0.4)                             # łagodnie dla serwera między stronami
    args.out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in out))
    suffix = f"/{total}" if total is not None else ""
    print(f"[copart:listingi] kart={len(out)}{suffix} (stron={page}) -> {args.out}")

    # 🔴 KRYTYK: kompletność-listy (analogicznie do IAAI). Urwany crawl -> exit 1,
    # by NIE reconcile'ować względem niepełnego feedu.
    issues = []
    if not out:
        issues.append("0 kart — możliwa blokada anty-bot / wymagane logowanie")
    elif args.mode == "full" and isinstance(total, int) and len(out) < total and page >= max_pages:
        issues.append(f"limit stron: pobrano {len(out)} < zadeklarowanych {total} "
                      f"(zwiększ --max-pages)")
    if issues:
        print("[krytyk:kompletność-copart] ZASTRZEŻENIA: " + "; ".join(issues), file=sys.stderr)
        return 1
    print("[krytyk:kompletność-copart] OK ✅")
    return 0


def stage_szczegoly(args):
    sess = _session()
    lots = []
    for _l in args.infile.read_text().splitlines():
        if not _l.strip():
            continue
        try:                                    # P4: zły wiersz nie ubija całego etapu
            lots.append(json.loads(_l)["salvage_id"])
        except (ValueError, KeyError):
            continue
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
    lots = []
    for _l in args.infile.read_text().splitlines():
        if not _l.strip():
            continue
        try:                                    # P4: zły wiersz nie ubija całego etapu
            lots.append(json.loads(_l)["salvage_id"])
        except (ValueError, KeyError):
            continue
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
    rc = {"listingi": stage_listingi, "szczegoly": stage_szczegoly,
          "zdjecia": stage_zdjecia}[args.stage](args)
    sys.exit(rc or 0)          # listingi zwraca kod krytyka kompletności; reszta None -> 0


if __name__ == "__main__":
    main()
