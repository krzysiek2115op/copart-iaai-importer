#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Buduje paczke wtyczki dla wersji DEMO (Playground) -> demo/iaai-importer.zip
i sprawdza poprawnosc blueprint.json.

Uruchom:  python3 demo/build-demo.py
"""
import os, sys, json, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = os.path.join(ROOT, "demo")
PLUG = os.path.join(ROOT, "wp-plugin", "iaai-importer")
ZIP  = os.path.join(DEMO, "iaai-importer.zip")

SKIP_DIRS = {"__pycache__", "tests", ".git", ".idea", ".vscode"}
SKIP_EXT  = {".pyc", ".pyo"}

def build_zip():
    n = 0
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for base, dirs, files in os.walk(PLUG):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fn in files:
                if fn == ".DS_Store" or os.path.splitext(fn)[1] in SKIP_EXT:
                    continue
                full = os.path.join(base, fn)
                arc  = os.path.join("iaai-importer", os.path.relpath(full, PLUG))
                z.write(full, arc); n += 1
    return n

def check_blueprint():
    bp = os.path.join(DEMO, "blueprint.json")
    with open(bp, encoding="utf-8") as f:
        data = json.load(f)
    steps = [s.get("step") for s in data.get("steps", [])]
    assert "installPlugin" in steps, "brak installPlugin"
    assert steps.count("writeFile") >= 2, "brak writeFile (seed + tresci)"
    assert data.get("landingPage") == "/", "zla landingPage"
    # plik tresci stron musi istniec
    assert os.path.isfile(os.path.join(DEMO, "kredyt-kompas-content.php")), "brak kredyt-kompas-content.php"
    return steps

if __name__ == "__main__":
    n = build_zip()
    steps = check_blueprint()
    size = round(os.path.getsize(ZIP) / 1024, 1)
    print(f"OK  iaai-importer.zip: {n} plikow, {size} KB")
    print(f"OK  blueprint.json: kroki = {steps}")
    print("OK  demo gotowe do wypchniecia do publicznego repo.")
