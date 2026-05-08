#!/usr/bin/env python3
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
products=json.loads((ROOT/'config/products.json').read_text(encoding='utf-8'))
stores={s['store_id']:s for s in json.loads((ROOT/'config/stores.json').read_text(encoding='utf-8'))}
PARSERS={'mi-com','mi-home','mi-store','media-expert','media-markt','rtv-euro-agd','morele','x-kom'}
errors=[]
for p in products:
  for s in p.get('sources',[]):
    sid=s.get('store_id')
    if sid not in stores: errors.append(f"missing store {sid}")
    if s.get('scrape_enabled') and sid not in PARSERS: errors.append(f"active source without parser {sid}")
    if s.get('scrape_enabled') and not s.get('url'): errors.append(f"active source without url {p['model_id']} {sid}")
    vl=s.get('variant_label','')
    expected=f"{p.get('ram_gb')}/{p.get('storage_gb')}"
    if vl and expected not in vl: errors.append(f"variant_label mismatch {p['model_id']} {sid}")
    url=(s.get('url') or '').lower()
    if s.get('scrape_enabled') and stores.get(sid,{}).get('source_type')=='marketplace': errors.append(f"active marketplace {sid}")
    domain_ok={
      'media-expert':'mediaexpert.pl',
      'media-markt':'mediamarkt.pl',
      'rtv-euro-agd':'euro.com.pl',
      'mi-com':'mi.com','mi-home':'mi-home.pl','mi-store':'mi-store.pl'
    }
    if sid in domain_ok and url and domain_ok[sid] not in url and not (s.get('status')=='manual_review' and not s.get('scrape_enabled')):
      errors.append(f"domain mismatch {sid} -> {url}")
if errors:
  print('\n'.join(errors)); raise SystemExit(1)
print('OK')
