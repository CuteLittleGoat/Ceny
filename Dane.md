# Ceny telefonów — dokumentacja projektowa

## 1. Cel projektu

Celem projektu jest stworzenie aplikacji działającej na GitHubie, która będzie monitorować ceny wybranych modeli telefonów w polskich sklepach internetowych, zapisywać historię cen i prezentować ją na wykresach.

Projekt ma służyć do obserwowania zmian cen przez kilka miesięcy przed planowanym zakupem telefonu, np. przed większymi promocjami typu Black Friday.

Aplikacja ma umożliwiać sprawdzenie:

- jak zmieniała się cena konkretnego modelu w czasie,
- w którym sklepie dany model był najtańszy,
- jaka była najniższa zanotowana cena,
- czy aktualna cena jest dobrą okazją względem historii,
- czy cena promocyjna faktycznie jest atrakcyjna.

---

## 2. Repozytorium projektu

Repozytorium GitHub:

- właściciel: `CuteLittleGoat`
- nazwa repozytorium: `Ceny`
- pełna nazwa: `CuteLittleGoat/Ceny`
- gałąź domyślna: `main`
- widoczność: publiczne
- obecny stan: puste repozytorium
- projekt ma być rozwijany jako aplikacja działająca z użyciem GitHub Pages oraz GitHub Actions

---

## 3. Główne założenie techniczne

GitHub Pages sam w sobie hostuje tylko statyczną stronę internetową. Nie działa jak serwer backendowy, który samodzielnie uruchamia zadania w tle.

Dlatego projekt powinien być zbudowany w dwóch częściach:

1. GitHub Actions
   - cyklicznie pobiera ceny z wybranych sklepów,
   - zapisuje wyniki do plików w repozytorium,
   - aktualizuje pliki z historią cen,
   - zapisuje błędy pobierania,
   - wykonuje automatyczny commit z nowymi danymi.

2. GitHub Pages
   - wyświetla statyczną stronę z dashboardem,
   - czyta dane zapisane w repozytorium,
   - pokazuje wykresy zmian cen,
   - umożliwia filtrowanie modeli i sklepów.

Projekt nie powinien wymagać zewnętrznego płatnego serwera.

---

## 4. Modele telefonów do obserwowania

Do monitorowania wybrano następujące modele:

| ID modelu | Model | Pamięć RAM | Pamięć wewnętrzna | Uwagi |
|---|---|---:|---:|---|
| `poco-x7-pro-12-512` | POCO X7 Pro | 12 GB | 512 GB | Kolory traktowane jako ten sam model |
| `oneplus-nord-4-12-256` | OnePlus Nord 4 | 12 GB | 256 GB | Kolory traktowane jako ten sam model |
| `nothing-phone-3a-12-256` | Nothing Phone (3a) | 12 GB | 256 GB | Kolory traktowane jako ten sam model |
| `samsung-galaxy-a56-8-256` | Samsung Galaxy A56 | 8 GB | 256 GB | Kolory traktowane jako ten sam model |
| `xiaomi-13t-8-256` | Xiaomi 13T | 8 GB | 256 GB | Kolory traktowane jako ten sam model |

---

## 5. Zasada dotycząca kolorów

Kolory traktujemy jako ten sam model.

Oznacza to, że np. telefon:

- Samsung Galaxy A56 8/256 czarny,
- Samsung Galaxy A56 8/256 różowy,
- Samsung Galaxy A56 8/256 zielony,

są z punktu widzenia porównania cen tym samym modelem.

Jednocześnie technicznie aplikacja powinna móc zapisać osobne URL-e dla różnych kolorów, ponieważ sklepy często mają osobne karty produktu dla każdego koloru i ceny mogą się różnić.

Rekomendowane podejście:

- w konfiguracji trzymamy osobne linki do różnych kolorów,
- na wykresie pokazujemy najniższą znalezioną cenę danego wariantu pamięciowego w danym sklepie,
- w szczegółach zapisujemy, którego koloru dotyczyła najniższa cena.

Przykład:

- Galaxy A56 8/256 czarny — 1599 zł
- Galaxy A56 8/256 różowy — 1699 zł
- Galaxy A56 8/256 zielony — niedostępny

Na głównym wykresie dla sklepu pokazujemy:

- Galaxy A56 8/256 — 1599 zł

W szczegółach można zapisać:

- najniższa cena dotyczyła wariantu czarnego.

---

## 6. Sklepy do obserwowania

