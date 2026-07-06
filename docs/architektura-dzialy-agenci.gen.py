# Generator szczegółowego diagramu architektury (SVG) -> PDF przez rsvg-convert.
import html

def esc(s): return html.escape(s, quote=True)

# Dane: (numer, nazwa, tech, doc, [(agent, co_robi, krytyk), ...])
DZIALY = [
 # DZIAŁ 1 (POBIERANIE) jest ROZDZIELONY per źródło — patrz DZIAL1_IAAI / DZIAL1_COPART niżej.
 ("7","ZGODNOŚĆ","Python","robots-rfc9309.md",[
    ("zgody","respektuje robots.txt, trzyma rate-limit, wykrywa blokady","blokady"),
 ]),
 ("2","NORMALIZACJA","Python","vin-nhtsa.md",[
    ("VIN","format + cyfra kontrolna, maska, vPIC → marka/model/rok","poprawność-VIN"),
    ("jednostki","mile→km, ceny→liczby, daty→ISO, tytuł→marka/stan","jakość-jednostek"),
 ]),
 ("3","DEDUPLIKACJA","Python","(logika własna)",[
    ("match","usuwa duplikaty (salvage_id); relist po PEŁNYM VIN","fałszywe-trafienia"),
 ]),
 ("4","SYNCHRONIZACJA","Python","mysql-upsert.md",[
    ("diff","wykrywa zmiany (raw_hash: new / changed / unchanged)","spójność"),
    ("json","zapis do bazy (upsert) + reconcile (sold/removed)","poprawność-json"),
 ]),
 ("5","AUDYT","Python","json-schema.md",[
    ("walidacja","sprawdza dane regułami (JSON Schema)","poprawność"),
 ]),
 ("6","BEZPIECZEŃSTWO","PHP/WP","wordpress-security.md",[
    ("sanityzacja","czyści dane wchodzące do WP (escape/prepare)","podatności"),
    ("nonce","chroni akcje administratora (CSRF)","podatności"),
 ]),
 ("8","PUBLIKACJA","PHP/WP","wordpress-cpt.md",[
    ("CPT","tworzy typ treści „Pojazd” w WordPress","poprawność-publikacji"),
    ("meta","pola pojazdu (VIN, rok, cena, przebieg…)","poprawność-publikacji"),
 ]),
 ("9","FRONT I MEDIA","PHP/WP","wordpress-media.md",[
    ("front","lista + strona pojazdu (dane escapowane) + plakietka/filtr źródła","render"),
    ("media","zdjęcia (HOTLINK z vis.iaai.com / cs.copart.com)","render"),
 ]),
]

# DZIAŁ 1 ROZDZIELONY per źródło — każdy ma WŁASNY kanał AJAX (zasada: dział = AJAX + 1 wyjście).
DZIAL1_IAAI = ("1", "POBIERANIE — IAAI", "Python", "playwright.md", [
    ("pokrycie", "filtry/segmenty → cała oferta IAAI", "kompletność-pokrycia"),
    ("listingi", "karty wyników + paginacja (Playwright)", "kompletność-listy"),
    ("szczegóły", "strona lotu (render JS), pola", "kompletność-pól"),
    ("zdjęcia", "vis.iaai.com (klucze + URL-e)", "kompletność-zdjęć"),
])
DZIAL1_COPART = ("1", "POBIERANIE — Copart", "Python", "copart-api.md", [
    ("pokrycie", "wyszukiwarka Copart per filtr", "kompletność-pokrycia"),
    ("copart", "API lotdetails/solr (konto Member)", "kompletność-copart"),
    ("zdjęcia", "lotImages → cs.copart.com", "kompletność-zdjęć"),
])

W = 960
LINE_H = 30
HEAD_H = 52
PAD = 14
GAP = 30

def card_h(d): return HEAD_H + len(d[4])*LINE_H + PAD

parts = []
def add(s): parts.append(s)

# wysokość całości
y = 0
TOP = 176           # nagłówek (tytuł + podtytuł + legenda + licznik AJAX/JSON)
y = TOP
# część 1 header + 6 kart (1,7,2,3,4,5) + baza band + część2 header + 3 karty + strona band
sec1 = DZIALY[:5]   # wspólny pipeline: działy 7,2,3,4,5
sec2 = DZIALY[5:]   # WordPress: działy 6,8,9
def section_height(cards):
    return sum(card_h(c)+GAP for c in cards)
def narrow_h(d):    # węższa karta Działu 1 (agent + krytyk POD nim, bo wąsko)
    return 46 + len(d[4])*34 + 14
