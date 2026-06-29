# Dział 9 · FRONT I MEDIA — dokumentacja działu

> Jeden dział = jedna dokumentacja. 1 agent : 1 krytyk. Wtyczka WordPress (PHP).
> **Ostatni dział** — tu dane stają się widoczne dla klienta na stronie.

Oryginał: [`docs/refs/wordpress-media.md`](../refs/wordpress-media.md).
Kod: [`wp-plugin/iaai-importer/includes/front.php`](../../wp-plugin/iaai-importer/includes/front.php).

### 🔵 `media` → 🔴 `render`
- **Agent:** `iaai_import_images($salvage_id, $post_id)` — sideload zdjęć z
  `iaai_vehicle_images` (URL `vis.iaai.com/resizer`) do biblioteki mediów WP
  (`media_sideload_image`), pierwsze = miniatura (`set_post_thumbnail`), reszta = galeria
  (meta `iaai_gallery`). Lazy (flaga `_iaai_media_done`).
- **Krytyk `render` (media):** post ma miniaturę; liczba zaimportowanych = liczba zdjęć w bazie.

### 🔵 `front` → 🔴 `render`
- **Agent:** shortcode `[iaai_pojazdy]` (siatka kart) + filtr `the_content` dla pojedynczego
  pojazdu (tabela danych + galeria). Całe wyjście **escapowane** (`esc_html/esc_url`,
  `wp_get_attachment_image`).
- **Krytyk `render` (front):** brak surowego echo — wszystko przez `esc_*` (anty-XSS).

> PHP/WP niewykonywalne lokalnie — kod zgodny ze standardem WP (weryfikacja statyczna).
> Runtime po wpięciu do instalacji WordPress + ustawieniu połączenia z nową bazą.

## Przepływ (koniec pipeline'u)
`publikacja` (CPT+meta) → `front i media` (miniatura, galeria, szablony) → **Strona WordPress**
(odwiedzający widzi listę i strony pojazdów).
