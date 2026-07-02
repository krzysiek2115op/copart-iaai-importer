#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generyczny renderer Markdown -> ŁADNY PDF (offline, rsvg-convert + gs).

Zamienia każdy plik etapu instrukcji (docs/klient/0X-*.md) na osobny, estetyczny
PDF (docs/klient/pdf/0X-*.pdf) w tym samym stylu co komplet Instrukcja-klienta.pdf.
Obsługuje: # ## ### nagłówki, akapity, listy - i 1., cytaty > (ramka), bloki ```kod```,
tabele |...|, linie ---, pogrubienia/linki (spłaszczane), emoji (usuwane/zamieniane).

Uruchom:  python3 docs/klient/gen_etapy_pdf.py
"""
from __future__ import annotations
import html, os, re, subprocess, tempfile

PW, PH = 595.28, 841.89
MX = 46
CW = PW - 2 * MX
TOP = 96
BOTTOM = 792
BLUE = "#1f4fd8"; DARK = "#12203a"; GRAYBG = "#f1f5f9"; GRAYBORDER = "#d7dee7"
CALLBG = "#eef4ff"; CALLBORDER = "#1f4fd8"; MUTED = "#5b6b82"
LH = 14.5

_NARROW = set("ijltfr.,:;'!|()[]{} -")
_WIDE = set("mwMW@%—–")
def _cw(c, s):
    if c in _NARROW: return .30 * s
    if c in _WIDE: return .90 * s
    if c.isupper(): return .70 * s
    return .54 * s
def tw(t, s): return sum(_cw(c, s) for c in t)
def wrap(text, size, maxw):
    out = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split(" "):
            t = (cur + " " + w).strip()
            if tw(t, size) <= maxw or not cur: cur = t
            else: out.append(cur); cur = w
        out.append(cur)
    return out or [""]
def esc(s): return html.escape(s, quote=True)
def T(x, y, s, size=10.5, color=DARK, w="normal", anchor="start", fam="DejaVu Sans"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" '
            f'fill="{color}" font-weight="{w}" text-anchor="{anchor}">{esc(s)}</text>')
def R(x, y, w, h, fill, rx=8, stroke="none", sw=1):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

# ---- czyszczenie tekstu ----
_EMO = {'✅':'[OK]','⚠️':'[!]','⚠':'[!]','❌':'[X]','✔':'-','☑':'-','→':'->','▸':'-',
        '•':'-','ℹ️':'i','🗺️':'','👋':'','⚙️':'','📘':'','📄':'','🔴':'','🔵':'','👀':'',
        '🚗':'','🧩':'','✂':'','📦':'','🟢':'','🔧':'','ℹ':'i'}
def strip_emoji(s):
    o = []
    for ch in s:
        c = ord(ch)
        if 0xFE00 <= c <= 0xFE0F: continue
        if 0x1F000 <= c <= 0x1FFFF: continue
        if 0x2600 <= c <= 0x27BF: continue
        if 0x2B00 <= c <= 0x2BFF: continue
        o.append(ch)
    return "".join(o)
def inline(s):
    s = re.sub(r'\*\*(.+?)\*\*', r'\1', s)
    s = re.sub(r'(?<!\*)\*(?!\*)(.+?)\*', r'\1', s)
    s = re.sub(r'`([^`]+)`', r'\1', s)
    s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', s)
    for k, v in _EMO.items(): s = s.replace(k, v)
    return strip_emoji(s).rstrip()

# ---- parser markdown -> bloki ----
def parse(md):
    lines = md.split("\n")
    blocks = []
    i = 0
    title = None
    while i < len(lines):
        ln = lines[i].rstrip()
        s = ln.strip()
        if s.startswith("```"):
            code = []; i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i]); i += 1
            i += 1; blocks.append(("code", code)); continue
        if not s:
            i += 1; continue
        if s.startswith("# "):
            t = inline(s[2:])
            if title is None: title = t
            else: blocks.append(("h1", t))
            i += 1; continue
        if s.startswith("## "):
            blocks.append(("h2", inline(s[3:]))); i += 1; continue
        if s.startswith("### "):
            blocks.append(("h3", inline(s[4:]))); i += 1; continue
        if re.match(r'^(---+|\*\*\*+)$', s):
            blocks.append(("hr",)); i += 1; continue
        if s.startswith(">"):
            q = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q.append(inline(lines[i].strip().lstrip(">").strip())); i += 1
            blocks.append(("callout", [x for x in q if x != ""] or [""])); continue
        if s.startswith("|") and "|" in s[1:]:
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not re.match(r'^[:\- ]+$', "".join(cells)):   # pomiń separator |---|
                    rows.append([inline(c) for c in cells])
                i += 1
            if rows: blocks.append(("table", rows)); continue
        m = re.match(r'^(\d+)\.\s+(.*)', s)
        if m or s.startswith(("- ", "* ")):
            items = []
            while i < len(lines):
                t = lines[i].strip()
                mm = re.match(r'^(\d+)\.\s+(.*)', t)
                if mm: items.append(inline(mm.group(2)))
                elif t.startswith(("- ", "* ")): items.append(inline(t[2:]))
                elif t == "": break
                else: break
                i += 1
            ordered = bool(m)
            blocks.append(("num" if ordered else "bullet", items)); continue
        # akapit — zlep SUROWE linie, potem wyczyść (pogrubienia/linki bywają łamane)
        raw = [s]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r'^(#|\d+\.\s|-\s|\*\s|>|\||```|---)', lines[i].strip()):
            raw.append(lines[i].strip()); i += 1
        blocks.append(("p", inline(" ".join(raw))))
    return title or "Instrukcja", blocks

# ---- pomiar / rysowanie bloków ----
def col_widths(rows):
    n = max(len(r) for r in rows)
    return [CW / n] * n

def bh(b):
    k = b[0]
    if k == "h1": return 40
    if k == "h2": return 10 + 17 * len(wrap(b[1], 13, CW)) + 6
    if k == "h3": return 8 + 15 * len(wrap(b[1], 11.5, CW)) + 4
    if k == "p": return len(wrap(b[1], 10.5, CW)) * LH + 8
    if k in ("bullet", "num"):
        h = 0
        for it in b[1]: h += len(wrap(it, 10.5, CW - 20)) * LH
        return h + 8
    if k == "callout":
        h = 0
        for ln in b[1]: h += len(wrap(ln, 10, CW - 34)) * 13.5
        return 14 + h + 14
    if k == "code": return 12 + len(b[1]) * 13 + 12
    if k == "hr": return 16
    if k == "table":
        cw = col_widths(b[1]); h = 0
        for r in b[1]:
            rh = max(len(wrap(c, 9.5, cw[j] - 10)) for j, c in enumerate(r))
            h += rh * 13 + 8
        return h + 4
    return 0

def draw(b, x, y):
    k = b[0]; s = []
    if k == "h1":
        s.append(R(x, y + 4, CW, 30, BLUE, 8)); s.append(T(x + 14, y + 24, b[1], 15, "#fff", "bold")); return "".join(s), 40
    if k == "h2":
        yy = y + 14
        for ln in wrap(b[1], 13, CW): s.append(T(x, yy, ln, 13, BLUE, "bold")); yy += 17
        return "".join(s), bh(b)
    if k == "h3":
        yy = y + 13
        for ln in wrap(b[1], 11.5, CW): s.append(T(x, yy, ln, 11.5, DARK, "bold")); yy += 15
        return "".join(s), bh(b)
    if k == "p":
        yy = y + 11
        for ln in wrap(b[1], 10.5, CW): s.append(T(x, yy, ln, 10.5, DARK)); yy += LH
        return "".join(s), bh(b)
    if k in ("bullet", "num"):
        yy = y + 11; idx = 0
        for it in b[1]:
            idx += 1; mark = f"{idx}." if k == "num" else "-"
            first = True
            for ln in wrap(it, 10.5, CW - 20):
                if first: s.append(T(x + 4, yy, mark, 10.5, BLUE, "bold")); first = False
                s.append(T(x + 22, yy, ln, 10.5, DARK)); yy += LH
        return "".join(s), (yy - y) + 8
    if k == "callout":
        lines = []
        for ln in b[1]: lines += wrap(ln, 10, CW - 34)
        h = 14 + len(lines) * 13.5 + 14
        s.append(R(x, y, CW, h, CALLBG, 8, CALLBORDER)); s.append(R(x, y, 5, h, CALLBORDER, 2))
        yy = y + 20
        for ln in lines: s.append(T(x + 18, yy, ln, 10, DARK)); yy += 13.5
        return "".join(s), h
    if k == "code":
        h = 12 + len(b[1]) * 13 + 12
        s.append(R(x, y, CW, h, GRAYBG, 6, GRAYBORDER)); yy = y + 22
        for ln in b[1]: s.append(T(x + 12, yy, ln[:120], 9.5, DARK, fam="DejaVu Sans Mono")); yy += 13
        return "".join(s), h
    if k == "hr":
        s.append(f'<line x1="{x}" y1="{y+8}" x2="{x+CW}" y2="{y+8}" stroke="{GRAYBORDER}" stroke-width="1"/>'); return "".join(s), 16
    if k == "table":
        cw = col_widths(b[1]); yy = y
        for ri, r in enumerate(b[1]):
            rh = max(len(wrap(c, 9.5, cw[j] - 10)) for j, c in enumerate(r)) * 13 + 8
            if ri == 0: s.append(R(x, yy, CW, rh, GRAYBG, 0, GRAYBORDER))
            xx = x
            for j, c in enumerate(r):
                s.append(f'<rect x="{xx:.1f}" y="{yy:.1f}" width="{cw[j]:.1f}" height="{rh:.1f}" fill="none" stroke="{GRAYBORDER}" stroke-width="1"/>')
                ty = yy + 15
                for ln in wrap(c, 9.5, cw[j] - 10):
                    s.append(T(xx + 6, ty, ln, 9.5, DARK, "bold" if ri == 0 else "normal")); ty += 13
                xx += cw[j]
            yy += rh
        return "".join(s), (yy - y) + 4
    return "", 0

def header(title, pno):
    s = [R(0, 0, PW, 60, DARK, 0), R(0, 57, PW, 3, BLUE, 0),
         T(MX, 26, "IAAI Importer", 13, "#fff", "bold"),
         T(MX, 46, title[:70], 10, "#aebfd8"),
         T(PW - MX, 38, "instrukcja klienta", 9.5, "#aebfd8", anchor="end")]
    return "".join(s)
def footer(pno, total):
    return (f'<line x1="{MX}" y1="808" x2="{PW-MX}" y2="808" stroke="{GRAYBORDER}" stroke-width="1"/>'
            + T(MX, 822, "IAAI Importer — importer aut z IAAI do WordPress", 8.5, MUTED)
            + T(PW - MX, 822, f"Strona {pno} / {total}", 8.5, MUTED, anchor="end"))

def render_doc(title, blocks):
    # tytuł na starcie treści
    items = [("title", title)] + blocks
    pages = []; cur = []; y = TOP
    for b in items:
        h = 46 if b[0] == "title" else bh(b)
        need = h + (bh(items[items.index(b)+1]) if b[0] == "h1" and items.index(b)+1 < len(items) else 0)
        if y + need > BOTTOM and cur:
            pages.append(cur); cur = []; y = TOP
        cur.append((b, y)); y += h + 5
    if cur: pages.append(cur)
    total = len(pages); svgs = []
    for pi, page in enumerate(pages):
        s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{PW}" height="{PH}" viewBox="0 0 {PW} {PH}">',
             R(0, 0, PW, PH, "#fff", 0), header(title, pi + 1)]
        for b, y in page:
            if b[0] == "title":
                s.append(T(MX, y + 34, b[1], 22, DARK, "bold"))
            else:
                svg, _ = draw(b, MX, y); s.append(svg)
        s.append(footer(pi + 1, total)); s.append("</svg>"); svgs.append("".join(s))
    return svgs

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    outdir = os.path.join(here, "pdf"); os.makedirs(outdir, exist_ok=True)
    targets = ["00-START-TUTAJ", "01-instalacja-wtyczki", "02-pokaz-auta-na-stronie",
               "03-uruchom-automatyzacje", "04-jak-dziala-i-obsluga",
               "05-problemy-i-pytania", "06-edycja-podstrony-i-motyw"]
    done = []
    for name in targets:
        md_path = os.path.join(here, name + ".md")
        if not os.path.exists(md_path): continue
        title, blocks = parse(open(md_path, encoding="utf-8").read())
        svgs = render_doc(title, blocks)
        out = os.path.join(outdir, name + ".pdf")
        with tempfile.TemporaryDirectory() as td:
            pdfs = []
            for i, svg in enumerate(svgs):
                sp = os.path.join(td, f"p{i}.svg"); pp = os.path.join(td, f"p{i}.pdf")
                open(sp, "w", encoding="utf-8").write(svg)
                subprocess.run(["rsvg-convert", "-f", "pdf", "-o", pp, sp], check=True)
                pdfs.append(pp)
            subprocess.run(["gs", "-dBATCH", "-dNOPAUSE", "-q", "-sDEVICE=pdfwrite",
                            f"-sOutputFile={out}", *pdfs], check=True)
        done.append((name, len(svgs)))
        print(f"OK {name}.pdf ({len(svgs)} str.)")
    print(f"Gotowe: {len(done)} PDF w {outdir}")

if __name__ == "__main__":
    main()
