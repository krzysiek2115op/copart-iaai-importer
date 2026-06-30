# Etap 4 — Jak to działa i obsługa na co dzień

## Najważniejsze: na co dzień nie robisz NIC
Po Etapie 3 system działa sam. Auta pojawiają się i znikają automatycznie. Ten dokument jest
„do poczytania" — żebyś wiedział(a), co się dzieje pod spodem i jak ewentualnie coś zmienić.

---

## Jak to działa (cały obieg, prosto)
```
 co 15 minut:                          raz na dobę (03:30):
 „są nowe auta?"                       „pełna synchronizacja"
        │                                      │
        ▼                                      ▼
[1] Program wchodzi na IAAI i czyta listę aut (zdjęcia + dane)
        │
        ▼
[2] Porządkuje dane: przelicza mile→km, czyta markę/model z VIN, odrzuca błędne wpisy
        │
        ▼
[3] Zapisuje do bazy (ta sama baza, której używa Twój WordPress)
        │   — nowe auta dodaje, zmienione aktualizuje, znikłe oznacza jako „sprzedane/zdjęte"
        ▼
[4] Wtyczka publikuje auta jako wpisy „Pojazd" i pokazuje na stronie
        — auta zdjęte z aukcji znikają ze strony (zostają ukryte, nie kasujemy historii)
```

Dwa „zegary" (usługi w tle):
- **live** — co 15 minut: szybkie sprawdzenie nowych aut.
- **backfill** — raz na dobę o 03:30: pełna synchronizacja całości (porządkuje, co zniknęło).

---

## Proste zmiany (opcjonalnie)

### Zmienić, ile aut na stronie
Edytuj krótki kod na swojej stronie (Etap 2), np. `[iaai_pojazdy ile="24"]`.

### Zmienić częstotliwość sprawdzania (np. co 30 min)
Na serwerze:
```
sudo nano /etc/systemd/system/iaai-importer-live.timer
```
zmień `OnUnitInactiveSec=15min` na `=30min`, zapisz (Ctrl+O, Enter, Ctrl+X), potem:
```
sudo systemctl daemon-reload
sudo systemctl restart iaai-importer-live.timer
```

### Zatrzymać / wznowić automatyzację
```
sudo systemctl stop  iaai-importer-live.timer      # pauza
sudo systemctl start iaai-importer-live.timer      # wznów
```

---

## Co warto wiedzieć
- **Zdjęcia** nie zajmują miejsca na Twoim serwerze — ładują się wprost z IAAI.
- **VIN** w trybie anonimowym bywa częściowo zakryty (`...******`) — to normalne; markę, model i
  rok i tak rozpoznajemy z oficjalnej bazy pojazdów (NHTSA).
- **Sprzedane/zdjęte auta** nie są kasowane — znikają ze strony, ale zostają w bazie (historia).
- System sam **zwalnia tempo / odpuszcza**, gdy serwis IAAI zacznie blokować ruch.

Masz pytanie lub coś nie działa? → **[05-problemy-i-pytania.md](05-problemy-i-pytania.md)**.
