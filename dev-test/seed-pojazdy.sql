-- ==========================================================================
-- SEED TESTOWY — kilka przykładowych aut do wizualnego sprawdzenia wtyczki
-- LOKALNIE (bez scrapera). NIE używać na produkcji.
--
-- Prefiks tabel: domyślnie `wp_`. Jeśli Twój WordPress ma inny prefiks
-- (sprawdź w wp-config.php:  $table_prefix = 'xyz_';) — zamień wszystkie
-- `wp_` poniżej na swój prefiks.
--
-- Uruchom w Adminer/phpMyAdmin (zakładka „SQL") albo:  wp db query < seed-pojazdy.sql
-- ==========================================================================

INSERT INTO wp_iaai_vehicles
  (salvage_id, vin, year, make, model, body_style, odometer, odometer_uom,
   primary_damage, secondary_damage, color, fuel_type, transmission, drive_line,
   key_available, run_and_drive, title, selling_branch, buy_now, current_bid,
   detail_url, status)
VALUES
 (900001,'1HGCM82633A004352',2018,'Toyota','Camry','Sedan',105380,'mi',
  'Front End','Minor Dent/Scratches','White','Gasoline','Automatic','FWD',
  'Yes','Run and Drive','Salvage','TX - Dallas',8200,5100,
  'https://www.iaai.com/VehicleDetail/900001','active'),
 (900002,'2C3CDXBG5FH123456',2016,'Dodge','Charger','Sedan',88231,'mi',
  'Rear End',NULL,'Black','Gasoline','Automatic','RWD',
  'Yes','Run and Drive','Salvage','CA - Los Angeles',6900,4300,
  'https://www.iaai.com/VehicleDetail/900002','active'),
 (900003,'1FTFW1ET5DFC12345',2019,'Ford','F-150','Pickup',42210,'mi',
  'Side','All Over','Blue','Gasoline','Automatic','4WD',
  'Yes','Run and Drive','Clean','FL - Miami',15400,11200,
  'https://www.iaai.com/VehicleDetail/900003','active'),
 (900004,'5YJ3E1EA7KF123456',2019,'Tesla','Model 3','Sedan',33110,'mi',
  'Front End',NULL,'Red','Electric','Automatic','RWD',
  'No','Starts','Salvage','NJ - Somerville',18900,14000,
  'https://www.iaai.com/VehicleDetail/900004','active'),
 (900005,'WBA8E9G50GNT12345',2016,'BMW','328i','Sedan',77650,'mi',
  'Rear','Minor Dent/Scratches','Gray','Gasoline','Automatic','RWD',
  'Yes','Run and Drive','Salvage','IL - Chicago',7300,4900,
  'https://www.iaai.com/VehicleDetail/900005','active'),
 (900006,'1N4AL3AP7JC123456',2018,'Nissan','Altima','Sedan',60120,'mi',
  'Water/Flood',NULL,'Silver','Gasoline','Automatic','FWD',
  'No','Does Not Run','Salvage','TX - Houston',3200,2100,
  'https://www.iaai.com/VehicleDetail/900006','active');

-- Zdjęcia (placeholdery, żeby było widać obrazy). Aby się pokazały, host
-- placehold.co musi być dozwolony — patrz dev-test/mu-plugins/iaai-allow-test-images.php
INSERT INTO wp_iaai_vehicle_images (salvage_id, image_key, seq, width, height, url) VALUES
 (900001,'t900001-1',1,600,400,'https://placehold.co/600x400/1f4fd8/ffffff?text=Toyota+Camry+1'),
 (900001,'t900001-2',2,600,400,'https://placehold.co/600x400/12203a/ffffff?text=Toyota+Camry+2'),
 (900002,'t900002-1',1,600,400,'https://placehold.co/600x400/111111/ffffff?text=Dodge+Charger'),
 (900003,'t900003-1',1,600,400,'https://placehold.co/600x400/2b6cb0/ffffff?text=Ford+F-150'),
 (900004,'t900004-1',1,600,400,'https://placehold.co/600x400/c53030/ffffff?text=Tesla+Model+3'),
 (900005,'t900005-1',1,600,400,'https://placehold.co/600x400/4a5568/ffffff?text=BMW+328i'),
 (900006,'t900006-1',1,600,400,'https://placehold.co/600x400/718096/ffffff?text=Nissan+Altima');
