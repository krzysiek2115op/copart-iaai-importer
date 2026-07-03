#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Buduje STATYCZNĄ migawkę strony Kredyt Kompas + podstronę „Nasze auta" (z wtyczki)
do wrzucenia na GitHub Pages.  Źródło wyglądu: prawdziwy motyw kredyt-kompas
(header/footer + parts/*.html) oraz CSS wtyczki (assets/iaai.css).

Wynik:  demo/pages/  (index.html, podstrony, nasze-auta.html, assets/, iaai.css)

Uruchom:  python3 demo/build-static.py
"""
import os, re, html, shutil

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEME = "/home/krzysiek/kredyt-kompas-wp/wp-content/themes/kredyt-kompas"
PLUGCSS = os.path.join(ROOT, "wp-plugin", "iaai-importer", "assets", "iaai.css")
OUT   = os.path.join(ROOT, "demo", "pages")

# --- strony: (plik parts, plik wyjsciowy, slug-do-active, tytul) ---------
PAGES = [
    ("index",                "index.html",                "index",                "Kredyt Kompas — eksperci kredytów hipotecznych"),
    ("kredyty-hipoteczne",   "kredyty-hipoteczne.html",   "kredyty-hipoteczne",   "Kredyty hipoteczne — Kredyt Kompas"),
    ("kalkulator",           "kalkulator.html",           "kalkulator",           "Kalkulator zdolności — Kredyt Kompas"),
    ("o-nas",                "o-nas.html",                "o-nas",                "O nas — Kredyt Kompas"),
    ("faq",                  "faq.html",                  "faq",                  "FAQ — Kredyt Kompas"),
    ("kontakt",              "kontakt.html",              "kontakt",              "Kontakt — Kredyt Kompas"),
    ("polityka-prywatnosci", "polityka-prywatnosci.html", "polityka-prywatnosci", "Polityka prywatności — Kredyt Kompas"),
]

# pozycje menu (active-slug, etykieta, plik) — Panel pominięty, „Nasze auta" dodane
MENU = [
    ("index",              "Start",                "index.html"),
    ("kredyty-hipoteczne", "Kredyty hipoteczne",   "kredyty-hipoteczne.html"),
    ("kalkulator",         "Kalkulator zdolności", "kalkulator.html"),
    ("o-nas",              "O nas",                "o-nas.html"),
    ("faq",                "FAQ",                  "faq.html"),
    ("kontakt",            "Kontakt",              "kontakt.html"),
    ("nasze-auta",         "Nasze auta",           "nasze-auta.html"),
]

LOGO_SVG = ('<svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
    '<circle cx="20" cy="20" r="18" stroke="#10B981" stroke-width="2.2"/>'
    '<circle cx="20" cy="20" r="2" fill="#10B981"/>'
    '<path class="needle" d="M20 6 L24 20 L20 34 L16 20 Z" fill="#10B981" fill-opacity=".25" stroke="#10B981" stroke-width="1.6"/>'
    '</svg>')

FONTS = ('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800'
         '&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap')

def nav_html(active):
    lis = []
    for slug, label, href in MENU:
        cls = ' class="active"' if slug == active else ''
        lis.append('<li><a href="%s"%s>%s</a></li>' % (href, cls, html.escape(label)))
    return '<nav aria-label="Menu główne"><ul class="nav-links">\n' + "\n".join(lis) + '\n</ul></nav>'

def head_html(title, extra=""):
    return ('<!DOCTYPE html>\n<html lang="pl">\n<head>\n'
        '<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>%s</title>\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<meta name="theme-color" content="#081730">\n'
        '<link rel="icon" href="data:image/svg+xml,%%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 40 40\'%%3E%%3Ccircle cx=\'20\' cy=\'20\' r=\'18\' fill=\'none\' stroke=\'%%2310B981\' stroke-width=\'3\'/%%3E%%3Cpath d=\'M20 6 L24 20 L20 34 L16 20 Z\' fill=\'%%2310B981\'/%%3E%%3C/svg%%3E">\n'
        '<link rel="stylesheet" href="%s">\n'
        '<link rel="stylesheet" href="assets/styles.css">\n'
        '%s</head>\n' % (html.escape(title), FONTS, extra))

def header_html(active):
    return ('<body>\n'
        '<header class="nav on-hero"><div class="container nav-inner">\n'
        '<a href="index.html" class="logo" aria-label="Kredyt Kompas — strona główna">\n'
        + LOGO_SVG + '\n<span>Kredyt<em>Kompas</em></span></a>\n'
        + nav_html(active) + '\n'
        '<a class="nav-cta" href="kontakt.html#formularz">Bezpłatna konsultacja</a>\n'
        '<button class="burger" aria-label="Otwórz menu" aria-expanded="false"><span></span><span></span><span></span></button>\n'
        '</div></header>\n<main id="main">\n')

FOOTER = ('</main>\n<footer><div class="container">\n<div class="foot-grid">\n'
    '<div><a href="index.html" class="logo" aria-label="Kredyt Kompas — strona główna">\n' + LOGO_SVG +
    '\n<span>Kredyt<em>Kompas</em></span></a>\n'
    '<p style="max-width:300px">Niezależni eksperci kredytowi. Porównujemy oferty kilkunastu banków i prowadzimy Cię przez cały proces — od analizy zdolności po podpisanie umowy.</p></div>\n'
    '<div><h4>Nawigacja</h4><ul>\n'
    '<li><a href="index.html">Start</a></li><li><a href="kredyty-hipoteczne.html">Kredyty hipoteczne</a></li>\n'
    '<li><a href="kalkulator.html">Kalkulator zdolności</a></li><li><a href="o-nas.html">O nas</a></li>\n'
    '<li><a href="faq.html">FAQ</a></li><li><a href="kontakt.html">Kontakt</a></li><li><a href="nasze-auta.html">Nasze auta</a></li></ul></div>\n'
    '<div><h4>Kontakt</h4><ul>\n<li><a href="tel:+48500678799">+48 500 678 799</a></li>\n'
    '<li><a href="mailto:kontakt@kompas.pl">kontakt@kompas.pl</a></li>\n'
    '<li>ul. Przykładowa 13/3<br>00-001 Warszawa</li></ul></div>\n'
    '<div><h4>Godziny pracy</h4><ul>\n<li>pon.–pt.: 9:00–18:00</li><li>sobota: 10:00–14:00</li><li>niedziela: nieczynne</li></ul></div>\n'
    '</div>\n<div class="foot-bottom">\n<span>© 2026 Kredyt Kompas. Wszelkie prawa zastrzeżone.</span>\n'
    '<div class="legal"><a href="polityka-prywatnosci.html">Polityka prywatności</a><a href="polityka-prywatnosci.html#rodo">RODO</a></div>\n'
    '</div></div></footer>\n<script src="assets/script.js"></script>\n')

LINK_MAP = [
    ('/kontakt/#formularz', 'kontakt.html#formularz'),
    ('/polityka-prywatnosci/#rodo', 'polityka-prywatnosci.html#rodo'),
    ('/polityka-prywatnosci/', 'polityka-prywatnosci.html'),
    ('/kredyty-hipoteczne/', 'kredyty-hipoteczne.html'),
    ('/kalkulator/', 'kalkulator.html'),
    ('/o-nas/', 'o-nas.html'),
    ('/faq/', 'faq.html'),
    ('/nasze-auta/', 'nasze-auta.html'),
    ('/kontakt/', 'kontakt.html'),
]

def fix_links(s):
    for a, b in LINK_MAP:
        s = s.replace('href="%s"' % a, 'href="%s"' % b)
    return s

# ---------------- Nasze auta: dane + render (jak we wtyczce) --------------
def nbsp(n):
    return format(int(n), ",").replace(",", " ")

def odo(mi):
    km = round(int(mi) * 1.609344)
    return "%s km (%s mi)" % (nbsp(km), nbsp(mi))

CARS = [
    dict(t="2018 Toyota Camry", make="Toyota", year=2018, dmg="Front End", trans="Automatic", odo=105380, buy=8200, rd=1, key=1, bg="1f4fd8", lbl="Toyota Camry"),
    dict(t="2016 Dodge Charger", make="Dodge", year=2016, dmg="Rear End", trans="Automatic", odo=88231, buy=6900, rd=1, key=1, bg="111111", lbl="Dodge Charger"),
    dict(t="2019 Ford F-150", make="Ford", year=2019, dmg="Side", trans="Automatic", odo=42210, buy=15400, rd=1, key=1, bg="2b6cb0", lbl="Ford F-150"),
    dict(t="2019 Tesla Model 3", make="Tesla", year=2019, dmg="Front End", trans="Automatic", odo=33110, buy=18900, rd=0, key=0, bg="c53030", lbl="Tesla Model 3"),
    dict(t="2016 BMW 328i", make="BMW", year=2016, dmg="Rear", trans="Automatic", odo=77650, buy=7300, rd=1, key=1, bg="4a5568", lbl="BMW 328i"),
    dict(t="2018 Nissan Altima", make="Nissan", year=2018, dmg="Water/Flood", trans="Automatic", odo=60120, buy=3200, rd=0, key=0, bg="718096", lbl="Nissan Altima"),
    dict(t="2018 Chevrolet Malibu", make="Chevrolet", year=2018, dmg="Front End", trans="Automatic", odo=51230, buy=6100, rd=1, key=1, bg="285e8a", lbl="Chevrolet Malibu"),
    dict(t="2020 Honda Accord", make="Honda", year=2020, dmg="Minor Dent/Scratches", trans="Automatic", odo=28900, buy=13500, rd=1, key=1, bg="0d7a5f", lbl="Honda Accord"),
    dict(t="2017 Volkswagen Jetta", make="Volkswagen", year=2017, dmg="Side", trans="Manual", odo=69540, buy=5400, rd=1, key=1, bg="5b4b8a", lbl="VW Jetta"),
]

def card_html(c):
    img = ('https://placehold.co/700x500/%s/ffffff?text=%s'
           % (c["bg"], c["lbl"].replace(" ", "+")))
    rows = ('<span class="iaai-price">Buy Now: USD %s</span>'
            '<span class="iaai-odo">%s</span>'
            '<span class="iaai-dmg">%s</span>'
            '<span class="iaai-trans">%s</span>'
            % (nbsp(c["buy"]), odo(c["odo"]), html.escape(c["dmg"]), html.escape(c["trans"])))
    badges = ""
    if c["rd"]:
        badges += '<span class="iaai-badge iaai-badge--rd">Run &amp; Drive</span>'
    if c["key"]:
        badges += '<span class="iaai-badge iaai-badge--key">Key Available</span>'
    return ('<article class="iaai-card" data-make="%s" data-year="%s" data-dmg="%s">'
        '<a class="iaai-card__media" href="#">'
        '<img loading="lazy" src="%s" alt="%s"/></a>'
        '<div class="iaai-card__body">'
        '<a class="iaai-card__title" href="#">%s</a>'
        '<div class="iaai-card__rows">%s</div>'
        '<div class="iaai-card__badges">%s</div>'
        '</div></article>'
        % (html.escape(c["make"]), c["year"], html.escape(c["dmg"]),
           img, html.escape(c["t"]), html.escape(c["t"]), rows, badges))

def filters_html():
    makes = sorted({c["make"] for c in CARS})
    years = sorted({c["year"] for c in CARS}, reverse=True)
    dmgs  = sorted({c["dmg"] for c in CARS})
    def sel(name, opts, ph):
        o = '<option value="">%s</option>' % ph
        for v in opts:
            o += '<option value="%s">%s</option>' % (html.escape(str(v)), html.escape(str(v)))
        return '<select id="%s">%s</select>' % (name, o)
    return ('<form class="iaai-filters" onsubmit="return false">'
        + sel("f-make", makes, "Marka")
        + sel("f-year", years, "Rok")
        + sel("f-dmg", dmgs, "Uszkodzenie")
        + '<button type="button" id="f-clear" class="iaai-filters__clear">Wyczyść</button>'
        + '</form>')

FILTER_JS = ("""<script>
(function(){
 var m=document.getElementById('f-make'),y=document.getElementById('f-year'),d=document.getElementById('f-dmg');
 var cards=[].slice.call(document.querySelectorAll('.iaai-card'));
 function apply(){var mv=m.value,yv=y.value,dv=d.value,n=0;
  cards.forEach(function(c){
   var ok=(!mv||c.dataset.make===mv)&&(!yv||c.dataset.year===yv)&&(!dv||c.dataset.dmg===dv);
   c.style.display=ok?'':'none'; if(ok)n++;});
  var e=document.getElementById('iaai-count'); if(e)e.textContent=n;
 }
 [m,y,d].forEach(function(s){s.addEventListener('change',apply);});
 document.getElementById('f-clear').addEventListener('click',function(){m.value='';y.value='';d.value='';apply();});
})();
</script>""")

def nasze_auta_html():
    cards = "".join(card_html(c) for c in CARS)
    intro = ('<section class="container" style="padding:48px 0 8px">'
        '<h1 style="margin:0 0 6px">Nasze auta</h1>'
        '<p style="opacity:.75;margin:0 0 4px">Aktualna oferta pojazdów z aukcji IAAI '
        '(<span id="iaai-count">%d</span> szt.). Filtruj po marce, roku i uszkodzeniu.</p>'
        '<p style="opacity:.6;font-size:.9em;margin:.2em 0 0">To podgląd demonstracyjny — dane i zdjęcia przykładowe.</p>'
        '</section>' % len(CARS))
    body = ('<div class="container" style="padding:16px 0 64px">'
        '<div class="iaai-pojazdy" id="iaai" style="--iaai-accent:#10B981">'
        + filters_html() + '<div class="iaai-grid">' + cards + '</div></div></div>')
    head = head_html("Nasze auta — Kredyt Kompas", '<link rel="stylesheet" href="iaai.css">\n')
    return head + header_html("nasze-auta") + intro + body + FOOTER + FILTER_JS + "\n</body></html>\n"

def build():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)

    # strony z parts/
    for part, outfn, active, title in PAGES:
        pf = os.path.join(THEME, "parts", part + ".html")
        content = ""
        if os.path.isfile(pf):
            with open(pf, encoding="utf-8") as f:
                content = f.read()
        content = fix_links(content)
        page = head_html(title) + header_html(active) + content + FOOTER + "\n</body></html>\n"
        with open(os.path.join(OUT, outfn), "w", encoding="utf-8") as f:
            f.write(page)

    # Nasze auta
    with open(os.path.join(OUT, "nasze-auta.html"), "w", encoding="utf-8") as f:
        f.write(nasze_auta_html())

    # zasoby motywu + css wtyczki
    shutil.copy2(os.path.join(THEME, "assets", "styles.css"), os.path.join(OUT, "assets", "styles.css"))
    shutil.copy2(os.path.join(THEME, "assets", "script.js"),  os.path.join(OUT, "assets", "script.js"))
    shutil.copy2(PLUGCSS, os.path.join(OUT, "iaai.css"))
    open(os.path.join(OUT, ".nojekyll"), "w").close()

    files = sorted(os.listdir(OUT))
    print("Zbudowano statyczna migawke -> demo/pages/")
    print("  pliki:", ", ".join(files))
    print("  aut:", len(CARS))

if __name__ == "__main__":
    build()
