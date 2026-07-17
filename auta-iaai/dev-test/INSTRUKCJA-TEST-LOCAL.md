# Test ręczny wtyczki na lokalnym WordPressie („gołym okiem")

Cel: wgrać wtyczkę na lokalną stronę (np. „Kredyt Kompas" w Local/XAMPP/Laragon),
sprawdzić, że **sama tworzy się podstrona „Nasze auta"**, że działa siatka aut,
strona pojedynczego auta i SEO. Scraper NIE jest tu potrzebny — kilka aut wrzucamy
ręcznie seedem, żeby było co oglądać.

> Bez scrapera baza jest pusta, więc strona „Nasze auta" pokaże „Brak pojazdów".
> To normalne — dlatego w kroku 5 wrzucamy testowe auta.

---

## 0. Czego potrzebujesz
- Lokalny WordPress (Local by WP Engine / XAMPP / Laragon / wp-env).
- Dostęp do bazy (Adminer/phpMyAdmin) — w **Local** zakładka **Database → Open Adminer**.
- WP-CLI — w **Local**: prawy klik na stronie → **Open site shell** (WP-CLI jest w środku).

---

## 1. Spakuj wtyczkę do ZIP
Spakuj **sam folder** `wp-plugin/iaai-importer` → powstanie `iaai-importer.zip`.
(Windows: prawy klik na folder → „Wyślij do → Folder skompresowany (ZIP)".)

Albo z terminala w katalogu projektu:
```
cd wp-plugin && zip -r ../iaai-importer.zip iaai-importer && cd ..
```

## 2. Wgraj i włącz wtyczkę
Panel WP → **Wtyczki → Dodaj nową → Wyślij wtyczkę na serwer** → wybierz
`iaai-importer.zip` → **Zainstaluj teraz** → **Włącz wtyczkę**.

## 3. Sprawdź, co zrobiła się SAMO (najważniejszy moment testu) ✅
- **Wtyczki → Zainstalowane** → „IAAI Importer" aktywna.
- W menu po lewej pojawia się **„Pojazdy"**.
- **Strony → Wszystkie strony** → istnieje **„Nasze auta"** (adres `/nasze-auta`).
- **Tabele w bazie** (Adminer): są `wp_iaai_vehicles` i `wp_iaai_vehicle_images`.
- **Menu**: jeśli motyw ma klasyczne menu — „Nasze auta" jest w nim dopięte.
  ⚠ Motywy blokowe (Twenty Twenty-Four/Five) często nie mają klasycznych menu —
  wtedy pozycja NIE doda się automatycznie (to zaplanowane zachowanie), a stronę
  dodasz ręcznie w edytorze motywu. Sama strona i tak istnieje.

## 4. (Opcjonalnie) pozwól na zdjęcia testowe
Żeby na testowych autach było widać obrazki (z placehold.co), skopiuj plik
`dev-test/mu-plugins/iaai-allow-test-images.php` do `wp-content/mu-plugins/`
(utwórz katalog `mu-plugins`, jeśli go nie ma). Bez tego auta pokażą się bez zdjęć
— to też jest poprawny wynik (allowlista SSRF działa).

## 5. Wrzuć testowe auta do bazy
W Adminer/phpMyAdmin otwórz zakładkę **SQL** i wklej zawartość
`dev-test/seed-pojazdy.sql` → wykonaj.
Albo z site shell:
```
wp db query < dev-test/seed-pojazdy.sql
```
> Jeśli Twój prefiks tabel nie jest `wp_` (sprawdź w `wp-config.php`:
> `$table_prefix`), zamień `wp_` w seedzie na swój.

## 6. Opublikuj auta (zamiana rekordów bazy na wpisy „Pojazd")
Wtyczka pokazuje na stronie **wpisy CPT**, nie surową tabelę — trzeba raz odpalić
publikację. W **site shell** (WP-CLI):
```
wp eval 'iaai_publish_all_active();'
```
Powinno zwrócić liczbę opublikowanych (np. `6`).

## 7. Obejrzyj efekt gołym okiem 👀
- **Strona „Nasze auta"** (`/nasze-auta`): siatka kart — miniatura, „rok marka model",
  przebieg w km, uszkodzenie. Zwęź okno przeglądarki → siatka ma się zwijać
  (responsywność): 3–4 kolumny → 2 → 1.
- **Klik w auto** → strona pojazdu: tabela danych (VIN, rok, przebieg…) + galeria zdjęć.
- **Archiwum** `/pojazdy` → lista wszystkich aut (z motywu).
- Sprawdź, że wygląd **pasuje do motywu** (kolory/fonty dziedziczone).

## 8. Sprawdź SEO (widok źródła strony auta)
Na stronie pojedynczego auta: prawy klik → **Pokaż źródło strony** i poszukaj:
- `application/ld+json` → blok Schema.org `"@type":"Car"` (marka, model, rok, przebieg, zdjęcia).
- `<meta name="description"` oraz `og:title` / `og:image` (jeśli nie masz wtyczki SEO).
- Wklej adres auta w **Google Rich Results Test** (rich-results-test) — powinien
  wykryć obiekt „Pojazd/Car".

## 9. Sprawdź „znikanie" auta (opcjonalnie)
W Adminer zmień jednemu autu `status` z `active` na `sold`, potem:
```
wp eval 'iaai_publish_all_active();'
```
→ to auto powinno zniknąć ze strony (wpis przechodzi w szkic).

---

## 10. Sprzątanie po teście
```
wp db query < dev-test/seed-cleanup.sql
wp eval 'iaai_unpublish_inactive();'
```
Usuń też `wp-content/mu-plugins/iaai-allow-test-images.php`.
(Ewentualnie skasuj wpisy: `wp post delete $(wp post list --post_type=pojazd --format=ids) --force`.)

---

## Co ma wyjść (lista kontrolna)
- [ ] Wtyczka aktywna, brak błędów po włączeniu.
- [ ] Tabele `wp_iaai_vehicles` i `wp_iaai_vehicle_images` istnieją.
- [ ] Strona „Nasze auta" utworzona SAMA.
- [ ] Po seedzie + publikacji widać siatkę aut, responsywną, w stylu motywu.
- [ ] Strona pojedynczego auta: dane + galeria.
- [ ] W źródle strony jest JSON-LD „Car" (SEO).
- [ ] Zmiana statusu na `sold` + publikacja → auto znika ze strony.

## Gdyby coś nie zagrało
- „Brak pojazdów" mimo seeda → nie uruchomiłeś kroku 6 (`iaai_publish_all_active`),
  albo zły prefiks tabel w seedzie.
- Auta bez zdjęć → nie skopiowałeś mu-plugina z kroku 4 (to OK dla testu danych).
- Błąd przy wgrywaniu ZIP → wysyłasz folder zamiast pliku ZIP, albo limit uploadu
  (wgraj folder `iaai-importer` przez plik-menedżer do `wp-content/plugins/`).
- Strona „Nasze auta" nie powstała → wejdź do panelu (tworzy się też przy `admin_init`),
  albo dezaktywuj i włącz wtyczkę ponownie.
