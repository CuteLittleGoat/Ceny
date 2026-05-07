# Prompt dla agenta Codex — projekt „Ceny”

Pracujesz w repozytorium GitHub:

`CuteLittleGoat/Ceny`

Celem jest stworzenie czytelnej, estetycznej i funkcjonalnej strony do porównywania cen telefonów. Projekt ma działać jako statyczna aplikacja na GitHub Pages, a dane mają być przygotowywane i aktualizowane przez GitHub Actions.

## 1. Aktualny stan repozytorium

Repozytorium ma już podstawowy szkielet:

- `README.md`
- `index.html`
- `docs/app.js`
- `docs/styles.css`
- `config/products.json`
- `config/stores.json`
- `data/latest.json`
- `data/errors.json`
- `data/prices.csv`
- `scripts/fetch_prices.py`
- `.github/workflows/price-tracker.yml`

Obecny `index.html` jest bardzo prosty. Zawiera:

- tytuł „Porównanie cen telefonów”,
- krótką informację, że porównanie dotyczy zakupu telefonu bez ofert operatorów,
- liczbę modeli,
- datę ostatniej aktualizacji,
- prostą tabelę z kolumnami:
  - Kolejność,
  - Model,
  - Najniższa cena,
  - Sklep,
  - Ostatni odczyt.

Obecny `docs/app.js`:

- ładuje `data/latest.json`,
- renderuje liczbę modeli,
- renderuje datę wygenerowania danych,
- sortuje modele po `display_order`,
- renderuje prostą tabelę.

Obecny `docs/styles.css` zawiera tylko bardzo podstawowy styl.

Obecny `config/products.json` zawiera docelową listę 16 modeli telefonów, ale każdy model ma puste `sources: []`.

Obecny `config/stores.json` zawiera listę sklepów i ich statusy.

Obecny `scripts/fetch_prices.py` jest szkieletem. Nie pobiera jeszcze realnych cen. Przy źródłach zapisuje tylko błąd `not_implemented`.

## 2. Najważniejsze zadanie

Zbuduj pierwszą naprawdę użyteczną wersję strony do porównywania cen telefonów.

Strona ma być wizualnie przejrzysta, nowoczesna, czytelna i wygodna do szybkiego porównania modeli.

Nie rób ciężkiego frameworka. Preferowane rozwiązanie:

- czysty HTML,
- CSS,
- JavaScript,
- ewentualnie lekka biblioteka do wykresów, np. Chart.js z CDN.

Projekt ma pozostać prosty do hostowania na GitHub Pages.

## 3. Modele telefonów

W aplikacji należy zachować dokładnie tę kolejność modeli:

1. POCO F8 Pro 12/512 GB
2. POCO F8 Ultra 12/512 GB
3. POCO F7 Ultra 12/512 GB
4. POCO F7 Pro 12/512 GB
5. POCO F7 12/512 GB
6. POCO X7 Pro 12/512 GB
7. OnePlus Nord 4 12/256 GB
8. POCO F6 Pro 12/512 GB
9. POCO F6 12/512 GB
10. realme 14 Pro+ 12/512 GB
11. Xiaomi 13T 8/256 GB
12. Samsung Galaxy A56 8/256 GB
13. Nothing Phone (3a) 12/256 GB
14. Redmi Note 14 Pro+ 5G 12/512 GB
15. Motorola Edge 50 Neo 12/512 GB
16. POCO X7 12/512 GB

Modele są już zapisane w `config/products.json`.

Nie sortuj modeli alfabetycznie. Zawsze używaj `display_order`.

Kolory telefonów traktujemy jako ten sam model. Jeżeli sklep ma osobne URL-e dla różnych kolorów, można dodać je jako osobne źródła, ale na wykresie i w podsumowaniu model ma być traktowany jako jeden wariant pamięciowy.

## 4. Sklepy i źródła

W `config/stores.json` są już zapisane sklepy.

W pierwszej kolejności skup się na sklepach oznaczonych jako `scrape_enabled: true` i `status: ok`, szczególnie:

- x-kom,
- RTV Euro AGD,
- Komputronik,
- Morele,
- Neonet,
- OleOle!,
- Avans,
- Mi-Home.pl,
- Mi-Store.pl,
- Samsung.com/pl,
- Nothing.tech PL.

Źródła problematyczne lub kontrolne traktuj ostrożnie:

