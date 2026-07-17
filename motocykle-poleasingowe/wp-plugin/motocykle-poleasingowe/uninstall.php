<?php
// SPDX-License-Identifier: GPL-2.0-or-later
// Sprzątanie przy usunięciu wtyczki. NIE dotyka zewnętrznej bazy polea_* (należy do scrapera).
if (!defined('WP_UNINSTALL_PLUGIN')) {
    exit;
}

$pid = (int) get_option('polea_nasze_motory_page_id');
if ($pid) {
    wp_delete_post($pid, true);
}
delete_option('polea_nasze_motory_page_id');

global $wpdb;
$wpdb->query(
    "DELETE FROM {$wpdb->options} WHERE option_name LIKE '\\_transient\\_polea\\_%' " .
    "OR option_name LIKE '\\_transient\\_timeout\\_polea\\_%'"
);
