# Ceny telefonów

Aplikacja do monitorowania i porównywania cen telefonów bez ofert operatorów komórkowych (np. Play, Orange, Plus, T‑Mobile).

## Założenia

- **GitHub Actions** cyklicznie pobiera ceny i zapisuje historię w repozytorium.
- **GitHub Pages** prezentuje dashboard (statyczna strona).
- Porównywane są ceny zakupu **bez abonamentu**.
- Modele mają stałą kolejność (`display_order`) i nie są sortowane alfabetycznie.
- Różne kolory tego samego wariantu pamięci są traktowane jako jeden model.

## Struktura repozytorium

- `config/products.json` – modele i źródła URL.
- `config/stores.json` – sklepy i zasady zbierania danych.
- `data/prices.csv` – historia odczytów.
- `data/latest.json` – ostatni znany stan.
- `data/errors.json` – historia błędów.
- `scripts/fetch_prices.py` – skrypt pobierania cen (MVP/szkielet).
- `docs/` – dashboard pod GitHub Pages.
- `.github/workflows/price-tracker.yml` – automatyzacja.

## Uruchomienie lokalne (MVP)

```bash
python3 scripts/fetch_prices.py
python3 -m http.server 8000 -d docs
```

Następnie otwórz `http://localhost:8000`.

## Ważne ograniczenia

- Brak obchodzenia CAPTCHA i zabezpieczeń antybotowych.
- Brak agresywnego crawlowania (tylko ręcznie wskazane URL-e).
- Operatorzy komórkowi są wyłączeni z porównania w pierwszej wersji.
