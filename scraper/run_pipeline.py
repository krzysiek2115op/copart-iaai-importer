"""
ORKIESTRATOR pipeline (M4) — jedna komenda spina wszystkie działy Pythona do bazy.

Kolejność: zgodność(check) -> listingi -> szczegóły -> [merge] -> zdjęcia
           -> VIN -> jednostki -> match -> diff -> audyt -> json(upsert+zdjęcia[, reconcile]).

Tryby:
  full  — cała bieżąca oferta + reconcile (oznacza zniknięte loty jako removed)
  live  — tylko nowe; bez reconcile

Most do WordPressa (publikacja CPT + media) odpala się PO STRONIE WP (PHP):
  wp eval 'iaai_publish_all_active();'        # WP-CLI, po imporcie do bazy
(lub wp-cron). PHP nie jest uruchamiany z tego runnera.

Wymagania: jak w poszczególnych działach (playwright, bs4, requests, pymysql, jsonschema).
Użycie:   python run_pipeline.py --mode full --base "https://www.iaai.com/Search?Keyword=Ferrari" --limit 5
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, urllib.robotparser
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "dzialy"
PY = sys.executable


def step(name: str, cwd: Path, cmd: list[str], keep_going: bool):
    print(f"\n===== {name} =====")
    r = subprocess.run([PY, *cmd], cwd=cwd)
    if r.returncode != 0:
        print(f"[orkiestrator] krytyk działu '{name}' zgłosił problem (exit {r.returncode}).")
        if not keep_going:
            print("[orkiestrator] STOP. Użyj --keep-going, by kontynuować mimo zastrzeżeń.")
            sys.exit(r.returncode)
    return r.returncode


def merge_card_detail(card: Path, detail: Path, out: Path):
    """Łączy rekordy z listy (karta) i szczegółów po salvage_id (szczegóły nadpisują,
    karta uzupełnia pola których szczegóły nie mają: buy_now, lane, aisle...)."""
    by_id = {}
    for p in (card, detail):                 # najpierw karta, potem szczegóły (override)
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            sid = r.get("salvage_id")
            base = by_id.get(sid, {})
            for k, v in r.items():
                if v not in (None, ""):
                    base[k] = v
            by_id[sid] = base
    out.write_text("\n".join(json.dumps(v, ensure_ascii=False) for v in by_id.values()))
    return len(by_id)


def compliance_note(base_url: str):
    rp = urllib.robotparser.RobotFileParser()
    from urllib.parse import urlparse
    p = urlparse(base_url)
    rp.set_url(f"{p.scheme}://{p.netloc}/robots.txt")
    try:
        rp.read()
        if not rp.can_fetch("*", base_url):
            print(f"[zgodność] ⚠️ robots.txt ZABRANIA {base_url} — decyzja prawna (ToS) po stronie właściciela.")
        else:
            print(f"[zgodność] robots.txt dopuszcza {base_url}.")
    except Exception:
        print("[zgodność] nie udało się wczytać robots.txt.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["full", "live"], default="full")
    ap.add_argument("--base", default="https://www.iaai.com/Search")
    ap.add_argument("--segments", type=Path, default=None,
                    help="#6: JSON segmentów do PEŁNEGO pokrycia IAAI (iteracja filtrów). "
                         "Gdy podany — zamiast pojedynczego --base używa agenta `pokrycie`.")
    ap.add_argument("--max-pages", type=int, default=100)
    ap.add_argument("--limit", type=int, default=0, help="ogranicz liczbę lotów do szczegółów/zdjęć (0=bez limitu)")
    ap.add_argument("--workdir", type=Path, default=Path("pipeline_out"))
    ap.add_argument("--keep-going", action="store_true")
    ap.add_argument("--source", choices=["iaai", "copart"], default="iaai",
                    help="źródło danych. Copart używa modułu 01_pobieranie/copart.py "
                         "(logowanie przez ENV COPART_COOKIES) i zapisuje source='copart'.")
    args = ap.parse_args()

    # Copart: gdy nie podano własnego --base, użyj słowa kluczowego z ENV (puste = cała oferta).
    if args.source == "copart" and args.base == "https://www.iaai.com/Search":
        args.base = os.environ.get("COPART_BASE", "")

    W = args.workdir
    W.mkdir(parents=True, exist_ok=True)
    kg = args.keep_going
    if args.base:
        compliance_note(args.base if args.base.startswith("http")
                        else f"https://www.copart.com/?q={args.base}")

    # 1. POBIERANIE — dobór modułów wg źródła (IAAI: listingi/szczegoly/zdjecia; Copart: copart.py)
    d1 = ROOT / "01_pobieranie"
    cop = ( args.source == "copart" )
    if not cop and args.segments:              # #6: pełne pokrycie przez iterację segmentów (tylko IAAI)
        step("1a pokrycie (iteracja filtrów)", d1,
             ["pokrycie.py", "--segments", str(args.segments.resolve()), "--mode", args.mode,
              "--max-pages", str(args.max_pages), "--out", str((W / "listingi.jsonl").resolve())], kg)
    elif cop:
        step("1a listingi (copart)", d1, ["copart.py", "--stage", "listingi", "--base", args.base,
             "--mode", args.mode, "--max-pages", str(args.max_pages), "--out", str(W / "listingi.jsonl")], kg)
    else:
        step("1a listingi", d1, ["listingi.py", "--base", args.base, "--mode", args.mode,
                                 "--max-pages", str(args.max_pages), "--out", str(W / "listingi.jsonl")], kg)
    listings = W / "listingi.jsonl"
    if args.limit:                            # ogranicz wejście do szczegółów/zdjęć
        lines = listings.read_text().splitlines()[: args.limit]
        (W / "listingi_lim.jsonl").write_text("\n".join(lines))
        listings = W / "listingi_lim.jsonl"
    det = ["copart.py", "--stage", "szczegoly"] if cop else ["szczegoly.py"]
    zdj = ["copart.py", "--stage", "zdjecia"] if cop else ["zdjecia.py"]
    step("1b szczegóły", d1, det + ["--in", str(listings), "--out", str(W / "szczegoly.jsonl")], kg)
    step("1c zdjęcia", d1, zdj + ["--in", str(listings), "--out", str(W / "zdjecia.jsonl")], kg)

    # merge karta + szczegóły
    n = merge_card_detail(listings, W / "szczegoly.jsonl", W / "merged.jsonl")
    print(f"\n[merge] połączono karta+szczegóły -> {n} rekordów ({W/'merged.jsonl'})")

    # 2. NORMALIZACJA
    d2 = ROOT / "02_normalizacja"
    step("2a VIN", d2, ["vin.py", "--in", str(W / "merged.jsonl"), "--out", str(W / "vin.jsonl")], kg)
    step("2b jednostki", d2, ["jednostki.py", "--in", str(W / "vin.jsonl"), "--out", str(W / "jedn.jsonl")], kg)

    # 3. DEDUPLIKACJA
    step("3 match", ROOT / "03_deduplikacja",
         ["match.py", "--in", str(W / "jedn.jsonl"), "--out", str(W / "dedup.jsonl")], kg)

    # 4a. DIFF -> 5. AUDYT -> 4b. JSON (kolejność po naprawie H2)
    d4 = ROOT / "04_synchronizacja"
    step("4a diff", d4, ["diff.py", "--in", str(W / "dedup.jsonl"), "--out", str(W / "diff.jsonl")], kg)
    step("5 audyt", ROOT / "05_audyt",
         ["walidacja.py", "--in", str(W / "diff.jsonl"), "--out", str(W / "audyt.jsonl")], kg)
    json_cmd = ["json_agent.py", "--in", str(W / "audyt.jsonl"), "--images", str(W / "zdjecia.jsonl"),
                "--source", args.source]
    if args.mode == "full" and not args.limit:
        json_cmd.append("--reconcile")          # reconcile TYLKO przy pełnym feedzie
    elif args.mode == "full" and args.limit:
        print("[orkiestrator] --limit ustawiony -> reconcile POMINIĘTY (feed niepełny, by nie oznaczyć błędnie 'removed')")
    step("4b json (zapis do bazy)", d4, json_cmd, kg)

    print("\n[orkiestrator] PIPELINE ZAKOŃCZONY ✅")
    print("[orkiestrator] Krok WP (osobno, w WordPressie):  wp eval 'iaai_publish_all_active();'")


if __name__ == "__main__":
    main()
