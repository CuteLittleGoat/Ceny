#!/usr/bin/env python3
from __future__ import annotations
import csv, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

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


def parse_xkom(url:str)->dict:
    req=Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; CenyBot/1.0; +https://example.local)"})
    with urlopen(req, timeout=20) as r:
        html=r.read().decode('utf-8','ignore')
    m=re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    if not m:
        raise ValueError('Brak JSON-LD')
    blobs=re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    product=None
    for b in blobs:
        try:
            j=json.loads(b)
        except Exception:
            continue
        candidates=j if isinstance(j,list) else [j]
        for c in candidates:
            if isinstance(c,dict) and c.get('@type')=='Product' and c.get('offers'):
                product=c
                break
        if product:
            break
    if not product:
        raise ValueError('Brak Product JSON-LD')
    offers=product.get('offers',{})
    if isinstance(offers,list):
        offers=offers[0] if offers else {}
    price=offers.get('price')
    if price is None:
        raise ValueError('Brak ceny')
    avail=offers.get('availability','')
    availability='in_stock' if 'InStock' in avail else ('out_of_stock' if 'OutOfStock' in avail else 'unknown')
    return {
        'price_current': float(str(price).replace(',','.')),
        'currency': offers.get('priceCurrency','PLN'),
        'availability': availability,
        'seller': 'x-kom'
    }


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
            try:
                if src['store_id']=='x-kom':
                    parsed=parse_xkom(src['url'])
                else:
                    raise NotImplementedError('Scraper for store not implemented')
            except (URLError, HTTPError, TimeoutError) as e:
                failed+=1; errors.append({'timestamp':now.isoformat(),'model_id':pr['model_id'],'store_id':src['store_id'],'url':src['url'],'error_type':'network_error','error_message':str(e)}); continue
            except Exception as e:
                failed+=1; errors.append({'timestamp':now.isoformat(),'model_id':pr['model_id'],'store_id':src['store_id'],'url':src['url'],'error_type':'parse_error','error_message':str(e)}); continue
            row={'timestamp':now.isoformat(),'date':now.date().isoformat(),'display_order':pr['display_order'],'model_id':pr['model_id'],'model_name':pr['model_name'],'store_id':src['store_id'],'store_name':src.get('store_name',src['store_id']),'price_current':parsed['price_current'],'price_regular':None,'price_lowest_30_days':None,'currency':parsed['currency'],'availability':parsed['availability'],'color':src.get('color'),'source_url':src['url'],'seller':parsed['seller'],'is_marketplace':False,'status':'ok','notes':'x-kom parser v1'}
            rows.append(row)
            ok.append(row)
        best=min(ok,key=lambda r:r['price_current']) if ok else None
        item={'display_order':pr['display_order'],'model_id':pr['model_id'],'model_name':pr['model_name'],'ram_gb':pr.get('ram_gb'),'storage_gb':pr.get('storage_gb'),'best_price':best['price_current'] if best else None,'best_store':best['store_name'] if best else None,'best_url':best['source_url'] if best else None,'best_color':best['color'] if best else None,'currency':best['currency'] if best else 'PLN','availability':best['availability'] if best else None,'last_success_at':now.isoformat() if best else None,'previous_price':None,'price_change':None,'price_change_percent':None,'historical_min_price':None,'historical_max_price':None,'sources_checked':checked,'sources_ok':len(ok),'sources_failed':failed,'status':'ok' if best else ('future_or_not_yet_available' if any(s.get('status')=='future_or_not_yet_available' for s in pr.get('sources',[])) else 'no_data')}
        latest.append(item)
    append_rows(rows)
    DATA_LATEST.write_text(json.dumps({'generated_at':now.isoformat(),'items':latest},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    DATA_ERRORS.write_text(json.dumps({'generated_at':now.isoformat(),'errors':errors},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__': main()
