#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Buduje CZYSTĄ paczkę dostawy dla klienta (bez plików deweloperskich).

Zawartość paczki (tylko to, czego klient realnie potrzebuje):
  0-PRZECZYTAJ-MNIE-NAJPIERW.md   — instrukcja tekstem (na wierzchu)
  0-Instrukcja-klienta.pdf        — pełna instrukcja A–Z (ładny PDF)
  Instrukcje-PDF/                 — każdy etap jako osobny PDF
  iaai-importer.zip               — wtyczka do wgrania w WordPress
  scraper/                        — program zbierający (na VPS)
  deploy/                         — instalator + usługi systemd
  db/                             — schemat bazy (referencja)

Świadomie POMIJANE (zbędne dla klienta): .git, dev-test, dist, __pycache__,
wp-plugin/ (źródło zdublowane z iaai-importer.zip), docs/ wewnętrzne
(dzialy/refs/audyty/pipeline/architektura), generatory PDF (*.py), STATUS.md,
README.md, .gitignore, testy, pliki .pyc, .svg/.gen.

Uruchom:  python3 dev-test/pakuj-dostawe.py
Wynik:    dist/IAAI-Importer-dostawa.zip (+ kopia na Pulpicie)
"""
import os, zipfile, shutil, tempfile, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist"); os.makedirs(DIST, exist_ok=True)
PLUG_ZIP = os.path.join(DIST, "iaai-importer.zip")
OUT = os.path.join(DIST, "IAAI-Importer-dostawa.zip")

SKIP_DIRS = {"__pycache__", "tests", ".git", ".idea", ".vscode"}
SKIP_EXT = {".pyc", ".pyo"}

def add_tree(z, src_abs, arc_prefix):
    for base, dirs, files in os.walk(src_abs):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if fn == ".DS_Store" or os.path.splitext(fn)[1] in SKIP_EXT:
                continue
            full = os.path.join(base, fn)
            arc = os.path.join(arc_prefix, os.path.relpath(full, src_abs))
            z.write(full, arc)

def build_plugin_zip():
    plug = os.path.join(ROOT, "wp-plugin", "iaai-importer")
    with zipfile.ZipFile(PLUG_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        add_tree(z, plug, "iaai-importer")

def main():
    build_plugin_zip()
    if os.path.exists(OUT):
        os.remove(OUT)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        # instrukcje na wierzchu
        z.write(os.path.join(ROOT, "docs/klient/PRZECZYTAJ-MNIE-NAJPIERW.md"), "0-PRZECZYTAJ-MNIE-NAJPIERW.md")
        pdf = os.path.join(ROOT, "docs/klient/Instrukcja-klienta.pdf")
        if os.path.exists(pdf):
            z.write(pdf, "0-Instrukcja-klienta.pdf")
        # etapy jako osobne PDF
        pdir = os.path.join(ROOT, "docs/klient/pdf")
        if os.path.isdir(pdir):
            for fn in sorted(os.listdir(pdir)):
                if fn.endswith(".pdf"):
                    z.write(os.path.join(pdir, fn), os.path.join("Instrukcje-PDF", fn))
        # wtyczka
        z.write(PLUG_ZIP, "iaai-importer.zip")
        # części działające na serwerze
        for d in ("scraper", "deploy", "db"):
            add_tree(z, os.path.join(ROOT, d), d)

    names = zipfile.ZipFile(OUT).namelist()
    print("Zbudowano:", OUT)
    print("  plikow:", len(names), "| rozmiar:", round(os.path.getsize(OUT)/1024/1024, 2), "MB")
    top = sorted({n.split("/")[0] for n in names})
    print("  na wierzchu:", top)
    # kontrola: nic deweloperskiego
    bad = [n for n in names if n.startswith(("wp-plugin/", "docs/", "STATUS", "README", ".git"))
           or "__pycache__" in n or n.endswith((".pyc", ".gen.py")) or "/tests/" in n
           or n in ("STATUS.md", "README.md", ".gitignore")]
    print("  zbednych dla klienta:", len(bad), bad[:6] if bad else "")
    desk = os.path.expanduser("~/Pulpit")
    if os.path.isdir(desk):
        shutil.copy2(OUT, os.path.join(desk, "IAAI-Importer-dostawa.zip"))
        print("  kopia na Pulpicie")
    return 0 if not bad else 1

if __name__ == "__main__":
    sys.exit(main())