- Media Expert — nie opieraj głównego działania na scrapowaniu tego sklepu,
- Media Markt — tylko po ręcznej weryfikacji,
- Amazon.pl, Allegro, Empik — marketplace, najlepiej osobny tryb albo na razie pominąć,
- Ceneo, Skąpiec, Pepper — źródła kontrolne, nie podstawowe źródła cen.

Nie omijaj CAPTCHA, zabezpieczeń antybotowych ani jednoznacznych blokad. Nie wykonuj agresywnego crawlowania. Używaj tylko konkretnych stron produktów, a nie masowego skanowania całych kategorii.

## 5. Uzupełnienie początkowych danych

Uzupełnij początkowe dane, odczytując zawartość stron sklepów.

Zadanie:

1. Dla każdego modelu spróbuj znaleźć konkretne karty produktów w sklepach.
2. Dodaj znalezione URL-e do `config/products.json` w polu `sources`.
3. Dla każdego źródła zapisz:
   - `store_id`,
   - `store_name`,
   - `url`,
   - `color`, jeżeli da się ustalić,
   - `variant_label`, np. `12/512 GB`,
   - `scrape_enabled`,
   - `status`,
   - `notes`.

Przykładowa struktura źródła:

```json
{
  "store_id": "x-kom",
  "store_name": "x-kom",
  "url": "https://...",
  "color": "black",
  "variant_label": "12/512 GB",
  "scrape_enabled": true,
  "status": "ok",
  "notes": "Karta produktu zweryfikowana ręcznie przez agenta."
}
```

Jeżeli nie znajdziesz produktu:

```json
{
  "store_id": "x-kom",
  "store_name": "x-kom",
  "url": null,
  "color": null,
  "variant_label": "12/512 GB",
  "scrape_enabled": false,
  "status": "not_found",
  "notes": "Nie znaleziono jednoznacznej karty produktu."
}
```

Jeżeli znajdziesz podobny, ale niepoprawny wariant, nie dodawaj go jako aktywnego źródła. Oznacz go jako similar_variant_only.

Przykładowe błędne dopasowania:

POCO F7 zamiast POCO F7 Pro,
POCO F7 Pro zamiast POCO F7 Ultra,
POCO X7 zamiast POCO X7 Pro,
POCO F6 zamiast POCO F6 Pro,
POCO F6 Pro 12/256 zamiast 12/512,
POCO X7 Pro 8/256 zamiast 12/512,
OnePlus Nord 4 16/512 zamiast 12/256,
realme 14 Pro zamiast realme 14 Pro+,
Redmi Note 14 Pro 5G zamiast Redmi Note 14 Pro+ 5G,
Samsung Galaxy A56 8/128 zamiast 8/256,
Xiaomi 13T Pro zamiast Xiaomi 13T,
Motorola Edge 50 Fusion zamiast Motorola Edge 50 Neo.

Jeżeli model jest przyszły, niedostępny albo jeszcze nie ma kart produktów, oznacz go jako:

future_or_not_yet_available

## 6. Pobieranie cen

Rozbuduj scripts/fetch_prices.py, ale zachowaj ostrożność.

Wersja MVP może obsługiwać tylko część sklepów. Lepiej zrobić mniej sklepów dobrze niż wiele niestabilnie.

Skrypt powinien:

Czytać config/products.json.
Czytać config/stores.json.
Pomijać źródła z scrape_enabled: false.
Pobierać strony produktów tylko z konkretnych URL-i.
Odczytywać:
aktualną cenę,
cenę regularną, jeśli dostępna,
najniższą cenę z 30 dni, jeśli dostępna,
dostępność,
sprzedawcę, jeśli dotyczy,
kolor, jeśli da się ustalić.
Zapisywać poprawne odczyty do data/prices.csv.
Aktualizować data/latest.json.
Zapisywać błędy do data/errors.json.
Nie wpisywać ceny 0, jeżeli nie udało się odczytać ceny.
Nie usuwać starej historii.

Jeżeli scraper dla danego sklepu nie jest gotowy, zapisz błąd typu:

not_implemented

Jeżeli cena nie została znaleziona:

price_not_found

Jeżeli wariant nie pasuje:

variant_mismatch

Jeżeli strona wymaga JavaScriptu:

javascript_required

Jeżeli pojawia się blokada lub CAPTCHA:

blocked

## 7. Format danych

Zachowaj istniejący nagłówek data/prices.csv:

```csv
timestamp,date,display_order,model_id,model_name,store_id,store_name,price_current,price_regular,price_lowest_30_days,currency,availability,color,source_url,seller,is_marketplace,status,notes
```

