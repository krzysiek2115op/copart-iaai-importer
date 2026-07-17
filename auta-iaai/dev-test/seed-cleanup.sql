-- ==========================================================================
-- SPRZĄTANIE po teście — usuwa TYLKO auta testowe (salvage_id 900001–900999).
-- Zamień `wp_` na swój prefiks, jeśli inny.
-- Po tym uruchom jeszcze publikację, aby zdjąć testowe wpisy ze strony:
--   wp eval 'iaai_unpublish_inactive();'
-- albo skasuj wpisy CPT:
--   wp post delete $(wp post list --post_type=pojazd --format=ids) --force
-- ==========================================================================
DELETE FROM wp_iaai_vehicle_images WHERE salvage_id BETWEEN 900001 AND 900999;
DELETE FROM wp_iaai_vehicles        WHERE salvage_id BETWEEN 900001 AND 900999;
