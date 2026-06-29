# Dział 6 · BEZPIECZEŃSTWO — dokumentacja działu

> Jeden dział = jedna dokumentacja. 1 agent : 1 krytyk.
> To już **wtyczka WordPress (PHP)** — `wp-plugin/iaai-importer/`.

Cel: dane wchodzące do WP/bazy są sanityzowane, wychodzące escapowane, akcje admina
chronione nonce, SQL przez `$wpdb->prepare()`. Bezpieczna ścieżka = domyślna dla działów 8–9.

Oryginał: [`docs/refs/wordpress-security.md`](../refs/wordpress-security.md).
Kod: [`wp-plugin/iaai-importer/includes/security.php`](../../wp-plugin/iaai-importer/includes/security.php).

### 🔵 `sanityzacja` → 🔴 `podatności`
- **Agent:** `iaai_sanitize_vehicle()` — każde pole przez właściwą funkcję WP
  (`absint`, `sanitize_text_field`, `esc_url_raw`, `sanitize_key`); `iaai_escape_vehicle_for_output()`
  (`esc_html`/`esc_url`) tuż przed wyświetleniem.
- **Krytyk `podatności`:** checklista wymuszana kodem — każdy echo przez `esc_*`, każde
  SQL przez `$wpdb->prepare()` (chroni przed XSS / SQLi).

### 🔵 `nonce` → 🔴 `podatności`
- **Agent:** `iaai_nonce_field()` + `iaai_verify_admin_action()` (`check_admin_referer` +
  `current_user_can`) — chroni akcje admina przed CSRF / brakiem uprawnień.
- **Krytyk `podatności`:** każda akcja admina musi wołać `iaai_verify_admin_action()`.

> Uwaga: PHP/WP nie ma w środowisku do uruchomienia — kod zgodny ze standardem WP
> (weryfikacja statyczna). Runtime sprawdzony będzie po wpięciu do instalacji WordPress.

## Przepływ
`audyt` → (dane wchodzą do WP) `bezpieczeństwo` → dział 7 (zgodność).
