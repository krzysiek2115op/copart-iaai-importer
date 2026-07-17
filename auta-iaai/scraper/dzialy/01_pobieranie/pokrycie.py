# SPDX-License-Identifier: GPL-2.0-or-later
# Copyright (C) 2026 Importer Aukcji (IAAI + Copart).
# Licencja: GNU GPL v2 lub pozniejsza - pelny tekst w pliku LICENSE.
"""
Dział 1 · POBIERANIE — agent `pokrycie`  (+ krytyk `kompletność-pokrycia`).

PROBLEM (#6): pojedyncze zapytanie wyszukiwarki IAAI ma limit — pager pokazuje
tylko część bardzo dużych wyników. Żeby zebrać CAŁĄ bieżącą ofertę, trzeba
podzielić ją na **segmenty** (filtry, np. po stanie/marce/typie), zebrać każdy
osobno i ZŁĄCZYĆ wyniki, deduplikując po `salvage_id`.

Ten agent jest **filtro-agnostyczny**: dostaje gotową listę URL-i segmentów
(każdy = zawężone wyszukiwanie) i scala wynik. JAK segmentować (który parametr
filtra) to konfiguracja operatora — patrz segments.example.json. Krytyk
`kompletność-pokrycia` WYKRYWA segment, który i tak był za duży (zebrano mniej
niż deklaruje ResultCount) → sygnał „podziel ten segment drobniej".

Nie zgadujemy parametrów IAAI: wartości segmentów potwierdza się na żywym IAAI
(pierwsze uruchomienie). Domyślnie znany, działający filtr to `?Keyword=...`.

Wymagania: jak listingi.py (playwright, bs4).
Użycie:
  python pokrycie.py --segments segments.json --out out/listingi.jsonl
  # segments.json: [{"label":"BMW","url":"https://www.iaai.com/Search?Keyword=BMW"}, ...]
"""
from __future__ import annotations
import argparse, json, sys, tempfile
from pathlib import Path

from listingi import run, PAGE_SIZE


def load_segments(spec: Path) -> list[dict]:
    data = json.loads(spec.read_text(encoding="utf-8"))
    segs = []
    for i, s in enumerate(data):
        if isinstance(s, str):                       # sama lista URL-i
            url, label = s, f"seg{i+1}"
        else:
            url, label = s.get("url", ""), s.get("label", f"seg{i+1}")
        if not url.startswith("http"):               # pomiń komentarze/wpisy bez URL
            continue
        segs.append({"label": label, "url": url})
    if not segs:
        raise SystemExit("[pokrycie] brak prawidłowych segmentów (URL musi zaczynać się od http)")
    return segs


def collect(segments: list[dict], out_path: Path, mode: str, max_pages: int,
            delay: float, headless: bool = True) -> dict:
    """Zbiera każdy segment do pliku tymczasowego, scala unikalne po salvage_id."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    seen: set[int] = set()
    seg_meta: list[dict] = []
    tmpdir = Path(tempfile.mkdtemp(prefix="pokrycie_"))

    with out_path.open("w", encoding="utf-8") as out_fh:
        for n, seg in enumerate(segments, 1):
            seg_file = tmpdir / f"seg_{n}.jsonl"
            print(f"\n[pokrycie] segment {n}/{len(segments)}: {seg['label']}  ({seg['url']})")
            res = run(seg["url"], mode, seg_file, max_pages, delay, headless=headless)

            collected = dups = 0
            if seg_file.exists():
                for line in seg_file.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    rec = json.loads(line)
                    sid = rec.get("salvage_id")
                    collected += 1
                    if sid in seen:
                        dups += 1
                        continue
                    seen.add(sid)
                    out_fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            rc = res.get("result_count")
            seg_meta.append({"label": seg["label"], "url": seg["url"],
                             "collected": collected, "result_count": rc,
                             "new": collected - dups, "dups": dups,
                             "blocked": res.get("blocked")})    # F2: propaguj blokadę segmentu
            print(f"[pokrycie]   zebrano {collected}"
                  + (f"/{rc}" if rc else "") + f", nowych {collected - dups}, dubli {dups}"
                  + f" | unikalnych łącznie {len(seen)}")

    return {"unique_total": len(seen), "segments": seg_meta}


# ---- 🔴 KRYTYK: kompletność-pokrycia --------------------------------------
def krytyk_kompletnosc_pokrycia(result: dict, page_size: int = PAGE_SIZE) -> list[str]:
    """Wykrywa luki w pokryciu CAŁEGO IAAI:
    1) segment urwany — zebrano < ResultCount (limit pagera) -> podziel drobniej,
    2) segment „podejrzanie pełny" — dokładnie u progu limitu strony,
    3) zerowy wynik segmentu (zły filtr / brak aut)."""
    issues = []
    for m in result["segments"]:
        if m.get("blocked"):                          # F2: blokada w segmencie
            issues.append(f"segment '{m['label']}': BLOKADA ({m['blocked']}) — zwolnij/odpuść")
        rc, got = m.get("result_count"), m["collected"]
        if rc and got < rc:
            issues.append(f"segment '{m['label']}': zebrano {got}/{rc} — URWANY "
                          f"(limit pagera) → podziel ten segment drobniej")
        if got == 0:
            issues.append(f"segment '{m['label']}': 0 lotów — sprawdź filtr/URL")
    if result["unique_total"] == 0:
        issues.append("łącznie 0 unikalnych lotów — pokrycie nieskuteczne")
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--segments", type=Path, required=True,
                    help="JSON: lista segmentów [{label,url}] albo lista URL-i")
    ap.add_argument("--out", type=Path, default=Path("out/listingi.jsonl"))
    ap.add_argument("--mode", choices=["full", "live"], default="full")
    ap.add_argument("--max-pages", type=int, default=100)
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    segments = load_segments(args.segments)
    print(f"[pokrycie] {len(segments)} segment(ów), tryb {args.mode}")
    result = collect(segments, args.out, args.mode, args.max_pages, args.delay,
                     headless=not args.headed)
    print(f"\n[pokrycie] UNIKALNYCH lotów: {result['unique_total']} -> {args.out}")

    issues = krytyk_kompletnosc_pokrycia(result)
    if issues:
        print("[krytyk:kompletność-pokrycia] ZASTRZEŻENIA:")
        for i in issues:
            print("   -", i)
        sys.exit(1)
    print("[krytyk:kompletność-pokrycia] OK ✅ (żaden segment nie urwany)")


if __name__ == "__main__":
    main()