### 6.1. Główne elektromarkety i sklepy z elektroniką

Te sklepy powinny być rozważone jako główne źródła cen:

| Sklep | Priorytet | Uwagi |
|---|---:|---|
| x-kom | wysoki | Bardzo dobry kandydat do monitorowania cen telefonów. Wcześniej znaleziono konkretne strony produktów dla kilku wskazanych modeli. |
| RTV Euro AGD | wysoki | Duży sklep, ważny punkt odniesienia dla cen elektroniki. |
| Komputronik | wysoki | Dobry sklep do monitorowania, często ma konkretne warianty pamięciowe. |
| Morele | średni/wysoki | Przydatne źródło dodatkowe, szczególnie dla popularnych modeli. |
| Neonet | średni/wysoki | Warto monitorować jako osobne źródło cen. |
| OleOle! | średni | Sklep powiązany asortymentowo z RTV Euro AGD, ale ceny/promocje mogą się różnić. |
| Avans | średni | Przydatne źródło dodatkowe, ale może mieć powiązania asortymentowe z Media Expert. |
| Media Markt | średni | Warto monitorować, ale ostrożnie. Trzeba sprawdzać konkretne URL-e i zasady pobierania. |
| Media Expert | niski/ostrożny | Sklep ważny cenowo, ale problematyczny technicznie i prawnie/etycznie pod automatyczne pobieranie stron produktów. |
| Empik | pomocniczy | Marketplace — trzeba rozróżniać sprzedawcę. |
| Amazon.pl | pomocniczy | Ceny mogą być zmienne, a sprzedawcy różni. Wymaga ostrożnego traktowania. |
| Allegro | osobny tryb | Bardzo przydatne rynkowo, ale trudne do uczciwego porównania ze zwykłymi sklepami. |

---

### 6.2. Oficjalne sklepy producentów

Te sklepy powinny być monitorowane osobno, jako sklepy oficjalne lub autoryzowane:

| Sklep | Dotyczy modeli | Uwagi |
|---|---|---|
| Mi.com Polska | Xiaomi, POCO | Oficjalny sklep Xiaomi. Może być technicznie trudniejszy, bo strona może mocno korzystać z JavaScriptu. |
| Mi-Home.pl | Xiaomi, POCO | Autoryzowany sklep Xiaomi. Wydaje się dobrym kandydatem do monitorowania cen. |
| Mi-Store.pl | Xiaomi, POCO | Dodatkowy autoryzowany kanał sprzedaży Xiaomi. |
| Samsung.com/pl | Samsung Galaxy A56 | Oficjalny sklep Samsunga. Warto monitorować dla Galaxy A56. |
| OnePlus.com/pl | OnePlus Nord 4 | Oficjalny sklep OnePlus. Może mieć problem z dostępnością Nord 4 w Polsce. |
| Nothing.tech PL | Nothing Phone (3a) | Oficjalna strona Nothing dla Polski. Warto monitorować dla Nothing Phone (3a). |

---

### 6.3. Porównywarki i źródła promocji

Te źródła nie muszą być głównym źródłem danych do wykresu, ale warto je traktować jako warstwę kontrolną.

| Źródło | Rola |
|---|---|
| Ceneo | Kontrola cen, znajdowanie sklepów, porównanie rynku. |
| Skąpiec | Dodatkowe porównanie cen. |
| Pepper.pl | Wykrywanie promocji, kodów rabatowych i krótkich okazji. Nie traktować jako zwykłego sklepu. |

---

### 6.4. Operatorzy komórkowi

Operatorzy, np.:

- Orange,
- Play,
- Plus,
- T-Mobile,

nie powinni być głównym źródłem porównania cen w pierwszej wersji projektu.

Powód:

- ceny często zależą od abonamentu,
- telefony bywają sprzedawane w ratach,
- promocje są powiązane z usługami,
- trudno porównać cenę operatora z normalną ceną sklepową.

Operatorów można dodać później jako osobną kategorię:

- cena bez abonamentu,
- cena z abonamentem,
- rata miesięczna,
- całkowity koszt urządzenia.

---

## 7. Rekomendowana lista sklepów na start

Na pierwszą wersję projektu rekomendowane są następujące źródła:

