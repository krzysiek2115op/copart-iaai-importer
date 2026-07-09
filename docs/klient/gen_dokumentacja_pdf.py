# SPDX-License-Identifier: GPL-2.0-or-later
"""
Generator kompletnej dokumentacji systemu (PDF) dla klienta — plugin-2.

Bez zaleznosci zewnetrznych: sklad wlasny SVG -> PDF przez `rsvg-convert`,
scalanie stron przez `gs`. Szerokosci glifow czytane wprost z plikow czcionek
DejaVu (parser TTF w czystym Pythonie) -> poprawne zawijanie tekstu bez
wychodzenia poza margines. BEZ diagramow/grafik (te powstaja w draw.io).

Wynik: docs/klient/pdf/dokumentacja-systemu.pdf
"""
import os
import re
import struct
import shutil
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "pdf")
OUT = os.path.join(OUTDIR, "dokumentacja-systemu.pdf")

FONT_FILES = {
    "reg":  "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "bold": "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "mono": "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
    "ital": "/usr/share/fonts/TTF/DejaVuSans-Oblique.ttf",
}
FAMILY = {
    "reg":  ("DejaVu Sans", "normal", "normal"),
    "bold": ("DejaVu Sans", "bold",   "normal"),
    "mono": ("DejaVu Sans Mono", "normal", "normal"),
    "ital": ("DejaVu Sans", "normal", "italic"),
}

# ---------------------------------------------------------------- metryki TTF
def _load_font(path):
    data = open(path, "rb").read()
    num = struct.unpack(">H", data[4:6])[0]
    tab = {}
    for i in range(num):
        rec = 12 + 16 * i
        tag = data[rec:rec + 4].decode("latin1")
        off, ln = struct.unpack(">II", data[rec + 8:rec + 16])
        tab[tag] = (off, ln)
    head = tab["head"][0]
    upm = struct.unpack(">H", data[head + 18:head + 20])[0]
    hhea = tab["hhea"][0]
    num_hm = struct.unpack(">H", data[hhea + 34:hhea + 36])[0]
    hmtx = tab["hmtx"][0]
    adv = [struct.unpack(">H", data[hmtx + 4 * i:hmtx + 4 * i + 2])[0] for i in range(num_hm)]
    cmap = _parse_cmap(data, tab["cmap"][0])
    return {"upm": upm, "num_hm": num_hm, "adv": adv, "cmap": cmap}


def _parse_cmap(data, off):
    n = struct.unpack(">H", data[off + 2:off + 4])[0]
    best = None
    for i in range(n):
        rec = off + 4 + 8 * i
        plat, enc, sub = struct.unpack(">HHI", data[rec:rec + 8])
        score = {(3, 1): 4, (0, 3): 4, (0, 4): 4, (3, 10): 3, (0, 6): 3}.get((plat, enc), 1 if plat == 0 else 0)
        if best is None or score > best[0]:
            best = (score, off + sub)
    so = best[1]
    fmt = struct.unpack(">H", data[so:so + 2])[0]
    res = {}
    if fmt == 4:
        segx2 = struct.unpack(">H", data[so + 6:so + 8])[0]
        seg = segx2 // 2
        p = so + 14
        end = struct.unpack(">%dH" % seg, data[p:p + segx2]); p += segx2 + 2
        start = struct.unpack(">%dH" % seg, data[p:p + segx2]); p += segx2
        delta = struct.unpack(">%dh" % seg, data[p:p + segx2]); p += segx2
        ro_pos = p
        ro = struct.unpack(">%dH" % seg, data[p:p + segx2])
        for i in range(seg):
            for c in range(start[i], end[i] + 1):
                if c == 0xFFFF:
                    continue
                if ro[i] == 0:
                    g = (c + delta[i]) & 0xFFFF
                else:
                    addr = ro_pos + 2 * i + ro[i] + 2 * (c - start[i])
                    g = struct.unpack(">H", data[addr:addr + 2])[0]
                    if g:
                        g = (g + delta[i]) & 0xFFFF
                if g:
                    res[c] = g
    elif fmt == 12:
        ng = struct.unpack(">I", data[so + 12:so + 16])[0]
        p = so + 16
        for _ in range(ng):
            sc, ec, sg = struct.unpack(">III", data[p:p + 12]); p += 12
            for c in range(sc, ec + 1):
                res[c] = sg + (c - sc)
    return res


FONTS = {k: _load_font(v) for k, v in FONT_FILES.items()}


def tw(style, s, size):
    """Szerokosc tekstu [pt] dla stylu (reg/bold/mono/ital)."""
    f = FONTS[style]
    cmap, adv, nhm, upm = f["cmap"], f["adv"], f["num_hm"], f["upm"]
    total = 0
    for ch in s:
        g = cmap.get(ord(ch), 0)
        total += adv[g] if g < nhm else adv[-1]
    return total / upm * size


# ------------------------------------------------------------------- geometria
PW, PH = 595.28, 841.89          # A4 pionowo
ML, MR, MT, MB = 56, 52, 64, 64
CW = PW - ML - MR
CTOP, CBOT = 74.0, 778.0

INK = "#1f2937"; ACCENT = "#1f4e79"; ACCENT2 = "#2563eb"; MUTE = "#6b7280"
RULE = "#d5d9df"; CODEBG = "#f3f4f6"; CODEINK = "#0f172a"
ZEBRA = "#f6f8fa"; THBG = "#1f4e79"

BODY = 9.3; LH = 13.0
H2 = 13.5; H3 = 10.6; SMALL = 8.4
CODE = 8.1; CODE_LH = 11.4
TB = 8.5; TB_LH = 11.6


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def T(x, y, s, size, style="reg", fill=INK, anchor="start"):
    fam, w, st = FAMILY[style]
    return ('<text x="%.2f" y="%.2f" font-family="%s" font-size="%.2f" '
            'font-weight="%s" font-style="%s" fill="%s" text-anchor="%s" '
            'xml:space="preserve">%s</text>') % (x, y, fam, size, w, st, fill, anchor, esc(s))


def rect(x, y, w, h, fill, rx=0, stroke=None, sw=1):
    s = '<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%.2f" fill="%s"' % (x, y, w, h, rx, fill)
    if stroke:
        s += ' stroke="%s" stroke-width="%.2f"' % (stroke, sw)
    return s + "/>"


def line(x1, y1, x2, y2, stroke=RULE, sw=1):
    return '<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%.2f"/>' % (x1, y1, x2, y2, stroke, sw)


# --------------------------------------------------------------- inline markup
def parse_inline(s):
    runs, i = [], 0
    for m in re.finditer(r"\*\*(.+?)\*\*|`([^`]+)`", s):
        if m.start() > i:
            runs.append((s[i:m.start()], "reg"))
        if m.group(1) is not None:
            runs.append((m.group(1), "bold"))
        else:
            runs.append((m.group(2), "mono"))
        i = m.end()
    if i < len(s):
        runs.append((s[i:], "reg"))
    return runs or [("", "reg")]


def _split_long(word, style, size, maxw):
    if tw(style, word, size) <= maxw:
        return [word]
    out, part = [], ""
    for ch in word:
        if tw(style, part + ch, size) <= maxw:
            part += ch
        else:
            if part:
                out.append(part)
            part = ch
    if part:
        out.append(part)
    return out


def layout_runs(runs, size, maxw):
    """Zwraca liste linii; kazda linia = [(word, style, xoff)]."""
    words = []
    for text, style in runs:
        for j, seg in enumerate(text.split(" ")):
            if seg == "":
                continue
            for chunk in _split_long(seg, style, size, maxw):
                words.append((chunk, style))
    spw = tw("reg", " ", size)
    lines, cur, x = [], [], 0.0
    for word, style in words:
        w = tw(style, word, size)
        if not cur:
            cur, x = [(word, style, 0.0)], w
        elif x + spw + w <= maxw:
            xoff = x + spw
            cur.append((word, style, xoff)); x = xoff + w
        else:
            lines.append(cur); cur, x = [(word, style, 0.0)], w
    if cur:
        lines.append(cur)
    return lines or [[("", "reg", 0.0)]]


