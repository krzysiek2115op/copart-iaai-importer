#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Generator PDF instrukcji z Markdown (docs/TESTY-RECZNE.md).

Brak w srodowisku pandoc/chromium/weasyprint, wiec skladamy PDF sami:
Markdown -> strony SVG (A4) -> rsvg-convert (PDF na strone) -> gs (scalenie).
rsvg-convert poprawnie renderuje polskie znaki (fontconfig), groff nie.

Uzycie:  python3 docs/gen_instrukcja_pdf.py [zrodlo.md] [wynik.pdf]
"""
import html
import os
import re
import subprocess
import sys

# --- geometria strony A4 @96dpi (rsvg mapuje 96px -> 72pt) ---
W, H = 794, 1123
ML, MR, MT, MB = 52, 52, 58, 60
USABLE = W - ML - MR
FS = 10                      # bazowy rozmiar tekstu (mono)
LH = 15                      # interlinia
CHARW = FS * 0.6            # szerokosc znaku w foncie monospace
MONO = "Liberation Mono, DejaVu Sans Mono, Noto Sans Mono, monospace"

C_TEXT = "#1b1b1b"
C_H1 = "#0b3d66"
C_H2 = "#0b5cad"
C_H3 = "#333333"
C_CODEBG = "#f1f2f5"
C_CODE = "#0f3b2e"
C_THEAD = "#dde7f1"
C_BORDER = "#c6cfda"
C_RULE = "#d7dce3"
C_QUOTEBG = "#f3f6ef"
C_QUOTEBAR = "#82b366"
C_MUTED = "#5a6470"


def esc(s):
    return html.escape(s, quote=False)


def inline(s):
    """Usuwa skladnie inline Markdown i zamienia znaki spoza monospace na ASCII."""
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', s)   # [tekst](url) -> tekst (url)
    s = s.replace('**', '').replace('`', '')
    for a, b in (('→', '->'), ('←', '<-'), ('↔', '<->'),
                 ('≤', '<='), ('≥', '>='), ('•', '-'), ('✓', '[x]')):
        s = s.replace(a, b)
    return s


def wrap(text, ncols):
    """Zawija tekst do ncols znakow (po slowach; dlugie slowa twardo lamie)."""
    if ncols < 1:
        ncols = 1
    out, line = [], ""
    for word in text.split():
        while len(word) > ncols:                # slowo dluzsze niz kolumna
            if line:
                out.append(line); line = ""
            out.append(word[:ncols]); word = word[ncols:]
        if not line:
            line = word
        elif len(line) + 1 + len(word) <= ncols:
            line += " " + word
        else:
            out.append(line); line = word
    if line:
        out.append(line)
    return out or [""]


class Doc:
    def __init__(self):
        self.pages = []
        self.cur = []
        self.y = MT

    def _newpage(self):
        self.pages.append(self.cur)
        self.cur = []
        self.y = MT

    def _ensure(self, h):
        if self.y + h > H - MB:
            self._newpage()

    def _txt(self, s, x, fs=FS, color=C_TEXT, weight="normal"):
        base = self.y + fs * 0.8
        self.cur.append(
            f'<text x="{x:.1f}" y="{base:.1f}" font-family="{MONO}" '
            f'font-size="{fs}" fill="{color}" font-weight="{weight}" '
            f'xml:space="preserve">{esc(s)}</text>')

    def _rect(self, x, y, w, h, fill, stroke=None):
        s = f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"'
        if stroke:
            s += f' stroke="{stroke}" stroke-width="0.6"'
        self.cur.append(s + '/>')

    def _line(self, x1, y1, x2, y2, color=C_RULE, wdt=0.6):
        self.cur.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                        f'stroke="{color}" stroke-width="{wdt}"/>')

    # --- bloki ---
    def gap(self, px):
        self.y += px

    def heading(self, level, text):
        text = inline(text)
        if level == 1:
            self._ensure(46)
            self._rect(ML, self.y, USABLE, 30, C_H1)
            self.cur.append(
                f'<text x="{ML+10:.1f}" y="{self.y+20:.1f}" font-family="{MONO}" '
                f'font-size="15" fill="#ffffff" font-weight="bold">{esc(text)}</text>')
            self.y += 42
        elif level == 2:
            self.gap(8)
            self._ensure(26)
            self._txt(text, ML, fs=13, color=C_H2, weight="bold")
            self.y += 18
            self._line(ML, self.y, ML + USABLE, self.y, C_H2, 1.0)
            self.y += 8
        else:
            self.gap(5)
            self._ensure(20)
            self._txt(text, ML, fs=11, color=C_H3, weight="bold")
            self.y += 17

    def para(self, text, indent=0, bullet=None, color=C_TEXT):
        x = ML + indent
        cap = int((USABLE - indent) / CHARW)
        lines = wrap(inline(text), cap - (2 if bullet else 0))
        for i, ln in enumerate(lines):
            self._ensure(LH)
            if bullet and i == 0:
                self._txt(bullet, x, color=C_MUTED)
                self._txt(ln, x + 2 * CHARW, color=color)
            elif bullet:
                self._txt(ln, x + 2 * CHARW, color=color)
            else:
                self._txt(ln, x, color=color)
            self.y += LH

    def code(self, lines):
        self.gap(4)
        pad = 5
        cap = int((USABLE - 2 * pad) / CHARW)
        for raw in lines:
            raw = raw.replace('\t', '    ')
            segs = [raw]
            if len(raw) > cap:                    # dlugie linie zawijamy z wcieciem (kontynuacja)
                segs = [raw[:cap]]
                rest = raw[cap:]
                while rest:
                    segs.append('    ' + rest[:cap - 4])
                    rest = rest[cap - 4:]
            for seg in segs:
                self._ensure(LH)
                self._rect(ML, self.y, USABLE, LH, C_CODEBG)
                self._txt(seg, ML + pad, color=C_CODE)
                self.y += LH
        self.gap(5)

    def quote(self, lines):
        self.gap(3)
        text = inline(" ".join(lines))
        cap = int((USABLE - 16) / CHARW)
        for ln in wrap(text, cap):
            self._ensure(LH)
            self._rect(ML, self.y, USABLE, LH, C_QUOTEBG)
            self._rect(ML, self.y, 3, LH, C_QUOTEBAR)
            self._txt(ln, ML + 12, color=C_MUTED)
            self.y += LH
        self.gap(4)

    def table(self, header, rows):
        ncol = len(header)
        gutter = 8
        avail = USABLE - gutter * (ncol - 1)
        weights = []
        for c in range(ncol):
            mx = len(header[c])
            for r in rows:
                if c < len(r):
                    mx = max(mx, min(len(r[c]), 46))
            weights.append(max(mx, 3))
        tot = sum(weights)
        widths = [max(46, avail * w / tot) for w in weights]
        # skala, by zmiescic sie w dostepnej szerokosci
        scale = avail / sum(widths)
        widths = [w * scale for w in widths]
        caps = [max(3, int((w) / CHARW)) for w in widths]

        xs = [ML]
        for w in widths[:-1]:
            xs.append(xs[-1] + w + gutter)

        def draw_row(cells, head=False):
            wrapped = [wrap(inline(cells[c]) if c < len(cells) else "", caps[c])
                       for c in range(ncol)]
            rh = max(len(w) for w in wrapped) * LH + 6
            self._ensure(rh)
            y0 = self.y
            if head:
                self._rect(ML, y0, USABLE, rh, C_THEAD)
            for c in range(ncol):
                for i, ln in enumerate(wrapped[c]):
                    self.cur.append(
                        f'<text x="{xs[c]+3:.1f}" y="{y0+3+i*LH+FS*0.8:.1f}" '
                        f'font-family="{MONO}" font-size="{FS}" fill="{C_TEXT}" '
                        f'font-weight="{"bold" if head else "normal"}" '
                        f'xml:space="preserve">{esc(ln)}</text>')
            self.y = y0 + rh
            self._line(ML, self.y, ML + USABLE, self.y, C_BORDER, 0.6)

        self.gap(4)
        self._line(ML, self.y, ML + USABLE, self.y, C_BORDER, 0.6)
        draw_row(header, head=True)
        for r in rows:
            draw_row(r)
        self.gap(6)

    def svg_pages(self):
        total = len(self.pages)
        out = []
        for idx, page in enumerate(self.pages, 1):
            body = "".join(page)
            foot = (f'<text x="{W-MR:.1f}" y="{H-28:.1f}" text-anchor="end" '
                    f'font-family="{MONO}" font-size="8" fill="{C_MUTED}">'
                    f'Importer Motocykli (poleasingowe.pl) — instrukcja testów   '
                    f'str. {idx}/{total}</text>')
            out.append(
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
                f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="#ffffff"/>'
                f'{body}{foot}</svg>')
        return out


def parse_md(text):
    doc = Doc()
    lines = text.split("\n")
    i, n = 0, len(lines)
    in_code, code_buf = False, []
    while i < n:
        ln = lines[i]
        st = ln.strip()
        if st.startswith("```"):
            if in_code:
                doc.code(code_buf); code_buf = []; in_code = False
            else:
                in_code = True
            i += 1; continue
        if in_code:
            code_buf.append(ln); i += 1; continue
        if st.startswith("<!--"):
            i += 1; continue
        if not st:
            doc.gap(6); i += 1; continue
        if st.startswith("### "):
            doc.heading(3, st[4:]); i += 1; continue
        if st.startswith("## "):
            doc.heading(2, st[3:]); i += 1; continue
        if st.startswith("# "):
            doc.heading(1, st[2:]); i += 1; continue
        if st.startswith("---"):
            doc.gap(3); doc._ensure(6)
            doc._line(ML, doc.y, ML + USABLE, doc.y, C_RULE, 0.8); doc.gap(6)
            i += 1; continue
        if st.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip()); i += 1
            doc.quote(buf); continue
        if st.startswith("|") and i + 1 < n and re.match(r'^\|[\s:|-]+\|?$', lines[i+1].strip()):
            def cells(row):
                row = row.strip().strip("|")
                return [c.strip() for c in row.split("|")]
            header = cells(lines[i]); i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(cells(lines[i])); i += 1
            doc.table(header, rows); continue
        m = re.match(r'^(\s*)([-*])\s+(.*)$', ln)
        if m:
            indent = 8 + len(m.group(1))
            doc.para(m.group(3), indent=indent, bullet="-"); i += 1; continue
        m = re.match(r'^(\s*)(\d+)\.\s+(.*)$', ln)
        if m:
            indent = 8 + len(m.group(1))
            doc.para(m.group(3), indent=indent, bullet=m.group(2) + "."); i += 1; continue
        doc.para(st); i += 1
    if in_code and code_buf:
        doc.code(code_buf)
    return doc


def render(doc, out_pdf):
    build = os.path.join(os.path.dirname(out_pdf) or ".", "_pdfbuild")
    os.makedirs(build, exist_ok=True)
    page_pdfs = []
    for idx, svg in enumerate(doc.svg_pages()):
        sp = os.path.join(build, f"p{idx:03d}.svg")
        pp = os.path.join(build, f"p{idx:03d}.pdf")
        with open(sp, "w", encoding="utf-8") as f:
            f.write(svg)
        subprocess.run(["rsvg-convert", "-f", "pdf", "-o", pp, sp], check=True)
        page_pdfs.append(pp)
    subprocess.run(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite",
                    "-dCompatibilityLevel=1.5", f"-sOutputFile={out_pdf}", *page_pdfs],
                   check=True)
    for p in page_pdfs:
        os.remove(p); os.remove(p[:-4] + ".svg")
    os.rmdir(build)
    return len(page_pdfs)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "TESTY-RECZNE.md")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "INSTRUKCJA-TESTOW-RECZNYCH.pdf")
    with open(src, encoding="utf-8") as f:
        doc = parse_md(f.read())
    pages = render(doc, out)
    print(f"OK: {out} ({pages} stron)")


if __name__ == "__main__":
    main()