1. x-kom
2. RTV Euro AGD
3. Komputronik
4. Morele
5. Neonet
6. OleOle!
7. Avans
8. Mi-Home.pl
9. Mi.com Polska
10. Mi-Store.pl
11. Samsung.com/pl
12. Nothing.tech PL
13. OnePlus.com/pl
14. Amazon.pl — opcjonalnie
15. Allegro — opcjonalnie, raczej jako osobny tryb
16. Ceneo — jako źródło kontrolne
17. Skąpiec — jako źródło kontrolne
18. Pepper — jako alert okazji, nie jako zwykła cena sklepowa

Media Markt można dodać ostrożnie po sprawdzeniu konkretnych URL-i.

Media Expert traktować ostrożnie i prawdopodobnie nie opierać na nim automatycznego scrapingu kart produktów, jeżeli aktualne zasady sklepu nadal blokują takie pobieranie.

---

## 8. Najważniejsze ograniczenia projektu

### 8.1. GitHub Pages nie jest backendem

GitHub Pages może wyświetlać stronę, ale nie może samodzielnie cyklicznie sprawdzać cen.

Rozwiązanie:

- GitHub Actions pobiera dane,
- GitHub Pages tylko je prezentuje.

---

### 8.2. GitHub Actions nie gwarantuje idealnej punktualności

GitHub Actions może uruchamiać zadania według harmonogramu, ale nie należy zakładać idealnej punktualności.

Możliwe problemy:

- opóźnienie uruchomienia,
- pominięcie pojedynczego uruchomienia,
- wyłączenie harmonogramu po dłuższej nieaktywności repozytorium,
- większe opóźnienia w godzinach pełnych.

Dla tego projektu nie jest to duży problem, bo celem jest historia cen w skali dni, tygodni i miesięcy, a nie alarm co do minuty.

---

### 8.3. Sklepy mogą blokować automatyczne pobieranie

Największym ograniczeniem nie jest GitHub, tylko sklepy.

Możliwe problemy:

- zabezpieczenia antybotowe,
- Cloudflare,
- CAPTCHA,
- dynamiczne ładowanie ceny przez JavaScript,
- zmiana struktury strony,
- blokowanie scraperów,
- ograniczenia w robots.txt,
- regulaminy zabraniające automatycznego pobierania.

Projekt nie powinien omijać CAPTCHA, zabezpieczeń ani blokad antybotowych.

---

### 8.4. Media Expert jest problematyczny

W rozmowie ustalono, że Media Expert ma problematyczne zasady dla automatycznego pobierania stron produktów, ponieważ w robots.txt blokowana była ścieżka `/product/`.

Wniosek projektowy:

- Media Expert można zostawić jako sklep do ręcznej obserwacji lub źródło informacyjne,
- nie należy opierać głównego działania aplikacji na scrapowaniu kart produktów Media Expert,
- przed implementacją trzeba ponownie sprawdzić aktualne robots.txt i regulamin.

---

### 8.5. Media Markt wymaga ostrożności

Media Markt może być możliwy do monitorowania, ale należy sprawdzać konkretne adresy produktów.

W rozmowie ustalono, że robots.txt blokował między innymi wyszukiwanie, filtrowanie, sortowanie i część zapytań, ale nie zostało to jednoznacznie potraktowane jako całkowita blokada wszystkich kart produktów.

Wniosek projektowy:

- nie skanować wyszukiwarki Media Markt,
- nie używać agresywnego crawlignu,
- ewentualnie używać tylko ręcznie wskazanych URL-i produktów,
- ponownie sprawdzić zasady przed implementacją.

---

### 8.6. Oficjalne sklepy producentów mogą być trudne technicznie

Niektóre sklepy producentów, np. Mi.com, mogą mocno korzystać z JavaScriptu.

Możliwe konsekwencje:

- zwykłe pobranie HTML może nie wystarczyć,
- może być potrzebny Playwright lub podobne narzędzie,
- pobieranie będzie wolniejsze,
- rozwiązanie będzie bardziej kruche,
- ryzyko blokad będzie większe.

W pierwszej wersji lepiej preferować źródła, w których cena jest dostępna w prostym HTML lub w łatwo dostępnym JSON-ie.

---

## 9. Strategia pobierania cen

Najlepsza strategia to nie wyszukiwanie produktów automatycznie w każdym sklepie, tylko monitorowanie konkretnych kart produktów.

Zamiast:

- wyszukaj w sklepie „POCO X7 Pro 12/512”,
- wejdź w wyniki,
- wybierz najlepszy produkt,

lepiej:

- przygotować plik konfiguracyjny,
- wpisać konkretne URL-e produktów,
- odczytywać cenę tylko z tych adresów.

To jest:

