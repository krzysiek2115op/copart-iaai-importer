<!-- SPDX-License-Identifier: GPL-2.0-or-later -->
# Dział 6 · BEZPIECZEŃSTWO (WordPress)

**Cel:** dane z bazy i akcje admina bezpieczne w WordPressie; poświadczenia osobnej bazy chronione.

## Agenci
### agent: sanityzacja
- **Zadanie:** każde pole na wyjściu escapowane (`esc_html`/`esc_url`/`esc_attr`); zapytania przez `$wpdb->prepare`; **poświadczenia osobnej bazy MySQL** trzymane bezpiecznie (stałe w `wp-config.php` lub szyfrowana opcja) — nigdy w kodzie/repo.

### agent: nonce
- **Zadanie:** akcje admina (ręczny import, zapis ustawień) chronione `wp_nonce` + `current_user_can`; żadnej akcji zmieniającej stan na czystym GET.

## Krytyk
### krytyk: podatności
Odrzuca gdy: `echo` bez escape; konkatenacja SQL zamiast `prepare`; sekret/poświadczenia w repo; brak nonce lub sprawdzenia uprawnień na akcji; XSS przez pole ze źródła.
