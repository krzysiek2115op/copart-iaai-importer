# Generator szczegółowego diagramu architektury (SVG) -> PDF przez rsvg-convert.
import html

def esc(s): return html.escape(s, quote=True)

# Dane: (numer, nazwa, tech, doc, [(agent, co_robi, krytyk), ...])
DZIALY = [
 ("1","POBIERANIE","Python","playwright-python.md + copart-api.md",[
    ("pokrycie","iteruje filtry/segmenty, scala ofertę (per źródło)","kompletność-pokrycia"),
    ("listingi","IAAI: karty wyników + paginacja (Playwright/Knockout)","kompletność-listy"),
    ("szczegóły","IAAI: otwiera stronę lotu (render JS), uzupełnia pola","kompletność-pól"),
    ("zdjęcia","IAAI: lista zdjęć z vis.iaai.com (klucze + URL-e)","kompletność-zdjęć"),
    ("copart","COPART: API lotdetails/solr + lotImages (Member)","kompletność-copart"),
 ]),
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
sec1 = DZIALY[:6]
sec2 = DZIALY[6:]
def section_height(cards):
    return sum(card_h(c)+GAP for c in cards)
SEC_HDR=46; BAND=70; CAP=26
SBOX=72; SNOTE=22; AJAXZONE=56; SRCBLK = SBOX + AJAXZONE + SNOTE   # dwa źródła --AJAX--> Dział 1
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
    f'<tspan font-weight="bold" fill="#1e5fb0">AJAX do źródeł: 2 kanały = 6 żądań</tspan> (IAAI 3 · Copart 3)'
    f'   •   <tspan font-weight="bold" fill="#2e7d32">JSON</tspan>: źródła→JSON, pipeline→JSONL (5 działów) → 1 wspólna baza</text>')

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
# strzałki AJAX zbiegające do środka (wejście do Działu 1)
midx = W/2; ajy = y + AJAXZONE - 6
add(f'<line x1="{ix+srcw/2}" y1="{y+2}" x2="{midx-6}" y2="{ajy}" stroke="#666" stroke-width="2.5" marker-end="url(#arr)"/>')
add(f'<line x1="{cxx+srcw/2}" y1="{y+2}" x2="{midx+6}" y2="{ajy}" stroke="#1e5fb0" stroke-width="2.5" marker-end="url(#arr)"/>')
add(f'<text x="{ix+srcw/2}" y="{y+32}" text-anchor="middle" font-size="12" font-style="italic" fill="#777">AJAX ① — render Playwright (HTML→dane)</text>')
add(f'<text x="{cxx+srcw/2}" y="{y+32}" text-anchor="middle" font-size="12" font-style="italic" fill="#1e5fb0">AJAX ② — JSON API + cookies Member</text>')
y += AJAXZONE
add(f'<text x="{W/2}" y="{y+2}" text-anchor="middle" font-size="11.5" font-style="italic" fill="#777">Dział 1 pobiera z OBU źródeł — osobny przebieg na źródło: run_pipeline.py --source iaai | copart</text>')
y += SNOTE
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