- stabilniejsze,
- mniej podatne na błędne dopasowania,
- mniej agresywne wobec sklepów,
- łatwiejsze do debugowania,
- łatwiejsze do ręcznej kontroli.

---

## 10. Plik konfiguracyjny

Docelowo powinien istnieć plik konfiguracyjny, np.:

- `config/products.json`

Plik powinien zawierać:

- ID modelu,
- nazwę modelu,
- wariant RAM/pamięć,
- informację, że kolor nie wpływa na identyfikację modelu,
- listę źródeł/sklepów,
- URL-e do konkretnych kart produktów,
- status danego źródła,
- informację, czy źródło może być automatycznie sprawdzane,
- ewentualne uwagi.

Przykładowe pola logiczne:

- `model_id`
- `model_name`
- `ram_gb`
- `storage_gb`
- `colors_as_same_model`
- `sources`
- `store_id`
- `store_name`
- `url`
- `color`
- `variant_label`
- `scrape_enabled`
- `source_type`
- `status`
- `notes`

Przykładowe statusy:

- `ok`
- `manual_review`
- `not_found`
- `out_of_stock`
- `similar_variant_only`
- `blocked_by_robots`
- `blocked_or_unreliable`
- `requires_javascript`
- `marketplace`
- `do_not_scrape`

---

## 11. Samodzielne przygotowanie konfiguracji

Założenie z rozmowy:

Asystent ma być w stanie samodzielnie przygotować pierwszy plik konfiguracyjny z linkami do produktów.

Plan przygotowania konfiguracji:

1. Wyszukać konkretne karty produktów dla każdego modelu.
2. Zweryfikować wariant pamięciowy.
3. Odrzucić błędne dopasowania.
4. Odrzucić inne wersje pamięciowe, np. 8/128 zamiast 8/256.
5. Odrzucić wersje Pro/Plus/Ultra, jeśli nie są właściwym modelem.
6. Oznaczyć produkty niedostępne, jeśli karta produktu istnieje, ale nie ma sprzedaży.
7. Oznaczyć sklepy problematyczne technicznie.
8. Zapisać źródła, których nie wolno lub nie warto scrapować automatycznie.
9. Zapisać osobne URL-e dla różnych kolorów, ale traktować je jako jeden model na wykresie.

---

## 12. Dane do zapisywania

Aplikacja nie powinna zapisywać wyłącznie jednej ceny.

Rekomendowane dane dla każdego odczytu:

| Pole | Opis |
|---|---|
| `timestamp` | Data i godzina pobrania |
| `date` | Sama data, przydatna do wykresów dziennych |
| `model_id` | ID modelu |
| `model_name` | Nazwa modelu |
| `ram_gb` | Ilość RAM |
| `storage_gb` | Pamięć wewnętrzna |
| `store_id` | ID sklepu |
| `store_name` | Nazwa sklepu |
| `source_url` | URL karty produktu |
| `color` | Kolor, jeśli możliwy do ustalenia |
| `price_current` | Aktualna cena |
| `price_regular` | Cena regularna/przekreślona, jeśli jest |
| `price_lowest_30_days` | Najniższa cena z 30 dni przed obniżką, jeśli sklep ją pokazuje |
| `currency` | Waluta, np. PLN |
| `availability` | Dostępność |
| `seller` | Sprzedawca, szczególnie ważne dla marketplace |
| `is_marketplace` | Czy oferta jest marketplace |
| `scrape_status` | Status pobrania |
| `error_message` | Błąd, jeśli wystąpił |
| `notes` | Uwagi dodatkowe |

---

## 13. Struktura danych w repozytorium

Proponowana struktura:

- `README.md`
  - główna dokumentacja projektu

- `config/products.json`
  - lista modeli i źródeł do monitorowania

- `config/stores.json`
  - lista sklepów, ich typów i zasad pobierania

- `data/prices.csv`
  - pełna historia cen w formacie tabelarycznym

- `data/latest.json`
  - ostatni znany stan cen dla każdego modelu i sklepu

- `data/errors.json`
  - historia błędów pobierania

- `data/snapshots/`
  - opcjonalnie dzienne snapshoty danych

- `scripts/`
  - skrypty pobierające ceny

- `docs/` albo katalog główny GitHub Pages
  - pliki strony internetowej

- `.github/workflows/`
  - workflow GitHub Actions uruchamiający pobieranie cen

---

## 14. Proponowana logika zapisu ceny

Dla każdego modelu i sklepu może istnieć kilka URL-i, np. różne kolory.

