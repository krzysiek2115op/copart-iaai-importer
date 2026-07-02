#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generator ŁADNEGO PDF instrukcji klienta (offline).

Buduje kolorowe strony A4 jako SVG (font DejaVu Sans), renderuje każdą przez
rsvg-convert do jednostronicowego PDF i scala ghostscriptem w jeden dokument.
Zależności systemowe: rsvg-convert, gs (ghostscript). Bez przeglądarki/pandoc.

Uruchom:  python3 docs/klient/gen_instrukcja_pdf.py
Wynik:    docs/klient/Instrukcja-klienta.pdf
"""
from __future__ import annotations
import html
import os
import subprocess
import tempfile
from pathlib import Path

# ---- Wymiary A4 w punktach ------------------------------------------------
PW, PH = 595.28, 841.89
MX = 46                      # margines lewy/prawy
CONTENT_W = PW - 2 * MX
TOP = 92                     # start treści pod nagłówkiem strony
BOTTOM = 792                 # dolna granica treści (nad stopką)

# ---- Kolory ---------------------------------------------------------------
BLUE = "#1f4fd8"
DARK = "#12203a"
GREEN = "#16a34a"
GRAYBG = "#f1f5f9"
GRAYBORDER = "#d7dee7"
CALLBG = "#eef4ff"
CALLBORDER = "#1f4fd8"
MUTED = "#5b6b82"

# ---- Szacowanie szerokości tekstu (DejaVu Sans, wrap zachowawczy) ---------
_NARROW = set("ijltfr.,:;'!|()[]{} -")
_WIDE = set("mwMW@%—–")


def _cw(c: str, size: float) -> float:
    if c in _NARROW:
        return 0.30 * size
    if c in _WIDE:
        return 0.90 * size
    if c.isupper():
        return 0.70 * size
    return 0.54 * size


def tw(s: str, size: float) -> float:
    return sum(_cw(c, size) for c in s)


def wrap(text: str, size: float, maxw: float) -> list[str]:
    out: list[str] = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for w in words:
            t = (cur + " " + w).strip()
            if tw(t, size) <= maxw or not cur:
                cur = t
            else:
                out.append(cur)
                cur = w
        out.append(cur)
    return out or [""]


def esc(s: str) -> str:
    return html.escape(s, quote=True)


# ---- Prymitywy SVG --------------------------------------------------------
def text(x, y, s, size=10.5, color=DARK, weight="normal", anchor="start", family="DejaVu Sans"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" '
            f'font-size="{size}" fill="{color}" font-weight="{weight}" '
            f'text-anchor="{anchor}">{esc(s)}</text>')


def rect(x, y, w, h, fill, rx=8, stroke="none", sw=1):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


# ==========================================================================
# TREŚĆ — struktura bloków (ten sam materiał co PRZECZYTAJ-MNIE-NAJPIERW.md)
# ==========================================================================
LH = 14.5   # interlinia body


def block_h(b) -> float:
    k = b[0]
    if k == "h1":
        return 40
    if k == "h2":
        lines = wrap(b[1], 13, CONTENT_W)
        return 10 + 17 * len(lines) + 6
    if k == "p":
        return len(wrap(b[1], 10.5, CONTENT_W)) * LH + 8
    if k == "bullet":
        h = 0
        for it in b[1]:
            h += len(wrap(it, 10.5, CONTENT_W - 16)) * LH
        return h + 8
    if k == "flow":
        return 40
    if k == "step":
        inner = CONTENT_W - 60
        lines = 0
        for ln in b[3]:
            lines += len(wrap(ln, 10.5, inner))
        return 30 + lines * LH + 14
    if k == "callout":
        inner = CONTENT_W - 34
        lines = 0
        for ln in b[2]:
            lines += len(wrap(ln, 10, inner))
        return 14 + lines * 13.5 + 14
    if k == "faq":
        q = len(wrap("P: " + b[1], 10.5, CONTENT_W))
        a = len(wrap("O: " + b[2], 10.5, CONTENT_W))
        return (q + a) * LH + 12
    if k == "gloss":
        h = 0
        for term, dfn in b[1]:
            h += len(wrap(f"{term} — {dfn}", 10, CONTENT_W - 14)) * 13.5
        return h + 8
    if k == "space":
        return b[1]
    return 0


def draw_block(b, x, y) -> tuple[str, float]:
    """Zwraca (svg, wysokosc). Rysuje blok od górnej krawędzi y."""
    k = b[0]
    s = []
    if k == "h1":
        s.append(rect(x, y + 4, CONTENT_W, 30, BLUE, rx=8))
        s.append(text(x + 14, y + 24, b[1], size=15, color="#ffffff", weight="bold"))
        return "".join(s), 40
    if k == "h2":
        yy = y + 14
        for ln in wrap(b[1], 13, CONTENT_W):
            s.append(text(x, yy, ln, size=13, color=BLUE, weight="bold"))
            yy += 17
        return "".join(s), 10 + 17 * len(wrap(b[1], 13, CONTENT_W)) + 6
    if k == "p":
        yy = y + 11
        for ln in wrap(b[1], 10.5, CONTENT_W):
            s.append(text(x, yy, ln, size=10.5, color=DARK))
            yy += LH
        return "".join(s), (yy - y) + 8 - LH + LH
    if k == "bullet":
        yy = y + 11
        for it in b[1]:
            first = True
            for ln in wrap(it, 10.5, CONTENT_W - 16):
                if first:
                    s.append(text(x + 3, yy, "•", size=10.5, color=BLUE, weight="bold"))
                    first = False
                s.append(text(x + 16, yy, ln, size=10.5, color=DARK))
                yy += LH
        return "".join(s), (yy - y) + 8
    if k == "flow":
        s.append(rect(x, y + 4, CONTENT_W, 28, GRAYBG, rx=6, stroke=GRAYBORDER))
        s.append(text(PW / 2, y + 22, b[1], size=10.5, color=DARK, weight="bold",
                      anchor="middle", family="DejaVu Sans Mono"))
        return "".join(s), 40
    if k == "step":
        inner = CONTENT_W - 60
        lines = []
        for ln in b[3]:
            lines += wrap(ln, 10.5, inner)
        h = 30 + len(lines) * LH + 14
        s.append(rect(x, y, CONTENT_W, h, "#ffffff", rx=10, stroke=GRAYBORDER))
        s.append(rect(x, y, 6, h, BLUE, rx=3))
        # numer w kółku
        s.append(f'<circle cx="{x+34:.1f}" cy="{y+26:.1f}" r="15" fill="{BLUE}"/>')
        s.append(text(x + 34, y + 30, str(b[1]), size=13, color="#ffffff",
                      weight="bold", anchor="middle"))
        s.append(text(x + 58, y + 24, b[2], size=12, color=DARK, weight="bold"))
        yy = y + 46
        for ln in lines:
            s.append(text(x + 58, yy, ln, size=10.5, color=DARK))
            yy += LH
        return "".join(s), h
    if k == "callout":
        inner = CONTENT_W - 34
        lines = []
        for ln in b[2]:
            lines += wrap(ln, 10, inner)
        h = 14 + len(lines) * 13.5 + 14
        s.append(rect(x, y, CONTENT_W, h, CALLBG, rx=8, stroke=CALLBORDER))
        s.append(rect(x, y, 5, h, CALLBORDER, rx=2))
        yy = y + 20
        for i, ln in enumerate(lines):
            w = "bold" if (i == 0 and b[1]) else "normal"
            s.append(text(x + 18, yy, ln, size=10, color=DARK, weight=w))
            yy += 13.5
        return "".join(s), h
    if k == "faq":
        yy = y + 12
        for ln in wrap("P: " + b[1], 10.5, CONTENT_W):
            s.append(text(x, yy, ln, size=10.5, color=BLUE, weight="bold"))
            yy += LH
        for ln in wrap("O: " + b[2], 10.5, CONTENT_W):
            s.append(text(x, yy, ln, size=10.5, color=DARK))
            yy += LH
        return "".join(s), (yy - y) + 12
    if k == "gloss":
        yy = y + 11
        for term, dfn in b[1]:
            first = True
            for ln in wrap(f"{term} — {dfn}", 10, CONTENT_W - 14):
                if first:
                    s.append(text(x + 2, yy, "▪", size=9, color=GREEN))
                    first = False
                # pogrub sam termin w pierwszej linii
                s.append(text(x + 14, yy, ln, size=10, color=DARK))
                yy += 13.5
        return "".join(s), (yy - y) + 8
    if k == "space":
        return "", b[1]
    return "", 0


CONTENT = [
    ("h1", "Jak to działa (w skrócie)"),
    ("p", "System sam pobiera samochody z serwisu aukcyjnego IAAI (zdjęcia i dane) i pokazuje je na Twojej stronie WordPress — automatycznie, przez całą dobę. Gdy pojawia się nowe auto, trafia na stronę; gdy znika z aukcji, znika też u Ciebie."),
    ("flow", "IAAI.com  →  Program zbierający (24/7)  →  Baza danych  →  Twoja strona WWW"),
    ("bullet", [
        "Program zbierający pilnuje IAAI i pobiera nowe auta.",
        "Baza danych przechowuje auta (ta sama, na której stoi WordPress).",
        "Wtyczka WordPress bierze auta z bazy i pokazuje je na stronie.",
    ]),
    ("callout", True, [
        "Dwie części, dwa poziomy trudności:",
        "• Wgranie wtyczki i pokazanie aut — zrobisz sam, to klikanie.",
        "• Automatyzacja na serwerze — bardziej techniczna; jest instalator „jednym",
        "  poleceniem”, a w razie potrzeby przekaż ją administratorowi hostingu.",
    ]),
    ("h2", "Co dostajesz w paczce"),
    ("bullet", [
        "wp-plugin/iaai-importer/ — WTYCZKA do WordPress (pokazuje auta).",
        "scraper/ — PROGRAM ZBIERAJĄCY (pobiera auta z IAAI).",
        "deploy/ — INSTALATOR automatyzacji (install.sh) i ustawienia.",
        "docs/klient/ — instrukcje (ten dokument oraz wersje etapowe).",
    ]),
    ("h2", "Czego potrzebujesz"),
    ("bullet", [
        "WordPress na własnym hostingu (Twoja strona).",
        "Do pełnej automatyzacji: serwer VPS z dostępem do terminala (SSH). Uwaga:"
        " najtańszy hosting współdzielony nie wystarczy do programu zbierającego.",
    ]),

    ("h1", "Instalacja wtyczki krok po kroku"),
    ("step", 1, "Rozpakuj otrzymaną paczkę", [
        "Kliknij prawym na plik ZIP → „Wyodrębnij/Rozpakuj”. Powstanie folder",
        "z zawartością wypisaną wyżej.",
    ]),
    ("step", 2, "Przygotuj plik wtyczki do wgrania", [
        "WordPress wgrywa wtyczki jako ZIP. Wejdź do folderu wp-plugin/, kliknij",
        "prawym na folder iaai-importer → „Wyślij do” → „Folder skompresowany (ZIP)”.",
        "Powstanie iaai-importer.zip — ten plik wgrasz do WordPress.",
        "(Jeśli w paczce jest już gotowy iaai-importer.zip — użyj go.)",
    ]),
    ("step", 3, "Zaloguj się do panelu WordPress", [
        "W przeglądarce wejdź na: https://twojastrona.pl/wp-admin",
        "Zaloguj się loginem i hasłem administratora.",
    ]),
    ("step", 4, "Wgraj wtyczkę", [
        "Menu po lewej: Wtyczki → Dodaj nową wtyczkę.",
        "Na górze: „Wyślij wtyczkę na serwer” → „Wybierz plik” → wskaż iaai-importer.zip",
        "→ „Zainstaluj teraz”.",
    ]),
    ("step", 5, "Włącz wtyczkę", [
        "Kliknij „Włącz wtyczkę”. Automatycznie (nic nie klikasz) wtyczka: zakłada tabele,",
        "tworzy gotową podstronę „Nasze auta” dopasowaną do motywu i działającą na telefonie,",
        "oraz próbuje dodać ją do głównego menu.",
    ]),
    ("step", 6, "Sprawdź, że się udało", [
        "Wtyczki → Zainstalowane: jest „IAAI Importer” (aktywna).",
        "W menu po lewej pojawia się „Pojazdy”. Strony → „Nasze auta” istnieje (/nasze-auta).",
        "Strona bywa pusta do czasu uruchomienia automatyzacji — to normalne.",
    ]),
    ("step", 7, "Jeśli menu nie dodało się samo", [
        "Wygląd → Menu → zaznacz „Nasze auta” → „Dodaj do menu” → „Zapisz menu”.",
    ]),
    ("step", 8, "Opcjonalnie: własna, dodatkowa strona z autami", [
        "Strony → Dodaj nową, wstaw blok „Krótki kod” i wklej: [iaai_pojazdy ile=\"24\"]",
        "(liczba 24 = ile aut pokazać). Opublikuj.",
    ]),

    ("h1", "Uruchomienie automatyzacji (część techniczna)"),
    ("p", "To sprawia, że auta zaczynają się pojawiać i aktualizować same. Wykonuje się raz, na serwerze VPS przez terminal (SSH). Jeśli nie czujesz się pewnie — przekaż ten rozdział administratorowi hostingu."),
    ("step", 9, "Uruchom instalator", [
        "W terminalu, w folderze projektu:  sudo bash deploy/install.sh /var/www/html",
        "(zamień /var/www/html na katalog Twojego WordPressa). Instalator sam zainstaluje",
        "potrzebne programy, połączy się z bazą i włączy usługę sprawdzającą IAAI co kilkanaście minut.",
        "Szczegóły: docs/klient/03-uruchom-automatyzacje.md",
    ]),
    ("step", 10, "Sprawdź, że auta się pojawiają", [
        "Po pierwszym przebiegu (kilka–kilkanaście minut) na stronie „Nasze auta” pojawią się",
        "pierwsze pojazdy ze zdjęciami. Gotowe — system działa sam, nie musisz nic robić na co dzień.",
    ]),

    ("h1", "Co może pójść nie tak (i jak to naprawić)"),
    ("callout", False, [
        "„Wtyczka nie mogła zostać zainstalowana” → wysłano folder zamiast ZIP; wgraj plik ZIP.",
        "Brak przycisku „Wyślij wtyczkę” → hosting blokuje; wgraj folder iaai-importer przez FTP",
        "   do wp-content/plugins/ i włącz w panelu.",
        "ZIP za duży / limit wgrywania → wgraj przez FTP lub poproś hosting o wyższy limit.",
        "Strona „Nasze auta” nie powstała → odśwież panel; wtyczka tworzy ją też przy wejściu.",
        "Menu bez pozycji → dodaj ręcznie (Krok 7).",
        "Auta się nie pokazują → jeśli nie zrobiłeś automatyzacji, to oczekiwane; jeśli działa,",
        "   daj jej kilkanaście minut na pierwszy przebieg.",
        "Zdjęcia się nie ładują → sprawdź łącze serwera i dostępność IAAI.",
        "Brak VPS → sama wtyczka działa; automatyzacja wymaga VPS z SSH.",
    ]),

    ("h1", "FAQ — najczęstsze pytania"),
    ("faq", "Czy muszę coś robić codziennie?",
     "Nie. Po uruchomieniu system działa sam 24/7 — pobiera nowe auta i aktualizuje stronę."),
    ("faq", "Czy zdjęcia zajmują miejsce na hostingu?",
     "Nie. Domyślnie są pokazywane wprost z serwerów IAAI (0 miejsca na dysku)."),
    ("faq", "Czy auta same znikają, gdy schodzą z aukcji?",
     "Tak. Wpis jest wtedy ukrywany (szkic) — nie kasujemy historii."),
    ("faq", "Czy to jest zoptymalizowane pod Google (SEO)?",
     "Tak. Każde auto ma dane strukturalne Schema.org „Car”, opis, podgląd Open Graph i opisowe zdjęcia; trafia też do mapy strony WordPressa."),
    ("faq", "Mam już wtyczkę SEO (Yoast/Rank Math). Będzie konflikt?",
     "Nie. Tytuły/opisy zostają dla Twojej wtyczki SEO, a my dokładamy tylko dane strukturalne pojazdu."),
    ("faq", "Czy mogę zmienić, ile aut pokazuje strona?",
     "Tak — w krótkim kodzie zmień liczbę, np. [iaai_pojazdy ile=\"12\"]."),
    ("faq", "Czy wtyczka jest bezpieczna?",
     "Tak. Przeszła audyt bezpieczeństwa (ocena 9/10): ochrona przed SQL injection, XSS, SSRF, kontrola zdjęć, brak sekretów w kodzie."),
    ("faq", "Aktualizacja wtyczki w przyszłości — stracę dane?",
     "Nie. Dane aut są w bazie; podmiana plików wtyczki ich nie usuwa."),
    ("faq", "Nie mam VPS — co robić?",
     "Sama wtyczka działa na zwykłym WordPressie. Automatyzacja pobierania wymaga VPS — załóż VPS lub poproś dostawcę o taki plan."),

    ("h1", "Słowniczek"),
    ("gloss", [
        ("Wtyczka (plugin)", "mały dodatek do WordPressa dokładający nową funkcję."),
        ("Shortcode („krótki kod”)", "gotowy klocek w [nawiasach], który sam coś wyświetla."),
        ("CPT / „Pojazdy”", "specjalny typ wpisów WordPressa; tu trafiają auta."),
        ("VPS", "Twój prywatny serwer, na którym można uruchamiać własne programy."),
        ("SSH / terminal", "łączenie się z serwerem i wpisywanie poleceń tekstem."),
        ("FTP", "przesyłanie plików na serwer (np. programem FileZilla)."),
        ("Baza danych", "magazyn treści WordPressa; tu też trzymamy auta."),
        ("Hotlink", "pokazywanie zdjęcia wprost z cudzego serwera, bez kopiowania na dysk."),
        ("SEO", "optymalizacja pod wyszukiwarki (by Google lepiej pokazywał Twoje auta)."),
    ]),
    ("callout", True, [
        "Gdy utkniesz:",
        "1) Zajrzyj do sekcji „Co może pójść nie tak” i FAQ powyżej.",
        "2) Szczegółowe instrukcje etapami są w folderze docs/klient/.",
        "3) Część techniczną możesz przekazać administratorowi hostingu.",
    ]),
]


# ---- Nagłówek/stopka strony ----------------------------------------------
def page_header(page_no):
    s = []
    s.append(rect(0, 0, PW, 66, DARK, rx=0))
    s.append(rect(0, 63, PW, 3, BLUE, rx=0))
    s.append(text(MX, 30, "IAAI Importer", size=15, color="#ffffff", weight="bold"))
    s.append(text(MX, 50, "Instrukcja klienta — od A do Z", size=10.5, color="#aebfd8"))
    s.append(text(PW - MX, 40, "dla osoby nietechnicznej", size=9.5, color="#aebfd8", anchor="end"))
    return "".join(s)


def page_footer(page_no, total):
    s = []
    s.append(f'<line x1="{MX}" y1="808" x2="{PW-MX}" y2="808" stroke="{GRAYBORDER}" stroke-width="1"/>')
    s.append(text(MX, 822, "IAAI Importer — importer aut z IAAI do WordPress", size=8.5, color=MUTED))
    s.append(text(PW - MX, 822, f"Strona {page_no} / {total}", size=8.5, color=MUTED, anchor="end"))
    return "".join(s)


def cover_page(total):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{PW}" height="{PH}" viewBox="0 0 {PW} {PH}">']
    s.append(rect(0, 0, PW, PH, "#ffffff", rx=0))
    s.append(rect(0, 0, PW, 300, DARK, rx=0))
    s.append(rect(0, 297, PW, 6, BLUE, rx=0))
    s.append(text(MX, 120, "IAAI Importer", size=40, color="#ffffff", weight="bold"))
    s.append(text(MX, 165, "Instrukcja klienta — od A do Z", size=20, color="#aebfd8"))
    s.append(text(MX, 215, "Jak wgrać wtyczkę i uruchomić import aut z IAAI", size=13, color="#8ea3c8"))
    s.append(text(MX, 235, "do strony WordPress. Dla osoby nietechnicznej.", size=13, color="#8ea3c8"))
    # kafelki
    tiles = [
        ("1", "Jak to działa"),
        ("2", "Instalacja wtyczki (kroki 1–8)"),
        ("3", "Uruchomienie automatyzacji"),
        ("4", "Problemy, FAQ i słowniczek"),
    ]
    ty = 360
    for n, t in tiles:
        s.append(rect(MX, ty, CONTENT_W, 56, GRAYBG, rx=10, stroke=GRAYBORDER))
        s.append(f'<circle cx="{MX+34}" cy="{ty+28}" r="17" fill="{BLUE}"/>')
        s.append(text(MX + 34, ty + 33, n, size=15, color="#ffffff", weight="bold", anchor="middle"))
        s.append(text(MX + 64, ty + 34, t, size=13.5, color=DARK, weight="bold"))
        ty += 68
    s.append(rect(MX, 690, CONTENT_W, 70, CALLBG, rx=10, stroke=CALLBORDER))
    s.append(rect(MX, 690, 5, 70, CALLBORDER, rx=2))
    s.append(text(MX + 18, 716, "Spokojnie — wgranie wtyczki i pokazanie aut to głównie klikanie.",
                  size=11, color=DARK, weight="bold"))
    s.append(text(MX + 18, 736, "Rób kroki po kolei. Część techniczną (serwer) możesz przekazać",
                  size=11, color=DARK))
    s.append(text(MX + 18, 752, "administratorowi hostingu.", size=11, color=DARK))
    s.append(page_footer(1, total))
    s.append("</svg>")
    return "".join(s)


def build_pages():
    # paginacja: bloki atomowe, przełamanie całych bloków
    pages = []          # lista list bloków
    cur = []
    y = TOP
    for b in CONTENT:
        h = block_h(b)
        # h1 nie zostawiaj samego na dole strony
        need = h + (block_h(CONTENT[CONTENT.index(b) + 1]) if b[0] == "h1" and CONTENT.index(b) + 1 < len(CONTENT) else 0)
        if y + need > BOTTOM and cur:
            pages.append(cur)
            cur = []
            y = TOP
        cur.append((b, y))
        y += h + 4
    if cur:
        pages.append(cur)
    return pages


def render():
    pages = build_pages()
    total = len(pages) + 1  # + okładka
    svgs = [cover_page(total)]
    for i, page in enumerate(pages):
        pno = i + 2
        s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{PW}" height="{PH}" viewBox="0 0 {PW} {PH}">']
        s.append(rect(0, 0, PW, PH, "#ffffff", rx=0))
        s.append(page_header(pno))
        for b, y in page:
            svg, _ = draw_block(b, MX, y)
            s.append(svg)
        s.append(page_footer(pno, total))
        s.append("</svg>")
        svgs.append("".join(s))
    return svgs


def main():
    out_dir = Path(__file__).resolve().parent
    out_pdf = out_dir / "Instrukcja-klienta.pdf"
    svgs = render()
    with tempfile.TemporaryDirectory() as td:
        pdfs = []
        for i, svg in enumerate(svgs):
            sp = Path(td) / f"p{i:02d}.svg"
            pp = Path(td) / f"p{i:02d}.pdf"
            sp.write_text(svg, encoding="utf-8")
            subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(pp), str(sp)], check=True)
            pdfs.append(str(pp))
        subprocess.run(["gs", "-dBATCH", "-dNOPAUSE", "-q", "-sDEVICE=pdfwrite",
                        "-dCompatibilityLevel=1.5", f"-sOutputFile={out_pdf}", *pdfs], check=True)
    print(f"OK: {out_pdf}  ({len(svgs)} stron)")

    # kopia na pulpit (jeśli istnieje)
    for desk in (Path.home() / "Pulpit", Path.home() / "Desktop"):
        if desk.is_dir():
            import shutil
            shutil.copy2(out_pdf, desk / out_pdf.name)
            print(f"Kopia: {desk / out_pdf.name}")
            break


if __name__ == "__main__":
    main()
