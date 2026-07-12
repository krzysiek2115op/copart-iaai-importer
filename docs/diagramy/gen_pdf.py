# SPDX-License-Identifier: GPL-2.0-or-later
"""Odtwarza 3 diagramy (.drawio) jako PDF przez SVG -> rsvg-convert.
Ta sama treść/układ/kolory co pliki .drawio; służy do podglądu i druku."""
import os
import subprocess

OUT = os.path.join(os.path.dirname(__file__), "pdf")
os.makedirs(OUT, exist_ok=True)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg_open(w, h):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="DejaVu Sans, Arial, sans-serif">'
        '<defs>'
        '<marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">'
        '<path d="M0,0 L8,3 L0,6 z" fill="#555"/></marker>'
        '<marker id="arro" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">'
        '<path d="M0,0 L8,3 L0,6" fill="none" stroke="#9673a6"/></marker>'
        '</defs>'
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="#ffffff"/>'
    )


def box(x, y, w, h, lines, fill="#ffffff", stroke="#666666", size=12,
        align="center", dashed=False, rx=8, bold_first=False, container=False):
    dash = ' stroke-dasharray="6 4"' if dashed else ''
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" ry="{rx}" '
         f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"{dash}/>')
    lh = size * 1.4
    if container:  # etykieta w lewym-górnym rogu
        s += (f'<text x="{x+10}" y="{y+18}" font-size="{size}" font-weight="bold" '
              f'fill="#333">{esc(lines[0])}</text>')
        return s
    if align == "left":
        tx = x + 10
        anchor = "start"
        ty = y + 18
    else:
        tx = x + w / 2
        anchor = "middle"
        total = len(lines) * lh
        ty = y + h / 2 - total / 2 + size
    for i, ln in enumerate(lines):
        fw = 'bold' if (bold_first and i == 0) else 'normal'
        s += (f'<text x="{tx}" y="{ty + i*lh:.1f}" font-size="{size}" '
              f'font-weight="{fw}" text-anchor="{anchor}" fill="#222">{esc(ln)}</text>')
    return s


def title(x, y, w, s, size=18):
    return (f'<text x="{x+w/2}" y="{y}" font-size="{size}" font-weight="bold" '
            f'text-anchor="middle" fill="#111">{esc(s)}</text>')


def line(pts, color="#555", dashed=False, arrow=True, marker="arr"):
    dash = ' stroke-dasharray="6 4"' if dashed else ''
    d = "M " + " L ".join(f"{px},{py}" for px, py in pts)
    mk = f' marker-end="url(#{marker})"' if arrow else ''
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.6"{dash}{mk}/>')


