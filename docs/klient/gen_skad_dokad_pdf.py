#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generuje dodatek do instrukcji: „Skąd pochodzą Twoje dane" — dowód (2 zrzuty
źródło→cel) + szczegółowy, przystępny diagram przepływu.

Wyjście: docs/klient/pdf/07-skad-pochodza-dane.pdf  (A4 poziomo, 2 strony)
Zależności: rsvg-convert, gs (jak reszta generatorów). Obrazy z docs/klient/img/.

Uruchom:  python3 docs/klient/gen_skad_dokad_pdf.py
"""
import os, base64, subprocess, tempfile, html

HERE = os.path.dirname(os.path.abspath(__file__))
IMG  = os.path.join(HERE, "img")
OUT  = os.path.join(HERE, "pdf", "07-skad-pochodza-dane.pdf")

# A4 poziomo (punkty)
W, H = 842.0, 595.0
NAVY, INK, MUT = "#0d2340", "#1c2b3a", "#5b6b7b"
EM, EMD, LINE  = "#10B981", "#0C8D62", "#d7dee6"
CLOUD, CARD    = "#eef2f6", "#ffffff"

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
    """Pozioma strzałka w prawo."""
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

# ---------------- STRONA 1: dowód (2 zrzuty) -------------------------------
def page1():
    s = page_open()
    s += header("Skąd pochodzą Twoje dane — i gdzie trafiają",
                "Dowód: te same auta z serwisu aukcyjnego IAAI pojawiają się na Twojej stronie.")
    iw, ih = 352.0, 352.0*516/1100      # ~165
    y0 = 120
    lx, rx = 40, W-40-iw
    # etykiety
    s += num_badge(lx+13, y0-16, "1")
    s += T(lx+34, y0-11, "ŹRÓDŁO — IAAI.com (aukcje w USA)", size=12, color=NAVY, weight="bold")
    s += num_badge(rx+13, y0-16, "2")
    s += T(rx+34, y0-11, "TWOJA STRONA — „Nasze auta”", size=12, color=NAVY, weight="bold")
    # ramki + obrazy
    s += rect(lx-4, y0-4, iw+8, ih+8, r=8, fill=CARD, stroke=LINE)
    s += img(os.path.join(IMG, "iaai-zrodlo.jpg"), lx, y0, iw, ih)
    s += rect(rx-4, y0-4, iw+8, ih+8, r=8, fill=CARD, stroke=EM, sw=1.5)
    s += img(os.path.join(IMG, "nasza-strona.jpg"), rx, y0, iw, ih)
    # strzalka miedzy
    midy = y0 + ih/2
    ax1, ax2 = lx+iw+10, rx-10
    s += arrow(ax1, midy, ax2)
    s += T((ax1+ax2)/2, midy-12, "automat", size=10, color=EMD, weight="bold", anchor="middle")
    s += T((ax1+ax2)/2, midy+20, "pobiera", size=10, color=EMD, weight="bold", anchor="middle")
    # opis pod spodem
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
    s += T(W-40, H-18, "Kredyt Kompas · IAAI Importer — jak to działa (1/2)", size=9, color=MUT, anchor="end")
    s += "</svg>"
    return s

# ---------------- STRONA 2: diagram przepływu ------------------------------
def box(x, y, w, h, n, title, lines, fill=CARD, stroke=LINE, tcol=NAVY):
    s  = rect(x, y, w, h, r=12, fill=fill, stroke=stroke, sw=1.4)
    s += num_badge(x+w/2, y-2, n)
    s += T(x+w/2, y+30, title, size=11.5, color=tcol, weight="bold", anchor="middle")
    yy = y+50
    for ln in lines:
        s += T(x+w/2, yy, ln, size=9.3, color=MUT, anchor="middle"); yy += 14
    return s

def page2():
    s = page_open()
    s += header("Jak to działa — krok po kroku",
                "Droga jednego auta: z aukcji IAAI aż na Twoją stronę. Wszystko dzieje się samo, całą dobę.")
    # miniatury na koncach (źródło / cel)
    tw, th = 150.0, 150.0*516/1100
    s += rect(40-3, 96-3, tw+6, th+6, r=6, fill=CARD, stroke=LINE)
    s += img(os.path.join(IMG, "iaai-zrodlo.jpg"), 40, 96, tw, th)
    s += T(40, 96+th+16, "IAAI.com (źródło)", size=9, color=MUT)
    s += rect(W-40-tw-3, 96-3, tw+6, th+6, r=6, fill=CARD, stroke=EM, sw=1.3)
    s += img(os.path.join(IMG, "nasza-strona.jpg"), W-40-tw, 96, tw, th)
    s += T(W-40-tw, 96+th+16, "Twoja strona (cel)", size=9, color=MUT)

    # 5 pudełek przepływu
    bx, by, bw, bh = 30, 250, 132, 118
    gap = (W - 2*bx - 5*bw) / 4          # odstęp = strzałka
    boxes = [
        ("1", "IAAI.com", ["Aukcje aut", "powypadkowych", "w USA (źródło)"], "#eaf6f1", EM, NAVY),
        ("2", "Automat (scraper)", ["Sam pobiera", "oferty i zdjęcia", "co godzinę, 24/7"], CARD, LINE, NAVY),
        ("3", "Baza danych", ["Magazyn ofert", "na Twoim", "serwerze"], CARD, LINE, NAVY),
        ("4", "Wtyczka WordPress", ["Publikuje auta", "w Twoim", "wyglądzie strony"], CARD, LINE, NAVY),
        ("5", "„Nasze auta”", ["Klient widzi", "i przegląda", "ofertę"], "#eaf6f1", EM, NAVY),
    ]
    xs = []
    for i, (n, ti, ln, fl, st, tc) in enumerate(boxes):
        x = bx + i*(bw+gap)
        xs.append(x)
        s += box(x, by, bw, bh, n, ti, ln, fill=fl, stroke=st, tcol=tc)
        if i < len(boxes)-1:
            s += arrow(x+bw+4, by+bh/2, x+bw+gap-4)
    # podpis pod przepływem
    dy = by+bh+44
    s += rect(30, dy, W-60, 96, r=10, fill=CLOUD, stroke=LINE)
    s += T(48, dy+27, "Najważniejsze:", size=13, color=NAVY, weight="bold")
    outs = [
        "•  Ty nie robisz nic na co dzień — po jednorazowym uruchomieniu cały łańcuch działa automatycznie.",
        "•  Dane są zawsze aktualne: nowe auta dochodzą, sprzedane/zniknięte są zdejmowane ze strony.",
        "•  W tej wersji demonstracyjnej dane i zdjęcia aut są przykładowe — pokazują sam sposób działania.",
    ]
    yy = dy+50
    for ln in outs:
        s += T(48, yy, ln, size=11, color=INK); yy += 20
    s += T(W-40, H-18, "Kredyt Kompas · IAAI Importer — jak to działa (2/2)", size=9, color=MUT, anchor="end")
    s += "</svg>"
    return s

def build():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        pdfs = []
        for i, svg in enumerate([page1(), page2()]):
            sp = os.path.join(td, f"p{i}.svg"); pp = os.path.join(td, f"p{i}.pdf")
            open(sp, "w", encoding="utf-8").write(svg)
            subprocess.run(["rsvg-convert", "-f", "pdf", "-o", pp, sp], check=True)
            pdfs.append(pp)
        subprocess.run(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite",
                        "-dAutoRotatePages=/None", f"-sOutputFile={OUT}", *pdfs], check=True)
    print("OK ->", OUT, f"({os.path.getsize(OUT)//1024} KB)")

if __name__ == "__main__":
    build()