data/latest.json powinien być bogatszy niż obecnie. Dla każdego modelu dodaj przynajmniej:

```json
{
  "display_order": 1,
  "model_id": "poco-f8-pro-12-512",
  "model_name": "POCO F8 Pro",
  "ram_gb": 12,
  "storage_gb": 512,
  "best_price": 2499.00,
  "best_store": "x-kom",
  "best_url": "https://...",
  "best_color": "black",
  "currency": "PLN",
  "availability": "available",
  "last_success_at": "2026-05-07T18:17:00+00:00",
  "previous_price": 2599.00,
  "price_change": -100.00,
  "price_change_percent": -3.85,
  "historical_min_price": 2499.00,
  "historical_max_price": 2999.00,
  "sources_checked": 4,
  "sources_ok": 2,
  "sources_failed": 2,
  "status": "ok"
}
```

Jeżeli nie ma danych:

```json
{
  "display_order": 1,
  "model_id": "poco-f8-pro-12-512",
  "model_name": "POCO F8 Pro",
  "best_price": null,
  "best_store": null,
  "status": "no_data"
}
```

## 8. Strona — wymagania wizualne

Przebuduj stronę tak, żeby była czytelna i przyjemna wizualnie.

Wymagania:

Nowoczesny layout.
Dobre odstępy.
Czytelne karty/statystyki.
Responsywność na telefonie i desktopie.
Wyraźne oznaczenie braku danych.
Wyraźne oznaczenie spadku/wzrostu ceny.
Tabela nie może wyglądać jak surowy HTML.
Strona powinna dobrze wyglądać bez zewnętrznego backendu.
Nie używaj ciężkiego frameworka.

Proponowany układ:

Góra strony
tytuł: „Porównanie cen telefonów”
krótki opis: „Ceny zakupu bez abonamentu i ofert operatorów”
data ostatniej aktualizacji
liczba monitorowanych modeli
liczba modeli z jakimikolwiek danymi
liczba źródeł/sklepów

Karty podsumowania

Dodaj karty:

Najtańszy aktualnie model
Największy spadek ceny
Najwięcej źródeł z ceną
Ostatnia aktualizacja

Sekcja filtrów

Dodaj filtry:

wyszukiwanie po nazwie modelu,
filtr sklepu,
filtr statusu:
wszystkie,
z ceną,
bez danych,
problem z odczytem,
sortowanie:
kolejność domyślna,
najniższa cena,
największy spadek,
nazwa modelu.

Domyślnie używaj kolejności display_order.

Główna tabela

Tabela powinna mieć kolumny:

Model
RAM / pamięć
Najniższa cena
Sklep
Zmiana
Min. historyczna
Max. historyczna
Dostępność
Ostatni odczyt
Link

Dla braku danych pokazuj czytelny badge, np. „Brak danych”.

Dla modeli przyszłych lub jeszcze niedostępnych pokazuj badge, np. „Czekamy na oferty”.

Widok szczegółów modelu

Po kliknięciu modelu pokaż rozwijane szczegóły albo panel:

lista źródeł/sklepów,
cena w każdym sklepie,
status źródła,
link do produktu,
kolor, jeśli dotyczy,
data ostatniego odczytu,
błąd, jeśli był.

Wykres

Dodaj wykres historii cen.

Możesz użyć Chart.js z CDN.

Wykres powinien umożliwiać:

wybór modelu,
pokazanie cen w czasie,
osobne linie dla sklepów,
pokazanie najniższej ceny jako wyróżnionej wartości.

Jeżeli data/prices.csv jest puste, pokaż elegancki komunikat:

„Brak historii cen. Dane pojawią się po pierwszym poprawnym odczycie.”

## 9. Struktura plików strony

Możesz zostawić obecny układ:

index.html
docs/app.js
docs/styles.css

Ale upewnij się, że ścieżki działają na GitHub Pages.

Obecny index.html w katalogu głównym ładuje:

```html
<link rel="stylesheet" href="docs/styles.css" />
<script src="docs/app.js"></script>
```

jest OK, jeśli GitHub Pages publikuje katalog główny repozytorium.

Upewnij się, że docs/app.js poprawnie ładuje dane z:

```js
fetch('data/latest.json')
fetch('data/prices.csv')
fetch('data/errors.json')
fetch('config/products.json')
fetch('config/stores.json')
```

Jeżeli zdecydujesz się przenieść index.html do docs/, popraw wszystkie ścieżki i README.

## 10. Wymagania dla JavaScriptu

docs/app.js powinien:

