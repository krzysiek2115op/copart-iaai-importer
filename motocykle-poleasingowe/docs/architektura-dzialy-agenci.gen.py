# -*- coding: utf-8 -*-
# Generator szczegółowego diagramu architektury (SVG -> PDF przez rsvg-convert) — PLUGIN 2.
# Importer motocykli poleasingowe.pl → WordPress. JEDNO źródło (server-side HTML, bez JS),
# osobna baza MySQL polea_*, front DB-driven (bez CPT), zdjęcia hotlink.
#   Uruchom:  python3 docs/architektura-dzialy-agenci.gen.py
import html

def esc(s): return html.escape(s, quote=True)

# Dane: (numer, nazwa, tech, doc, [(agent, co_robi, krytyk), ...])
# Kolejność pipeline scrapera: 7 (bramka) → 1A → 1B → 2 → 5 → 3 → 4 → baza
SEC1 = [
 ("7","ZGODNOŚĆ","Python","7-zgodnosc.md",[
    ("zgody","respektuje robots.txt, rate-limit + jitter, backoff na 429/503","blokady"),
 ]),
 ("1A","POBIERANIE — LISTA","Python","1A-pobieranie-lista.md",[
    ("crawl","paginacja ?page=N, wyłuskuje /pl/auctions/details/<id>","kompletność-listy"),
    ("filtr-reklam","odrzuca partnerów z innych domen (aukcje.pkoleasing.pl)","zakres"),
 ]),
 ("1B","POBIERANIE — SZCZEGÓŁY","Python","1B-pobieranie-szczegoly.md",[
    ("pola","auction-data-label/value, cena z og:description, lokalizacja","kompletność-pól"),
    ("zdjęcia","sgallery_<UUID>_75.png (URL-e w kolejności)","kompletność-zdjęć"),
 ]),
 ("2","NORMALIZACJA","Python","2-normalizacja.md",[
    ("VIN","format + cyfra kontrolna (ISO 3779) — flaga soft, nie odrzuca","poprawność-VIN"),
    ("jednostki","przebieg→km, cena→liczba (PLN netto), daty→ISO, typy pól","jakość-jednostek"),
 ]),
 ("5","AUDYT","Python","5-audyt.md",[
    ("walidacja","reguły HARD (odrzuca) i SOFT (flaguje) na rekordzie","poprawność"),
 ]),
 ("3","DEDUPLIKACJA","Python","3-deduplikacja.md",[
    ("match","unikalny lot_id; wykrycie relistu po pełnym VIN","fałszywe-trafienia"),
 ]),
 ("4","SYNCHRONIZACJA","Python","4-synchronizacja.md",[
    ("diff","raw_hash (MD5): new / changed / unchanged","spójność"),
    ("zapis","upsert (PyMySQL) + reconcile (znikł → 'zakończona')","poprawność-zapisu"),
 ]),
]

# Część WordPress (wtyczka PHP) — front czyta osobną bazę TYLKO do odczytu
SEC2 = [
 ("6","BEZPIECZEŃSTWO","PHP/WP","6-bezpieczenstwo.md",[
    ("połączenie","mysqli z obsługą błędów — nie wpdb (brak wp_die)","odporność"),
    ("sanityzacja","prepared + escape wyjścia + nonce w adminie","podatności"),
 ]),
 ("8","PUBLIKACJA (REPO)","PHP/WP","8-publikacja.md",[
    ("repo","Polea_DB czyta polea_* (read-only) — bez CPT/postów WP","poprawność-odczytu"),
 ]),
 ("9","FRONT I MEDIA","PHP/WP","9-front-media.md",[
    ("front","lista + szczegóły + filtry (marka/paliwo/rok/cena) + cache 5 min","render"),
    ("media","zdjęcia HOTLINK ze źródła; miniatury 1 zapytaniem (bez N+1)","render"),
 ]),
 ("10","PODSTRONA I MOTYW","PHP/WP","10-podstrona-motyw.md",[
    ("podstrona","auto-tworzy „Nasze motory\" + wpina w menu","kompletność-wpięcia"),
    ("motyw","dziedziczy fonty/kolory motywu (currentColor + color-mix)","dopasowanie-motywu"),
 ]),
]

W = 960
LINE_H = 30
HEAD_H = 52
PAD = 14
GAP = 30

def card_h(d): return HEAD_H + len(d[4])*LINE_H + PAD

parts = []
def add(s): parts.append(s)

TOP = 176
def section_height(cards):
    return sum(card_h(c)+GAP for c in cards)
SEC_HDR=46; BAND=52; CAP=26
SBOX=80; AJ=78; AJ2=78
SRCBLK = SBOX + AJ
total = (TOP + SEC_HDR + SRCBLK + section_height(SEC1) + BAND + CAP + AJ2
         + SEC_HDR + section_height(SEC2) + BAND + 60)

