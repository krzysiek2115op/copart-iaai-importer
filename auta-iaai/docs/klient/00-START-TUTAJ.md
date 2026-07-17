# 👋 START TUTAJ — zanim zaczniesz

To jest komplet instrukcji do uruchomienia **importera aut z IAAI i Copart** na Twojej stronie.
Pisane prostym językiem — **nie musisz być informatykiem**. Idź etapami, po kolei.

> 📘 Wolisz **wszystko w jednym pliku** (A–Z, z FAQ i „co może pójść nie tak")?
> → [PRZECZYTAJ-MNIE-NAJPIERW.md](PRZECZYTAJ-MNIE-NAJPIERW.md). Poniżej ten sam
> materiał rozbity na krótkie etapy.

---

## Co to robi? (w jednym zdaniu)
Sam pobiera samochody z **dwóch** serwisów aukcyjnych — **iaai.com** oraz **copart.com**
(zdjęcia + dane) — i **pokazuje je na Twojej stronie WordPress** — automatycznie, przez całą
dobę. Gdy pojawia się nowe auto, trafia na stronę; gdy auto znika z aukcji, znika też u Ciebie.
Każde auto ma **plakietkę źródła** (IAAI / Copart), a odwiedzający mogą **filtrować listę po źródle**.

```
IAAI + Copart  ──►  [Twój serwer: program zbierający]  ──►  [Baza danych]  ──►  [Twoja strona WordPress]
 (dwa źródła aut)        (działa sam, 24/7)               (auta)            (klienci widzą auta)
```

> ℹ️ **Uwaga o Copart:** IAAI działa od razu. Copart mocniej broni się przed automatami
> (Cloudflare), a pełne dane i zdjęcia bywają dostępne dopiero **po zalogowaniu na konto
> Member** — dlatego drugie źródło uruchamia się z danymi logowania (patrz Etap 3). Bez konta
> działa samo IAAI; Copart dołączasz, gdy masz dostęp.

## Co dostajesz w paczce?
- **Wtyczkę do WordPress** (folder `wp-plugin/iaai-importer`) — pokazuje auta na stronie.
- **Program zbierający** („scraper", folder `scraper`) — pobiera auta z IAAI i Copart.
- **Instalator** (`deploy/install.sh`) — ustawia automatyzację jednym poleceniem.
- **Te instrukcje** (`docs/klient/`).

## Czego potrzebujesz (wymagania)
| Potrzebne | Po co | Jeśli nie masz |
|-----------|-------|----------------|
| **WordPress** na własnym hostingu | strona, na której pokażą się auta | załóż WordPressa u dostawcy hostingu |
| **Serwer typu VPS** (z dostępem do „terminala") | tu działa program zbierający 24/7 | ⚠️ zwykły „hosting współdzielony" NIE wystarczy — patrz niżej |
| Pomoc dostawcy hostingu (czasem) | instalacja Pythona/WP-CLI | napisz do supportu hostingu — to standard |

> ⚠️ **Ważne:** część „programu zbierającego" wymaga serwera **VPS** (gdzie można uruchamiać
> własne programy). Na najtańszym „hostingu współdzielonym" to nie zadziała. Jeśli nie wiesz,
> co masz — zapytaj dostawcę: „Czy mam VPS z dostępem SSH i mogę uruchamiać Pythona?".

---

## 🗺️ Mapa etapów (rób po kolei)
| Etap | Co robisz | Plik | Trudność |
|------|-----------|------|----------|
| **1** | Wgrywasz wtyczkę do WordPress i włączasz | [01-instalacja-wtyczki.md](01-instalacja-wtyczki.md) | łatwe (klikanie) |
| **2** | Pokazujesz auta na stronie (jeden „krótki kod") | [02-pokaz-auta-na-stronie.md](02-pokaz-auta-na-stronie.md) | łatwe (klikanie) |
| **3** | Uruchamiasz automatyzację na serwerze | [03-uruchom-automatyzacje.md](03-uruchom-automatyzacje.md) | średnie (kopiuj-wklej) |
| **4** | Sprawdzasz, że działa + obsługa na co dzień | [04-jak-dziala-i-obsluga.md](04-jak-dziala-i-obsluga.md) | informacyjne |
| **5** | Edycja podstrony + dopasowanie do motywu (dla Ciebie) | [06-edycja-podstrony-i-motyw.md](06-edycja-podstrony-i-motyw.md) | łatwe |
| **—** | Problemy i pytania (FAQ) + słowniczek | [05-problemy-i-pytania.md](05-problemy-i-pytania.md) | na wszelki wypadek |

> 🗺️ Chcesz najpierw zobaczyć, **jak to działa na obrazku**? →
> [diagram-systemu.md](diagram-systemu.md)

**Na co dzień nie musisz robić nic** — po Etapie 3 wszystko dzieje się samo.
Zacznij od **[Etapu 1 →](01-instalacja-wtyczki.md)**.