Ładować dane asynchronicznie.
Obsługiwać brak plików lub błędy ładowania.
Renderować dashboard bez crashowania strony.
Formatować ceny jako PLN.
Formatować daty po polsku.
Obsługiwać puste dane.
Obsługiwać filtry.
Obsługiwać sortowanie.
Obsługiwać rozwijanie szczegółów modelu.
Ładować historię z CSV i rysować wykres.

Format ceny:

```js
new Intl.NumberFormat('pl-PL', {
  style: 'currency',
  currency: 'PLN'
})
```

Format daty:

```js
new Intl.DateTimeFormat('pl-PL', {
  dateStyle: 'medium',
  timeStyle: 'short'
})
```

## 11. Wymagania dla CSS

docs/styles.css powinien stworzyć pełny wygląd aplikacji.

Styl:

jasny,
przejrzysty,
nowoczesny,
bez przesady,
dobrze działający na telefonie.

Zastosuj:

zmienne CSS,
karty,
badge/statusy,
responsywną tabelę,
czytelne kontrasty,
delikatne obramowania,
sensowne odstępy,
sticky albo wyróżniony nagłówek tabeli, jeśli pasuje.

Nie używaj agresywnych kolorów.

Przykładowe statusy wizualne:

ok — zielony badge,
no_data — szary badge,
error — czerwony badge,
manual_review — żółty badge,
future_or_not_yet_available — niebieski/szary badge.

## 12. GitHub Actions

Obecny workflow uruchamia się:

ręcznie,
codziennie o 06:17 UTC,
codziennie o 18:17 UTC.

Zostaw to jako domyślne.

Upewnij się, że workflow:

Uruchamia skrypt pobierania cen.
Commituje zmiany w:
data/latest.json,
data/errors.json,
data/prices.csv,
ewentualnie config/products.json, jeśli agent uzupełnił początkowe źródła.
Nie wywala się całkowicie przez błąd jednego sklepu.
Nie commituję pustych zmian.

## 13. README

Zaktualizuj README.md.

README powinien zawierać:

opis projektu,
listę modeli,
listę sklepów,
sposób działania GitHub Pages + GitHub Actions,
informację, że kolory traktujemy jako ten sam model,
informację, że operatorzy komórkowi są wyłączeni,
informację, że scraping jest ograniczony do konkretnych URL-i,
instrukcję uruchomienia lokalnego,
opis plików danych,
ostrzeżenie o ograniczeniach.

Popraw instrukcję lokalnego uruchamiania, jeśli obecna ścieżka jest niezgodna z położeniem index.html.

Jeżeli index.html zostaje w katalogu głównym, lokalne uruchomienie powinno być raczej:

```bash
python3 -m http.server 8000
```

a potem:

```text
http://localhost:8000
```

## 14. Ważne ograniczenia

Nie rób:

obchodzenia CAPTCHA,
obchodzenia zabezpieczeń antybotowych,
agresywnego crawlowania,
masowego pobierania kategorii,
automatycznego klikania po wynikach wyszukiwania bez kontroli,
fałszywych danych,
wpisywania 0 zł jako ceny przy błędzie.

Jeżeli czegoś nie da się pewnie odczytać, zapisz status/błąd i pokaż to w aplikacji.

## 15. Priorytet pracy

Wykonaj pracę w tej kolejności:

Przejrzyj aktualne pliki.
Popraw strukturę strony i UI.
Rozbuduj docs/app.js.
Rozbuduj docs/styles.css.
Uzupełnij config/products.json o początkowe źródła, odczytując strony sklepów.
Rozbuduj scripts/fetch_prices.py dla kilku najprostszych sklepów.
Zaktualizuj data/latest.json danymi startowymi, jeśli uda się je wiarygodnie odczytać.
Zostaw puste/brakujące dane jako null i odpowiednie statusy.
Zaktualizuj README.md.
Sprawdź, czy strona działa po otwarciu przez GitHub Pages.

## 16. Oczekiwany efekt końcowy

Po zakończeniu aplikacja powinna:

wyglądać jak gotowy dashboard, a nie surowa tabela,
pokazywać 16 modeli w ustalonej kolejności,
pokazywać aktualnie najniższą znaną cenę,
pokazywać sklep z najlepszą ceną,
pokazywać statusy braku danych i błędów,
mieć filtry i sortowanie,
mieć miejsce na wykres historii cen,
działać na GitHub Pages,
aktualizować dane przez GitHub Actions,
zachowywać ostrożność wobec sklepów i ich zabezpieczeń.