def label(x, y, s, size=11, color="#333"):
    w = len(s) * size * 0.55
    return (f'<rect x="{x-w/2-3}" y="{y-size}" width="{w+6}" height="{size+6}" fill="#ffffff" opacity="0.85"/>'
            f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="middle" fill="{color}">{esc(s)}</text>')


# ---------------------------------------------------------------- 1. nietechniczny
def d1():
    W, H = 820, 660
    s = svg_open(W, H)
    s += title(0, 40, W, "Jak działa system „Nasze motory”", 20)
    cx = 410
    s += box(265, 70, 290, 64, ["1. Portal poleasingowe.pl", "Aukcje motocykli poleasingowych"],
             "#dae8fc", "#6c8ebf", 13, bold_first=True)
    s += box(265, 185, 290, 78, ["2. Nasz system (na serwerze)", "Co kilka godzin automatycznie pobiera", "i porządkuje oferty"],
             "#d5e8d4", "#82b366", 13, bold_first=True)
    s += box(265, 305, 290, 64, ["3. Baza danych ofert", "Aktualne motocykle w jednym miejscu"],
             "#fff2cc", "#d6b656", 13, bold_first=True)
    s += box(265, 420, 290, 86, ["4. Twoja strona WWW", "Podstrona „Nasze motory” —", "gotowa lista z filtrami i zdjęciami"],
             "#e1d5e7", "#9673a6", 13, bold_first=True)
    s += box(600, 420, 200, 86, ["Zdjęcia pokazują się wprost", "z poleasingowe.pl", "(bez kopiowania)"],
             "#f5f5f5", "#999999", 11, dashed=True)
    s += line([(cx, 134), (cx, 185)]) + label(cx + 42, 165, "pobieranie")
    s += line([(cx, 263), (cx, 305)]) + label(cx + 30, 289, "zapis")
    s += line([(cx, 369), (cx, 420)]) + label(cx + 45, 399, "wyświetlanie")
    s += line([(555, 463), (600, 463)], "#999", dashed=True, arrow=False)
    s += (f'<text x="{W/2}" y="560" font-size="13" font-style="italic" '
          f'text-anchor="middle" fill="#444">Wszystko dzieje się automatycznie — nie musisz nic robić ręcznie.</text>')
    return s + "</svg>"


# ------------------------------------------------------------------- 2. techniczny
def d2():
    W, H = 1180, 770
    s = svg_open(W, H)
    s += title(0, 30, W, "Plugin 2 — architektura i przepływ danych", 18)
    # kontenery
    s += box(40, 120, 350, 470, ["VPS — scraper Python 3  (CRON + flock: 1 instancja)"], "none", "#888", 12, container=True)
    s += box(440, 210, 250, 220, ["MySQL — osobna baza polea_*"], "none", "#888", 12, container=True)
    s += box(740, 120, 390, 470, ["WordPress — wtyczka (PHP, tylko odczyt)"], "none", "#888", 12, container=True)
    # source
    s += box(40, 46, 210, 50, ["poleasingowe.pl", "źródło (serwerowy HTML)"], "#ffe6cc", "#d79b00", 12, bold_first=True)
    # pipeline
    bl = "#dae8fc"; br_ = "#6c8ebf"
    s += box(70, 152, 290, 40, ["Dział 1A — Lista (crawl, paginacja)"], bl, br_, 11)
    s += box(70, 202, 290, 40, ["Dział 1B — Szczegóły + zdjęcia"], bl, br_, 11)
    s += box(70, 252, 290, 40, ["Dział 2 — Normalizacja (VIN, jednostki)"], bl, br_, 11)
    s += box(70, 302, 290, 40, ["Dział 5 — Audyt (reguły twarde/miękkie)"], bl, br_, 11)
    s += box(70, 352, 290, 40, ["Dział 3 — Deduplikacja (lot_id, VIN)"], bl, br_, 11)
    s += box(70, 402, 290, 46, ["Dział 4 — Synchronizacja", "upsert + reconcile (próg)"], "#d5e8d4", "#82b366", 11, bold_first=True)
    s += box(70, 470, 290, 58, ["Brama 7 — robots, rate-limit, anty-SSRF", "(allowlist + IP), TLS verify, limity"], "#f8cecc", "#b85450", 10, dashed=True)
    for y0 in (192, 242, 292, 342):
        s += line([(215, y0), (215, y0 + 10)])
    # MySQL tables
    s += box(460, 252, 210, 44, ["polea_motocykle (PK lot_id)"], "#fff2cc", "#d6b656", 11)
    s += box(460, 306, 210, 44, ["polea_zdjecia (FK lot_id)"], "#fff2cc", "#d6b656", 11)
    s += box(460, 362, 210, 44, ["polea_ro: tylko SELECT", "(least privilege dla WP)"], "#f5f5f5", "#999", 9, dashed=True)
    # WP
    pl = "#e1d5e7"; pr = "#9673a6"
    s += box(765, 152, 340, 48, ["Polea_DB — mysqli, prepared,", "timeouty, LOCAL INFILE off"], pl, pr, 11, bold_first=True)
    s += box(765, 210, 340, 40, ["shortcode [motocykle] — lista + szczegóły"], pl, pr, 11)
    s += box(765, 258, 340, 48, ["seo.php — meta/OG/JSON-LD,", "canonical, ładne URL-e, sitemap"], pl, pr, 11)
    s += box(765, 314, 340, 42, ["admin.php — status + flush cache (nonce)"], pl, pr, 11)
    s += box(765, 364, 340, 36, ["Cache — transient 5 min"], "#f5f5f5", "#999", 10, dashed=True)
    s += box(765, 410, 340, 50, ["Podstrona „Nasze motory”", "siatka + filtry + szczegóły"], "#d5e8d4", "#82b366", 11, bold_first=True)
    s += box(765, 640, 220, 46, ["Przeglądarka użytkownika"], "#ffe6cc", "#d79b00", 12)
    # edges
    s += line([(145, 96), (145, 152)], "#d79b00") + label(150, 128, "HTTPS", 10, "#b8860b")
    s += line([(360, 425), (460, 300), (460, 296)], "#82b366") + label(410, 360, "INSERT/UPDATE", 10, "#4a7a3a")
    s += line([(765, 176), (670, 260), (670, 274)], "#9673a6") + label(700, 210, "SELECT", 10, "#6a4a86")
    s += line([(875, 640), (875, 460)], "#555") + label(905, 560, "HTTP", 10)
    s += line([(985, 663), (1150, 663), (1150, 71), (250, 71)], "#999", dashed=True) + label(700, 655, "zdjęcia (hotlink)", 10, "#777")
    return s + "</svg>"


# ------------------------------------------------------------------ 3. schema bazy
def d3():
    W, H = 900, 600
    s = svg_open(W, H)
    s += title(0, 34, W, "Schemat bazy polea_*  (MySQL / InnoDB / utf8mb4)", 18)
    moto = ["polea_motocykle", "──────────────",
            "PK  lot_id VARCHAR(32)", "numer_aukcji, slug, url",
            "marka, model, typ, rok_produkcji", "data_pierwszej_rej, vin, nr_rej",
            "naped, skrzynia, moc_km, pojemnosc_ccm", "paliwo, przebieg_km, kolor, ilosc_kluczykow",
            "forma_sprzedazy", "cena_pln, cena_netto, najnizsza_cena_30d",
            "tryb_licytacji, lokalizacja, termin_zakonczenia", "status, liczba_ofert, uwagi",
            "raw_hash, relist_of", "first_seen, last_seen, updated_at",
            "──────────────", "INDEX: marka · status · (status,termin) · vin · last_seen"]
    s += box(60, 70, 360, 380, moto, "#dae8fc", "#6c8ebf", 11, align="left", rx=4, bold_first=True)
    zdj = ["polea_zdjecia", "──────────────",
           "PK  id BIGINT AUTO_INCREMENT", "FK  lot_id VARCHAR(32)",
           "image_key VARCHAR(64)", "url VARCHAR(512)", "sort_order SMALLINT",
           "──────────────", "UNIQUE (lot_id, image_key)", "INDEX  lot_id"]
    s += box(540, 150, 300, 220, zdj, "#fff2cc", "#d6b656", 11, align="left", rx=4, bold_first=True)
    s += line([(420, 250), (540, 250)], "#333")
    s += label(480, 242, "1 : N", 12, "#111")
    s += (f'<text x="480" y="272" font-size="10" text-anchor="middle" fill="#555">ON DELETE CASCADE</text>')
    s += box(60, 500, 780, 60,
             ["Właściciel zapisu: scraper (upsert ON DUPLICATE KEY). WordPress: tylko odczyt (SELECT).",
              "Zdjęcia = hotlink (url) — pliki nie są przechowywane w bazie."],
             "#f5f5f5", "#999", 11, align="left", dashed=True)
    return s + "</svg>"


def render(name, svg):
    svg_path = os.path.join(OUT, name + ".svg")
    pdf_path = os.path.join(OUT, name + ".pdf")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    subprocess.run(["rsvg-convert", "-f", "pdf", "-o", pdf_path, svg_path], check=True)
    return pdf_path


def main():
    pdfs = [
        render("plugin2-nietechniczny", d1()),
        render("plugin2-techniczny", d2()),
        render("plugin2-schema-bazy", d3()),
    ]
    combined = os.path.join(OUT, "plugin2-diagramy-wszystkie.pdf")
    subprocess.run(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite",
                    "-sOutputFile=" + combined, *pdfs], check=True)
    for p in pdfs + [combined]:
        print("PDF:", p)


if __name__ == "__main__":
    main()
