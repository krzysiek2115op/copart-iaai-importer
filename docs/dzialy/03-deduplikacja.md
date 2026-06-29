# Dział 3 · DEDUPLIKACJA — dokumentacja działu

> Jeden dział = jedna dokumentacja. 1 agent : 1 krytyk.

Cel: nie dopuścić, by to samo auto trafiło do bazy dwa razy — bez błędnego łączenia
RÓŻNYCH aut. Oryginał zewnętrzny niepotrzebny: to nasza logika dopasowania na kluczach.

### 🔵 `match` → 🔴 `fałszywe-trafienia`  ✅ zaimplementowany
Kod: [`scraper/dzialy/03_deduplikacja/match.py`](../../scraper/dzialy/03_deduplikacja/match.py).

**Polityka dopasowania (od najpewniejszej):**
1. **`salvage_id`** — pewny klucz lotu. Dokładne duplikaty **usuwane**.
2. **Pełny VIN** (NIE zamaskowany, 17 znaków) — to samo fizyczne auto wystawione
   ponownie pod innym lotem → grupa **„relist"** (oznaczana w `relist_group`, nie kasowana).
3. **Dopasowanie miękkie** (marka+model+rok+przebieg+oddział) → **kandydat**
   (`dup_candidates`). **Nie łączymy automatycznie** — różne auta bywają identyczne w polach.

**Dlaczego tak:** VIN jest **maskowany anonimowo** (`...******`), więc dedup po VIN tylko
dla pełnych VIN-ów; zamaskowane nigdy nie służą do łączenia (różne auta mają ten sam
zamaskowany prefiks).

**🔴 Krytyk `fałszywe-trafienia`:** pilnuje, by nie powstał błędny merge — relisty muszą
opierać się na pełnym VIN; miękkich kandydatów zgłasza do **ręcznej weryfikacji**, nigdy
nie łączy automatycznie.

**Zweryfikowane (fikstura):** 5 rekordów → 4 unikalne (1 dokładny dup usunięty);
relist [111,222] po pełnym VIN; zamaskowane [333,444] NIE złączone; miękki kandydat
[BMW 335i 2011 …] zgłoszony, nie złączony.

## Przepływ
`normalizacja` (JSONL) → `match` → dalej do działu 4 (synchronizacja). Wyjście wzbogacone
o `relist_group` i `dup_candidates` (podpięcie do bazy = technikalia na potem).
