# Referencja: WordPress Security — oryginał dla działu „bezpieczeństwo"

> Z oficjalnej dokumentacji developer.wordpress.org/apis/security/. Stan: 2026-06-29.

## Zasady
- **Nigdy nie ufaj** wejściu użytkownika, API third-party ani danym w bazie.
- **Sanityzuj wejście**, **escapuj wyjście** (jak najpóźniej), **waliduj/odrzucaj** gdy się da.

## Funkcje (WordPress)
**Sanityzacja wejścia:**
- `sanitize_text_field()` — krótki tekst; `sanitize_textarea_field()` — wieloliniowy
- `absint()` — dodatnia liczba całkowita; `intval()` / `(float)` — liczby
- `sanitize_key()` — klucze (a-z0-9_-); `esc_url_raw()` — URL do zapisu w bazie
- `sanitize_email()`, `wp_kses_post()` — dozwolony HTML

**Escapowanie wyjścia (tuż przed echo):**
- `esc_html()` — tekst; `esc_attr()` — atrybut; `esc_url()` — URL; `wp_kses_post()` — HTML

**Nonce (CSRF):**
- `wp_nonce_field( $action, $name )` — pole w formularzu
- `wp_create_nonce()` / `wp_verify_nonce()`; `check_admin_referer( $action, $name )` — w handlerze
- + zawsze `current_user_can( $cap )`

**SQL (SQLi):**
- `$wpdb->prepare( "… WHERE id = %d AND k = %s", $id, $k )` — zawsze placeholdery `%d/%s/%f`

## Zastosowanie (dział bezpieczeństwo)
`includes/security.php`: `iaai_sanitize_vehicle()` (wejście), `iaai_escape_vehicle_for_output()`
(wyjście), `iaai_nonce_field()` + `iaai_verify_admin_action()` (akcje admina). Bezpieczna
ścieżka jest domyślna — używają jej działy 8 (publikacja) i 9 (front/media).
