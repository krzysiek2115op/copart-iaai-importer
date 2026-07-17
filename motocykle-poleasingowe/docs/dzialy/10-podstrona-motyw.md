<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Dział 10 · PODSTRONA I MOTYW (WordPress)

**Powstał z rozbicia Działu 9** — automatyczna podstrona i dopasowanie do motywu to **sztandarowe wymaganie klienta**, za duże na jednego agenta „front".

**Cel:** podstrona „Nasze motory" tworzy się sama i wygląda jak reszta strony — **niezależnie od motywu**, do którego wtyczkę wepniemy.

## Agenci
### agent: podstrona
- **Zadanie:** przy aktywacji utworzyć stronę „Nasze motory" (idempotentnie, guard przed duplikatem), wstawić blok/shortcode listy, dodać do menu — **block theme:** `wp_navigation`; **classic theme:** menu location. Bez podwójnej pozycji w menu.

### agent: motyw
- **Zadanie:** podstrona dziedziczy wygląd aktywnego motywu — render przez `the_content`/wrappery blokowe, **bez sztywnych kolorów/fontów**, użycie zmiennych CSS i klas motywu (`wp-block-*`), tak by pasowała do dowolnego motywu bez konfiguracji.

## Krytyk
### krytyk: zgodność-wizualna
Odrzuca gdy: na motywie block (np. Twenty Twenty-Five) i classic podstrona odstaje od reszty (nadpisane fonty/kolory motywu); duplikat pozycji „Nasze motory" w menu; brak responsywności; sztywne style łamią spójność.
