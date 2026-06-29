# Dział 8 · PUBLIKACJA — dokumentacja działu

> Jeden dział = jedna dokumentacja. 1 agent : 1 krytyk. Wtyczka WordPress (PHP).

Cel: zamienić rekordy z nowej bazy na wpisy WordPressa typu **„pojazd" (CPT)** + meta,
gotowe do wyświetlenia na stronie.

Oryginał: [`docs/refs/wordpress-cpt.md`](../refs/wordpress-cpt.md).
Kod: [`wp-plugin/iaai-importer/includes/publikacja.php`](../../wp-plugin/iaai-importer/includes/publikacja.php).

### 🔵 `CPT` → 🔴 `poprawność-CPT`
- **Agent:** `register_post_type('pojazd', …)`; `iaai_publish_vehicle($id)` tworzy/aktualizuje
  wpis z rekordu bazy (powiązanie przez meta `iaai_salvage_id`, odczyt `$wpdb->prepare`).
- **Krytyk `poprawność-CPT`:** dla każdego `salvage_id` istnieje **dokładnie jeden** wpis CPT.

### 🔵 `meta` → 🔴 `poprawność-meta`
- **Agent:** `register_post_meta()` dla pól pojazdu (`iaai_*`, typy + `sanitize_callback`);
  `update_post_meta()` przy publikacji (dane sanityzowane przez dział 6).
- **Krytyk `poprawność-meta`:** kluczowe meta (`iaai_make/model/year/odometer`) ustawione.

Kontrola: `iaai_krytyk_publikacja($salvage_id)` sprawdza oba po publikacji.

> PHP/WP niewykonywalne lokalnie — kod zgodny ze standardem WP (weryfikacja statyczna).

## Przepływ
`bezpieczeństwo`/`zgodność` → `publikacja` (CPT + meta) → dział 9 (front i media → strona WP).