Aplikacja powinna:

1. Pobierać wszystkie aktywne URL-e dla danego modelu i sklepu.
2. Odczytywać ceny i dostępność.
3. Odrzucać odczyty błędne.
4. Odrzucać oferty niedostępne, jeżeli nie da się ich kupić.
5. Jeżeli kilka kolorów jest dostępnych, wybrać najniższą cenę.
6. Zapisać najniższą cenę jako reprezentatywną dla modelu w danym sklepie.
7. W szczegółach zapisać URL i kolor, którego dotyczyła najniższa cena.

Przykład:

- POCO X7 Pro 12/512 czarny — 1799 zł
- POCO X7 Pro 12/512 zielony — 1899 zł
- POCO X7 Pro 12/512 żółty — niedostępny

W danych głównych:

- POCO X7 Pro 12/512 — sklep X — 1799 zł

W szczegółach:

- cena pochodziła z wariantu czarnego.

---

## 15. Częstotliwość sprawdzania cen

Rekomendowana częstotliwość:

- 1 raz dziennie jako minimum,
- 2 razy dziennie jako rozsądna opcja,
- maksymalnie kilka razy dziennie,
- nie odpytywać sklepów zbyt często.

Propozycja:

- rano, np. około 06:17,
- wieczorem, np. około 18:17.

Nie należy ustawiać uruchomienia dokładnie o pełnej godzinie, ponieważ GitHub Actions może mieć wtedy większe opóźnienia.

---

## 16. Dashboard na GitHub Pages

Strona powinna pokazywać:

- listę modeli,
- ostatnią znaną cenę,
- najniższą zanotowaną cenę,
- najwyższą zanotowaną cenę,
- zmianę ceny względem poprzedniego odczytu,
- zmianę procentową,
- wykres ceny w czasie,
- filtr po sklepie,
- filtr po modelu,
- link do produktu w sklepie,
- status dostępności,
- datę ostatniego udanego odczytu,
- ostrzeżenie, jeśli sklep od dłuższego czasu zwraca błędy.

---

## 17. Proponowane widoki strony

### 17.1. Widok główny

Tabela:

| Model | Najniższa aktualna cena | Sklep | Zmiana | Najniższa w historii | Ostatni odczyt |
|---|---:|---|---:|---:|---|

### 17.2. Widok modelu

Dla jednego modelu:

- wykres cen w czasie,
- osobna linia dla każdego sklepu,
- tabela ostatnich cen,
- lista źródeł,
- historia najniższych cen,
- linki do sklepów.

### 17.3. Widok sklepu

Dla jednego sklepu:

- lista monitorowanych modeli,
- ostatnie ceny,
- status działania scrapera,
- ostatni błąd, jeśli był.

### 17.4. Widok błędów

Tabela błędów:

| Data | Sklep | Model | URL | Błąd |
|---|---|---|---|---|

---

## 18. Ważne rozróżnienie cen

Aplikacja powinna rozróżniać różne typy cen.

Możliwe typy:

- cena aktualna,
- cena regularna,
- cena przekreślona,
- cena promocyjna,
- najniższa cena z 30 dni przed obniżką,
- cena z kodem rabatowym,
- cena w aplikacji mobilnej,
- cena dla zalogowanych,
- cena marketplace,
- cena ratalna,
- cena z abonamentem.

W pierwszej wersji najważniejsza jest:

- cena aktualna zakupu bez abonamentu.

Pozostałe ceny można zapisywać, jeśli są łatwe do odczytania.

---

## 19. Marketplace

Sklepy takie jak:

- Allegro,
- Amazon.pl,
- Empik,

mogą działać jako marketplace.

To oznacza, że produkt może być sprzedawany przez różne podmioty, niekoniecznie przez sam sklep.

W aplikacji trzeba zapisywać:

- nazwę sprzedawcy,
- czy oferta jest marketplace,
- czy sprzedawcą jest sam sklep,
- czy produkt jest nowy,
- czy produkt pochodzi z oficjalnej polskiej dystrybucji, jeśli da się to ustalić.

W pierwszej wersji marketplace najlepiej traktować osobno albo ostrożnie.

---

## 20. Ceneo, Skąpiec i Pepper

### Ceneo

Ceneo może być przydatne do:

- wykrywania sklepów sprzedających dany model,
- kontroli, czy aplikacja nie pominęła dobrej ceny,
- porównania aktualnych cen rynkowych.

