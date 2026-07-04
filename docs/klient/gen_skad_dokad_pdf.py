#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generuje 2 osobne dodatki do instrukcji (A4 poziomo):
  • skad-pochodza-dane.pdf  — DOWÓD (2 str.): zrzuty źródło→cel + mapowanie „to samo
                              auto, pole po polu" (karta IAAI → karta na Twojej stronie)
  • jak-to-dziala.pdf       — DIAGRAM (2 str.): przepływ w strefach serwerów + cykl 24/7;
                              rozgałęzienie nowe/zmienione/sprzedane + dane + niezawodność

Zależności: rsvg-convert, gs. Obrazy z docs/klient/img/.
Uruchom:  python3 docs/klient/gen_skad_dokad_pdf.py
"""
import os, base64, subprocess, tempfile, html

HERE = os.path.dirname(os.path.abspath(__file__))
IMG  = os.path.join(HERE, "img")
OUT_PROOF = os.path.join(HERE, "pdf", "skad-pochodza-dane.pdf")
OUT_DIAG  = os.path.join(HERE, "pdf", "jak-to-dziala.pdf")

W, H = 842.0, 595.0
NAVY, INK, MUT = "#0d2340", "#1c2b3a", "#5b6b7b"
EM, EMD, LINE  = "#10B981", "#0C8D62", "#d7dee6"
CLOUD, CARD, MINT = "#eef2f6", "#ffffff", "#eaf6f1"
BLUE, AMBER      = "#eef4fb", "#fbf3e6"

def esc(s): return html.escape(str(s), quote=True)

def T(x, y, s, size=11, color=INK, weight="normal", anchor="start", mono=False):
    fam = "DejaVu Sans Mono" if mono else "DejaVu Sans"
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}">{esc(s)}</text>')

def rect(x, y, w, h, r=10, fill=CARD, stroke=LINE, sw=1):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

def img(path, x, y, w, h, par="xMidYMid meet"):
    b = base64.b64encode(open(path, "rb").read()).decode()
    return (f'<image x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'preserveAspectRatio="{par}" xlink:href="data:image/jpeg;base64,{b}"/>')

def arrow(x1, y, x2, color=EM, sw=3):
    return (f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2-8:.1f}" y2="{y:.1f}" stroke="{color}" '
            f'stroke-width="{sw}"/>'
            f'<polygon points="{x2:.1f},{y:.1f} {x2-11:.1f},{y-6:.1f} {x2-11:.1f},{y+6:.1f}" fill="{color}"/>')

def line(x1, y1, x2, y2, color=LINE, sw=1.2, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{sw}"{d}/>'

def num_badge(cx, cy, n, r=13, fill=EM):
    return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}"/>'
            + T(cx, cy+4.5, n, size=14, color="#fff", weight="bold", anchor="middle"))

def page_open():
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{W}pt" height="{H}pt" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="#fff"/>')

def header(title, sub):
    s  = f'<rect x="0" y="0" width="{W}" height="70" fill="{NAVY}"/>'
    s += f'<rect x="0" y="70" width="{W}" height="3" fill="{EM}"/>'
    s += T(40, 40, title, size=20, color="#fff", weight="bold")
    s += T(40, 60, sub, size=11, color="#b9c6d6")
    return s

def foot(txt):
    return T(W-40, H-14, txt, size=9, color=MUT, anchor="end")

# =================== PROOF — strona 1: zrzuty ==============================
def proof_p1():
    s = page_open()
    s += header("Skąd pochodzą Twoje dane — i gdzie trafiają",
                "Dowód: te same auta z serwisu aukcyjnego IAAI pojawiają się na Twojej stronie.")
    iw, ih = 352.0, 352.0*516/1100
    y0 = 120; lx, rx = 40, W-40-iw
    s += num_badge(lx+13, y0-16, "1"); s += T(lx+34, y0-11, "ŹRÓDŁO — IAAI.com (aukcje w USA)", size=12, color=NAVY, weight="bold")
    s += num_badge(rx+13, y0-16, "2"); s += T(rx+34, y0-11, "TWOJA STRONA — „Nasze auta”", size=12, color=NAVY, weight="bold")
    s += rect(lx-4, y0-4, iw+8, ih+8, r=8, fill=CARD, stroke=LINE) + img(os.path.join(IMG, "iaai-zrodlo.jpg"), lx, y0, iw, ih)
    s += rect(rx-4, y0-4, iw+8, ih+8, r=8, fill=CARD, stroke=EM, sw=1.5) + img(os.path.join(IMG, "nasza-strona.jpg"), rx, y0, iw, ih)
    midy = y0 + ih/2
    s += arrow(lx+iw+10, midy, rx-10)
    s += T((lx+iw+rx)/2, midy-12, "automat", size=10, color=EMD, weight="bold", anchor="middle")
    s += T((lx+iw+rx)/2, midy+20, "pobiera", size=10, color=EMD, weight="bold", anchor="middle")
    by = y0+ih+42
    s += rect(40, by, W-80, 118, r=10, fill=CLOUD, stroke=LINE)
    s += T(58, by+28, "Co to znaczy — po ludzku:", size=13, color=NAVY, weight="bold")
    for i, ln in enumerate([
        "•  Po lewej: oryginalne ogłoszenia na IAAI.com (amerykański serwis aukcyjny aut powypadkowych).",
        "•  Po prawej: te same pojazdy — automatycznie przeniesione na Twoją stronę, w Twoim wyglądzie.",
        "•  Nic nie przepisujesz ręcznie. Program sam pobiera zdjęcia i dane, a strona pokazuje je klientom.",
        "•  Szczegóły, jak jedno ogłoszenie zamienia się w kartę — na następnej stronie."]):
        s += T(58, by+52+i*20, ln, size=11, color=INK)
    s += foot("Kredyt Kompas · IAAI Importer — skąd pochodzą dane (1/2)")
    return s + "</svg>"

# =================== PROOF — strona 2: mapowanie pól =======================
def our_card(x, y, w):
    """Karta w stylu Twojej strony (te same dane co Accord z IAAI)."""
    ih = 140.0; s = ""
    s += rect(x, y, w, 262, r=12, fill=CARD, stroke=EM, sw=1.4)
    s += f'<clipPath id="cc"><rect x="{x+1:.1f}" y="{y+1:.1f}" width="{w-2:.1f}" height="{ih:.1f}" rx="11"/></clipPath>'
    s += f'<g clip-path="url(#cc)">' + img(os.path.join(IMG, "accord-photo.jpg"), x+1, y+1, w-2, ih, par="xMidYMid slice") + '</g>'
    tx = x+14
    s += T(tx, y+ih+26, "2004 Honda Accord 2.4 EX", size=11.5, color=NAVY, weight="bold")
    s += T(tx, y+ih+48, "Buy Now: USD 1 000", size=11, color=EMD, weight="bold")
    s += T(tx, y+ih+68, "351 701 km (218 536 mi)", size=9.6, color=MUT)
    s += T(tx, y+ih+84, "Manual", size=9.6, color=MUT)
    s += rect(tx, y+ih+94, 96, 20, r=10, fill=MINT, stroke=EM, sw=1)
    s += T(tx+48, y+ih+108, "Key Available", size=8.6, color=EMD, weight="bold", anchor="middle")
    return s

def proof_p2():
    s = page_open()
    s += header("To samo auto — pole po polu",
                "Jak jedno ogłoszenie z IAAI zamienia się w kartę na Twojej stronie (przykład: Honda Accord).")
    # lewa: karta IAAI (zrzut), prawa: nasza karta (SVG)
    lcw = 200.0; lch = 200.0*520/430          # ~242
    lx, ly = 60, 130
    rx, ry = W-60-210, 130
    s += num_badge(lx+13, ly-14, "1"); s += T(lx+32, ly-9, "Karta na IAAI.com", size=11, color=NAVY, weight="bold")
    s += num_badge(rx+13, ry-14, "2"); s += T(rx+32, ry-9, "Karta na Twojej stronie", size=11, color=NAVY, weight="bold")
    s += rect(lx-4, ly-4, lcw+8, lch+8, r=8, fill=CARD, stroke=LINE) + img(os.path.join(IMG, "iaai-accord.jpg"), lx, ly, lcw, lch)
    s += our_card(rx, ry, 210)
    # srodkowe pola z liniami do obu kart
    cx = (lx+lcw + rx)/2
    fields = ["Zdjęcie auta", "Nazwa i rocznik", "Cena „Buy Now”", "Przebieg (mile → km)", "Skrzynia biegów", "Kluczyk / stan"]
    pw = 176; ys = [150, 198, 246, 294, 342, 388]
    for f, yy in zip(fields, ys):
        s += line(lx+lcw+4, yy, cx-pw/2, yy, color=EM, sw=1)
        s += line(cx+pw/2, yy, rx-4, yy, color=EM, sw=1)
        s += rect(cx-pw/2, yy-13, pw, 26, r=13, fill="#fff", stroke=EM, sw=1.2)
        s += T(cx, yy+4, f, size=9.6, color=NAVY, weight="bold", anchor="middle")
    s += rect(40, 445, W-80, 92, r=10, fill=CLOUD, stroke=LINE)
    s += T(58, 470, "Każde pole trafia automatycznie:", size=12.5, color=NAVY, weight="bold")
    for i, ln in enumerate([
        "•  Zdjęcia, cena, przebieg, skrzynia, kluczyk i uszkodzenia — nic nie wpisujesz ręcznie.",
        "•  Dodatkowo przeliczamy przebieg z mil na kilometry, żeby był czytelny dla polskiego klienta."]):
        s += T(58, 494+i*20, ln, size=11, color=INK)
    s += foot("Kredyt Kompas · IAAI Importer — skąd pochodzą dane (2/2)")
    return s + "</svg>"

# =================== DIAGRAM — strona 1: przepływ + strefy + cykl ==========
def flow_tile(x, y, w, h, n, title, lines, accent=False):
    s  = rect(x, y, w, h, r=12, fill=(MINT if accent else CARD), stroke=(EM if accent else LINE), sw=1.4)
    s += num_badge(x+w/2, y-2, n)
    s += T(x+w/2, y+28, title, size=11, color=NAVY, weight="bold", anchor="middle")
    yy = y+46
    for ln in lines:
        s += T(x+w/2, yy, ln, size=9, color=MUT, anchor="middle"); yy += 13
    return s

def diag_p1():
    s = page_open()
    s += header("Jak to działa — droga auta (krok po kroku)",
                "Gdzie co się dzieje: IAAI → Twój serwer (automat + baza) → Twój WordPress → klient.")
    bx, bw = 30, 132
    gap = (W - 2*bx - 5*bw) / 4
    xs = [bx + i*(bw+gap) for i in range(5)]
    ty, th = 300, 104
    # strefy serwerów (tło)
    def zone(x1, x2, label, fill):
        s2  = rect(x1, 258, x2-x1, 150, r=12, fill=fill, stroke=LINE, sw=1)
        s2 += T((x1+x2)/2, 276, label, size=10, color=NAVY, weight="bold", anchor="middle")
        return s2
    s += zone(xs[0]-8, xs[0]+bw+8, "IAAI.com — USA", MINT)
    s += zone(xs[1]-8, xs[2]+bw+8, "TWÓJ SERWER (VPS) — działa 24/7", BLUE)
    s += zone(xs[3]-8, xs[4]+bw+8, "TWÓJ WORDPRESS", "#eef7f2")
    # kafelki
    boxes = [
        ("1", "IAAI.com", ["Aukcje aut", "w USA (źródło)"], True),
        ("2", "Automat (scraper)", ["Pobiera oferty", "i zdjęcia"], False),
        ("3", "Baza danych", ["Magazyn ofert", "na serwerze"], False),
        ("4", "Wtyczka WordPress", ["Publikuje auta", "na stronie"], False),
        ("5", "„Nasze auta”", ["Klient widzi", "i filtruje"], True),
    ]
    for i, (n, ti, ln, acc) in enumerate(boxes):
        s += flow_tile(xs[i], ty, bw, th, n, ti, ln, accent=acc)
        if i < 4:
            s += arrow(xs[i]+bw+4, ty+th/2, xs[i+1]-4)
    # pętla „co godzinę" nad krokami 1–3
    lyc = 232
    x_from, x_to = xs[2]+bw/2, xs[0]+bw/2
    s += line(x_to, lyc, x_from, lyc, color=EMD, sw=2)
    s += line(x_to, lyc, x_to, ty-2, color=EMD, sw=2)
    s += f'<polygon points="{x_to:.1f},{ty-2:.1f} {x_to-5:.1f},{ty-12:.1f} {x_to+5:.1f},{ty-12:.1f}" fill="{EMD}"/>'
    s += line(x_from, lyc, x_from, 258, color=EMD, sw=2, dash="3,3")
    s += T((x_to+x_from)/2, lyc-8, "↺  cykl automatyczny — co ~60 min, całą dobę", size=10.5, color=EMD, weight="bold", anchor="middle")
    # dolny podpis
    s += rect(30, 430, W-60, 92, r=10, fill=CLOUD, stroke=LINE)
    s += T(48, 456, "Najprościej:", size=12.5, color=NAVY, weight="bold")
    for i, ln in enumerate([
        "•  Auto wędruje z lewej na prawą: z aukcji IAAI, przez Twój serwer, aż na stronę — samo.",
        "•  Automat i baza żyją na Twoim serwerze (VPS); wtyczka i strona to Twój WordPress.",
        "•  Cały cykl powtarza się w kółko co ~60 minut, całą dobę — Ty nie robisz nic."]):
        s += T(48, 478+i*18, ln, size=10.5, color=INK)
    s += foot("Kredyt Kompas · IAAI Importer — jak to działa (1/2)")
    return s + "</svg>"

# =================== DIAGRAM — strona 2: decyzje + dane + niezawodność =====
def data_tile(x, y, w, h, title, sub):
    s  = rect(x, y, w, h, r=9, fill=CARD, stroke=LINE, sw=1.2)
    s += f'<rect x="{x:.1f}" y="{y:.1f}" width="4" height="{h:.1f}" rx="2" fill="{EM}"/>'
    s += T(x+13, y+25, title, size=10.3, color=NAVY, weight="bold")
    s += T(x+13, y+42, sub, size=8.6, color=MUT)
    return s

def branch_tile(x, y, w, h, tag, tagcol, desc):
    s  = rect(x, y, w, h, r=11, fill=CARD, stroke=LINE, sw=1.3)
    s += f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="6" rx="3" fill="{tagcol}"/>'
    s += T(x+w/2, y+34, tag, size=12, color=NAVY, weight="bold", anchor="middle")
    s += T(x+w/2, y+58, "→ " + desc, size=10, color=MUT, anchor="middle")
    return s

def diag_p2():
    s = page_open()
    s += header("Jak to działa — co program robi z ofertami",
                "Decyzje przy każdym sprawdzeniu, jakie dane przenosi i dlaczego jest to bezpieczne.")
    # ① rozgałęzienie
    s += T(30, 100, "①  Przy każdym sprawdzeniu porównuje aukcje z Twoją bazą:", size=12.5, color=NAVY, weight="bold")
    bw = (W-60-2*16)/3; by = 112; bh = 92
    br = [
        ("NOWE ogłoszenie", EM,    "dodaje auto na stronę"),
        ("ZMIENIONE (cena/status)", "#3b82f6", "aktualizuje kartę"),
        ("SPRZEDANE / zniknęło", "#e0a92e", "ukrywa (nie kasuje historii)"),
    ]
    for i, (tg, c, d) in enumerate(br):
        s += branch_tile(30+i*(bw+16), by, bw, bh, tg, c, d)
    # ② dane
    s += T(30, 240, "②  Co przenosi z każdego auta:", size=12.5, color=NAVY, weight="bold")
    dy, dh = 250, 58; dbw = (W-60-5*13)/6
    data = [("Zdjęcia","cała galeria"),("Cena","Buy Now / oferta"),("Przebieg","mile + km"),
            ("Rok · Marka","model, typ"),("Uszkodzenia","gł. i dodatkowe"),("VIN · Kluczyk","skrzynia, napęd")]
    for i, (t, u) in enumerate(data):
        s += data_tile(30+i*(dbw+13), dy, dbw, dh, t, u)
    # ③ niezawodność
    s += T(30, 342, "③  Niezawodność i bezpieczeństwo:", size=12.5, color=NAVY, weight="bold")
    ry, rh = 352, 74; rbw = (W-60-3*14)/4
    rel = [("Nie dubluje pracy","blokada podwójnego\nuruchomienia"),
           ("Tylko z IAAI","zdjęcia z zaufanego\nźródła"),
           ("Log na serwerze","każdy krok\nzapisany"),
           ("Sprzedane znikają","oferta zawsze\naktualna")]
    for i, (t, u) in enumerate(rel):
        x = 30+i*(rbw+14)
        s += rect(x, ry, rbw, rh, r=10, fill=MINT, stroke=EM, sw=1.1)
        s += T(x+rbw/2, ry+26, t, size=10.6, color=NAVY, weight="bold", anchor="middle")
        for j, part in enumerate(u.split("\n")):
            s += T(x+rbw/2, ry+44+j*13, part, size=8.5, color=EMD, anchor="middle")
    s += T(40, H-30, "W tej wersji demonstracyjnej dane i zdjęcia aut są przykładowe — pokazują sam sposób działania.",
           size=10, color=MUT)
    s += foot("Kredyt Kompas · IAAI Importer — jak to działa (2/2)")
    return s + "</svg>"

# =================== budowa =================================================
def _svgs_to_pdf(svgs, out):
    with tempfile.TemporaryDirectory() as td:
        pdfs = []
        for i, svg in enumerate(svgs):
            sp = os.path.join(td, f"p{i}.svg"); pp = os.path.join(td, f"p{i}.pdf")
            open(sp, "w", encoding="utf-8").write(svg)
            subprocess.run(["rsvg-convert", "-f", "pdf", "-o", pp, sp], check=True)
            pdfs.append(pp)
        subprocess.run(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite",
                        "-dAutoRotatePages=/None", f"-sOutputFile={out}", *pdfs], check=True)

def build():
    os.makedirs(os.path.dirname(OUT_PROOF), exist_ok=True)
    old = os.path.join(HERE, "pdf", "07-skad-pochodza-dane.pdf")
    if os.path.exists(old):
        os.remove(old)
    _svgs_to_pdf([proof_p1(), proof_p2()], OUT_PROOF)
    _svgs_to_pdf([diag_p1(), diag_p2()], OUT_DIAG)
    for p in (OUT_PROOF, OUT_DIAG):
        print("OK ->", os.path.basename(p), f"({os.path.getsize(p)//1024} KB)")

if __name__ == "__main__":
    build()
