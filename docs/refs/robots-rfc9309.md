# Referencja: Robots Exclusion Protocol (RFC 9309) — oryginał dla działu „zgodność"

> RFC 9309 (rfc-editor.org). Implementacja: stdlib `urllib.robotparser`. Stan: 2026-06-29.

## robots.txt — format i reguły
- Lokalizacja: zawsze `https://host/robots.txt`, UTF-8, plain text.
- Grupy: `User-Agent:` (jedna lub więcej) + reguły `Allow:` / `Disallow:`.
- `*` w User-Agent = wszystkie crawlery nienazwane.
- **Najdłuższe dopasowanie wygrywa** (most-specific path). Ścieżki case-sensitive.
- Znaki: `#` komentarz, `$` koniec wzorca, `*` wildcard (0+ znaków). `/robots.txt` zawsze dozwolony.

## Obowiązki crawlera
- Cache robots.txt ≤ 24 h. Do 5 przekierowań.
- **5xx** robots.txt → traktuj jako pełny disallow; **4xx** → wolno wszystko.
- Protokół jest **dobrowolny** — to nie zabezpieczenie; ścieżki są publicznie widoczne.

## Zastosowanie (dział zgodność)
`zgody.py`: `RobotsPolicy.can_fetch(url)` (urllib.robotparser), `RateLimiter` (min odstęp),
`detect_block(status, body)` (403/429/503 + markery Incapsula/CAPTCHA).

⚠️ **IAAI robots.txt zabrania `/Search`** — a tam są listingi. Agent to sygnalizuje;
decyzja o scrapingu mimo to jest biznesowo-prawna (ToS) i należy do właściciela projektu.
`/VehicleDetail/` jest dozwolone.
