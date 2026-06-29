# Referencja: WordPress CPT + meta — oryginał dla działu „publikacja"

> developer.wordpress.org (register_post_type / register_post_meta). Stan: 2026-06-29.

## register_post_type()
```php
register_post_type( string $post_type, array $args ) : WP_Post_Type|WP_Error
```
```php
add_action( 'init', function () {
    register_post_type( 'pojazd', array(
        'labels'       => array( 'name' => 'Pojazdy', 'singular_name' => 'Pojazd' ),
        'public'       => true,
        'show_in_rest' => true,                 // Gutenberg + REST API
        'has_archive'  => true,                 // strona archiwum /pojazdy
        'supports'     => array( 'title', 'editor', 'thumbnail', 'custom-fields' ),
        'rewrite'      => array( 'slug' => 'pojazdy' ),
    ) );
} );
```

## register_post_meta()
```php
register_post_meta( 'pojazd', 'iaai_vin', array(
    'type'              => 'string',
    'single'            => true,
    'show_in_rest'      => true,
    'sanitize_callback' => 'sanitize_text_field',
) );
```

## Zapis/aktualizacja wpisu
- `wp_insert_post()` / `wp_update_post()` (po `ID`); powiązanie z lotem przez meta
  `iaai_salvage_id` (`get_posts` z `meta_key`/`meta_value`).
- `update_post_meta()` dla każdego pola.
- Odczyt z bazy zawsze `$wpdb->prepare()` (dział 6).

## Zastosowanie (dział publikacja)
`includes/publikacja.php`: rejestracja CPT „pojazd" + meta, `iaai_publish_vehicle($id)`
(upsert wpisu z bazy), `iaai_publish_all_active()`, krytyk `iaai_krytyk_publikacja()`.
