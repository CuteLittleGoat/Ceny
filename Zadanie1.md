INSTRUKCJA DLA AGENTA AI CODEX — repo CuteLittleGoat/Ceny
Zadanie: uruchomić poprawny odczyt cen z Xiaomi, Media Markt, Media Expert i Euro RTV AGD
Nie zmieniaj celu aplikacji: statyczny frontend czyta dane z plików data/*.json, a dane są generowane przez scripts/fetch_prices.py.

WNIOSKI Z OBECNEGO STANU
1. Aplikacja ma już architekturę przygotowaną pod wiele sklepów:
   - config/stores.json zawiera aktywne sklepy:
     - rtv-euro-agd
     - mi-com
     - mi-home
     - mi-store
     - media-markt
     - media-expert
   - scripts/fetch_prices.py zawiera mapę PARSERS dla:
     - mi-com
     - mi-home
     - mi-store
     - media-expert
     - media-markt
     - rtv-euro-agd
     - morele
     - x-kom
   - workflow .github/workflows/price-tracker.yml instaluje requests, BeautifulSoup, lxml i Playwright, uruchamia walidację, pobiera ceny i commituję data/latest.json, data/errors.json, data/prices.csv, data/prices.json.

2. Obecnie dane widoczne w UI pochodzą głównie z Morele, ponieważ:
   - wiele źródeł Xiaomi w config/products.json ma scrape_enabled=false i status manual_review;
   - część źródeł Media Expert ma błędny store_id albo URL prowadzący do strony producenta zamiast do Media Expert;
   - źródła RTV Euro AGD są aktywne, ale często kończą jako product_mismatch;
   - parsery dla Xiaomi/Media Markt/Media Expert/RTV Euro AGD są w praktyce tylko wrapperami na parse_generic(), więc nie są jeszcze dedykowane pod DOM/JSON tych sklepów;
   - frontend pokazuje w głównej tabeli tylko best_store/best_price, więc nawet po pobraniu kilku sklepów użytkownik może widzieć głównie Morele, jeżeli Morele jest najtańsze.

CEL FUNKCJONALNY
Po zmianach aplikacja ma:
1. Pobierać dane z:
   - Xiaomi: traktuj jako grupę oficjalnych sklepów mi-com, mi-home, mi-store; przynajmniej mi-com musi działać, jeśli karta produktu zawiera cenę.
   - Media Markt: store_id media-markt.
   - Media Expert: store_id media-expert.
   - Euro RTV AGD: store_id rtv-euro-agd.
2. Nie pobierać cen z wyników wyszukiwania, kategorii, marketplace, ofert operatorów ani kart z innym RAM/pamięcią.
3. Zapisywać poprawne wyniki do data/prices.csv, data/prices.json i data/latest.json.
4. Zapisywać niepowodzenia do data/errors.json z czytelnym error_type.
5. W UI dać użytkownikowi możliwość zobaczenia, że dane pochodzą z więcej niż Morele, nawet jeśli Morele pozostaje najtańsze.

PLIKI DO ZMIANY
1. scripts/fetch_prices.py
2. config/products.json
3. docs/app.js
4. opcjonalnie scripts/validate_config.py, jeżeli trzeba dodać aliasy domen lub reguły walidacyjne
5. opcjonalnie README.md / config/Instrukcja.txt, tylko jeśli zmieniasz format danych

SZCZEGÓŁOWE ZMIANY W scripts/fetch_prices.py

A. Nie zostawiaj parserów docelowych jako zwykłych aliasów parse_generic().
Obecnie:
- parse_mi(html) -> parse_generic(html, 'Mi.com Polska')
- parse_media_expert(html) -> parse_generic(html, 'Media Expert')
- parse_media_markt(html) -> parse_generic(html, 'Media Markt')
- parse_rtv(html) -> parse_generic(html, 'RTV Euro AGD')

Zmień to na dedykowane parsery:
- parse_mi(html)
- parse_media_expert(html)
- parse_media_markt(html)
- parse_rtv(html)

Każdy parser ma zwracać dict:
{
  "price_current": float albo None,
  "price_regular": float albo None,
  "price_lowest_30_days": float albo None,
  "currency": "PLN",
  "availability": "in_stock" | "out_of_stock" | "withdrawn" | "unknown",
  "seller": nazwa sklepu,
  "product_name": nazwa z karty produktu,
  "raw_source": krótka informacja, skąd wyciągnięto cenę, np. "jsonld", "__NEXT_DATA__", "meta", "dom"
}

B. Rozszerz extract_jsonld_product().
Ma obsługiwać:
- @type jako string "Product"
- @type jako lista zawierająca "Product"
- @graph
- offers jako dict
- offers jako lista
- offers.price
- offers.lowPrice
- offers.highPrice, tylko jeśli nie ma price/lowPrice
- offers.priceSpecification.price
- aggregateOffer.lowPrice
- availability w postaci URL schema.org

C. Dodaj helpery:
- first_valid_price(*values)
- deep_find_prices(obj)
- deep_find_strings(obj, keys)
- extract_next_data(html)
- extract_embedded_json_objects(html)
- normalize_text_for_match(text)
- model_matches(product, parsed, html)

D. Popraw product_mismatch().
Obecna logika jest zbyt agresywna:
- bierze tylko parsed.product_name + pierwsze 5000 znaków HTML,
- wymaga jednego z pierwszych dwóch słów modelu,
- przez to poprawne strony mogą zostać odrzucone jako product_mismatch.

Nowa logika:
1. Najpierw zbuduj tekst do dopasowania z:
   - parsed.product_name
   - title strony
   - h1
   - canonical URL
   - og:title
   - JSON-LD name
   - wybrane fragmenty JSON aplikacji, jeśli dostępne
2. Normalizuj:
   - lower()
   - usuń polskie znaki
   - zamień plus/+ na plus i znak plus jednocześnie
   - usuń nadmiarowe spacje
   - ujednolić "gb", "5g", "pro+", "pro plus"
3. Wymagaj zgodności wariantu:
   - ram_gb i storage_gb z config/products.json muszą wystąpić w tekście albo w URL w formie np. 12/512, 12-512, 12gb 512gb, 12 gb / 512 gb.
4. Dla nazwy modelu stosuj tokeny istotne, ale ignoruj słowa marki, gdy sklep dodaje markę automatycznie:
   - Xiaomi Redmi Note 14 Pro+ 5G ma pasować do Redmi Note 14 Pro+ 5G.
   - Xiaomi POCO X7 Pro ma pasować do POCO X7 Pro.
5. Nie ustawiaj product_mismatch, jeśli:
   - cena jest poprawna,
   - wariant RAM/pamięć pasuje,
   - nazwa zawiera większość tokenów modelu.
6. Akcesoria odrzucaj dalej, ale ostrożnie:
   - etui, case, szkło, folia, ładowarka, kabel, abonament, rata z abonamentem.
   - Nie odrzucaj strony tylko dlatego, że HTML zawiera słowo "ładowarka" w sekcji rekomendacji; akcesoria mają być wykrywane głównie w product_name/title/h1.

E. Zmień kolejność walidacji w main().
Po parsed:
1. price = parse_price(...)
2. availability = normalize_availability(...)
3. jeśli availability == withdrawn -> status withdrawn
4. jeśli price jest None i availability == out_of_stock -> status out_of_stock
5. jeśli price jest None -> status price_missing
6. dopiero potem uruchom model_matches/product_mismatch
7. jeśli mismatch -> product_mismatch
8. jeśli validate_price(price) false -> price_missing / suspicious_price
9. jeśli OK -> zapisz row

Dzięki temu strony bez ceny nie będą myląco raportowane jako product_mismatch.

F. Dodaj lepsze logowanie błędów.
W data/errors.json zapisuj:
- status
- error_type
- error_message
- parser_name
- fetch_method: "requests" albo "playwright"
- http_status, jeśli znany
- product_name, jeśli udało się odczytać
- extracted_price_raw, jeśli była cena, ale nie przeszła walidacji

G. Playwright.
Aktualny fetch_playwright jest sensowny, ale trzeba:
- dla Media Markt, Media Expert i Xiaomi zawsze próbować Playwright, jeśli requests nie zawiera ceny;
- po page.goto wykonać wait_for_load_state("networkidle") z timeoutem, a jeśli timeout, kontynuować;
- dodać krótkie wait_for_timeout(2000-4000);
- odrzucić CAPTCHA/antybota tylko, gdy w treści występują jednoznaczne wzorce: captcha, access denied, cloudflare, bot detection.

SZCZEGÓŁOWE ZMIANY W config/products.json

A. Dla każdego modelu przejrzyj sources.
Dla sklepów docelowych używaj wyłącznie tych store_id:
- Xiaomi: mi-com, mi-home, mi-store
- Media Markt: media-markt
- Media Expert: media-expert
- Euro RTV AGD: rtv-euro-agd

B. Usuń albo wyłącz błędne źródła.
Przykład obecnego problemu:
- source z store_id "media-expert", ale URL prowadzi do realme.com — to nie jest Media Expert.
Taki wpis ma być:
- albo usunięty,
- albo scrape_enabled=false, status="manual_review" z notatką, że to oficjalna strona producenta, nie Media Expert.

C. scrape_enabled=true ustawiaj tylko wtedy, gdy:
- URL jest konkretną kartą produktu,
- domena pasuje do store_id,
- RAM/pamięć zgadzają się z modelem,
- cena jest widoczna,
- parser po zmianach faktycznie zwraca cenę,
- validate_config.py przechodzi.

D. Dla Xiaomi:
- mi-com: domena mi.com
- mi-home: domena mi-home.pl
- mi-store: domena mi-store.pl
Jeśli "Xiaomi" ma być widoczne jako jedna grupa w UI, nie zmieniaj store_id; dodaj w frontendzie grupowanie/display label "Xiaomi" dla mi-com/mi-home/mi-store.

SZCZEGÓŁOWE ZMIANY W docs/app.js

A. Obecnie tabela pokazuje tylko:
- best_price
- best_store
- best_url

To powoduje wrażenie, że są tylko dane z Morele.
Zmień szczegóły wiersza tak, aby pokazywały sources_summary dla każdego modelu:
- sklep
- status
- cena, jeśli jest
- dostępność
- link

B. Zmień renderFilters().
Obecnie filtr sklepów bazuje na best_store:
const stores=[...new Set(state.items.map(i=>i.best_store).filter(Boolean))];

Zmień na zbieranie sklepów z sources_summary, np.:
- wszystkie source.store_name, które mają status ok albo price != null,
- plus opcjonalnie sklepy z błędem, jeśli chcesz filtrować problemy.

C. Filtr po sklepie nie powinien sprawdzać tylko i.best_store.
Powinien przepuszczać model, jeśli:
- i.best_store === wybrany sklep
albo
- i.sources_summary zawiera source.store_name === wybrany sklep.

D. Dodaj liczniki:
- sources_checked = liczba źródeł w sources_summary
- sources_ok = liczba źródeł ze statusem ok i ceną
Można liczyć w app.js albo zapisywać w data/latest.json.

TESTY I KRYTERIA AKCEPTACJI

1. Uruchom:
python3 scripts/test_parse_price.py

2. Uruchom:
python3 scripts/validate_config.py

3. Uruchom:
python3 scripts/fetch_prices.py

4. Sprawdź data/errors.json.
Dla poprawnych kart produktów nie może być masowo:
- product_mismatch
- source_disabled
- domain mismatch
- parser_not_implemented

5. Sprawdź data/latest.json komendą:
python3 - <<'PY'
import json
wanted = {"media-markt", "media-expert", "rtv-euro-agd"}
xiaomi = {"mi-com", "mi-home", "mi-store"}

data = json.load(open("data/latest.json", encoding="utf-8"))
seen = set()
seen_xiaomi = set()

for item in data.get("items", []):
    for s in item.get("sources_summary", []):
        if s.get("status") == "ok" and s.get("price") is not None:
            sid = s.get("store_id")
            if sid in wanted:
                seen.add(sid)
            if sid in xiaomi:
                seen_xiaomi.add(sid)

print("seen:", sorted(seen))
print("seen_xiaomi:", sorted(seen_xiaomi))

missing = wanted - seen
if missing:
    raise SystemExit(f"Brak poprawnych odczytów dla: {sorted(missing)}")
if not seen_xiaomi:
    raise SystemExit("Brak poprawnego odczytu dla Xiaomi: mi-com/mi-home/mi-store")
print("OK")
PY

6. Sprawdź UI lokalnie:
python3 -m http.server 8000

Otwórz:
http://localhost:8000

W UI musi być możliwe zobaczenie źródeł:
- Xiaomi / Mi.com / Mi-Home / Mi-Store
- Media Markt
- Media Expert
- RTV Euro AGD
Nie wystarczy, że tabela pokazuje tylko Morele jako najtańszy sklep.

7. Nie commituj danych wygenerowanych z błędnego scrapingu.
Jeżeli parser pobiera losową cenę z rekomendacji, raty, akcesorium albo abonamentu, przerwij i popraw walidację.

OCZEKIWANY EFEKT KOŃCOWY
- scripts/fetch_prices.py ma dedykowane, odporne parsery dla Xiaomi, Media Markt, Media Expert i RTV Euro AGD.
- config/products.json ma poprawne linki do kart produktów w tych sklepach.
- data/latest.json zawiera sources_summary z cenami z więcej niż jednego sklepu.
- UI nie ukrywa dodatkowych sklepów tylko dlatego, że Morele jest najtańsze.
- GitHub Actions nadal działa przez price-tracker.yml i aktualizuje tylko pliki data/*.
