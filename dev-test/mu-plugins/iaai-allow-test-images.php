<?php
/**
 * TYLKO DO TESTU LOKALNEGO.
 *
 * Wtyczka domyślnie pokazuje zdjęcia wyłącznie z domeny IAAI (anty-SSRF).
 * Ten mały dodatek pozwala hotlinkować obrazy z placehold.co, żeby na
 * testowych autach było widać zdjęcia.
 *
 * INSTALACJA: skopiuj ten plik do  wp-content/mu-plugins/  (utwórz katalog,
 * jeśli go nie ma). „mu-plugins" ładują się same, bez włączania.
 *
 * ⚠ USUŃ ten plik przed wdrożeniem produkcyjnym.
 */
add_filter( 'iaai_allowed_image_hosts', function ( $hosts ) {
	$hosts[] = 'placehold.co';
	return $hosts;
} );
