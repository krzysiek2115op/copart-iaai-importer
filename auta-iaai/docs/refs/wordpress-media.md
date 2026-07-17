# Referencja: WordPress media + szablony — oryginał dla działu „front i media"

> developer.wordpress.org (media_sideload_image). Stan: 2026-06-29.

## media_sideload_image()
```php
media_sideload_image( string $file, int $post_id, ?string $desc = null,
                      string $return_type = 'html' ) : string|int|WP_Error
```
- `$file` — URL obrazu (u nas: `vis.iaai.com/resizer?...`)
- `$return_type` — `'id'` (ID załącznika), `'src'`, `'html'`
- Poza `/wp-admin/` wymagane include:
```php
require_once ABSPATH . 'wp-admin/includes/media.php';
require_once ABSPATH . 'wp-admin/includes/file.php';
require_once ABSPATH . 'wp-admin/includes/image.php';
```
- Miniatura: `set_post_thumbnail( $post_id, $attachment_id )`.

## Front (szablony)
- Lista: `add_shortcode('iaai_pojazdy', …)` + `WP_Query` → karty (escapowane `esc_html/esc_url`).
- Pojedynczy: `add_filter('the_content', …)` przy `is_singular('pojazd')` → tabela danych + galeria
  (`wp_get_attachment_image()` — bezpieczne).

## Zastosowanie (dział front i media)
`includes/front.php`: `iaai_import_images()` (lazy sideload, miniatura+galeria),
shortcode `iaai_render_list`, filtr `iaai_render_single`, krytyk `iaai_krytyk_render`.
