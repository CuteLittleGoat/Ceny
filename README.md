# Ceny telefonów (PL) — pełna dokumentacja projektu

Projekt **Ceny** to statyczna aplikacja webowa do monitorowania i porównywania cen smartfonów w polskich sklepach internetowych. System został zaprojektowany tak, aby:
- zbierać dane cenowe z konkretnych kart produktów,
- agregować je do jednego spójnego widoku,
- utrzymywać historię cen w czasie,
- publikować dashboard bez backendu (GitHub Pages),
- działać automatycznie według harmonogramu (GitHub Actions).

---

## 1) Cel i zakres aplikacji

### Główny cel
Aplikacja służy do codziennego śledzenia cen konkretnych modeli telefonów (zdefiniowanych z góry), aby łatwo porównać:
- aktualną najniższą cenę,
- sklep z najlepszą ofertą,
- zmiany cenowe,
- podstawowe statystyki historyczne (min/max).

### Co porównujemy
- **Wyłącznie konkretne modele i warianty RAM/pamięć** z pliku `config/products.json`.
- **Wyłącznie oferty bez abonamentu/operatora**.
- **Wyłącznie wybrane źródła** (sklepy i oficjalne kanały), które mają status i zasady wiarygodności.

### Czego projekt nie robi
- Nie jest to pełna porównywarka całego rynku (brak dowolnego wyszukiwania produktów).
- Nie ma dynamicznego backendu API ani bazy SQL.
- Nie omija CAPTCHA, WAF ani agresywnych blokad antybotowych.
- Nie pobiera cen z losowych stron — działa tylko na wcześniej przygotowanych linkach do kart produktów.

---

## 2) Architektura rozwiązania

Projekt ma trzy logiczne warstwy:

1. **Konfiguracja źródeł i modeli**
   - `config/products.json` — lista modeli + lista źródeł URL.
   - `config/stores.json` — słownik sklepów i ich metadane.

2. **Warstwa ETL / pobieranie i przetwarzanie danych**
   - `scripts/fetch_prices.py`:
     - pobiera HTML,
     - parsuje cenę i dostępność,
     - waliduje dane,
     - zapisuje wyniki bieżące i historyczne.

3. **Warstwa prezentacji (frontend statyczny)**
   - `index.html` + `docs/app.js` + `docs/styles.css`.
   - Interfejs ładuje JSON-y i renderuje tabelę, filtry, podsumowania oraz wykres historii.

W praktyce jest to pipeline typu **Config → Fetch/Parse → JSON/CSV → Dashboard**.

---

## 3) Model danych i kluczowe pliki

## `config/products.json`
Najważniejszy plik domenowy projektu.

Każdy rekord modelu zawiera m.in.:
- `display_order` — kolejność na dashboardzie,
- `model_id`, `model_name`, `ram_gb`, `storage_gb`,
- `colors_as_same_model` — czy kolory traktujemy jako ten sam model,
- `sources` — lista źródeł (sklep + URL + status operacyjny).

Każde źródło w `sources` zawiera m.in.:
- `store_id`, `store_name`,
- `url` (lub `null`, jeśli brak wiarygodnej karty),
- `variant_label`, `color`,
- `scrape_enabled` (czy skrypt ma realnie próbować odczytu),
- `status` (`ok`, `manual_review`, `withdrawn`, `not_found`, `blocked_or_unreliable`, `marketplace`, `future_or_not_yet_available`),
- `notes` — komentarz operacyjny.

### `config/stores.json`
Słownik sklepów i źródeł. Pozwala utrzymać spójne identyfikatory i metadane sklepów używane przez skrypt i frontend.

### `data/latest.json`
Najnowszy snapshot danych do dashboardu (stan „tu i teraz”).

### `data/errors.json`
Lista błędów i pominiętych źródeł z ostatniego uruchomienia (diagnostyka).

### `data/prices.csv`
Historia rekordów cenowych (append-only, pełny dziennik odczytów).

### `data/prices.json`
Wersja JSON historii (ułatwia wczytanie do wykresu po stronie frontendu).

---

## 4) Szczegóły działania skryptu `fetch_prices.py`

Skrypt jest sercem systemu i realizuje pełny przebieg aktualizacji.

### Krok A — inicjalizacja i wczytanie danych
- Wczytuje konfigurację produktów i sklepów.
- Wczytuje historię (`data/prices.csv`) do wyliczeń trendów.
- Przygotowuje znaczniki czasu (`timestamp`, `date`).

### Krok B — iteracja po modelach i źródłach
Dla każdego modelu:
1. Przechodzi po `sources`.
2. Sprawdza, czy źródło jest aktywne (`scrape_enabled`) i czy ma parser.
3. Pobiera HTML przez `urllib` z ustawionym `User-Agent` i timeout.

### Krok C — parsowanie danych
Aktualnie istnieją parsery dedykowane dla:
- `morele`,
- `rtv-euro-agd`,
- `x-kom`.

Mechanika parsowania:
- Najpierw próba odczytu `JSON-LD` (`application/ld+json`, typ `Product`).
- Fallback regexem dla ceny, gdy JSON-LD nie jest wystarczający.
- Normalizacja pola dostępności do wartości kontrolowanych (`in_stock`, `out_of_stock`, `preorder`, `withdrawn`, `unknown`).
- Normalizacja ceny (`parse_price`) z walidacją i odrzucaniem wartości nielogicznych.