Nie musi być głównym źródłem danych do wykresu.

### Skąpiec

Skąpiec może pełnić podobną funkcję jak Ceneo:

- dodatkowa kontrola cen,
- wykrywanie innych sklepów,
- porównanie rynku.

### Pepper

Pepper nie jest klasycznym sklepem.

Może być używany do:

- wykrywania okazji,
- kodów rabatowych,
- promocji czasowych,
- informacji od społeczności.

Nie powinien być traktowany jako źródło regularnej ceny katalogowej.

---

## 21. Błędy i odporność projektu

Aplikacja powinna być odporna na błędy.

Jeśli pobranie ceny się nie uda, aplikacja nie powinna usuwać poprzedniej ceny ani wpisywać fałszywego zera.

Zasady:

- brak ceny to błąd, nie cena 0 zł,
- poprzednia poprawna cena powinna pozostać w historii,
- błąd powinien zostać zapisany w `data/errors.json`,
- dashboard powinien pokazywać, że ostatni odczyt się nie udał,
- po kilku kolejnych błędach dane źródło powinno dostać status wymagający ręcznej weryfikacji.

---

## 22. Bezpieczeństwo i etyka

Projekt powinien działać ostrożnie.

Zasady:

- nie omijać CAPTCHA,
- nie omijać blokad antybotowych,
- nie ignorować jednoznacznych zakazów w robots.txt,
- nie wykonywać agresywnego crawlowania,
- nie pobierać masowo całych kategorii,
- nie skanować wyszukiwarek sklepów, jeśli można użyć konkretnych URL-i,
- ograniczyć częstotliwość pobierania,
- dodać czytelny User-Agent, jeśli będzie to technicznie użyteczne,
- zapisywać błędy i statusy zamiast udawać, że wszystko działa.

---

## 23. Podejście do sklepów problematycznych

Dla sklepów problematycznych aplikacja powinna mieć możliwość oznaczenia źródła jako:

- nie scrapować,
- tylko ręczna kontrola,
- wymaga JavaScript,
- wymaga sprawdzenia robots.txt,
- marketplace,
- niestabilne.

Nie każdy sklep musi być obsługiwany w pierwszej wersji.

Lepiej mieć mniejszą liczbę stabilnych źródeł niż dużą liczbę źródeł, które często się psują.

---

## 24. Proponowane fazy projektu

### Faza 1 — dokumentacja i konfiguracja

Cele:

- przygotować `README.md`,
- przygotować listę sklepów,
- przygotować listę modeli,
- przygotować pierwszy plik `config/products.json`,
- znaleźć konkretne URL-e produktów,
- oznaczyć źródła problematyczne.

### Faza 2 — minimalne pobieranie cen

Cele:

- obsłużyć kilka najłatwiejszych sklepów,
- zapisywać ceny do CSV,
- zapisywać błędy,
- uruchomić GitHub Actions ręcznie,
- sprawdzić, czy commit z danymi działa.

### Faza 3 — harmonogram

Cele:

- uruchomić pobieranie cen automatycznie,
- ustawić harmonogram np. 2 razy dziennie,
- dodać zabezpieczenia przed duplikatami,
- dodać logowanie błędów.

### Faza 4 — dashboard

Cele:

- stworzyć stronę GitHub Pages,
- dodać wykresy cen,
- dodać tabelę ostatnich cen,
- dodać filtry po modelu i sklepie.

### Faza 5 — rozszerzenia

Cele:

- dodać więcej sklepów,
- dodać marketplace w osobnym trybie,
- dodać kontrolę Ceneo/Skąpiec,
- dodać wykrywanie promocji z Pepper,
- dodać alerty, jeśli będą potrzebne.

---

## 25. Proponowana kolejność implementacji sklepów

Najpierw sklepy prawdopodobnie łatwiejsze i sensowne:

1. x-kom
2. Komputronik
3. RTV Euro AGD
4. Morele
5. Neonet
6. OleOle!
7. Mi-Home.pl
8. Mi-Store.pl
9. Samsung.com/pl
10. Nothing.tech PL

Potem:

11. Mi.com Polska
12. OnePlus.com/pl
13. Amazon.pl
14. Empik
15. Allegro

Ostrożnie lub ręcznie:

16. Media Markt
17. Media Expert

---

## 26. Kryteria poprawnego dopasowania produktu

Produkt można uznać za poprawny tylko wtedy, gdy zgadzają się:

