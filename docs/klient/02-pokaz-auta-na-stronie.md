# Etap 2 — Pokaż auta na stronie

Cel: stworzyć stronę, na której wyświetlą się auta. Używamy tzw. **krótkiego kodu**
(ang. *shortcode*) — to gotowy „klocek", który wstawiasz raz, a on sam pokazuje pojazdy.

> Auta pojawią się tu naprawdę dopiero po **Etapie 3** (gdy uruchomisz automatyzację).
> Stronę możesz jednak przygotować już teraz.

---

## Krok po kroku

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

## Gdzie wstawić, żeby był link w menu?
**Wygląd → Menu** → dodaj utworzoną stronę („Nasze auta") do menu na stronie.

## Dobrze wiedzieć
- **Zdjęcia** ładują się wprost z serwerów IAAI (nie zajmują miejsca na Twoim hostingu).
- Auta **pojawiają się i znikają same** — gdy auto schodzi z aukcji, jego wpis znika ze strony
  (zostaje ukryty jako szkic, nie kasujemy historii).
- Każde auto ma też własny adres (WordPress robi je automatycznie pod `/pojazdy/...`).

Następnie: **[Etap 3 — uruchom automatyzację →](03-uruchom-automatyzacje.md)**.
