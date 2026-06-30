# Etap 1 — Wgranie wtyczki do WordPress

Cel: zainstalować wtyczkę „IAAI Importer" w Twoim WordPressie. To samo klikanie, ~3 minuty.

> Najpierw spakuj folder wtyczki do pliku ZIP (jeśli dostałeś go rozpakowany):
> spakuj folder `wp-plugin/iaai-importer` → powstanie `iaai-importer.zip`.
> (Na Windowsie: prawy przycisk na folderze → „Wyślij do" → „Folder skompresowany (zip)".)

---

## Krok po kroku (gdzie kliknąć)

**1. Zaloguj się do panelu WordPress** — adres zwykle: `https://twojastrona.pl/wp-admin`

**2. Menu po lewej:** kliknij **Wtyczki → Dodaj nową wtyczkę**

```
┌──────────────────────────────┐
│  Kokpit                      │
│  Wpisy                       │
│  Media                       │
│  Strony                      │
│  ...                         │
│ ▸ Wtyczki        ← kliknij   │
│     • Zainstalowane wtyczki  │
│     • Dodaj nową wtyczkę  ←  │
└──────────────────────────────┘
```

**3. Na górze kliknij przycisk „Wyślij wtyczkę na serwer"** (ang. *Upload Plugin*)

```
[ Dodaj wtyczki ]   [ Wyślij wtyczkę na serwer ]  ← kliknij
```

**4. Kliknij „Wybierz plik"**, wskaż plik **`iaai-importer.zip`**, potem **„Zainstaluj teraz"**.

**5. Po chwili kliknij „Włącz wtyczkę"** (ang. *Activate Plugin*).

✅ **Gotowe.** W tym momencie wtyczka sama założyła w bazie potrzebne tabele (nic nie musisz robić).

---

## Skąd wiem, że się udało?
- Wejdź w **Wtyczki → Zainstalowane wtyczki** — na liście jest **„IAAI Importer"** (aktywna).
- W menu po lewej pojawi się nowa pozycja **„Pojazdy”** (tu trafią auta).

> Na razie lista „Pojazdy" będzie pusta — auta pojawią się po **Etapie 3** (automatyzacja).
> Najpierw zrób **[Etap 2 — pokaż auta na stronie →](02-pokaz-auta-na-stronie.md)**.

## Coś nie działa?
- „Wtyczka nie mogła zostać zainstalowana" → upewnij się, że wysyłasz **ZIP** (nie cały folder).
- Brak przycisku „Wyślij wtyczkę na serwer" → Twój hosting może blokować wgrywanie; wgraj folder
  `iaai-importer` przez FTP do `wp-content/plugins/`, potem włącz wtyczkę w panelu.
- Więcej: [05-problemy-i-pytania.md](05-problemy-i-pytania.md).