add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {total}" width="{W}" height="{total}" font-family="DejaVu Sans, Arial, sans-serif">')
add('<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#666"/></marker></defs>')
add(f'<rect x="0" y="0" width="{W}" height="{total}" fill="#ffffff"/>')

# Tytuł
add(f'<text x="{W/2}" y="54" text-anchor="middle" font-size="29" font-weight="bold" fill="#1a1a1a">Importer motocykli poleasingowe.pl — działy, agenci, krytycy</text>')
add(f'<text x="{W/2}" y="85" text-anchor="middle" font-size="15" fill="#555">1 źródło (poleasingowe.pl · motocykle) · 11 działów · każdy ma agentów (wykonują) i krytyka (sprawdza) · 1 dokumentacja na dział</text>')
# Legenda
lx=W/2-300
add(f'<circle cx="{lx}" cy="112" r="7" fill="#2f6fed"/><text x="{lx+14}" y="117" font-size="13.5" fill="#333">agent — wykonuje zadanie</text>')
add(f'<circle cx="{lx+250}" cy="112" r="7" fill="#e23b3b"/><text x="{lx+264}" y="117" font-size="13.5" fill="#333">krytyk — sprawdza wynik</text>')
add(f'<rect x="{lx+490}" y="105" width="16" height="15" rx="3" fill="#ede7f6" stroke="#7e57c2"/><text x="{lx+512}" y="117" font-size="13.5" fill="#333">dokumentacja działu</text>')
# Pasek kluczowej różnicy vs plugin-1
add(f'<rect x="120" y="134" width="{W-240}" height="30" rx="8" fill="#f4f7fb" stroke="#c7d2e0"/>')
add(f'<text x="{W/2}" y="153" text-anchor="middle" font-size="12.5" fill="#334">'
    f'<tspan font-weight="bold" fill="#1e5fb0">Źródło = zwykły HTML serwera (bez JavaScriptu)</tspan> → requests + parser (bez Playwright)'
    f'   •   <tspan font-weight="bold" fill="#2e7d32">Osobna baza MySQL polea_*</tspan> ·  front czyta ją TYLKO do odczytu (bez CPT)</text>')

def draw_card(d, y):
    n,name,tech,doc,agents = d
    h = card_h(d)
    py = "Python" in tech
    fill = "#eef4ff" if py else "#fff4ec"
    stroke = "#4f7cff" if py else "#ff8a3d"
    htext = "#1a3a8f" if py else "#9c4a00"
    add(f'<rect x="30" y="{y}" width="{W-60}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    add(f'<text x="52" y="{y+30}" font-size="17" font-weight="bold" fill="{htext}">DZIAŁ {n} · {esc(name)}'
        f'<tspan font-size="12" font-weight="normal" fill="#888">   ·   {tech}</tspan></text>')
    bw = 8.5*len(doc)+24
    bx = W-30-18-bw
    add(f'<rect x="{bx}" y="{y+12}" width="{bw}" height="24" rx="6" fill="#ede7f6" stroke="#7e57c2"/>')
    add(f'<text x="{bx+bw/2}" y="{y+28}" text-anchor="middle" font-size="12.5" fill="#5e35b1">dok: {esc(doc)}</text>')
    ly = y+HEAD_H+10
    for (ag,desc,kr) in agents:
        add(f'<circle cx="62" cy="{ly-4}" r="6.5" fill="#2f6fed"/>')
        add(f'<text x="76" y="{ly}" font-size="14.5"><tspan font-weight="bold" fill="#173a8f">{esc(ag)}</tspan><tspan fill="#444"> — {esc(desc)}</tspan></text>')
        kx = 640
        add(f'<circle cx="{kx}" cy="{ly-4}" r="6.5" fill="#e23b3b"/>')
        add(f'<text x="{kx+14}" y="{ly}" font-size="13.5" fill="#333">krytyk: <tspan font-weight="bold" fill="#a31818">{esc(kr)}</tspan></text>')
        ly += LINE_H
    return h