- marka,
- model,
- generacja,
- wariant pamięci RAM,
- wariant pamięci wewnętrznej,
- brak dopisku zmieniającego model, np. Pro/Plus/Ultra, jeśli nie dotyczy,
- produkt jest nowy, jeśli to możliwe do ustalenia,
- produkt nie jest akcesorium,
- produkt nie jest innym wariantem.

Kolor nie musi się zgadzać, ponieważ kolory traktujemy jako ten sam model.

---

## 27. Przykładowe błędne dopasowania

Należy odrzucać:

- POCO X7 zamiast POCO X7 Pro,
- POCO X7 Pro 8/256 zamiast 12/512,
- OnePlus Nord 4 16/512 zamiast 12/256,
- Nothing Phone (3a) Pro zamiast Nothing Phone (3a),
- Samsung Galaxy A56 8/128 zamiast 8/256,
- Xiaomi 13T Pro zamiast Xiaomi 13T,
- Xiaomi 13T 12/256, jeśli szukamy 8/256,
- produkty outletowe,
- produkty używane,
- telefony odnawiane, jeśli nie są celem projektu,
- etui, szkła, ładowarki i inne akcesoria.

---

## 28. Historia cen

Historia cen powinna być zapisywana tak, aby można było później wygenerować wykres dla:

- jednego modelu we wszystkich sklepach,
- jednego modelu w jednym sklepie,
- najniższej ceny danego modelu niezależnie od sklepu,
- porównania kilku modeli między sobą.

Nie należy nadpisywać historii jedną aktualną ceną.

---

## 29. Format `prices.csv`

Proponowane kolumny:

| Kolumna | Opis |
|---|---|
| `timestamp` | Pełna data i godzina odczytu |
| `date` | Data |
| `model_id` | ID modelu |
| `model_name` | Nazwa modelu |
| `store_id` | ID sklepu |
| `store_name` | Nazwa sklepu |
| `price_current` | Aktualna cena |
| `price_regular` | Cena regularna |
| `price_lowest_30_days` | Najniższa cena z 30 dni, jeśli dostępna |
| `currency` | PLN |
| `availability` | Dostępność |
| `color` | Kolor wariantu |
| `source_url` | URL |
| `seller` | Sprzedawca |
| `is_marketplace` | Czy marketplace |
| `status` | Status odczytu |
| `notes` | Uwagi |

---

## 30. Format `latest.json`

Plik `latest.json` powinien zawierać ostatni znany stan dla każdego modelu.

Przydatne pola:

- ostatnia cena,
- sklep,
- URL,
- kolor,
- dostępność,
- data ostatniego poprawnego odczytu,
- liczba kolejnych błędów,
- najniższa cena w historii,
- najwyższa cena w historii,
- zmiana od poprzedniego odczytu.

---

## 31. Format `errors.json`

Plik błędów powinien zawierać:

- datę błędu,
- model,
- sklep,
- URL,
- typ błędu,
- komunikat błędu,
- czy błąd jest chwilowy,
- czy źródło wymaga ręcznej weryfikacji.

Przykładowe typy błędów:

- `http_error`
- `timeout`
- `price_not_found`
- `product_not_found`
- `blocked`
- `captcha`
- `javascript_required`
- `parser_error`
- `variant_mismatch`
- `unknown_error`

---

## 32. GitHub Actions

Workflow powinien umożliwiać:

- uruchomienie ręczne,
- uruchomienie według harmonogramu,
- zapis danych,
- commit zmian do repozytorium.

Rekomendacje:

- harmonogram 1–2 razy dziennie,
- nie uruchamiać dokładnie o pełnej godzinie,
- zapisywać logi,
- nie przerywać całego procesu, jeśli jeden sklep się nie powiedzie,
- każdy sklep traktować niezależnie,
- błędy jednego źródła nie powinny blokować pozostałych.

---

## 33. GitHub Pages

Strona powinna być statyczna.

Może używać:

- HTML,
- CSS,
- JavaScript,
- biblioteki do wykresów, np. Chart.js,
- danych z plików JSON/CSV zapisanych w repozytorium.

Nie powinna wymagać backendu.

---

## 34. Najważniejsze decyzje projektowe z rozmowy