# ------------------------------------------------------------------- dokument
class Doc:
    def __init__(self):
        self.pages = []       # [{'frags':[...], 'label':str}]
        self.frags = []
        self.y = CTOP
        self.label = ""
        self.toc = []         # (level, text, body_page_index)

    def _break(self):
        self.pages.append({"frags": self.frags, "label": self.label})
        self.frags = []
        self.y = CTOP

    def _need(self, h):
        if self.y + h > CBOT:
            self._break()

    def finish(self):
        if self.frags:
            self.pages.append({"frags": self.frags, "label": self.label})

    # --- bloki ---
    def part(self, num, title, subtitle=""):
        if self.frags:
            self._break()
        h = 46 if not subtitle else 60
        self.frags.append(rect(ML, self.y, CW, h, ACCENT, rx=5))
        self.frags.append(T(ML + 14, self.y + 20, "CZĘŚĆ %s" % num, 10, "bold", "#bcd0e8"))
        self.frags.append(T(ML + 14, self.y + 37, title, 16.5, "bold", "#ffffff"))
        if subtitle:
            self.frags.append(T(ML + 14, self.y + 53, subtitle, 9.2, "reg", "#d7e3f2"))
        self.label = "Część %s — %s" % (num, title)
        self.toc.append((0, "Część %s. %s" % (num, title), len(self.pages)))
        self.y += h + 14

    def h2(self, text):
        self._need(H2 + 2 * LH + 10)
        self.y += 8
        self.frags.append(T(ML, self.y + H2, text, H2, "bold", ACCENT))
        self.y += H2 + 5
        self.frags.append(line(ML, self.y, ML + CW, self.y, RULE, 1))
        self.y += 7
        self.toc.append((1, text, len(self.pages)))

    def h3(self, text):
        self._need(H3 + LH + 6)
        self.y += 6
        self.frags.append(T(ML, self.y + H3, text, H3, "bold", INK))
        self.y += H3 + 4

    def para(self, text, gap=4, color=INK, size=BODY, indent=0.0):
        runs = parse_inline(text)
        lines = layout_runs(runs, size, CW - indent)
        for ln in lines:
            self._need(LH)
            base = self.y + size
            for word, style, xoff in ln:
                self.frags.append(T(ML + indent + xoff, base, word, size, style, color))
            self.y += LH
        self.y += gap

    def bullets(self, items, gap=3, marker="•"):
        for it in items:
            runs = parse_inline(it)
            lines = layout_runs(runs, BODY, CW - 16)
            for k, ln in enumerate(lines):
                self._need(LH)
                base = self.y + BODY
                if k == 0:
                    self.frags.append(T(ML + 2, base, marker, BODY, "bold", ACCENT))
                for word, style, xoff in ln:
                    self.frags.append(T(ML + 16 + xoff, base, word, BODY, style, INK))
                self.y += LH
            self.y += gap
        self.y += 2

    def numbered(self, items, gap=3):
        for i, it in enumerate(items, 1):
            lbl = "%d." % i
            lw = tw("bold", lbl, BODY) + 4
            runs = parse_inline(it)
            lines = layout_runs(runs, BODY, CW - lw)
            for k, ln in enumerate(lines):
                self._need(LH)
                base = self.y + BODY
                if k == 0:
                    self.frags.append(T(ML + 2, base, lbl, BODY, "bold", ACCENT))
                for word, style, xoff in ln:
                    self.frags.append(T(ML + 2 + lw + xoff, base, word, BODY, style, INK))
                self.y += LH
            self.y += gap
        self.y += 2

    def code(self, text):
        raw = text.split("\n")
        wrapped = []
        for rl in raw:
            if rl == "":
                wrapped.append("")
                continue
            cur = rl
            while tw("mono", cur, CODE) > CW - 16:
                cut = len(cur)
                while cut > 1 and tw("mono", cur[:cut], CODE) > CW - 16:
                    cut -= 1
                wrapped.append(cur[:cut])
                cur = cur[cut:]
            wrapped.append(cur)
        i = 0
        while i < len(wrapped):
            self._need(CODE_LH + 8)
            avail = int((CBOT - self.y - 8) // CODE_LH)
            chunk = wrapped[i:i + max(1, avail)]
            bh = len(chunk) * CODE_LH + 10
            self.frags.append(rect(ML, self.y, CW, bh, CODEBG, rx=3, stroke="#e2e5ea", sw=0.8))
            yy = self.y + 5
            for cl in chunk:
                self.frags.append(T(ML + 8, yy + CODE, cl, CODE, "mono", CODEINK))
                yy += CODE_LH
            self.y += bh + 4
            i += len(chunk)

    def note(self, kind, title, text):
        pal = {
            "warn": ("#fff7ed", "#f59e0b", "#92400e"),
            "info": ("#eff6ff", "#3b82f6", "#1e3a8a"),
            "ok":   ("#ecfdf5", "#10b981", "#065f46"),
        }[kind]
        bg, bar, ink = pal
        pad = 9
        maxw = CW - 2 * pad - 6
        blocks = []
        if title:
            blocks.append(("bold", title))
        for para in text.split("\n"):
            blocks.append(("reg", para))
        lines = []
        for style0, tx in blocks:
            for ln in layout_runs(parse_inline(tx), BODY, maxw):
                lines.append((style0, ln))
        bh = len(lines) * LH + 2 * pad
        self._need(bh + 4)
        self.frags.append(rect(ML, self.y, CW, bh, bg, rx=4))
        self.frags.append(rect(ML, self.y, 4, bh, bar, rx=0))
        yy = self.y + pad
        for style0, ln in lines:
            base = yy + BODY
            for word, style, xoff in ln:
                st = "bold" if style0 == "bold" and style == "reg" else style
                self.frags.append(T(ML + pad + 6 + xoff, base, word, BODY, st, ink))
            yy += LH
        self.y += bh + 6

    def table(self, headers, rows, fracs):
        colx = [ML]
        for f in fracs:
            colx.append(colx[-1] + f * CW)
        pad = 4

        def cell_lines(txt, w):
            return layout_runs(parse_inline(str(txt)), TB, w - 2 * pad)

        def draw_header():
            hh = TB_LH + 2 * pad
            self.frags.append(rect(ML, self.y, CW, hh, THBG, rx=0))
            for c, htxt in enumerate(headers):
                self.frags.append(T(colx[c] + pad, self.y + pad + TB, htxt, TB, "bold", "#ffffff"))
            self.y += hh

        self._need(TB_LH * 3 + 4 * pad)
        draw_header()
        zeb = False
        for row in rows:
            cells = [cell_lines(row[c], colx[c + 1] - colx[c]) for c in range(len(headers))]
            rh = max(len(cl) for cl in cells) * TB_LH + 2 * pad
            if self.y + rh > CBOT:
                self._break()
                draw_header()
            if zeb:
                self.frags.append(rect(ML, self.y, CW, rh, ZEBRA))
            zeb = not zeb
            for c in range(len(headers)):
                yy = self.y + pad
                for ln in cells[c]:
                    base = yy + TB
                    for word, style, xoff in ln:
                        self.frags.append(T(colx[c] + pad + xoff, base, word, TB, style, INK))
                    yy += TB_LH
            self.frags.append(line(ML, self.y + rh, ML + CW, self.y + rh, "#e5e7eb", 0.7))
            self.y += rh
        # ramka pionowa
        for c in range(len(headers) + 1):
            pass
        self.y += 6

    def spacer(self, h=6):
        self.y += h


# --------------------------------------------------------------- strony/render
def page_svg(frags, label, pageno, total, cover=False):
    body = ['<svg xmlns="http://www.w3.org/2000/svg" width="%.2fpt" height="%.2fpt" '
            'viewBox="0 0 %.2f %.2f">' % (PW, PH, PW, PH)]
    body.append(rect(0, 0, PW, PH, "#ffffff"))
    if cover:
        body += frags
        body.append("</svg>")
        return "\n".join(body)
    # naglowek
    body.append(T(ML, 42, "Importer Motocykli (poleasingowe.pl) — dokumentacja systemu", 8, "reg", MUTE))
    body.append(T(PW - MR, 42, label, 8, "reg", MUTE, anchor="end"))
    body.append(line(ML, 50, PW - MR, 50, RULE, 0.8))
    # stopka
    body.append(line(ML, 800, PW - MR, 800, RULE, 0.8))
    body.append(T(ML, 813, "Wersja wtyczki 0.7.1 • Kredyt Kompas • GPL-2.0-or-later", 7.6, "reg", MUTE))
    body.append(T(PW - MR, 813, "Strona %d / %d" % (pageno, total), 7.6, "reg", MUTE, anchor="end"))
    body += frags
    body.append("</svg>")
    return "\n".join(body)


def build_cover():
    f = []
    f.append(rect(0, 0, PW, 200, ACCENT))
    f.append(rect(0, 200, PW, 6, ACCENT2))
    f.append(T(ML, 92, "Importer Motocykli", 30, "bold", "#ffffff"))
    f.append(T(ML, 128, "(poleasingowe.pl)", 20, "bold", "#bcd0e8"))
    f.append(T(ML, 168, "Kompletna dokumentacja systemu", 13, "reg", "#e6eef7"))
    f.append(T(ML, 270, "Wtyczka WordPress + scraper Python + osobna baza MySQL", 12.5, "bold", INK))
    f.append(T(ML, 292, "Dokumentacja dla użytkownika biznesowego oraz administratora technicznego.", 10, "reg", INK))
    y = 340
    meta = [
        ("Produkt", "Podstrona „Nasze motory” z aukcjami motocykli z poleasingowe.pl"),
        ("Wersja wtyczki", "0.7.1"),
        ("Autor / właściciel", "Kredyt Kompas"),
        ("Licencja", "GPL-2.0-or-later"),
        ("Repozytorium", "copart-iaai-importer (branch plugin-2)"),
        ("Wymagania", "WordPress 6.0+ / PHP 7.4+ • MySQL 5.7+/MariaDB 10.2+ • Python 3 (VPS)"),
    ]
    for k, v in meta:
        f.append(T(ML, y, k, 9.5, "bold", ACCENT))
        for ln in layout_runs([(v, "reg")], 9.5, CW - 140):
            for word, style, xoff in ln:
                f.append(T(ML + 140 + xoff, y, word, 9.5, style, INK))
            y += 15
        y += 4
    # ramka informacyjna o diagramach
    y += 8
    bx, bw = ML, CW
    lines = layout_runs(parse_inline("Zgodnie z ustaleniami dokument **nie zawiera diagramów ani grafik** — "
                                     "schematy architektury zostaną wykonane oddzielnie w narzędziu draw.io. "
                                     "Wszystkie fakty w dokumencie wynikają z kodu źródłowego projektu; miejsca "
                                     "wymagające decyzji wdrożeniowej oznaczono jako „Wymaga potwierdzenia przez zespół projektowy”."),
                         9.3, bw - 30)
    bh = len(lines) * 14 + 20
    f.append(rect(bx, y, bw, bh, "#eff6ff", rx=5))
    f.append(rect(bx, y, 4, bh, "#3b82f6"))
    yy = y + 10
    for ln in lines:
        for word, style, xoff in ln:
            f.append(T(bx + 16 + xoff, yy + 9.3, word, 9.3, style, "#1e3a8a"))
        yy += 14
    f.append(T(ML, PH - 60, "Dokument wygenerowany automatycznie na podstawie brancha plugin-2.", 8.5, "ital", MUTE))
    return f


def build_toc(entries, base_offset):
    """entries: [(level, text, body_idx)]. Zwraca liste stron (frag-list)."""
    pages, frags, y = [], [], CTOP
    frags.append(T(ML, y + 18, "Spis treści", 18, "bold", ACCENT))
    y += 34
    frags.append(line(ML, y, ML + CW, y, RULE, 1)); y += 12
    for level, text, body_idx in entries:
        pageno = base_offset + body_idx + 1
        size = 10.2 if level == 0 else 9.3
        style = "bold" if level == 0 else "reg"
        indent = 0 if level == 0 else 18
        lh = 17 if level == 0 else 15
        if y + lh > CBOT:
            pages.append(frags); frags, y = [], CTOP
        if level == 0:
            y += 5
        col = ACCENT if level == 0 else INK
        label = text if tw(style, text, size) <= CW - 60 else text
        frags.append(T(ML + indent, y + size, label, size, style, col))
        frags.append(T(PW - MR, y + size, str(pageno), size, style, col, anchor="end"))
        y += lh
    pages.append(frags)
    return pages


# --------------------------------------------------------------------- TREŚĆ
def build_body(d):
    # ============================ CZĘŚĆ I ============================
    d.part("I", "Dokumentacja dla osoby nietechnicznej",
           "Do czego służy system, co widzi klient i jak nim zarządzać")

    d.h2("1. Czym jest system w skrócie")
    d.para("System automatycznie pobiera oferty aukcji **motocykli** z serwisu **poleasingowe.pl** "
           "i prezentuje je na stronie internetowej klienta na dedykowanej podstronie **„Nasze motory”**. "
           "Podstrona tworzy się sama po włączeniu wtyczki i wyglądem dopasowuje się do dowolnego motywu "
           "(kolory i czcionki dziedziczy ze strony klienta).")
    d.para("System składa się z dwóch współpracujących części, opisanych szczegółowo w części technicznej:")
    d.bullets([
        "**Wtyczka WordPress** — pokazuje motocykle na stronie klienta (lista, filtry, szczegóły).",
        "**Automat pobierający dane (scraper)** — działa na serwerze VPS i co pewien czas pobiera "
        "aktualne aukcje ze źródła, zapisując je do **osobnej bazy danych**.",
    ])
    d.para("Dzięki rozdzieleniu tych części strona klienta jest szybka i stabilna: nawet gdy źródło "
           "chwilowo nie odpowiada, strona nadal pokazuje ostatnio pobrane oferty.")

    d.h2("2. Co widzi osoba odwiedzająca stronę")
    d.para("Na podstronie **„Nasze motory”** odwiedzający zobaczy:")
    d.bullets([
        "**Listę (siatkę) motocykli** — kafelki ze zdjęciem, marką i modelem, ceną oraz podstawowymi "
        "parametrami: rok, przebieg, pojemność, paliwo.",
        "**Filtry** nad listą: marka, paliwo, rok, cena do (PLN). Po wybraniu filtrów lista sama się zawęża.",
        "**Podział na strony (paginacja)** — gdy ofert jest dużo, dzielą się na kolejne strony.",
        "**Widok pojedynczego motocykla** — po kliknięciu kafelka: galeria zdjęć oraz tabela szczegółów "
        "(VIN, rok produkcji, przebieg, pojemność, moc, paliwo, skrzynia, napęd, kolor, lokalizacja, "
        "numer aukcji) i przycisk **„Zobacz aukcję na poleasingowe.pl”**.",
    ])
    d.para("Komunikaty, które może zobaczyć odwiedzający:")
    d.bullets([
        "**„Oferta motocykli będzie dostępna wkrótce.”** — system nie ma jeszcze połączenia z bazą "
        "danych (zadanie dla administratora — patrz część techniczna).",
        "**„Brak motocykli spełniających kryteria.”** — żadna oferta nie pasuje do wybranych filtrów.",
        "**„Nie znaleziono tego motocykla.”** — link prowadzi do oferty, której już nie ma w bazie "
        "(np. aukcja się zakończyła).",
    ])

    d.h2("3. Skąd pochodzą dane (proces biznesowy)")
    d.numbered([
        "Automat łączy się ze stroną **poleasingowe.pl**, konkretnie z kategorią **motocykle**.",
        "Pobiera listę wszystkich aktualnych aukcji, a następnie wchodzi w każdą z nich po szczegóły "
        "i zdjęcia.",
        "Sprawdza poprawność danych (m.in. czy jest cena, marka, sensowny rok) i odrzuca wpisy błędne.",
        "Zapisuje uporządkowane dane do **osobnej bazy danych** (nie miesza się z bazą WordPressa).",
        "Wtyczka na stronie klienta **czyta** te dane i wyświetla je odwiedzającym.",
    ])
    d.para("Zdjęcia nie są kopiowane na serwer klienta — są pokazywane bezpośrednio ze źródła "
           "(tzw. **hotlink**). Oznacza to mniej miejsca na dysku, ale zależność od dostępności zdjęć w źródle.")

    d.h2("4. Aktualność danych i cykl życia oferty")
    d.para("Dane odświeżają się **automatycznie co pewien czas** (harmonogram na serwerze). To nie jest "
           "podgląd „na żywo” — między odświeżeniami może upłynąć kilka godzin.")
    d.para("Każda oferta przechodzi przez następujące stany:")
    d.bullets([
        "**Aktywna** — oferta jest dostępna w źródle i pokazywana na stronie.",
        "**Zakończona** — oferta zniknęła ze źródła (aukcja się skończyła). System **nie kasuje** jej "
        "od razu — oznacza jako zakończoną i przestaje pokazywać na liście aktywnych.",
        "**Wznowienie (relist)** — gdy ten sam motocykl (rozpoznany po numerze VIN) pojawia się ponownie "
        "jako nowa aukcja, system rozpoznaje, że to powtórka.",
    ])
    d.note("info", "Dobrze wiedzieć",
           "Ceny bywają podawane jako „netto”. Jeżeli w danych brakuje ceny, na stronie pojawia się "
           "napis „Cena do ustalenia”.")

    d.h2("5. Zarządzanie systemem przez właściciela strony")
    d.para("Do codziennej obsługi nie jest potrzebna wiedza techniczna. W panelu WordPress dostępny jest "
           "ekran **Ustawienia → Motocykle**, na którym można:")
    d.bullets([
        "sprawdzić **status połączenia z bazą** (czy system widzi dane i ile jest motocykli),",
        "przejść do podstrony **„Nasze motory”**,",
        "**wyczyścić pamięć podręczną (cache)** listy — przydatne, gdy chcemy natychmiast zobaczyć "
        "najnowsze dane bez czekania.",
    ])
    d.para("Podstronę można edytować jak każdą inną stronę WordPress. Za wyświetlanie motocykli odpowiada "
           "krótki znacznik **`[motocykle]`** wstawiony w treść strony — nie należy go usuwać.")

    d.h2("6. Najczęstsze pytania (część nietechniczna)")
    d.h3("Widzę „Oferta będzie dostępna wkrótce” — co robić?")
    d.para("Oznacza to brak konfiguracji połączenia z bazą danych. To jednorazowe zadanie dla "
           "administratora technicznego (patrz część II, rozdział „Instalacja i wdrożenie”).")
    d.h3("Lista jest pusta.")
    d.para("Możliwe przyczyny: wybrane filtry nie pasują do żadnej oferty, albo automat pobierający dane "
           "nie wykonał jeszcze importu. Warto wyczyścić filtry i sprawdzić status w Ustawienia → Motocykle.")
    d.h3("Zdjęcia się nie wyświetlają.")
    d.para("Zdjęcia pochodzą bezpośrednio ze źródła (hotlink). Jeżeli źródło je usunęło lub zablokowało, "
           "mogą się nie pokazać, mimo że reszta danych jest poprawna.")
    d.h3("Dane wyglądają na nieaktualne.")
    d.para("System odświeża dane cyklicznie, nie w czasie rzeczywistym. Można przyspieszyć pokazanie "
           "najnowszych danych, czyszcząc cache listy w panelu.")

    d.h2("7. Czego system nie robi (ograniczenia)")
    d.bullets([
        "Nie pośredniczy w licytacji ani zakupie — kieruje do oryginalnej aukcji na poleasingowe.pl.",
        "Obsługuje **wyłącznie kategorię motocykle** (nie samochody ani inne pojazdy).",
        "Dane są odświeżane cyklicznie — to nie jest podgląd na żywo.",
        "Zdjęcia są pokazywane ze źródła (hotlink), więc ich dostępność zależy od poleasingowe.pl.",
    ])

    # ============================ CZĘŚĆ II ============================
    d.part("II", "Dokumentacja dla osoby technicznej",
           "Architektura, moduły, instalacja, konfiguracja, wdrożenie i utrzymanie")

    d.h2("8. Architektura systemu")
    d.para("System składa się z trzech elementów połączonych osobną bazą danych MySQL:")
    d.bullets([
        "**Scraper (Python)** — uruchamiany cyklicznie na serwerze VPS; pobiera i przetwarza aukcje, "
        "jest **właścicielem danych** (zapisuje do bazy).",
        "**Baza MySQL `polea_*`** — osobna baza (tabele `polea_motocykle`, `polea_zdjecia`); pełni rolę "
        "warstwy pośredniej między scraperem a stroną.",
        "**Wtyczka WordPress** — czyta bazę **tylko do odczytu** i renderuje podstronę „Nasze motory”.",
    ])
    d.para("Przepływ danych: **poleasingowe.pl → scraper (pipeline działów) → MySQL `polea_*` → wtyczka → "
           "podstrona „Nasze motory”**. Projekt jest zorganizowany w „działy” z rolami agent (wykonanie) "
           "i krytyk (weryfikacja) — szczegółowy schemat powstanie w draw.io.")
    d.note("info", "Kluczowa decyzja projektowa",
           "Wtyczka NIE tworzy własnych wpisów/typów treści (CPT) w WordPressie. Aukcje są czasowe, a ich "
           "właścicielem jest scraper, dlatego front działa bezpośrednio na osobnej bazie (rozwiązanie "
           "„DB-driven”). Wtyczka łączy się przez `mysqli` z obsługą błędów, a nie przez `wpdb` — dzięki "
           "temu awaria bazy nie wywoła `wp_die` i nie wyłączy strony klienta.")

    d.h2("9. Zawartość repozytorium (branch plugin-2)")
    d.para("Poniżej wszystkie istotne pliki wraz z rolą:")
    d.table(
        ["Plik / katalog", "Rola"],
        [
            ["db/schema.sql", "Schemat osobnej bazy MySQL (tabele polea_motocykle, polea_zdjecia)."],
            ["scraper/config.py", "Konfiguracja i zmienne środowiskowe scrapera (URL, limity, dane bazy)."],
            ["scraper/dzial7_zgodnosc.py", "Bramka zgodności: robots.txt, rate-limit, anty-SSRF, limity, retry."],
            ["scraper/dzial1a_lista.py", "Dział 1A — crawl listy aukcji kategorii motocykle."],
            ["scraper/dzial1b_szczegoly.py", "Dział 1B — parsowanie strony szczegółów + zdjęcia."],
            ["scraper/dzial2_normalizacja.py", "Dział 2 — normalizacja pól, walidacja VIN, jednostki."],
            ["scraper/dzial5_audyt.py", "Dział 5 — reguły audytu (twarde/miękkie) przed zapisem."],
            ["scraper/dzial3_deduplikacja.py", "Dział 3 — deduplikacja lot_id + wykrywanie relistów po VIN."],
            ["scraper/dzial4_synchronizacja.py", "Dział 4 — upsert do bazy + reconcile (zamykanie nieobecnych)."],
            ["scraper/main.py", "Orkiestrator pipeline'u + blokada pojedynczej instancji (flock)."],
            ["scraper/requirements.txt", "Zależności: requests, PyMySQL (rdzeń działa na stdlib)."],
            ["scraper/tests/test_scraper.py", "Testy jednostkowe (16), w tym testy anty-SSRF; bez sieci i bazy."],
            ["wp-plugin/motocykle-poleasingowe/", "Katalog wtyczki WordPress (do wgrania do wp-content/plugins)."],
            ["…/motocykle-poleasingowe.php", "Główny plik wtyczki: nagłówek, stałe, hooki."],
            ["…/includes/class-db.php", "Klasa Polea_DB — połączenie i zapytania (odczyt) do bazy."],
            ["…/includes/security.php", "Sanityzacja wejścia, allowlisty, nonce/uprawnienia, cache."],
            ["…/includes/shortcode.php", "Shortcode [motocykle]: lista, szczegóły, filtry, paginacja."],
            ["…/includes/activation.php", "Tworzenie podstrony „Nasze motory” i wpięcie w menu."],
            ["…/includes/admin.php", "Ekran Ustawienia → Motocykle (status, cache, instrukcja)."],
            ["…/uninstall.php", "Sprzątanie przy usunięciu wtyczki (nie dotyka bazy polea_*)."],
            ["…/assets/front.css", "Style frontu dopasowane do motywu klienta."],
            ["docs/ARCHITEKTURA.md, docs/dzialy/*", "Dokumentacja architektury i poszczególnych działów."],
            ["docs/SECURITY-AUDIT.md", "Raport audytu bezpieczeństwa (2 iteracje utwardzania)."],
        ],
        [0.34, 0.66],
    )

    d.h2("10. Integracja ze źródłem (poleasingowe.pl)")
    d.para("Źródło serwuje **gotowy HTML po stronie serwera (bez JavaScript)**, dlatego scraper używa "
           "biblioteki `requests` i wyrażeń regularnych — **bez** przeglądarki/Playwright. Wykorzystywane "
           "adresy (endpointy źródła):")
    d.table(
        ["Zasób", "Adres (wzorzec)"],
        [
            ["Lista aukcji (kategoria motocykle)", "https://poleasingowe.pl/pl/auctions/list/pub/all/ecr_motorcycles?page=N"],
            ["Szczegóły pojedynczej aukcji", "https://poleasingowe.pl/pl/auctions/details/<slug>/<lot_id>"],
            ["Zdjęcie (hotlink)", "https://poleasingowe.pl/images/sgallery_<UUID>_75.png"],
            ["robots.txt", "https://poleasingowe.pl/robots.txt (respektowany przez scraper)"],
        ],
        [0.34, 0.66],
    )
    d.bullets([
        "`lot_id` z adresu szczegółów to **stały klucz** danej aukcji (np. `9pm53mj9`).",
        "Reklamy partnerów prowadzące do innych domen (np. `aukcje.pkoleasing.pl`) są **pomijane** — "
        "wzorzec linku wymaga ścieżki `/pl/auctions/details/`.",
        "Paginacja: parametr `?page=N`, przechodzona aż do wyczerpania nowych ofert (bezpiecznik "
        "`POLEA_MAX_PAGES`).",
    ])

    d.h2("11. Baza danych — schemat")
    d.para("Silnik **InnoDB**, kodowanie **utf8mb4**. Tabela główna `polea_motocykle` (jeden wiersz = "
           "jedna aukcja):")
    d.table(
        ["Kolumna", "Typ", "Znaczenie"],
        [
            ["lot_id", "VARCHAR(32) PK", "Stały identyfikator lotu z adresu URL."],
            ["numer_aukcji", "VARCHAR(64)", "Numer aukcji, np. 3110/BZ/AU/2026."],
            ["slug", "VARCHAR(255)", "Człon adresu URL oferty."],
            ["url", "VARCHAR(512)", "Pełny adres strony szczegółów."],
            ["marka / model / typ", "VARCHAR", "Dane pojazdu."],
            ["rok_produkcji", "SMALLINT UNSIGNED", "Rok produkcji."],
            ["data_pierwszej_rej", "DATE", "Data pierwszej rejestracji."],
            ["vin", "VARCHAR(20)", "Numer VIN (walidowany, patrz Dział 2)."],
            ["nr_rej", "VARCHAR(32)", "Numer rejestracyjny."],
            ["naped / skrzynia", "VARCHAR(64)", "Rodzaj napędu / skrzynia biegów."],
            ["moc_km", "SMALLINT UNSIGNED", "Moc w KM."],
            ["pojemnosc_ccm", "INT UNSIGNED", "Pojemność w ccm."],
            ["paliwo / kolor", "VARCHAR", "Rodzaj paliwa / kolor."],
            ["przebieg_km", "INT UNSIGNED", "Przebieg w km."],
            ["ilosc_kluczykow", "TINYINT UNSIGNED", "Liczba kluczyków."],
            ["forma_sprzedazy", "VARCHAR(64)", "Np. faktura VAT."],
            ["cena_pln", "DECIMAL(12,2)", "Aktualna cena."],
            ["cena_netto", "TINYINT(1)", "1 = cena netto."],
            ["najnizsza_cena_30d", "DECIMAL(12,2)", "Najniższa cena z 30 dni (patrz Załączniki)."],
            ["tryb_licytacji", "VARCHAR(64)", "Tryb licytacji (patrz Załączniki)."],
            ["lokalizacja", "VARCHAR(255)", "Lokalizacja pojazdu."],
            ["termin_zakonczenia", "DATETIME", "Data/godzina końca aukcji."],
            ["status", "VARCHAR(32)", "aktywna | zakonczona | usunieta (domyślnie aktywna)."],
            ["liczba_ofert", "INT UNSIGNED", "Liczba ofert (patrz Załączniki)."],
            ["uwagi", "TEXT", "Uwagi (patrz Załączniki)."],
            ["raw_hash", "CHAR(32)", "MD5 rekordu — wykrywanie zmian (nowy/zmieniony/bez zmian)."],
            ["first_seen / last_seen / updated_at", "TIMESTAMP", "Znaczniki czasu cyklu życia rekordu."],
        ],
        [0.26, 0.22, 0.52],
    )
    d.para("Indeksy: klucz główny `lot_id` oraz indeksy `marka`, `status`, `termin_zakonczenia`, `vin`, "
           "`last_seen`.")
    d.para("Tabela `polea_zdjecia` (wiele zdjęć na jeden lot):")
    d.table(
        ["Kolumna", "Typ", "Znaczenie"],
        [
            ["id", "BIGINT UNSIGNED PK", "Auto-increment."],
            ["lot_id", "VARCHAR(32)", "Powiązanie z aukcją (FK → polea_motocykle, ON DELETE CASCADE)."],
            ["image_key", "VARCHAR(64)", "UUID zdjęcia (z nazwy pliku)."],
            ["url", "VARCHAR(512)", "Pełny adres zdjęcia (hotlink)."],
            ["sort_order", "SMALLINT UNSIGNED", "Kolejność wyświetlania."],
        ],
        [0.26, 0.22, 0.52],
    )
    d.para("Unikalność `(lot_id, image_key)` zapewnia idempotentny zapis zdjęć (ponowny import nie duplikuje).")

    d.h2("12. Scraper — pipeline i moduły")
    d.para("Kolejność przetwarzania (orkiestrator `main.py`): **1A → 1B → 2 → 5 → 3 → 4**, a wszystkie "
           "żądania sieciowe przechodzą przez bramkę **Działu 7**. Rdzeń przetwarzania działa na bibliotece "
           "standardowej; `requests`/`PyMySQL` są importowane leniwie (dzięki temu testy działają bez instalacji).")

    d.h3("Dział 7 — Zgodność / bramka sieci (dzial7_zgodnosc.py)")
    d.bullets([
        "Respektuje **robots.txt** (pobierany z twardym timeoutem i limitem 512 KB).",
        "**Rate-limit**: odstęp `POLEA_DELAY` (domyślnie 2 s) + losowy `POLEA_JITTER`.",
        "**Anty-SSRF**: allowlista hostów (tylko `poleasingowe.pl` i `www.poleasingowe.pl`), blokada "
        "adresów prywatnych/lokalnych/metadanych, **ręczna walidacja każdego przekierowania** "
        "(`allow_redirects=False`).",
        "**Limit rozmiaru odpowiedzi** `POLEA_MAX_BYTES` (8 MB) czytany strumieniowo + **budżet czasu** "
        "`POLEA_MAX_TOTAL` (ochrona przed „slow-loris” i bombą dekompresyjną).",
        "Obsługa kodów: `403` → blokada, `429/503` → backoff, sieć → ponawianie do `POLEA_RETRIES`.",
        "Ignoruje proxy/.netrc ze środowiska (`trust_env=False`) — obrona anty-SSRF na współdzielonym hoście.",
    ])
    d.h3("Dział 1A — Pobieranie listy (dzial1a_lista.py)")
    d.para("Przechodzi kolejne strony listy i wyłuskuje „stuby” ofert (`lot_id`, `slug`, `url`) wzorcem "
           "`/pl/auctions/details/<slug>/<lot_id>`. Kończy, gdy strona nie przynosi nowych lotów.")
    d.h3("Dział 1B — Pobieranie szczegółów (dzial1b_szczegoly.py)")
    d.para("Parsuje pary etykieta/wartość (`auction-data-item`), `og:description` (cena), tekst statusu, "
           "lokalizację oraz listę zdjęć (`sgallery_<UUID>_75.png`). Funkcja `_clean` usuwa znaczniki HTML, "
           "znaki sterujące i przycina długość pól (obrona w głąb wobec niezaufanego HTML).")
    d.h3("Dział 2 — Normalizacja (dzial2_normalizacja.py)")
    d.bullets([
        "Mapuje polskie etykiety źródła na kolumny bazy i konwertuje jednostki (liczby, daty).",
        "**Waliduje VIN** zgodnie z ISO 3779 (17 znaków, cyfra kontrolna) — miękka flaga `vin_valid`.",
        "Nakłada zdroworozsądkowe **górne limity** (moc, pojemność, przebieg, cena) — anty-absurd/overflow.",
        "Wyznacza cenę z `og:description`, `cena_netto`, `termin_zakonczenia` i `status`.",
    ])
    d.h3("Dział 5 — Audyt (dzial5_audyt.py)")
    d.para("Reguły **twarde** (blokują publikację rekordu): brak `lot_id`, cena ≤ 0, brak marki, rok poza "
           "zakresem 1950…rok+1, nieznany status. Reguły **miękkie** (tylko flaga): niepoprawny VIN, brak "
           "zdjęć, brak terminu.")
    d.h3("Dział 3 — Deduplikacja (dzial3_deduplikacja.py)")
    d.para("Usuwa powtórzenia po `lot_id`. Wykrywa **relisty**: ten sam **pełny, poprawny VIN** pod nowym "
           "`lot_id` (nigdy nie łączy po pustym/niepoprawnym VIN); najnowszy wpis oznacza jako wiodący, "
           "pozostałe wskazują na niego polem `relist_of`.")
    d.h3("Dział 4 — Synchronizacja / zapis (dzial4_synchronizacja.py)")
    d.bullets([
        "Liczy `raw_hash` (MD5) do wykrywania zmian rekordu.",
        "**Upsert** ofert i zdjęć (`INSERT … ON DUPLICATE KEY UPDATE`) — parametryzowane zapytania.",
        "**Reconcile**: aktywne oferty nieobecne w bieżącym imporcie zmienia na `zakonczona`.",
        "Transakcja z `commit`/`rollback`; połączenie z timeoutami, wyłączonym `LOCAL INFILE` i opcjonalnym "
        "TLS (`POLEA_DB_SSL_CA`).",
    ])
    d.h3("Orkiestrator (main.py)")
    d.para("Uruchomienie modułowe: `python3 -m scraper.main`. Flagi: `--limit N` (test na N lotach), "
           "`--dry-run` (bez zapisu), `--no-lock`, `-v` (więcej logów). **Blokada pojedynczej instancji** "
           "(`flock`) zapobiega nakładaniu się przebiegów crona — drugi proces kończy się kodem 1.")

    d.h2("13. Wtyczka WordPress — moduły")
    d.h3("Plik główny (motocykle-poleasingowe.php)")
    d.para("Definiuje stałe: `POLEA_VERSION` (0.7.1), `POLEA_PAGE_OPTION`, `POLEA_CACHE_TTL` (5 minut). "
           "Rejestruje hooki aktywacji/dezaktywacji, shortcode (`init`) oraz styl frontu ładowany na żądanie.")
    d.h3("Warstwa danych — Polea_DB (includes/class-db.php)")
    d.bullets([
        "Łączy się przez `mysqli_real_connect` z **twardymi timeoutami** (connect 3 s, read 5 s) i wyłączonym "
        "`LOCAL INFILE`; **nigdy nie przerywa** działania strony (zwraca `null` przy błędzie).",
        "Wszystkie zapytania to **prepared statements** (bind_param).",
        "`query_list()` — filtry + paginacja + sortowanie po terminie; `get_one()`, `get_images()`.",
        "`first_images_map()` — pobiera miniatury dla wielu lotów jednym zapytaniem (unika problemu N+1).",
        "`distinct()` — wartości filtrów z **cache (transient, 1 h)**; `status()` — diagnostyka dla admina.",
    ])
    d.h3("Bezpieczeństwo wejścia (includes/security.php)")
    d.bullets([
        "`polea_sanitize_filters()` — allowlista pól z `$_GET`, sanityzacja, limity długości (64) i zakresów "
        "(rok 1900–2100, cena ≥ 0).",
        "`polea_constrain_filters()` — ogranicza filtry do **realnych wartości z bazy** i kubełkuje cenę "
        "(krok 500) — bramka przeciw zaśmiecaniu cache (storage DoS).",
        "`polea_current_lot_id()` — akceptuje wyłącznie `^[A-Za-z0-9]{1,32}$`.",
        "`polea_flush_cache()` — czyści transienty listy i wartości filtrów.",
    ])
    d.h3("Front — shortcode [motocykle] (includes/shortcode.php)")
    d.bullets([
        "Renderuje **listę** (siatka + filtry + paginacja) lub **szczegóły** (gdy w URL jest `?motocykl=<lot_id>`).",
        "Wynik **cache’owany** w transiencie na `POLEA_CACHE_TTL` (5 min), klucz zależny od filtrów.",
        "Całe wyjście **escapowane** (`esc_html`, `esc_url`, `esc_attr`); zdjęcia z `referrerpolicy=\"no-referrer\"`.",
        "Gdy brak konfiguracji bazy → komunikat „Oferta motocykli będzie dostępna wkrótce.” (błędy nigdy "
        "nie trafiają do klienta).",
    ])
    d.h3("Podstrona i motyw (includes/activation.php)")
    d.para("Przy aktywacji tworzy stronę **„Nasze motory”** (slug `nasze-motory`, treść `[motocykle]`) — "
           "idempotentnie — i wpina ją w menu: motyw blokowy (`wp_navigation`) lub klasyczny (lokalizacja "
           "menu). Styl dziedziczy kolory/fonty motywu (`currentColor`, `color-mix`).")
    d.h3("Panel administratora (includes/admin.php)")
    d.para("Ekran **Ustawienia → Motocykle**: status połączenia z bazą, instrukcja wpisania stałych do "
           "`wp-config.php`, link do podstrony oraz przycisk **czyszczenia cache** (zabezpieczony `nonce` i "
           "uprawnieniem `manage_options`).")
    d.h3("Deinstalacja (uninstall.php)")
    d.para("Usuwa podstronę, opcję i transienty wtyczki. **Nie dotyka** zewnętrznej bazy `polea_*` — należy "
           "ona do scrapera.")

    d.h2("14. Interfejsy i „endpointy”")
    d.note("info", "Brak własnych endpointów REST/AJAX",
           "Wtyczka świadomie NIE rejestruje własnych tras REST ani akcji AJAX — zmniejsza to powierzchnię "
           "ataku. Cała interakcja odbywa się przez shortcode i parametry URL strony oraz standardowy ekran "
           "ustawień w panelu.")
    d.para("Publiczne parametry URL podstrony:")
    d.table(
        ["Parametr URL / atrybut", "Znaczenie"],
        [
            ["?motocykl=<lot_id>", "Widok szczegółów wybranego motocykla."],
            ["?polea_marka=…", "Filtr: marka (walidowany do wartości z bazy)."],
            ["?polea_paliwo=…", "Filtr: paliwo."],
            ["?polea_rok=…", "Filtr: rok produkcji."],
            ["?polea_cena_max=… / ?polea_cena_min=…", "Filtr: cena (kubełkowana co 500 PLN)."],
            ["?polea_str=N", "Numer strony listy (paginacja)."],
            ["[motocykle ile=\"12\"]", "Atrybut shortcode: liczba kafelków na stronę (maks. 60)."],
        ],
        [0.40, 0.60],
    )
    d.para("Panel: **Ustawienia → Motocykle** (POST `polea_flush` z `nonce` `polea_flush_cache`).")

    d.h2("15. Instalacja i wdrożenie — krok po kroku (A–Z)")
    d.h3("15.1 Wymagania")
    d.bullets([
        "Serwer **VPS** z Pythonem 3 i dostępem sieciowym do poleasingowe.pl (dla scrapera).",
        "**MySQL 5.7+ / MariaDB 10.2+** (osobna baza `polea`).",
        "**WordPress 6.0+ / PHP 7.4+** z rozszerzeniem `mysqli`.",
    ])
    d.h3("15.2 Utworzenie bazy i tabel")
    d.code("CREATE DATABASE polea CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\n"
           "mysql -u root -p polea < db/schema.sql")
    d.h3("15.3 Konta MySQL (zalecany rozdział uprawnień)")
    d.para("Zalecane są **dwa** konta: jedno dla scrapera (zapis) i jedno dla wtyczki (**tylko odczyt**). "
           "Nazwy/hosty i hasła ustala zespół wdrożeniowy:")
    d.code("-- Konto scrapera (zapis danych)\n"
           "CREATE USER 'polea_scraper'@'localhost' IDENTIFIED BY 'HASLO_1';\n"
           "GRANT SELECT, INSERT, UPDATE, DELETE ON polea.* TO 'polea_scraper'@'localhost';\n\n"
           "-- Konto wtyczki WordPress (tylko odczyt)\n"
           "CREATE USER 'polea_ro'@'localhost' IDENTIFIED BY 'HASLO_2';\n"
           "GRANT SELECT ON polea.* TO 'polea_ro'@'localhost';\n"
           "FLUSH PRIVILEGES;")
    d.h3("15.4 Scraper na serwerze VPS")
    d.code("python3 -m venv .venv && . .venv/bin/activate\n"
           "pip install -r scraper/requirements.txt\n\n"
           "# poświadczenia bazy TYLKO przez zmienne środowiskowe (nigdy w kodzie):\n"
           "export POLEA_DB_HOST=127.0.0.1 POLEA_DB_NAME=polea \\\n"
           "       POLEA_DB_USER=polea_scraper POLEA_DB_PASSWORD='HASLO_1'\n\n"
           "python3 -m scraper.main --dry-run --limit 3   # test bez zapisu\n"
           "python3 -m scraper.main                        # pełny import")
    d.h3("15.5 Harmonogram (cron) — import co pewien czas")
    d.para("Przykład: import co 3 godziny (dokładną częstotliwość potwierdza zespół). Blokada `flock` jest "
           "już wbudowana w scraper, więc nakładające się przebiegi nie zaszkodzą.")
    d.code("# crontab -e  (na serwerze VPS)\n"
           "0 */3 * * *  cd /opt/polea && . .venv/bin/activate && \\\n"
           "  POLEA_DB_HOST=127.0.0.1 POLEA_DB_NAME=polea POLEA_DB_USER=polea_scraper \\\n"
           "  POLEA_DB_PASSWORD='HASLO_1' python3 -m scraper.main >> /var/log/polea.log 2>&1")
    d.para("Alternatywnie można użyć usługi **systemd + timer** (poświadczenia w `EnvironmentFile` z prawami "
           "600). Wybór metody i ścieżki logów — do potwierdzenia przez zespół.")
    d.h3("15.6 Wtyczka WordPress")
    d.numbered([
        "Skopiuj katalog `wp-plugin/motocykle-poleasingowe/` do `wp-content/plugins/` i **aktywuj** wtyczkę "
        "(automatycznie tworzy się podstrona „Nasze motory”).",
        "Dodaj poświadczenia bazy do `wp-config.php` (powyżej linii „That's all, stop editing”), używając "
        "konta **tylko do odczytu**:",
    ])
    d.code("define('POLEA_DB_HOST', '127.0.0.1');\n"
           "define('POLEA_DB_NAME', 'polea');\n"
           "define('POLEA_DB_USER', 'polea_ro');\n"
           "define('POLEA_DB_PASSWORD', 'HASLO_2');\n"
           "// opcjonalnie: define('POLEA_DB_PORT', 3306);")
    d.numbered([
        "Sprawdź **Ustawienia → Motocykle** — status powinien pokazać „Połączono. Motocykli w bazie: N”.",
    ])
    d.h3("15.7 Weryfikacja end-to-end")
    d.bullets([
        "Scraper: `python3 -m scraper.main --dry-run --limit 3` kończy się bez błędów.",
        "Testy: `python3 -m unittest scraper.tests.test_scraper -v` (16 testów).",
        "WordPress: podstrona „Nasze motory” pokazuje kafelki; filtry i szczegóły działają.",
    ])

    d.h2("16. Konfiguracja — zmienne środowiskowe scrapera")
    d.table(
        ["Zmienna", "Domyślnie", "Opis"],
        [
            ["POLEA_DB_HOST", "127.0.0.1", "Host bazy MySQL."],
            ["POLEA_DB_PORT", "3306", "Port bazy."],
            ["POLEA_DB_USER", "polea", "Użytkownik bazy (konto zapisu)."],
            ["POLEA_DB_PASSWORD", "(puste)", "Hasło — wymagane, tylko przez env."],
            ["POLEA_DB_NAME", "polea", "Nazwa bazy."],
            ["POLEA_DB_CONNECT_TIMEOUT", "10", "Timeout połączenia [s]."],
            ["POLEA_DB_READ_TIMEOUT", "30", "Timeout odczytu [s]."],
            ["POLEA_DB_WRITE_TIMEOUT", "30", "Timeout zapisu [s]."],
            ["POLEA_DB_SSL_CA", "(brak)", "Ścieżka do certyfikatu CA — włącza TLS do bazy."],
            ["POLEA_USER_AGENT", "PoleasingoweImporter/0.1 (+kontakt)", "Nagłówek User-Agent scrapera."],
            ["POLEA_DELAY / POLEA_JITTER", "2.0 / 1.0", "Odstęp między żądaniami + losowy jitter [s]."],
            ["POLEA_RETRIES", "3", "Liczba ponowień przy błędach sieci."],
            ["POLEA_TIMEOUT", "30", "Timeout pojedynczego żądania HTTP [s]."],
            ["POLEA_MAX_PAGES", "50", "Bezpiecznik paginacji listy."],
            ["POLEA_MAX_REDIRECTS", "3", "Limit przekierowań (anty-SSRF)."],
            ["POLEA_MAX_BYTES", "8388608", "Limit rozmiaru odpowiedzi (8 MB)."],
            ["POLEA_MAX_TOTAL", "60", "Budżet czasu na jedną odpowiedź [s]."],
            ["POLEA_LOCK", "/tmp/polea_import.lock", "Plik blokady pojedynczej instancji."],
            ["POLEA_TRUST_ENV", "0", "1 = ufaj proxy/.netrc ze środowiska (domyślnie nie)."],
        ],
        [0.30, 0.20, 0.50],
    )
    d.para("Stałe w `wp-config.php` (wtyczka): `POLEA_DB_HOST`, `POLEA_DB_NAME`, `POLEA_DB_USER`, "
           "`POLEA_DB_PASSWORD`, opcjonalnie `POLEA_DB_PORT`.")

    d.h2("17. Bezpieczeństwo (podsumowanie)")
    d.para("Pełny raport: `docs/SECURITY-AUDIT.md` (dwie iteracje utwardzania, wynik ~9,3/10). Powierzchnia "
           "ataku jest wąska — brak REST/AJAX, uploadu plików, `eval`/`unserialize`.")
    d.bullets([
        "**Wtyczka**: prepared statements, escapowanie wyjścia, `nonce` + uprawnienia w adminie, allowlisty "
        "i limity wejścia, `mysqli` zamiast `wpdb` (odporność na awarię bazy), `LOCAL INFILE` wyłączone, "
        "hotlink z `referrerpolicy=no-referrer`.",
        "**Scraper**: ochrona anty-SSRF (allowlista hostów, blokada IP prywatnych, walidacja przekierowań), "
        "limity rozmiaru i czasu odpowiedzi, `flock`, zaktualizowane zależności (CVE).",
    ])
    d.note("warn", "Zalecenia po stronie serwera (do wdrożenia przez administratora)",
           "Konto MySQL tylko-SELECT dla wtyczki • TLS do bazy, jeśli baza jest zdalna (POLEA_DB_SSL_CA) • "
           "nagłówki bezpieczeństwa HTTP na serwerze WWW • monitoring importu i logów. Szczegóły w "
           "docs/SECURITY-AUDIT.md (pkt 5).")

    d.h2("18. Utrzymanie i eksploatacja")
    d.bullets([
        "**Cache**: lista 5 min (transient), wartości filtrów 1 h. Ręczne czyszczenie: Ustawienia → Motocykle.",
        "**Aktualizacja wtyczki**: podbicie wersji unieważnia cache zasobów (CSS) po stronie przeglądarki.",
        "**Kopie zapasowe**: bazę `polea_*` można odtworzyć ponownym importem (źródło jest „prawdą”); bazę "
        "WordPressa backupuje się standardowo.",
        "**Monitoring**: warto obserwować logi scrapera oraz status w panelu (liczba motocykli, reconcile).",
        "**Retencja**: zakończone aukcje pozostają w bazie ze statusem `zakonczona` (polityka kasowania — "
        "do potwierdzenia).",
    ])
    d.para("Diagnostyka najczęstszych sytuacji:")
    d.table(
        ["Objaw", "Prawdopodobna przyczyna", "Działanie"],
        [
            ["„Oferta dostępna wkrótce”", "Brak stałych POLEA_DB_* w wp-config.php", "Uzupełnić konfigurację bazy."],
            ["„Motocykli w bazie: 0”", "Scraper nie wykonał importu", "Uruchomić import; sprawdzić cron i logi."],
            ["Brak tabeli polea_motocykle", "Nie wgrano schematu", "Wykonać db/schema.sql."],
            ["Zdjęcia się nie ładują", "Hotlink zablokowany przez źródło", "Zweryfikować dostępność zdjęć w źródle."],
            ["Stare dane mimo importu", "Cache listy (5 min)", "Wyczyścić cache w panelu."],
            ["Import się nie uruchamia", "Aktywna blokada flock innego przebiegu", "Sprawdzić, czy poprzedni proces nie wisi."],
        ],
        [0.28, 0.36, 0.36],
    )

    d.h2("19. Wydajność")
    d.bullets([
        "Cache listy (5 min) i wartości filtrów (1 h) ograniczają liczbę zapytań do bazy.",
        "`first_images_map()` pobiera miniatury zbiorczo — brak problemu N+1 na liście.",
        "Indeksy bazy (`marka`, `status`, `termin`, `vin`, `last_seen`) przyspieszają filtrowanie i sortowanie.",
        "Scraper stosuje rate-limit (2 s + jitter) i bezpiecznik `POLEA_MAX_PAGES`, by nie obciążać źródła.",
    ])

    # ============================ CZĘŚĆ III ============================
    d.part("III", "Załączniki i informacje wymagające potwierdzenia",
           "Otwarte decyzje wdrożeniowe, słownik pojęć, odnośniki")

    d.h2("20. Wymaga potwierdzenia przez zespół projektowy")
    d.para("Poniższych elementów **nie da się jednoznacznie ustalić z samego kodu** — wymagają decyzji lub "
           "potwierdzenia zespołu:")
    d.bullets([
        "**Częstotliwość importu (cron)** — kod nie narzuca harmonogramu; założono „co kilka godzin”.",
        "**Środowisko bazy** — czy baza jest lokalna (127.0.0.1) czy zdalna; jeśli zdalna, czy wymagany TLS "
        "(`POLEA_DB_SSL_CA`) oraz jakie hosty/nazwy kont MySQL.",
        "**Rozdział kont MySQL** (zapis vs tylko-SELECT) — zalecany, ale to decyzja wdrożeniowa.",
        "**Docelowy User-Agent** scrapera i adres kontaktowy w nim zawarty.",
        "**Pola obecnie niewypełniane przez scraper**: `najnizsza_cena_30d`, `tryb_licytacji`, `liczba_ofert`, "
        "`uwagi` — kolumny istnieją w schemacie, ale pipeline ich nie ustawia. Czy mają być uzupełniane?",
        "**Fallback zdjęć do Media Library** — wspomniany w decyzjach projektowych, nie zaimplementowany "
        "(obecnie wyłącznie hotlink).",
        "**Logi i monitoring** — docelowa lokalizacja logów scrapera, alerty, retencja logów.",
        "**Specyfikacja i dostęp do VPS** — hosting, wersja systemu, dostęp SSH, katalog wdrożenia.",
        "**Polityka retencji** zakończonych aukcji (czy i kiedy usuwać rekordy `zakonczona`).",
        "**CI/CD oraz skrypty deploymentu** — w branchu plugin-2 **nie ma** dedykowanych plików CI ani "
        "skryptów deploymentu; jeśli są wymagane, należy je ustalić i utworzyć.",
    ])
    d.note("warn", "Uwaga o „skryptach deploymentu”",
           "W treści zlecenia wspomniano o skryptach deploymentu. W obecnym stanie repozytorium (branch "
           "plugin-2) takie skrypty nie występują jako pliki — wdrożenie opisano ręcznie w rozdziale 15. "
           "Automatyzację wdrożenia (np. systemd/Ansible) należy potwierdzić z zespołem.")

    d.h2("21. Słownik pojęć")
    d.table(
        ["Pojęcie", "Znaczenie"],
        [
            ["lot_id", "Stały identyfikator aukcji z adresu URL — klucz główny rekordu."],
            ["relist (wznowienie)", "Ponowne wystawienie tego samego pojazdu (rozpoznanie po VIN) jako nowej aukcji."],
            ["reconcile", "Zamknięcie ofert, które zniknęły ze źródła (status → zakonczona)."],
            ["raw_hash", "Skrót MD5 rekordu do wykrywania zmian (nowy / zmieniony / bez zmian)."],
            ["hotlink", "Wyświetlanie zdjęcia bezpośrednio ze źródła, bez kopiowania na serwer klienta."],
            ["upsert", "INSERT lub UPDATE — wstaw nowy albo zaktualizuj istniejący rekord."],
            ["transient", "Wbudowany mechanizm pamięci podręcznej WordPressa z czasem ważności."],
            ["shortcode", "Znacznik w treści strony (tu: [motocykle]) renderowany przez wtyczkę."],
            ["SSRF", "Atak zmuszający serwer do żądań do zasobów wewnętrznych — tu blokowany allowlistą."],
            ["flock", "Blokada pliku zapewniająca uruchomienie tylko jednej instancji importu naraz."],
        ],
        [0.24, 0.76],
    )

    d.h2("22. Odnośniki (dokumentacja w repozytorium)")
    d.bullets([
        "`docs/ARCHITEKTURA.md` — architektura działy/agenci/krytycy.",
        "`docs/dzialy/*.md` — szczegółowy opis każdego działu (1A, 1B, 2, 3, 4, 5, 6, 7, 8, 9, 10).",
        "`docs/SECURITY-AUDIT.md` — pełny raport audytu bezpieczeństwa i utwardzania.",
        "`docs/klient/pdf/skad-pochodza-dane.pdf`, `jak-to-dziala.pdf` — materiały poglądowe dla klienta.",
        "`scraper/README.md`, `wp-plugin/motocykle-poleasingowe/README.md` — skrócone instrukcje modułów.",
    ])
    d.note("info", "Diagramy",
           "Zgodnie z ustaleniami dokument nie zawiera diagramów — schematy architektury i przepływu danych "
           "zostaną wykonane ręcznie w draw.io na podstawie rozdziałów 8–14.")


# --------------------------------------------------------------------- montaż
def main():
    os.makedirs(OUTDIR, exist_ok=True)
    d = Doc()
    build_body(d)
    d.finish()
    body_pages = d.pages
    toc_entries = d.toc

    cover = [{"frags": build_cover(), "label": "", "cover": True}]
    n_title = len(cover)
    # dwuprzebiegowe TOC (liczba stron TOC stabilna niezależnie od numerów)
    tmp = build_toc(toc_entries, base_offset=0)
    t_pages = len(tmp)
    toc_frag_pages = build_toc(toc_entries, base_offset=n_title + t_pages)
    toc_pages = [{"frags": f, "label": "Spis treści", "cover": False} for f in toc_frag_pages]

    all_pages = cover + toc_pages + [{"frags": p["frags"], "label": p["label"], "cover": False} for p in body_pages]
    total = len(all_pages)

    tmpdir = tempfile.mkdtemp(dir=OUTDIR, prefix=".build_")
    pdfs = []
    try:
        for i, pg in enumerate(all_pages, 1):
            svg = page_svg(pg["frags"], pg["label"], i, total, cover=pg.get("cover", False))
            sp = os.path.join(tmpdir, "p%03d.svg" % i)
            pp = os.path.join(tmpdir, "p%03d.pdf" % i)
            open(sp, "w", encoding="utf-8").write(svg)
            subprocess.run(["rsvg-convert", "-f", "pdf", "-o", pp, sp], check=True)
            pdfs.append(pp)
        merged = os.path.join(tmpdir, "merged.pdf")
        subprocess.run(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite",
                        "-dCompatibilityLevel=1.5", "-sOutputFile=" + merged] + pdfs, check=True)
        shutil.move(merged, OUT)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    print("OK ->", OUT, "| stron:", total)


if __name__ == "__main__":
    main()