SEC_HDR=46; BAND=70; CAP=26
SBOX=72; AJ=44; MERGE=100; SNOTE=22   # MERGE = 30(strzałki)+34(węzeł)+GAP+6(nota)
D1H = max(narrow_h(DZIAL1_IAAI), narrow_h(DZIAL1_COPART))
SRCBLK = SBOX + AJ + D1H + MERGE   # źródła → AJAX (pionowo) → dwa Działy 1 → scalenie strumieni
total = (TOP + SEC_HDR + SRCBLK + section_height(sec1) + BAND + CAP + GAP
         + SEC_HDR + section_height(sec2) + BAND + 60)

add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {total}" width="{W}" height="{total}" font-family="DejaVu Sans, Arial, sans-serif">')
add('<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#666"/></marker></defs>')
add(f'<rect x="0" y="0" width="{W}" height="{total}" fill="#ffffff"/>')

# Tytuł
add(f'<text x="{W/2}" y="54" text-anchor="middle" font-size="29" font-weight="bold" fill="#1a1a1a">System importera IAAI + Copart — działy, agenci, krytycy</text>')
add(f'<text x="{W/2}" y="85" text-anchor="middle" font-size="15" fill="#555">2 źródła (IAAI.com + Copart) · 9 działów · każdy ma agentów (wykonują) i krytyka (sprawdza) · 1 dokumentacja na dział</text>')
# Legenda
lx=W/2-300
add(f'<circle cx="{lx}" cy="112" r="7" fill="#2f6fed"/><text x="{lx+14}" y="117" font-size="13.5" fill="#333">agent — wykonuje zadanie</text>')
add(f'<circle cx="{lx+250}" cy="112" r="7" fill="#e23b3b"/><text x="{lx+264}" y="117" font-size="13.5" fill="#333">krytyk — sprawdza wynik</text>')
add(f'<rect x="{lx+490}" y="105" width="16" height="15" rx="3" fill="#ede7f6" stroke="#7e57c2"/><text x="{lx+512}" y="117" font-size="13.5" fill="#333">oryginalna dokumentacja</text>')
# Pasek licznika: ile AJAX, ile JSON
add(f'<rect x="120" y="134" width="{W-240}" height="30" rx="8" fill="#f4f7fb" stroke="#c7d2e0"/>')
add(f'<text x="{W/2}" y="153" text-anchor="middle" font-size="12.5" fill="#334">'
    f'<tspan font-weight="bold" fill="#1e5fb0">AJAX: 2 kanały, każdy do WŁASNEGO Działu 1</tspan> (6 żądań: IAAI 3 · Copart 3)'
    f'   •   <tspan font-weight="bold" fill="#2e7d32">JSON</tspan>: strumienie łączą się → wspólny pipeline → 1 baza</text>')