1. Projekt ma działać na GitHubie.
2. GitHub Pages będzie służyć do wyświetlania dashboardu.
3. GitHub Actions będzie służyć do cyklicznego pobierania cen.
4. Dane będą zapisywane w repozytorium.
5. Modele telefonów są z góry określone.
6. Kolory traktujemy jako ten sam model.
7. Różne kolory mogą mieć osobne URL-e.
8. Na wykresie najlepiej pokazywać najniższą cenę danego modelu w danym sklepie, niezależnie od koloru.
9. Najlepiej monitorować konkretne URL-e produktów, a nie wyniki wyszukiwania.
10. Nie należy agresywnie scrapować sklepów.
11. Nie należy omijać CAPTCHA ani blokad antybotowych.
12. Media Expert jest źródłem problematycznym.
13. Media Markt wymaga ostrożności.
14. Marketplace powinien być traktowany osobno.
15. Ceneo, Skąpiec i Pepper są raczej źródłami kontrolnymi, nie podstawowymi.
16. Pierwsza wersja powinna być prosta i stabilna.
17. Lepiej obsłużyć mniej sklepów dobrze niż wiele sklepów niestabilnie.

---

## 35. Otwarte decyzje na później

Do ustalenia przed implementacją lub w trakcie prac:

1. Czy dashboard ma pokazywać ceny tylko aktualnie dostępnych produktów, czy również niedostępnych?
2. Czy zapisywać ceny produktów niedostępnych, jeśli sklep nadal pokazuje cenę?
3. Czy marketplace ma być włączony od początku?
4. Czy Allegro ma pokazywać najniższą ofertę, czy tylko oferty od firm/sklepów?
5. Czy uwzględniać telefony z kodami rabatowymi?
6. Czy uwzględniać promocje tylko w aplikacji mobilnej sklepu?
7. Czy dodać alerty cenowe?
8. Czy repozytorium ma pozostać publiczne?
9. Czy zapisywać surowy HTML/debug snapshot przy błędach?
10. Czy wykres ma pokazywać dane dzienne, czy każdy pojedynczy odczyt?

---

## 36. Propozycja minimalnej pierwszej wersji

Minimalna działająca wersja powinna zawierać:

- `README.md`,
- `config/products.json`,
- `config/stores.json`,
- `data/prices.csv`,
- `data/latest.json`,
- `data/errors.json`,
- jeden workflow GitHub Actions,
- prostą stronę GitHub Pages z tabelą i wykresem.

Pierwsza wersja może obsługiwać tylko kilka sklepów, np.:

- x-kom,
- Komputronik,
- RTV Euro AGD,
- Morele,
- Mi-Home.pl.

Dopiero po potwierdzeniu stabilności należy dodawać kolejne sklepy.

---

## 37. Główne ryzyka

| Ryzyko | Znaczenie | Jak ograniczyć |
|---|---:|---|
| Zmiana struktury strony sklepu | wysokie | Pisać parsery per sklep i logować błędy |
| Blokada antybotowa | wysokie | Mała częstotliwość, konkretne URL-e, brak omijania zabezpieczeń |
| Błędne dopasowanie wariantu | wysokie | Ręcznie przygotowany config, walidacja nazwy i pamięci |
| Marketplace i różni sprzedawcy | średnie/wysokie | Oznaczać marketplace osobno |
| Brak ceny przez JavaScript | średnie | Preferować prostsze źródła, ewentualnie Playwright później |
| GitHub Actions opóźniony | niskie | Dla historii cen nie jest to krytyczne |
| Publiczne dane w repo | niskie/średnie | Założyć, że lista modeli i ceny są publiczne |
| Sklep blokuje robots.txt | wysokie | Oznaczać jako `do_not_scrape` |

---

## 38. Definicja sukcesu projektu

Projekt można uznać za działający, jeśli:

- codziennie zapisuje ceny przynajmniej z kilku sklepów,
- pokazuje wykres zmian cen dla każdego modelu,
- poprawnie rozróżnia warianty pamięciowe,
- traktuje kolory jako ten sam model,
- zapisuje błędy zamiast psuć dane,
- umożliwia ręczne dodawanie kolejnych URL-i,
- działa bez płatnego serwera,
- działa na GitHub Pages i GitHub Actions.

---

## 39. Następny logiczny krok

Następnym krokiem po tej dokumentacji powinno być przygotowanie początkowych plików projektu:

1. `README.md` — na podstawie tej dokumentacji.
2. `config/stores.json` — lista sklepów i ich statusów.
3. `config/products.json` — lista modeli i znalezionych URL-i.
4. Pusta struktura katalogów `data/`.
5. Decyzja, które sklepy obsłużyć w pierwszej kolejności.

Dopiero po tym należy pisać kod pobierający ceny.
