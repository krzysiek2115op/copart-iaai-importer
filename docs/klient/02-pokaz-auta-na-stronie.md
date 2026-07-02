# Etap 2 — Pokaż auta na stronie

> ✅ **Zwykle nie musisz tu nic robić.** Po włączeniu wtyczki (Etap 1) sama
> tworzy się gotowa podstrona **„Nasze auta"** z siatką aut, dopasowana do
> wyglądu Twojego motywu (kolory, fonty) i responsywna (ładnie działa na
> telefonie). Wtyczka próbuje też **dodać ją do głównego menu**.
>
> Znajdziesz ją w **Strony → Nasze auta** (adres `.../nasze-auta`).
> Auta wypełnią ją naprawdę dopiero po **Etapie 3** (uruchomienie automatyzacji).
>
> Reszta tej instrukcji przyda się tylko, gdy chcesz **dodatkową** stronę z autami
> albo gdy menu nie dodało się samo (patrz sekcja na dole).

Do ręcznego wstawienia aut w dowolnym miejscu używamy tzw. **krótkiego kodu**
(ang. *shortcode*) — gotowego „klocka", który wstawiasz raz, a on sam pokazuje pojazdy.

---

## Krok po kroku (opcjonalnie — własna, dodatkowa strona)

**1. Menu po lewej:** **Strony → Dodaj nową stronę**

**2. Wpisz tytuł**, np. `Nasze auta` albo `Oferta`.

**3. Kliknij „+” (dodaj blok)** i wyszukaj blok **„Krótki kod"** (ang. *Shortcode*).

```
Wpisz „/krótki kod" albo kliknij [+] i wyszukaj:  Krótki kod
```

**4. W bloku wklej dokładnie ten tekst:**

```
[iaai_pojazdy ile="12"]
```

`ile="12"` = ile aut pokazać (możesz zmienić, np. `ile="24"`).

**5. Kliknij „Opublikuj"** (prawy górny róg) i potwierdź.

✅ **Gotowe.** Strona pokazuje siatkę aut (miniatura + przebieg w km + uszkodzenie).
Po kliknięciu w auto otwiera się jego strona ze zdjęciami i danymi.

---

## Menu nie dodało się samo?
Wtyczka dopina „Nasze auta" do menu automatycznie, ale jeśli Twój motyw nie ma
jeszcze ustawionego menu, zrób to raz ręcznie:
**Wygląd → Menu** → zaznacz stronę „Nasze auta" → **Dodaj do menu** → **Zapisz menu**.

## Dobrze wiedzieć
- **Zdjęcia** ładują się wprost z serwerów IAAI (nie zajmują miejsca na Twoim hostingu).
- Auta **pojawiają się i znikają same** — gdy auto schodzi z aukcji, jego wpis znika ze strony
  (zostaje ukryty jako szkic, nie kasujemy historii).
- Każde auto ma też własny adres (WordPress robi je automatycznie pod `/pojazdy/...`).

Następnie: **[Etap 3 — uruchom automatyzację →](03-uruchom-automatyzacje.md)**.