def band(y, text, fill, stroke, tcol):
    add(f'<rect x="200" y="{y}" width="{W-400}" height="52" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    add(f'<text x="{W/2}" y="{y+32}" text-anchor="middle" font-size="16" font-weight="bold" fill="{tcol}">{esc(text)}</text>')

def arrow(y, label=None):
    add(f'<line x1="{W/2}" y1="{y}" x2="{W/2}" y2="{y+GAP-6}" stroke="#666" stroke-width="2.5" marker-end="url(#arr)"/>')
    if label:
        add(f'<text x="{W/2+16}" y="{y+GAP/2+2}" font-size="12.5" font-style="italic" fill="#777">{esc(label)}</text>')

def ajax_pill(y, height, title, subtitle):
    """Łącznik AJAX: strzałka w dół → pigułka → strzałka w dół (zajmuje 'height' px)."""
    pill_y = y + 14
    pill_h = 36
    pill_w = 560
    px = W/2 - pill_w/2
    add(f'<line x1="{W/2}" y1="{y}" x2="{W/2}" y2="{pill_y-4}" stroke="#666" stroke-width="2.5" marker-end="url(#arr)"/>')
    add(f'<rect x="{px}" y="{pill_y}" width="{pill_w}" height="{pill_h}" rx="9" fill="#e6eef7" stroke="#1e5fb0" stroke-width="1.8"/>')
    add(f'<text x="{W/2}" y="{pill_y+16}" text-anchor="middle" font-size="12.5" font-weight="bold" fill="#1e5fb0">{esc(title)}</text>')
    add(f'<text x="{W/2}" y="{pill_y+30}" text-anchor="middle" font-size="10" fill="#4a6f9c">{esc(subtitle)}</text>')
    add(f'<line x1="{W/2}" y1="{pill_y+pill_h}" x2="{W/2}" y2="{y+height-6}" stroke="#666" stroke-width="2.5" marker-end="url(#arr)"/>')

y = TOP
# Sekcja 1
add(f'<text x="48" y="{y+30}" font-size="18" font-weight="bold" fill="#333">▼ CZĘŚĆ 1 — SCRAPER (Python): pobiera motocykle z poleasingowe.pl, zapisuje do osobnej bazy</text>')
y += SEC_HDR
# JEDNO źródło
sx = 220; sw = W-2*220
add(f'<rect x="{sx}" y="{y}" width="{sw}" height="{SBOX}" rx="10" fill="#e0e0e0" stroke="#757575" stroke-width="2" stroke-dasharray="6 4"/>')
add(f'<text x="{W/2}" y="{y+26}" text-anchor="middle" font-size="15" font-weight="bold" fill="#424242">ŹRÓDŁO · poleasingowe.pl</text>')
add(f'<text x="{W/2}" y="{y+46}" text-anchor="middle" font-size="11" fill="#616161">ich serwer — brak dostępu do bazy; czytamy publiczny HTML aukcji</text>')
add(f'<text x="{W/2}" y="{y+65}" text-anchor="middle" font-size="11" fill="#616161">/pl/auctions/list/pub/all/ecr_motorcycles · /pl/auctions/details/&lt;id&gt; · images/sgallery_*.png</text>')
y += SBOX
# ŁĄCZNIK AJAX ① — pobiera dane z serwera źródła i przepuszcza je do sprawdzenia (działy/krytycy)
ajax_pill(y, AJ, "AJAX ① · łącznik pobierający dane z serwera źródła",
          "przepuszcza dane ze źródła do działów, które sprawdzają ich poprawność (przez HTTP, bez JS)")
y += AJ
for d in SEC1:
    h = draw_card(d, y)
    y += h
    arrow(y, "json"); y += GAP
# Baza
band(y, "OSOBNA BAZA MySQL  ·  polea_motocykle + polea_zdjecia  ·  klucz: lot_id", "#e8f5e9","#43a047","#2e7d32")
y += 52
add(f'<text x="{W/2}" y="{y+18}" text-anchor="middle" font-size="11.5" fill="#777">nie miesza się z bazą WordPressa ani z plugin-1 (inny prefix polea_) · scraper jest właścicielem danych (zapis: upsert PyMySQL)</text>')
y += CAP
# ŁĄCZNIK AJAX ② — czyta dane z bazy i podaje je do wtyczki WordPress (must have)
ajax_pill(y, AJ2, "AJAX ② · łącznik czytający dane z bazy",
          "wtyczka pobiera rekordy z bazy polea_* do wyświetlenia (mysqli, tylko odczyt)")
y += AJ2

# Sekcja 2
add(f'<text x="48" y="{y+30}" font-size="18" font-weight="bold" fill="#333">▼ CZĘŚĆ 2 — WORDPRESS (wtyczka PHP): pokazuje motocykle z bazy na podstronie</text>')
y += SEC_HDR
for d in SEC2:
    h = draw_card(d, y)
    y += h
    arrow(y); y += GAP
band(y, "PODSTRONA „NASZE MOTORY\"  →  klienci widzą motocykle w motywie ich strony", "#e1f5fe","#039be5","#0277bd")
y += 52

add(f'<text x="{W/2}" y="{total-22}" text-anchor="middle" font-size="11.5" fill="#999">Importer motocykli poleasingowe.pl → WordPress · diagram architektury (działy / agenci / krytycy / dokumentacja)</text>')
add('</svg>')

import os, subprocess
OUT_SVG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "architektura-dzialy-agenci.svg")
open(OUT_SVG, "w", encoding="utf-8").write("\n".join(parts))
try:
    subprocess.run(["rsvg-convert", "-f", "pdf", "-o", OUT_SVG[:-4] + ".pdf", OUT_SVG], check=True)
    print("PDF:", OUT_SVG[:-4] + ".pdf")
except Exception as e:
    print("PDF pominięty (brak rsvg-convert?):", e)
print("OK, wysokość:", total, "->", OUT_SVG)
