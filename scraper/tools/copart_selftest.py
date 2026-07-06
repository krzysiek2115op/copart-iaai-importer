#!/usr/bin/env python3
"""
Samotest Copart — czy DRUGIE ŹRÓDŁO oddaje prawdziwe dane i czy trafiają na kartę na stronie.

Dwie niezależne części:

  A) LIVE PROBE — realne żądanie HTTP do Copart (biblioteka standardowa `urllib`, bez zależności).
     Pokazuje, czy serwis oddaje dane anonimowo, czy blokuje (Cloudflare/anty-bot) i wymaga konta
     Member. Jeśli ustawisz `COPART_COOKIES` (ciasteczka zalogowanej sesji), próba idzie z nią —
     to docelowy tryb na VPS. Diagnostyka: nie zapisuje nic do bazy.

  B) MAPPING — realistyczny rekord z API Copart (kształt `lotdetails/solr`, klucze skrócone)
     przepuszczony przez `copart._map_detail` → walidacja kompletności pól + podgląd karty,
     jaka trafiłaby na stronę (tytuł, przebieg w km, cena, uszkodzenie, plakietka źródła).

Uruchom (lokalnie, bez konta — pokaże blokadę + pełne mapowanie):
    python3 scraper/tools/copart_selftest.py

Na VPS z kontem Member (realne dane live):
    COPART_COOKIES="<cookies zalogowanej sesji>" python3 scraper/tools/copart_selftest.py --lot <realny_lot>

Kod wyjścia: 0 = mapowanie OK (część B). Część A jest tylko informacyjna (blokada nie = błąd kodu).
"""
from __future__ import annotations
import os, sys, json, argparse, importlib.util, urllib.request, urllib.error
from pathlib import Path

BASE = "https://www.copart.com"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/125.0 Safari/537.36")

# Realistyczny kształt odpowiedzi Copart lotdetails/solr (klucze skrócone jak w realnym API).
FIXTURE = {
    "ln": 58421990, "lcy": 2018, "mkn": "FORD", "lmg": "ESCAPE SE", "lm": "SE",
    "fv": "1FMCU9GD5JUA12345", "orr": 72150, "ord": "ACTUAL", "bstl": "SPORT UTILITY",
    "egn": "1.5L 4", "cy": 4, "ftd": "GAS", "tmtp": "AUTOMATIC", "drv": "AWD", "clr": "WHITE",
    "dd": "FRONT END", "sdd": "SIDE", "lossType": "COLLISION", "tzd": "TX - CERT OF TITLE",
    "orgd": True, "key": "YES", "yn": "TX - DALLAS", "bnp": 8500, "hb": 5200,
}


def load_copart():
    p = Path(__file__).resolve().parents[1] / "dzialy" / "01_pobieranie" / "copart.py"
    spec = importlib.util.spec_from_file_location("copart", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def live_probe(lot: int) -> bool:
    print("=" * 66)
    print("A) LIVE PROBE — realne żądanie do Copart (diagnostyka, bez zapisu)")
    print("=" * 66)
    cookies = os.environ.get("COPART_COOKIES", "").strip()
    print(f"  Sesja Member (COPART_COOKIES): {'TAK' if cookies else 'NIE — próba anonimowa'}")
    url = f"{BASE}/public/data/lotdetails/solr/{lot}"
    print(f"  GET {url}")
    headers = {"User-Agent": UA, "Accept": "application/json, text/plain, */*",
               "Referer": BASE + "/", "X-Requested-With": "XMLHttpRequest"}
    if cookies:
        headers["Cookie"] = cookies
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as r:
            ctype = r.headers.get("Content-Type", "")
            body = r.read(6000).decode("utf-8", "replace")
            print(f"  HTTP {r.status}  ·  {ctype}")
            try:
                data = json.loads(body)
                print("  → Copart ODDAŁ JSON (dane dostępne):")
                print("    " + json.dumps(data, ensure_ascii=False)[:280] + " ...")
                return True
            except json.JSONDecodeError:
                print("  → odpowiedź NIE jest JSON-em (najpewniej strona ochrony Cloudflare).")
                print("    fragment: " + " ".join(body[:160].split()))
    except urllib.error.HTTPError as e:
        why = "blokada anty-bot / wymagane logowanie Member" if e.code in (401, 403, 412, 429) else e.reason
        print(f"  HTTP {e.code} — {why}")
    except Exception as e:  # timeout/DNS/sieć
        print(f"  Błąd sieci: {type(e).__name__}: {e}")
    print("  (Blokada/anonimowy brak danych to ZACHOWANIE SERWISU, nie błąd kodu — patrz część B.)")
    return False


def mapping_test(copart) -> bool:
    print()
    print("=" * 66)
    print("B) MAPPING — rekord z API Copart → karta na Twojej/kliencie stronie")
    print("=" * 66)
    rec = copart._map_detail(FIXTURE)
    show = ["source", "salvage_id", "year", "make", "model", "vin", "odometer", "odometer_uom",
            "primary_damage", "secondary_damage", "transmission", "fuel_type", "buy_now",
            "current_bid", "key_available", "run_and_drive"]
    print("  Zmapowany rekord (to trafia do wspólnej bazy, kolumna source):")
    for k in show:
        print(f"    {k:17}= {rec.get(k)}")
    need = ["salvage_id", "source", "year", "make", "model", "odometer", "primary_damage"]
    miss = [k for k in need if rec.get(k) in (None, "")]
    km = round(rec["odometer"] * 1.60934) if rec.get("odometer") else None
    print("\n  → PODGLĄD KARTY NA STRONIE (jak zrobi front.php):")
    print(f"    Tytuł:     {rec.get('year')} {rec.get('make')} {rec.get('model')}")
    print(f"    Przebieg:  {km} km ({rec.get('odometer')} mi)")
    print(f"    Cena:      Buy Now {rec.get('buy_now')} USD   (bid {rec.get('current_bid')})")
    print(f"    Uszkodz.:  {rec.get('primary_damage')} / {rec.get('secondary_damage')}")
    print(f"    Skrzynia:  {rec.get('transmission')} · Kluczyk: {rec.get('key_available')}")
    print(f"    Plakietka: {str(rec.get('source')).upper()}   (filtr źródła: Copart)")
    ok = (rec.get("source") == "copart") and not miss
    print(f"\n  WYNIK: {'✅ KOMPLET — dane Copart mapują się 1:1 na kartę' if ok else '❌ BRAKI: ' + str(miss)}")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lot", type=int, default=FIXTURE["ln"], help="numer lotu Copart do próby live")
    ap.add_argument("--skip-live", action="store_true", help="pomiń część A (tylko mapowanie)")
    args = ap.parse_args()
    if not args.skip_live:
        live_probe(args.lot)
    ok = mapping_test(load_copart())
    print("\n" + ("PODSUMOWANIE: mapowanie Copart→karta DZIAŁA. Live wymaga konta Member na VPS."
                  if ok else "PODSUMOWANIE: mapowanie ma braki — sprawdź _map_detail."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
