#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generuje 2 osobne dodatki do instrukcji (A4 poziomo, po 1 stronie):
  • skad-pochodza-dane.pdf  — DOWÓD: zrzuty IAAI.com (źródło) → Twoja strona (cel)
  • jak-to-dziala.pdf       — szczegółowy, przystępny DIAGRAM przepływu (kafelki)

Zależności: rsvg-convert, gs. Obrazy z docs/klient/img/.
Uruchom:  python3 docs/klient/gen_skad_dokad_pdf.py
"""
import os, base64, subprocess, tempfile, html

HERE = os.path.dirname(os.path.abspath(__file__))
IMG  = os.path.join(HERE, "img")
OUT_PROOF = os.path.join(HERE, "pdf", "skad-pochodza-dane.pdf")   # SS1 — dowód
OUT_DIAG  = os.path.join(HERE, "pdf", "jak-to-dziala.pdf")        # SS2 — diagram

# A4 poziomo (punkty)
W, H = 842.0, 595.0
NAVY, INK, MUT = "#0d2340", "#1c2b3a", "#5b6b7b"
EM, EMD, LINE  = "#10B981", "#0C8D62", "#d7dee6"
CLOUD, CARD, MINT = "#eef2f6", "#ffffff", "#eaf6f1"

def esc(s): return html.escape(str(s), quote=True)

def T(x, y, s, size=11, color=INK, weight="normal", anchor="start", mono=False):
    fam = "DejaVu Sans Mono" if mono else "DejaVu Sans"
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{esc(s)}</text>')

def rect(x, y, w, h, r=10, fill=CARD, stroke=LINE, sw=1):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

def img(path, x, y, w, h):
    b = base64.b64encode(open(path, "rb").read()).decode()
    return (f'<image x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'preserveAspectRatio="xMidYMid meet" xlink:href="data:image/jpeg;base64,{b}"/>')

def arrow(x1, y, x2, color=EM, sw=3):
    return (f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2-8:.1f}" y2="{y:.1f}" stroke="{color}" '
            f'stroke-width="{sw}"/>'
            f'<polygon points="{x2:.1f},{y:.1f} {x2-11:.1f},{y-6:.1f} {x2-11:.1f},{y+6:.1f}" fill="{color}"/>')

def num_badge(cx, cy, n, r=13):
    return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{EM}"/>'
            + T(cx, cy+4.5, n, size=14, color="#fff", weight="bold", anchor="middle"))

def page_open():
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{W}pt" height="{H}pt" viewBox="0 0 {W} {H}">'
            f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

def header(title, sub):
    s  = f'<rect x="0" y="0" width="{W}" height="70" fill="{NAVY}"/>'
    s += f'<rect x="0" y="70" width="{W}" height="3" fill="{EM}"/>'
    s += T(40, 40, title, size=20, color="#ffffff", weight="bold")
    s += T(40, 60, sub, size=11, color="#b9c6d6")
    return s

# ---------------- DOWÓD: 2 zrzuty źródło→cel -------------------------------
def page_proof():
    s = page_open()
    s += header("Skąd pochodzą Twoje dane — i gdzie trafiają",
                "Dowód: te same auta z serwisu aukcyjnego IAAI pojawiają się na Twojej stronie.")
    iw, ih = 352.0, 352.0*516/1100
    y0 = 120
    lx, rx = 40, W-40-iw
    s += num_badge(lx+13, y0-16, "1")
    s += T(lx+34, y0-11, "ŹRÓDŁO — IAAI.com (aukcje w USA)", size=12, color=NAVY, weight="bold")
    s += num_badge(rx+13, y0-16, "2")
    s += T(rx+34, y0-11, "TWOJA STRONA — „Nasze auta”", size=12, color=NAVY, weight="bold")
    s += rect(lx-4, y0-4, iw+8, ih+8, r=8, fill=CARD, stroke=LINE)
    s += img(os.path.join(IMG, "iaai-zrodlo.jpg"), lx, y0, iw, ih)
    s += rect(rx-4, y0-4, iw+8, ih+8, r=8, fill=CARD, stroke=EM, sw=1.5)
    s += img(os.path.join(IMG, "nasza-strona.jpg"), rx, y0, iw, ih)
    midy = y0 + ih/2
    ax1, ax2 = lx+iw+10, rx-10
    s += arrow(ax1, midy, ax2)
    s += T((ax1+ax2)/2, midy-12, "automat", size=10, color=EMD, weight="bold", anchor="middle")
    s += T((ax1+ax2)/2, midy+20, "pobiera", size=10, color=EMD, weight="bold", anchor="middle")
    by = y0+ih+42
    s += rect(40, by, W-80, 118, r=10, fill=CLOUD, stroke=LINE)
    s += T(58, by+28, "Co to znaczy — po ludzku:", size=13, color=NAVY, weight="bold")
    lines = [
        "•  Po lewej: oryginalne ogłoszenia na IAAI.com (amerykański serwis aukcyjny aut powypadkowych).",
        "•  Po prawej: te same pojazdy — automatycznie przeniesione na Twoją stronę, w Twoim wyglądzie.",
        "•  Nic nie przepisujesz ręcznie. Program sam pobiera zdjęcia i dane, a strona pokazuje je klientom.",
        "•  Gdy na IAAI pojawia się nowe auto — trafia na stronę; gdy znika z aukcji — znika też u Ciebie.",
    ]
    yy = by+52
    for ln in lines:
        s += T(58, yy, ln, size=11, color=INK); yy += 20
    s += T(W-40, H-18, "Kredyt Kompas · IAAI Importer — skąd pochodzą dane", size=9, color=MUT, anchor="end")
    s += "</svg>"
    return s

# ---------------- DIAGRAM przepływu (kafelki, szczegółowo) -----------------
def flow_tile(x, y, w, h, n, title, lines, accent=False):
    s  = rect(x, y, w, h, r=12, fill=(MINT if accent else CARD), stroke=(EM if accent else LINE), sw=1.4)
    s += num_badge(x+w/2, y-2, n)
    s += T(x+w/2, y+30, title, size=11.5, color=NAVY, weight="bold", anchor="middle")
    yy = y+49
    for ln in lines:
        s += T(x+w/2, yy, ln, size=9.2, color=MUT, anchor="middle"); yy += 13.5
    return s

def data_tile(x, y, w, h, title, sub):
    s  = rect(x, y, w, h, r=9, fill=CARD, stroke=LINE, sw=1.2)
    s += f'<rect x="{x:.1f}" y="{y:.1f}" width="4" height="{h:.1f}" rx="2" fill="{EM}"/>'
    s += T(x+13, y+26, title, size=10.5, color=NAVY, weight="bold")
    s += T(x+13, y+44, sub, size=8.8, color=MUT)
    return s

def page_diag():
    s = page_open()
    s += header("Jak to działa — krok po kroku",
                "Droga jednego auta: z aukcji IAAI aż na Twoją stronę. Wszystko dzieje się samo, całą dobę.")
    # małe miniatury źródło/cel u góry (zakotwiczenie w rzeczywistości)
    tw, th = 118.0, 118.0*516/1100
    s += rect(40-3, 84-3, tw+6, th+6, r=6, fill=CARD, stroke=LINE)
    s += img(os.path.join(IMG, "iaai-zrodlo.jpg"), 40, 84, tw, th)
    s += T(40, 84+th+13, "IAAI.com — źródło", size=8.5, color=MUT)
    s += rect(W-40-tw-3, 84-3, tw+6, th+6, r=6, fill=CARD, stroke=EM, sw=1.3)
    s += img(os.path.join(IMG, "nasza-strona.jpg"), W-40-tw, 84, tw, th)
    s += T(W-40-tw, 84+th+13, "Twoja strona — cel", size=8.5, color=MUT)

    # RZĄD 1 — przepływ (5 kafelków)
    s += T(30, 182, "① Droga jednego auta — od aukcji do Twojej strony:", size=12, color=NAVY, weight="bold")
    bx, by, bw, bh = 30, 194, 132, 104
    gap = (W - 2*bx - 5*bw) / 4
    boxes = [
        ("1", "IAAI.com", ["Aukcje aut", "powypadkowych", "w USA (źródło)"], True),
        ("2", "Automat (scraper)", ["Sam pobiera oferty", "i zdjęcia —", "co godzinę, 24/7"], False),
        ("3", "Baza danych", ["Magazyn ofert", "na Twoim", "serwerze VPS"], False),
        ("4", "Wtyczka WordPress", ["Publikuje auta", "w Twoim", "wyglądzie strony"], False),
        ("5", "„Nasze auta”", ["Klient widzi,", "filtruje i", "przegląda ofertę"], True),
    ]
    for i, (n, ti, ln, acc) in enumerate(boxes):
        x = bx + i*(bw+gap)
        s += flow_tile(x, by, bw, bh, n, ti, ln, accent=acc)
        if i < len(boxes)-1:
            s += arrow(x+bw+4, by+bh/2, x+bw+gap-4)

    # RZĄD 2 — co przenosi automat (kafelki danych)
    s += T(30, 335, "② Co dokładnie przenosi automat — z każdego auta:", size=12, color=NAVY, weight="bold")
    dy, dh = 345, 62
    dbx = 30
    dbw = (W - 2*dbx - 5*13) / 6
    data = [
        ("Zdjęcia", "cała galeria"),
        ("Cena", "Buy Now / oferta"),
        ("Przebieg", "mile + km"),
        ("Rok · Marka", "model, typ"),
        ("Uszkodzenia", "główne i dodatkowe"),
        ("VIN · Kluczyk", "skrzynia, napęd"),
    ]
    for i, (ti, su) in enumerate(data):
        x = dbx + i*(dbw+13)
        s += data_tile(x, dy, dbw, dh, ti, su)

    # RZĄD 3 — kiedy / jak często
    iy = 430
    s += rect(30, iy, W-60, 92, r=10, fill=CLOUD, stroke=LINE)
    s += T(48, iy+26, "③ Kiedy i jak często — najważniejsze:", size=12.5, color=NAVY, weight="bold")
    outs = [
        "•  Działa całą dobę (24/7) i sam sprawdza nowe oferty — Ty nie robisz nic na co dzień.",
        "•  Nowe auto na IAAI → pojawia się na stronie. Sprzedane lub zdjęte z aukcji → znika też u Ciebie.",
        "•  W tej wersji demonstracyjnej dane i zdjęcia aut są przykładowe — pokazują sam sposób działania.",
    ]
    yy = iy+48
    for ln in outs:
        s += T(48, yy, ln, size=10.5, color=INK); yy += 18
    s += T(W-40, H-14, "Kredyt Kompas · IAAI Importer — jak to działa", size=9, color=MUT, anchor="end")
    s += "</svg>"
    return s

def _svg_to_pdf(svg, out):
    with tempfile.TemporaryDirectory() as td:
        sp = os.path.join(td, "p.svg")
        open(sp, "w", encoding="utf-8").write(svg)
        subprocess.run(["rsvg-convert", "-f", "pdf", "-o", out, sp], check=True)

def build():
    os.makedirs(os.path.dirname(OUT_PROOF), exist_ok=True)
    # usuń stary połączony plik, jeśli został
    old = os.path.join(HERE, "pdf", "07-skad-pochodza-dane.pdf")
    if os.path.exists(old):
        os.remove(old)
    _svg_to_pdf(page_proof(), OUT_PROOF)
    _svg_to_pdf(page_diag(),  OUT_DIAG)
    for p in (OUT_PROOF, OUT_DIAG):
        print("OK ->", os.path.basename(p), f"({os.path.getsize(p)//1024} KB)")

if __name__ == "__main__":
    build()
