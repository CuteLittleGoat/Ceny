#!/usr/bin/env python3
from __future__ import annotations
import csv, json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PRODUCTS = ROOT / "config/products.json"
CONFIG_STORES = ROOT / "config/stores.json"
DATA_PRICES = ROOT / "data/prices.csv"
DATA_LATEST = ROOT / "data/latest.json"
DATA_ERRORS = ROOT / "data/errors.json"
FIELDS=["timestamp","date","display_order","model_id","model_name","store_id","store_name","price_current","price_regular","price_lowest_30_days","currency","availability","color","source_url","seller","is_marketplace","status","notes"]

def load_json(p:Path): return json.loads(p.read_text(encoding='utf-8'))

def append_rows(rows):
    if not rows: return
    with DATA_PRICES.open('a',encoding='utf-8',newline='') as f: csv.DictWriter(f,fieldnames=FIELDS).writerows(rows)

def main():
    now=datetime.now(timezone.utc)
    products=load_json(CONFIG_PRODUCTS); stores={s['store_id']:s for s in load_json(CONFIG_STORES)}
    errors=[]; rows=[]; latest=[]
    for pr in sorted(products,key=lambda x:x['display_order']):
        ok=[]; checked=0; failed=0
        for src in pr.get('sources',[]):
            checked+=1
            if not src.get('scrape_enabled') or not src.get('url'):
                failed+=1
                errors.append({'timestamp':now.isoformat(),'model_id':pr['model_id'],'store_id':src.get('store_id'),'url':src.get('url'),'error_type':src.get('status','not_found'),'error_message':src.get('notes','Źródło pominięte')})
                continue
            store=stores.get(src['store_id'])
            if not store:
                failed+=1; errors.append({'timestamp':now.isoformat(),'model_id':pr['model_id'],'store_id':src.get('store_id'),'url':src.get('url'),'error_type':'unknown_store','error_message':'Store missing'}); continue
            failed+=1; errors.append({'timestamp':now.isoformat(),'model_id':pr['model_id'],'store_id':src['store_id'],'url':src['url'],'error_type':'not_implemented','error_message':'Scraper for store not implemented'})
        item={'display_order':pr['display_order'],'model_id':pr['model_id'],'model_name':pr['model_name'],'ram_gb':pr.get('ram_gb'),'storage_gb':pr.get('storage_gb'),'best_price':None,'best_store':None,'best_url':None,'best_color':None,'currency':'PLN','availability':None,'last_success_at':None,'previous_price':None,'price_change':None,'price_change_percent':None,'historical_min_price':None,'historical_max_price':None,'sources_checked':checked,'sources_ok':len(ok),'sources_failed':failed,'status':'future_or_not_yet_available' if any(s.get('status')=='future_or_not_yet_available' for s in pr.get('sources',[])) else 'no_data'}
        latest.append(item)
    append_rows(rows)
    DATA_LATEST.write_text(json.dumps({'generated_at':now.isoformat(),'items':latest},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    DATA_ERRORS.write_text(json.dumps({'generated_at':now.isoformat(),'errors':errors},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__': main()
