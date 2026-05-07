# Ceny telefonów

Statyczny dashboard do porównywania cen telefonów (bez abonamentu i ofert operatorów), publikowany przez GitHub Pages i aktualizowany przez GitHub Actions.

## Modele
16 modeli w stałej kolejności `display_order` (bez sortowania alfabetycznego), m.in. POCO F8/F7/X7, OnePlus Nord 4, Xiaomi 13T, Samsung Galaxy A56, Nothing Phone (3a), Motorola Edge 50 Neo.

## Sklepy
Główne źródła: x-kom, RTV Euro AGD, Komputronik, Morele, Neonet, OleOle!, Avans, Mi-Home.pl, Mi-Store.pl, Samsung.com/pl, Nothing.tech PL.

## Jak to działa
- `scripts/fetch_prices.py` buduje `data/latest.json`, `data/errors.json` i dopisuje historię do `data/prices.csv`.
- Workflow `.github/workflows/price-tracker.yml` uruchamia proces ręcznie i 2x dziennie (06:17, 18:17 UTC).
- `index.html` + `docs/*` renderują dashboard bez backendu.

## Lokalnie
```bash
python3 scripts/fetch_prices.py
python3 -m http.server 8000
```
Otwórz: `http://localhost:8000`.

## Dane
- `config/products.json` – modele + źródła URL (kolory traktowane jako ten sam model).
- `config/stores.json` – konfiguracja sklepów i statusy.
- `data/prices.csv` – historia cen.
- `data/latest.json` – najnowszy stan dashboardu.
- `data/errors.json` – błędy i źródła pominięte.

## Ograniczenia
- Brak omijania CAPTCHA i zabezpieczeń antybotowych.
- Brak agresywnego crawlowania; tylko konkretne URL-e produktów.
- Marketplace i źródła kontrolne są ograniczane lub wyłączane.
- Gdy brak wiarygodnego odczytu, dane pozostają `null` (nigdy `0`).