def draw_card(d, y):
    n,name,tech,doc,agents = d
    h = card_h(d)
    py = "Python" in tech
    fill = "#eef4ff" if py else "#fff4ec"
    stroke = "#4f7cff" if py else "#ff8a3d"
    htext = "#1a3a8f" if py else "#9c4a00"
    add(f'<rect x="30" y="{y}" width="{W-60}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    # header (jedna linia: nazwa + tech)
    add(f'<text x="52" y="{y+30}" font-size="17" font-weight="bold" fill="{htext}">DZIAŁ {n} · {esc(name)}'
        f'<tspan font-size="12" font-weight="normal" fill="#888">   ·   {tech}</tspan></text>')
    # doc badge (prawy górny)
    bw = 8.5*len(doc)+24
    bx = W-30-18-bw
    add(f'<rect x="{bx}" y="{y+12}" width="{bw}" height="24" rx="6" fill="#ede7f6" stroke="#7e57c2"/>')
    add(f'<text x="{bx+bw/2}" y="{y+28}" text-anchor="middle" font-size="12.5" fill="#5e35b1">dok: {esc(doc)}</text>')
    # agenci
    ly = y+HEAD_H+10
    for (ag,desc,kr) in agents:
        add(f'<circle cx="62" cy="{ly-4}" r="6.5" fill="#2f6fed"/>')
        add(f'<text x="76" y="{ly}" font-size="14.5"><tspan font-weight="bold" fill="#173a8f">{esc(ag)}</tspan><tspan fill="#444"> — {esc(desc)}</tspan></text>')
        # krytyk po prawej
        kx = 585
        add(f'<circle cx="{kx}" cy="{ly-4}" r="6.5" fill="#e23b3b"/>')
        add(f'<text x="{kx+14}" y="{ly}" font-size="13.5" fill="#333">krytyk: <tspan font-weight="bold" fill="#a31818">{esc(kr)}</tspan></text>')
        ly += LINE_H
    return h

def draw_card_narrow(d, x, w, y, h):
    """Węższa karta Działu 1 (per źródło): krytyk POD agentem, bo mało miejsca w poziomie."""
    n,name,tech,doc,agents = d
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#eef4ff" stroke="#4f7cff" stroke-width="2"/>')
    add(f'<text x="{x+18}" y="{y+27}" font-size="14.5" font-weight="bold" fill="#1a3a8f">DZIAŁ {esc(n)} · {esc(name)}</text>')
    add(f'<text x="{x+w-14}" y="{y+27}" text-anchor="end" font-size="10" fill="#7e57c2">dok: {esc(doc)}</text>')
    ly = y+52
    for (ag,desc,kr) in agents:
        add(f'<circle cx="{x+20}" cy="{ly-4}" r="5.5" fill="#2f6fed"/>')
        add(f'<text x="{x+32}" y="{ly}" font-size="12.5"><tspan font-weight="bold" fill="#173a8f">{esc(ag)}</tspan><tspan fill="#444"> — {esc(desc)}</tspan></text>')
        add(f'<circle cx="{x+34}" cy="{ly+12}" r="4.5" fill="#e23b3b"/>')
        add(f'<text x="{x+44}" y="{ly+16}" font-size="10.5" fill="#555">krytyk: <tspan font-weight="bold" fill="#a31818">{esc(kr)}</tspan></text>')
        ly += 34
    return h

def band(y, text, fill, stroke, tcol):
    add(f'<rect x="200" y="{y}" width="{W-400}" height="52" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    add(f'<text x="{W/2}" y="{y+32}" text-anchor="middle" font-size="16" font-weight="bold" fill="{tcol}">{esc(text)}</text>')

def arrow(y, label=None):
    add(f'<line x1="{W/2}" y1="{y}" x2="{W/2}" y2="{y+GAP-6}" stroke="#666" stroke-width="2.5" marker-end="url(#arr)"/>')
    if label:
        add(f'<text x="{W/2+16}" y="{y+GAP/2+2}" font-size="12.5" font-style="italic" fill="#777">{esc(label)}</text>')

# Sekcja 1
add(f'<text x="48" y="{y+30}" font-size="18" font-weight="bold" fill="#333">▼ CZĘŚĆ 1 — SCRAPER (Python): zbiera dane z IAAI i Copart, zapisuje do wspólnej bazy</text>')
y += SEC_HDR
# DWA ŹRÓDŁA obok siebie — każde ma WŁASNĄ „starą bazę" i WŁASNY kanał AJAX do Działu 1
srcw = 366
ix = 88; cxx = W-88-srcw
add(f'<rect x="{ix}" y="{y}" width="{srcw}" height="{SBOX}" rx="10" fill="#e0e0e0" stroke="#757575" stroke-width="2" stroke-dasharray="6 4"/>')
add(f'<text x="{ix+srcw/2}" y="{y+23}" text-anchor="middle" font-size="14.5" font-weight="bold" fill="#424242">① SERWER / BAZA IAAI.com</text>')
add(f'<text x="{ix+srcw/2}" y="{y+41}" text-anchor="middle" font-size="10.5" fill="#757575">ich baza — brak dostępu; dane czytamy przez przeglądarkę</text>')
add(f'<text x="{ix+srcw/2}" y="{y+58}" text-anchor="middle" font-size="10.5" fill="#616161">/Search · /VehicleDetail · vis.iaai.com</text>')
add(f'<rect x="{cxx}" y="{y}" width="{srcw}" height="{SBOX}" rx="10" fill="#e6eef7" stroke="#1e5fb0" stroke-width="2" stroke-dasharray="6 4"/>')
add(f'<text x="{cxx+srcw/2}" y="{y+23}" text-anchor="middle" font-size="14.5" font-weight="bold" fill="#1e5fb0">② SERWER / BAZA Copart.com</text>')
add(f'<text x="{cxx+srcw/2}" y="{y+41}" text-anchor="middle" font-size="10.5" fill="#4a76a8">ich baza — brak dostępu; API po zalogowaniu (Member)</text>')
add(f'<text x="{cxx+srcw/2}" y="{y+58}" text-anchor="middle" font-size="10.5" fill="#3f6da3">search-results · lotdetails/solr · lotImages</text>')
y += SBOX
# AJAX PIONOWO — każde źródło do WŁASNEGO Działu 1 (proste w dół, bez krzyżowania; 1 AJAX na dział)
cxi = ix + srcw/2; cxc = cxx + srcw/2
d1y = y + AJ
add(f'<line x1="{cxi}" y1="{y}" x2="{cxi}" y2="{d1y-4}" stroke="#666" stroke-width="2.5" marker-end="url(#arr)"/>')
add(f'<line x1="{cxc}" y1="{y}" x2="{cxc}" y2="{d1y-4}" stroke="#1e5fb0" stroke-width="2.5" marker-end="url(#arr)"/>')
add(f'<text x="{cxi-12}" y="{y+27}" text-anchor="end" font-size="12.5" font-weight="bold" font-style="italic" fill="#555">AJAX ① · Playwright</text>')
add(f'<text x="{cxc+12}" y="{y+27}" text-anchor="start" font-size="12.5" font-weight="bold" font-style="italic" fill="#1e5fb0">AJAX ② · API + cookies</text>')
y = d1y
# Dwa Działy 1 (per źródło) — każdy dokładnie pod swoim źródłem (ta sama oś X co AJAX)
d1w = 400
draw_card_narrow(DZIAL1_IAAI, cxi - d1w/2, d1w, y, D1H)
draw_card_narrow(DZIAL1_COPART, cxc - d1w/2, d1w, y, D1H)
# json z obu Działów 1 → WĘZEŁ SCALENIA (to NIE „dział", tylko bufor → może mieć 2 wejścia)
mtop = y + D1H + 30
add(f'<line x1="{cxi}" y1="{y+D1H}" x2="{W/2-74}" y2="{mtop}" stroke="#666" stroke-width="2.2" marker-end="url(#arr)"/>')
add(f'<line x1="{cxc}" y1="{y+D1H}" x2="{W/2+74}" y2="{mtop}" stroke="#1e5fb0" stroke-width="2.2" marker-end="url(#arr)"/>')
add(f'<rect x="{W/2-168}" y="{mtop}" width="336" height="34" rx="9" fill="#fff7e6" stroke="#e0a92e" stroke-width="1.6"/>')
add(f'<text x="{W/2}" y="{mtop+14}" text-anchor="middle" font-size="12" font-weight="bold" fill="#8a6d1a">łączenie strumieni JSONL (oba źródła → jeden)</text>')
add(f'<text x="{W/2}" y="{mtop+28}" text-anchor="middle" font-size="9.5" fill="#a07d1a">to bufor/kolejka, nie „dział" — dlatego wolno mu mieć 2 wejścia</text>')
y = mtop + 34
arrow(y, "wspólny strumień"); y += GAP
add(f'<text x="{W/2}" y="{y-1}" text-anchor="middle" font-size="11" font-style="italic" fill="#777">dalej OBA źródła przez TEN SAM pipeline (uruchamiany osobno per źródło: --source iaai | copart)</text>')
y += 6
for i,d in enumerate(sec1):
    h = draw_card(d, y)
    y += h
    arrow(y, "json (plik JSONL)"); y += GAP
# Baza (NOWA = jedyna realna baza)
band(y, "NOWA BAZA  ·  wp_iaai_*  ·  klucz (source, salvage_id)", "#e8f5e9","#43a047","#2e7d32")
y += 52
add(f'<text x="{W/2}" y="{y+18}" text-anchor="middle" font-size="11.5" fill="#777">jedyna realna baza (ta sama, której używa WordPress) — OBA źródła w jednej tabeli (kolumna source); zapis SQL upsert (PyMySQL)</text>')
y += CAP
arrow(y, "wtyczka czyta bazę (SQL)"); y += GAP

# Sekcja 2
add(f'<text x="48" y="{y+30}" font-size="18" font-weight="bold" fill="#333">▼ CZĘŚĆ 2 — WORDPRESS (wtyczka PHP): pokazuje auta z bazy na stronie</text>')
y += SEC_HDR
for d in sec2:
    h = draw_card(d, y)
    y += h
    arrow(y); y += GAP
band(y, "STRONA WORDPRESS  →  klienci widzą auta", "#e1f5fe","#039be5","#0277bd")
y += 52

add(f'<text x="{W/2}" y="{total-22}" text-anchor="middle" font-size="11.5" fill="#999">Importer aut IAAI + Copart → WordPress · diagram architektury (działy / agenci / krytycy / dokumentacja)</text>')
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