### Krok D — walidacja i wybór najlepszej oferty
- Odrzucane są odczyty bez poprawnej ceny.
- Działa kontrola „plausible phone price” (zakres 300–20000 PLN).
- Dla modelu wybierana jest **najlepsza oferta**: preferowane oferty `in_stock`, a następnie najniższa cena.

### Krok E — zapis wyników
- Dopisywane są nowe wiersze do `data/prices.csv`.
- Aktualizowany jest `data/prices.json`.
- Generowany jest `data/latest.json` dla frontendu.
- Zapisywane są problemy do `data/errors.json`.

---

## 5) Jak działa frontend (`index.html` + `docs/app.js`)

Frontend jest statyczny i nie wymaga backendu aplikacyjnego.

### Co ładuje aplikacja
Po uruchomieniu strona pobiera równolegle:
- `data/latest.json`,
- `config/products.json`,
- `config/stores.json`,
- `data/errors.json`,
- `data/prices.json`.

### Co renderuje UI
- Podsumowanie: liczba modeli, liczba modeli z danymi, czas wygenerowania, liczba źródeł.
- Tabela modeli: nazwa, wariant RAM/pamięć, najlepsza cena, sklep, zmiana ceny, min/max historyczne, dostępność, czas ostatniego sukcesu, link oferty.
- Filtrowanie: po nazwie modelu, sklepie, statusie danych.
- Sortowanie: m.in. po cenie, zmianie, nazwie, kolejności `display_order`.
- Wykres historii (Chart.js) dla wybranego modelu.

### Statusy widoczne dla użytkownika
UI pokazuje m.in.:
- „OK” dla modeli z ceną,
- „Brak danych”,
- „Czekamy na oferty” dla statusów typu future/not yet available.

---

## 6) Założenia jakości danych

Projekt celowo stawia jakość nad ilość:

1. **Lepszy brak ceny niż fałszywa cena.**
   Jeśli nie da się uzyskać wiarygodnego odczytu, wartość powinna pozostać pusta (`null`).

2. **Źródła aktywne tylko po weryfikacji.**
   `scrape_enabled: true` ustawiamy tylko dla realnych i stabilnych kart produktu.

3. **Brak mieszania wariantów.**
   Model 12/512 nie może „łapać” ceny 8/256.

4. **Kolory jako ten sam model (gdy tak wskazuje konfiguracja).**
   Różne kolory tego samego RAM/pamięć traktowane są jako jeden byt porównawczy.

5. **Status operacyjny zawsze jawny.**
   Każde źródło ma status i notatkę, co ułatwia utrzymanie i audyt.

---

## 7) Ograniczenia techniczne i operacyjne

- Część sklepów może zwracać `403` lub dynamicznie ukrywać dane.
- Nie wszystkie sklepy mają gotowe parsery.
- Strony silnie JS-first mogą być trudne do parsowania bez silnika przeglądarki.
- Projekt nie korzysta z headless browsera ani komercyjnych proxy.
- Aktualność zależy od harmonogramu workflow i dostępności źródeł.

---

## 8) Uruchomienie lokalne

### Wymagania
- Python 3.10+ (zalecane 3.11+).
- Dostęp do internetu.

### Kroki
```bash
python3 scripts/fetch_prices.py
python3 -m http.server 8000
```
Następnie otwórz: `http://localhost:8000`.

Po pierwszym kroku odświeżane są pliki `data/*.json` i `data/prices.csv`.
Po drugim kroku uruchamiasz lokalny podgląd dashboardu.

---

## 9) Publikacja i automatyzacja

Docelowy model pracy:
- kod i konfiguracja w repozytorium,
- cykliczne uruchamianie skryptu przez GitHub Actions,
- commit/aktualizacja artefaktów danych,
- publikacja statycznej strony przez GitHub Pages.

Dzięki temu aplikacja działa bez stałego serwera backendowego i bez utrzymywania infrastruktury runtime.

---

## 10) Jak rozwijać projekt dalej

Najbardziej wartościowe kierunki:

1. **Nowe parsery sklepów**
   - np. Komputronik, Media Expert, oficjalne sklepy producentów.

2. **Lepsza odporność parserów**
   - bardziej precyzyjne selektory,
   - fallbacki semantyczne,
   - testy regresji parserów na próbkach HTML.

3. **Monitoring jakości**
   - alerty przy nagłym spadku liczby poprawnych odczytów,
   - raportowanie skuteczności per sklep.

4. **Rozszerzenia UI**
   - wykresy porównawcze wielu modeli,
   - mediany/średnie kroczące,
   - eksport wyfiltrowanego widoku.

---

## 11) Podsumowanie

**Ceny** to praktyczna, lekka i kontrolowalna platforma do monitorowania cen smartfonów:
- statyczna po stronie frontendu,
- deterministyczna po stronie danych,
- oparta na jawnej konfiguracji źródeł,
- nastawiona na wiarygodność odczytu i łatwe utrzymanie.

Jej siła wynika z przejrzystych zasad: precyzyjne linki produktowe, kontrola statusów źródeł, ostrożne aktywowanie scrapingu oraz pełna historia zmian cen.
