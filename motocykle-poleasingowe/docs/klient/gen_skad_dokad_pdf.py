#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLUGIN 2 — dwa dodatki do instrukcji klienta (A4 poziomo), w stylu plugin-1:
  • skad-pochodza-dane.pdf  — skąd biorą się motocykle: źródło → nasza baza → Twoja strona,
                              mapowanie „to samo ogłoszenie, pole po polu"
  • jak-to-dziala.pdf       — automatyczny obieg co kilka godzin; co się dzieje z nowym /
                              zmienionym / zakończonym ogłoszeniem; niezawodność

Samodzielne (bez zrzutów ekranu). Zależności: rsvg-convert, gs.
Uruchom:  python3 docs/klient/gen_skad_dokad_pdf.py
"""
import os, subprocess, tempfile, shutil, html

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "pdf")
OUT_PROOF = os.path.join(OUTDIR, "skad-pochodza-dane.pdf")
OUT_DIAG  = os.path.join(OUTDIR, "jak-to-dziala.pdf")

W, H = 842.0, 595.0
NAVY, INK, MUT = "#0d2340", "#1c2b3a", "#5b6b7b"
EM, EMD, LINE  = "#10B981", "#0C8D62", "#d7dee6"
CARD, MINT     = "#ffffff", "#eaf6f1"
BLUE, AMBER    = "#eef4fb", "#fbf3e6"
GREY, GREYB    = "#eef2f6", "#9aa7b4"

def esc(s): return html.escape(str(s), quote=True)

def T(x, y, s, size=11, color=INK, weight="normal", anchor="start", mono=False, italic=False):
    fam = "DejaVu Sans Mono" if mono else "DejaVu Sans"
    st = ' font-style="italic"' if italic else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}"{st}>{esc(s)}</text>')

def rect(x, y, w, h, r=10, fill=CARD, stroke=LINE, sw=1, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

def arrow(x1, y, x2, color=EM, sw=3):
    return (f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2-9:.1f}" y2="{y:.1f}" stroke="{color}" '
            f'stroke-width="{sw}"/>'
            f'<polygon points="{x2:.1f},{y:.1f} {x2-12:.1f},{y-7:.1f} {x2-12:.1f},{y+7:.1f}" fill="{color}"/>')

def varrow(x, y1, y2, color=EM, sw=3):
    return (f'<line x1="{x:.1f}" y1="{y1:.1f}" x2="{x:.1f}" y2="{y2-9:.1f}" stroke="{color}" '
            f'stroke-width="{sw}"/>'
            f'<polygon points="{x:.1f},{y2:.1f} {x-7:.1f},{y2-12:.1f} {x+7:.1f},{y2-12:.1f}" fill="{color}"/>')

def line(x1, y1, x2, y2, color=LINE, sw=1.2, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{sw}"{d}/>'

def num_badge(cx, cy, n, r=13, fill=EM):
    return (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}"/>'
            + T(cx, cy+4.5, str(n), size=13, color="#fff", weight="bold", anchor="middle"))

def page_open():
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{W}pt" height="{H}pt" viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="#fff"/>')

def header(title, sub):
    s  = f'<rect x="0" y="0" width="{W}" height="70" fill="{NAVY}"/>'
    s += f'<rect x="0" y="70" width="{W}" height="3" fill="{EM}"/>'
    s += T(40, 40, title, size=21, color="#fff", weight="bold")
    s += T(40, 60, sub, size=11.5, color="#b9c6d6")
    s += T(W-40, 44, "poleasingowe.pl → WordPress", size=11, color="#8fa3ba", anchor="end")
    return s

def foot(txt):
    return (line(40, H-26, W-40, H-26, LINE, 1)
            + T(40, H-12, txt, size=9, color=MUT)
            + T(W-40, H-12, "Importer motocykli · dokument dla klienta", size=9, color=MUT, anchor="end"))

def render(svgs, out_pdf):
    """svgs: lista stringów SVG (po jednej stronie) → jeden PDF (gs scala)."""
    os.makedirs(OUTDIR, exist_ok=True)
    tmp = []
    for i, s in enumerate(svgs):
        fsvg = tempfile.NamedTemporaryFile(suffix=f"_{i}.svg", delete=False, dir=OUTDIR)
        fsvg.write(s.encode("utf-8")); fsvg.close()
        fpdf = fsvg.name[:-4] + ".pdf"
        subprocess.run(["rsvg-convert", "-f", "pdf", "-o", fpdf, fsvg.name], check=True)
        tmp.append((fsvg.name, fpdf))
    pdfs = [p for _, p in tmp]
    if len(pdfs) == 1:
        shutil.move(pdfs[0], out_pdf)
    else:
        subprocess.run(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite",
                        f"-sOutputFile={out_pdf}", *pdfs], check=True)
    for s, _ in tmp:
        for f in (s, s[:-4] + ".pdf"):
            if os.path.exists(f):
                os.remove(f)
    print("PDF:", out_pdf)


# ============================================================ DOK 1: SKĄD DANE
def zone(x, y, w, h, tag, title, lines, tagfill, tagink, cardfill=CARD):
    s = rect(x, y, w, h, r=12, fill=cardfill, stroke=LINE, sw=1.4)
    s += rect(x+16, y+14, 96, 20, r=10, fill=tagfill, stroke="none")
    s += T(x+64, y+28, tag, size=10, color=tagink, weight="bold", anchor="middle")
    s += T(x+16, y+58, title, size=13.5, color=INK, weight="bold")
    yy = y+80
    for ic, ln in lines:
        s += T(x+18, yy, ic, size=12, color=EMD, weight="bold")
        s += T(x+38, yy, ln, size=10.3, color=MUT)
        yy += 20
    return s

def proof_page():
    s = page_open()
    s += header("Skąd pochodzą dane", "Motocykle z poleasingowe.pl trafiają na Twoją stronę same — nic nie wpisujesz ręcznie")

    # trzy strefy
    zw, zh, zy = 236, 156, 96
    x1, x3 = 40, W-40-zw
    x2 = (x1 + x3) / 2 - zw/2 + zw/2  # środek
    x2 = W/2 - zw/2
    s += zone(x1, zy, zw, zh, "ŹRÓDŁO", "poleasingowe.pl",
              [("•", "publiczne aukcje motocykli"),
               ("•", "kategoria: ecr_motorcycles"),
               ("•", "strona ogłoszenia + zdjęcia"),
               ("•", "ich serwer — my tylko czytamy")],
              GREY, "#556", cardfill="#fbfcfd")
    s += zone(x2, zy, zw, zh, "NASZA BAZA", "Osobna baza (kopia)",
              [("•", "polea_motocykle + polea_zdjecia"),
               ("•", "odświeżana automatycznie"),
               ("•", "oddzielna od bazy WordPressa"),
               ("•", "źródło prawdy dla wtyczki")],
              MINT, EMD, cardfill="#f4fbf8")
    s += zone(x3, zy, zw, zh, "TWOJA STRONA", "Podstrona „Nasze motory”",
              [("•", "lista motocykli + filtry"),
               ("•", "karta z pełnymi danymi"),
               ("•", "wygląd = motyw Twojej strony"),
               ("•", "aktualizuje się sama")],
              BLUE, "#1e5fb0", cardfill="#f5f9fe")
    ay = zy + zh/2
    s += arrow(x1+zw+6, ay, x2-6)
    s += arrow(x2+zw+6, ay, x3-6)
    s += T((x1+zw+x2)/2, ay-12, "pobieramy", size=9.5, color=EMD, anchor="middle", italic=True)
    s += T((x2+zw+x3)/2, ay-12, "pokazujemy", size=9.5, color="#1e5fb0", anchor="middle", italic=True)

    # mapowanie pól
    my = zy + zh + 20
    s += T(40, my, "To samo ogłoszenie — pole po polu", size=13, color=NAVY, weight="bold")
    s += T(40, my+16, "Co jest na stronie aukcji  →  co widzi klient na Twojej podstronie", size=10, color=MUT)
    ty = my + 30
    tw = W - 80
    rowh = 20
    rows = [
        ("Marka i model", "tytuł karty (np. „Benelli TRK 502”)"),
        ("Rok produkcji · data 1. rejestracji", "rok na liście i w szczegółach"),
        ("Przebieg", "km (sformatowane, np. 12 300 km)"),
        ("Pojemność · moc · paliwo · skrzynia · napęd", "specyfikacja techniczna"),
        ("VIN · numer rejestracyjny · kolor · kluczyki", "szczegóły pojazdu"),
        ("Cena (PLN, netto) · najniższa z 30 dni", "cena z dopiskiem „netto”"),
        ("Lokalizacja · forma sprzedaży · termin", "gdzie stoi i do kiedy trwa"),
        ("Zdjęcia z galerii aukcji", "galeria na karcie (hotlink — patrz niżej)"),
        ("Link do aukcji", "przycisk „Zobacz aukcję na poleasingowe.pl”"),
    ]
    s += rect(40, ty, tw, 20, r=6, fill=NAVY, stroke="none")
    s += T(52, ty+14, "POLE ŹRÓDŁA", size=9.5, color="#cfe6dd", weight="bold")
    s += T(40 + tw*0.52 + 12, ty+14, "U KLIENTA NA STRONIE", size=9.5, color="#cfe6dd", weight="bold")
    yy = ty + 20
    for i, (a, b) in enumerate(rows):
        bg = "#f6f9fb" if i % 2 == 0 else "#ffffff"
        s += rect(40, yy, tw, rowh, r=0, fill=bg, stroke="none")
        s += T(52, yy+14.5, a, size=9.6, color=INK)
        s += line(40 + tw*0.52, yy+2, 40 + tw*0.52, yy+rowh-2, LINE, 1)
        s += T(40 + tw*0.52 + 12, yy+14.5, "→ " + b, size=9.6, color=EMD)
        yy += rowh
    s += rect(40, ty, tw, 20 + rowh*len(rows), r=6, fill="none", stroke=LINE, sw=1.2)

    # nota prawna / hotlink
    ny = yy + 12
    s += rect(40, ny, tw, 38, r=10, fill=AMBER, stroke="#e0a92e", sw=1.2)
    s += T(56, ny+16, "Zdjęcia nie są kopiowane na Twój serwer — pokazujemy je bezpośrednio ze źródła (hotlink), więc nie zajmują miejsca.",
           size=9.6, color="#7a5b12")
    s += T(56, ny+31, "Pobieramy wyłącznie strony dozwolone przez robots.txt źródła, w wolnym tempie — z szacunkiem dla ich serwera.",
           size=9.6, color="#7a5b12")

    s += foot("Skąd pochodzą dane — dane są kopią publicznych ogłoszeń poleasingowe.pl, odświeżaną automatycznie.")
    s += "</svg>"
    return s


# ============================================================ DOK 2: JAK DZIAŁA
def step_box(x, y, w, h, n, title, desc):
    s = rect(x, y, w, h, r=11, fill="#f5f9fe", stroke="#c8dcf3", sw=1.3)
    s += num_badge(x+20, y+22, n, r=12, fill="#1e5fb0")
    s += T(x+40, y+20, title, size=11.5, color=NAVY, weight="bold")
    s += T(x+40, y+37, desc, size=9.2, color=MUT)
    return s

def diag_page():
    s = page_open()
    s += header("Jak to działa", "Automatyczny obieg co kilka godzin — działa w tle, bez Twojego udziału")

    # zegar / cron
    cy = 96
    s += rect(40, cy, W-80, 40, r=10, fill=MINT, stroke=EM, sw=1.4)
    s += T(58, cy+18, "⏱  Harmonogram (cron) uruchamia import CO KILKA GODZIN", size=12.5, color=EMD, weight="bold")
    s += T(58, cy+33, "Ty nic nie klikasz. Poniższy obieg wykonuje się sam i aktualizuje podstronę „Nasze motory”.",
           size=9.6, color="#4a6b5e")

    # 6 kroków scrapera 2x3
    sy = cy + 56
    bw, bh, gx, gy = (W-80-2*16)/3, 58, 16, 14
    steps = [
        ("Pobierz listę", "wszystkie aktualne motocykle z kategorii"),
        ("Pobierz szczegóły + zdjęcia", "dane techniczne, cena, galeria"),
        ("Uporządkuj dane", "km, ceny→liczby, daty, sprawdzenie VIN"),
        ("Sprawdź jakość", "reguły audytu odrzucają błędne rekordy"),
        ("Odsiej duplikaty", "jeden motocykl = jeden wpis (po VIN)"),
        ("Zapisz do bazy", "dodaj / zaktualizuj + oznacz zakończone"),
    ]
    for i, (t, d) in enumerate(steps):
        cx = 40 + (i % 3) * (bw + gx)
        ry = sy + (i // 3) * (bh + gy)
        s += step_box(cx, ry, bw, bh, i+1, t, d)
        if i % 3 != 2:
            s += arrow(cx+bw+2, ry+bh/2, cx+bw+gx-1, color="#1e5fb0", sw=2.4)
    # strzałka z wiersza 1 do wiersza 2 (zawijanie) — pod prawym boxem w dół, w lewo
    midy = sy + bh + gy/2
    s += line(40+2*(bw+gx)+bw/2, sy+bh, 40+2*(bw+gx)+bw/2, midy, "#1e5fb0", 2.2)
    s += line(40+bw/2, midy, 40+2*(bw+gx)+bw/2, midy, "#1e5fb0", 2.2, dash="4 3")
    s += varrow(40+bw/2, midy, sy+bh+gy, color="#1e5fb0", sw=2.2)

    # baza -> wordpress
    by = sy + 2*bh + gy + 20
    s += rect(40, by, (W-80-16)/2, 40, r=10, fill="#e8f5e9", stroke="#43a047", sw=1.4)
    s += T(40+((W-80-16)/2)/2, by+18, "BAZA polea_*", size=12, color="#2e7d32", weight="bold", anchor="middle")
    s += T(40+((W-80-16)/2)/2, by+33, "aktualny stan wszystkich ogłoszeń", size=9.3, color="#4a7a52", anchor="middle")
    x2 = 40 + (W-80-16)/2 + 16
    s += rect(x2, by, (W-80-16)/2, 40, r=10, fill="#e1f5fe", stroke="#039be5", sw=1.4)
    s += T(x2+((W-80-16)/2)/2, by+18, "PODSTRONA „NASZE MOTORY”", size=12, color="#0277bd", weight="bold", anchor="middle")
    s += T(x2+((W-80-16)/2)/2, by+33, "wtyczka czyta bazę i pokazuje motocykle", size=9.3, color="#296b8a", anchor="middle")
    s += arrow(40+(W-80-16)/2+1, by+20, x2-1, color="#039be5", sw=2.6)

    # co się dzieje z ogłoszeniem
    dy = by + 58
    s += T(40, dy, "Co dzieje się z każdym ogłoszeniem przy odświeżeniu", size=12.5, color=NAVY, weight="bold")
    dy += 12
    cw = (W-80-2*14)/3
    cards = [
        ("#2e7d32", "#e8f5e9", "NOWE", "pojawiło się → dodajemy je na Twoją stronę"),
        ("#b8860b", "#fbf3e6", "ZMIENIONE", "zmiana ceny / statusu → aktualizujemy wpis"),
        ("#a31818", "#fdecec", "ZAKOŃCZONE", "zniknęło ze źródła → znika z listy"),
    ]
    for i, (ink, bg, tag, desc) in enumerate(cards):
        cx = 40 + i*(cw+14)
        s += rect(cx, dy, cw, 54, r=10, fill=bg, stroke=ink, sw=1.3)
        s += T(cx+14, dy+22, tag, size=12, color=ink, weight="bold")
        s += T(cx+14, dy+40, desc, size=9.2, color=INK)

    # niezawodność
    ry = dy + 68
    s += rect(40, ry, W-80, 40, r=10, fill=GREY, stroke=GREYB, sw=1.2)
    s += T(56, ry+17, "Niezawodność:  wolne tempo pobierania + odczekanie przy przeciążeniu źródła (429/503).",
           size=9.6, color="#44515e")
    s += T(56, ry+32, "Awaria bazy NIE psuje Twojej strony (bezpieczne połączenie) · wyniki są chwilowo zapamiętane (cache 5 min) = szybkie ładowanie.",
           size=9.6, color="#44515e")

    s += foot("Jak to działa — pełny obieg powtarza się automatycznie co kilka godzin.")
    s += "</svg>"
    return s


if __name__ == "__main__":
    render([proof_page()], OUT_PROOF)
    render([diag_page()], OUT_DIAG)
