#!/usr/bin/env python3
from __future__ import annotations
import csv, json, re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PRODUCTS = ROOT / 'config/products.json'
CONFIG_STORES = ROOT / 'config/stores.json'
DATA_PRICES = ROOT / 'data/prices.csv'
DATA_PRICES_JSON = ROOT / 'data/prices.json'
DATA_LATEST = ROOT / 'data/latest.json'
DATA_ERRORS = ROOT / 'data/errors.json'

MIN_PRICE=300
MAX_PRICE=20000
SUSPICIOUS={0,1,72,99,181089,226934}
PRIORITY={k:i for i,k in enumerate(['mi-com','mi-home','mi-store','media-expert','media-markt','rtv-euro-agd','morele','x-kom'])}
HEADERS={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36","Accept-Language":"pl-PL,pl;q=0.9,en;q=0.8"}

FIELDS=["timestamp","date","display_order","model_id","model_name","store_id","store_name","price_current","price_regular","price_lowest_30_days","currency","availability","color","source_url","seller","is_marketplace","status","notes"]


def load_json(path): return json.loads(path.read_text(encoding='utf-8'))

def parse_price(raw):
    if raw is None: return None
    t=str(raw).strip().lower().replace('zł','').replace('pln','')
    t=re.sub(r'[^0-9,\.\s]','',t).strip()
    if not t: return None
    t=t.replace(' ','')
    if ',' in t and '.' in t:
        if t.rfind(',')>t.rfind('.'):
            t=t.replace('.','').replace(',','.')
        else:
            t=t.replace(',','')
    elif ',' in t:
        t=t.replace('.','').replace(',','.')
    try: v=float(t)
    except: return None
    return round(v,2) if v>0 else None

def validate_price(v):
    if v is None: return False
    if v in SUSPICIOUS: return False
    return MIN_PRICE<=v<=MAX_PRICE

def normalize_availability(raw):
    t=str(raw or '').lower()
    if any(k in t for k in ['instock','dostęp','dostep','available']): return 'in_stock'
    if any(k in t for k in ['outofstock','niedost','brak']): return 'out_of_stock'
    if any(k in t for k in ['withdrawn','wycof','discontinued']): return 'withdrawn'
    return 'unknown'

def fetch_http(url):
    try:
        r=requests.get(url,headers=HEADERS,timeout=20)
        if r.status_code==403: return None,'http_403_blocked','HTTP 403'
        if r.status_code>=400: return None,'network_error',f'HTTP {r.status_code}'
        return r.text,'ok',None
    except Exception as e:
        return None,'network_error',str(e)

def fetch_playwright(url):
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None,'requires_javascript','Playwright unavailable'
    try:
        with sync_playwright() as p:
            b=p.chromium.launch(headless=True)
            page=b.new_page(locale='pl-PL',user_agent=HEADERS['User-Agent'])
            page.goto(url,wait_until='domcontentloaded',timeout=45000)
            page.wait_for_timeout(2000)
            html=page.content(); b.close()
            if 'captcha' in html.lower(): return None,'blocked_or_captcha','CAPTCHA detected'
            return html,'ok',None
    except Exception as e:
        return None,'blocked_or_captcha',str(e)

def extract_jsonld_product(html):
    for m in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',html,re.S|re.I):
        try: obj=json.loads(m.strip())
        except: continue
        q=[obj] if not isinstance(obj,list) else list(obj)
        while q:
            it=q.pop(0)
            if isinstance(it,dict) and it.get('@type')=='Product': return it
            if isinstance(it,dict): q.extend(v for v in it.values() if isinstance(v,(dict,list)))
            elif isinstance(it,list): q.extend(it)
    return None

def parse_generic(html, seller):
    p=extract_jsonld_product(html)
    out={'price_current':None,'currency':'PLN','availability':'unknown','seller':seller,'product_name':''}
    if p:
        out['product_name']=str(p.get('name',''))
        offers=p.get('offers',{})
        if isinstance(offers,list): offers=offers[0] if offers else {}
        out['price_current']=parse_price(offers.get('price'))
        out['currency']=offers.get('priceCurrency') or 'PLN'
        out['availability']=normalize_availability(offers.get('availability'))
    if out['price_current'] is None:
        soup=BeautifulSoup(html,'lxml')
        title=soup.title.text if soup.title else ''
        out['product_name']=out['product_name'] or title
        for pat in [r'"price"\s*:\s*"?([0-9\s.,]+)"?',r'content="([0-9\s.,]+)"[^>]*itemprop="price"']:
            m=re.search(pat,html,re.I)
            if m:
                out['price_current']=parse_price(m.group(1)); break
    if out['availability']=='unknown' and re.search(r'niedostęp|brak w magazynie',html,re.I): out['availability']='out_of_stock'
    return out

def product_mismatch(product, parsed, html):
    text=(parsed.get('product_name','')+' '+html[:5000]).lower()
    model_words=[w.lower() for w in re.split(r'\W+',product['model_name']) if len(w)>=3]
    if not any(w in text for w in model_words[:2]): return True
    if any(bad in text for bad in ['etui','ładowarka','sluchawki','szkło','abonament']): return True
    return False

def parse_mi(html): return parse_generic(html,'Mi.com Polska')
def parse_media_expert(html): return parse_generic(html,'Media Expert')
def parse_media_markt(html): return parse_generic(html,'Media Markt')
def parse_rtv(html): return parse_generic(html,'RTV Euro AGD')
def parse_morele(html): return parse_generic(html,'Morele')
def parse_xkom(html): return parse_generic(html,'x-kom')

PARSERS={'mi-com':parse_mi,'mi-home':parse_mi,'mi-store':parse_mi,'media-expert':parse_media_expert,'media-markt':parse_media_markt,'rtv-euro-agd':parse_rtv,'morele':parse_morele,'x-kom':parse_xkom}

def clean_history(rows):
    return [r for r in rows if validate_price(parse_price(r.get('price_current')))]

def main():
    now=datetime.now(timezone.utc).isoformat(); day=now[:10]
    products=load_json(CONFIG_PRODUCTS); stores={s['store_id']:s for s in load_json(CONFIG_STORES)}
    old=[]
    if DATA_PRICES.exists():
        old=list(csv.DictReader(DATA_PRICES.open(encoding='utf-8')))
    old=clean_history(old)
    errs=[]; new=[]; latest=[]
    for p in sorted(products,key=lambda x:x['display_order']):
        offers=[]; summary=[]
        sources=sorted(p.get('sources',[]),key=lambda s:PRIORITY.get(s.get('store_id'),999))
        for s in sources:
            sid=s.get('store_id'); store=stores.get(sid,{}); url=s.get('url'); st_name=store.get('store_name',s.get('store_name',sid))
            status='ok'; msg=''; price=None; avail=None
            if not s.get('scrape_enabled',False): status='source_disabled'
            elif not store.get('scrape_enabled',False): status='store_disabled'
            elif sid not in PARSERS: status='parser_not_implemented'
            elif not url: status='price_missing'; msg='missing url'
            else:
                html,fs,fe=fetch_http(url)
                if html is None or not extract_jsonld_product(html):
                    if fs in ('http_403_blocked','ok'):
                        html2,fs2,fe2=fetch_playwright(url)
                        if html2 is not None: html=html2
                        else: fs,fe=fs2,fe2
                if html is None:
                    status=fs; msg=fe or ''
                else:
                    parsed=PARSERS[sid](html); price=parse_price(parsed.get('price_current')); avail=normalize_availability(parsed.get('availability'))
                    if product_mismatch(p,parsed,html): status='product_mismatch'
                    elif avail=='withdrawn': status='withdrawn'
                    elif avail=='out_of_stock' and price is None: status='out_of_stock'
                    elif not validate_price(price): status='price_missing'
                    else:
                        row={"timestamp":now,"date":day,"display_order":p['display_order'],"model_id":p['model_id'],"model_name":p['model_name'],"store_id":sid,"store_name":st_name,"price_current":price,"price_regular":None,"price_lowest_30_days":None,"currency":parsed.get('currency') or 'PLN',"availability":avail,"color":s.get('color'),"source_url":url,"seller":parsed.get('seller') or st_name,"is_marketplace":store.get('source_type')=='marketplace',"status":'ok',"notes":f'parser:{sid}'}
                        new.append(row); offers.append(row)
            if status!='ok': errs.append({"timestamp":now,"model_id":p['model_id'],"model_name":p['model_name'],"store_id":sid,"store_name":st_name,"url":url,"error_type":status,"error_message":msg or status,"status":status,"scrape_enabled":bool(s.get('scrape_enabled',False))})
            summary.append({'store_id':sid,'store_name':st_name,'status':status,'price':price,'availability':avail,'url':url})
        best=min(offers,key=lambda x:(x['price_current'],PRIORITY.get(x['store_id'],999))) if offers else None
        hist=[parse_price(r['price_current']) for r in old+new if r.get('model_id')==p['model_id'] and validate_price(parse_price(r.get('price_current')))]
        prev_list=[parse_price(r['price_current']) for r in old if r.get('model_id')==p['model_id'] and validate_price(parse_price(r.get('price_current')))]
        prev=prev_list[-1] if prev_list else None
        latest.append({'display_order':p['display_order'],'model_id':p['model_id'],'model_name':p['model_name'],'ram_gb':p.get('ram_gb'),'storage_gb':p.get('storage_gb'),'best_price':best['price_current'] if best else None,'best_store':best['store_name'] if best else None,'best_url':best['source_url'] if best else None,'currency':best['currency'] if best else 'PLN','availability':best['availability'] if best else None,'previous_price':prev,'historical_min_price':min(hist) if hist else None,'historical_max_price':max(hist) if hist else None,'status':'ok' if best else 'no_data','sources_summary':summary})
    # overwrite cleaned history
    with DATA_PRICES.open('w',encoding='utf-8',newline='') as h:
        w=csv.DictWriter(h,fieldnames=FIELDS); w.writeheader(); w.writerows(old+new)
    DATA_PRICES_JSON.write_text(json.dumps({'generated_at':now,'rows':old+new},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    DATA_LATEST.write_text(json.dumps({'generated_at':now,'items':latest},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    DATA_ERRORS.write_text(json.dumps({'generated_at':now,'errors':errs},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__': main()
