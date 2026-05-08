#!/usr/bin/env python3
from __future__ import annotations
import csv, json, re, unicodedata
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
TARGET_PLAYWRIGHT={'mi-com','mi-home','mi-store','media-expert','media-markt'}

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

def first_valid_price(*values):
    for v in values:
        p=parse_price(v)
        if p is not None:
            return p
    return None

def validate_price(v):
    if v is None: return False
    if v in SUSPICIOUS: return False
    return MIN_PRICE<=v<=MAX_PRICE

def normalize_availability(raw):
    t=str(raw or '').lower()
    if any(k in t for k in ['instock','dostęp','dostep','available','in stock','na stanie']): return 'in_stock'
    if any(k in t for k in ['outofstock','niedost','brak']): return 'out_of_stock'
    if any(k in t for k in ['withdrawn','wycof','discontinued']): return 'withdrawn'
    return 'unknown'

def fetch_http(url):
    try:
        r=requests.get(url,headers=HEADERS,timeout=20)
        if r.status_code==403: return None,'http_403_blocked','HTTP 403',403
        if r.status_code>=400: return None,'network_error',f'HTTP {r.status_code}',r.status_code
        return r.text,'ok',None,r.status_code
    except Exception as e:
        return None,'network_error',str(e),None

def fetch_playwright(url):
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None,'requires_javascript','Playwright unavailable',None
    try:
        with sync_playwright() as p:
            b=p.chromium.launch(headless=True)
            page=b.new_page(locale='pl-PL',user_agent=HEADERS['User-Agent'])
            page.goto(url,wait_until='domcontentloaded',timeout=45000)
            try:
                page.wait_for_load_state('networkidle',timeout=8000)
            except Exception:
                pass
            page.wait_for_timeout(3000)
            html=page.content(); b.close()
            low=html.lower()
            if any(p in low for p in ['captcha','access denied','cloudflare','bot detection']):
                return None,'blocked_or_captcha','Anti-bot detected',None
            return html,'ok',None,None
    except Exception as e:
        return None,'blocked_or_captcha',str(e),None

def deep_find_prices(obj):
    found=[]
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k in {'price','lowPrice','highPrice'}:
                found.append(v)
            found.extend(deep_find_prices(v))
    elif isinstance(obj,list):
        for it in obj: found.extend(deep_find_prices(it))
    return found

def deep_find_strings(obj, keys):
    vals=[]
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k in keys and isinstance(v,str): vals.append(v)
            vals.extend(deep_find_strings(v,keys))
    elif isinstance(obj,list):
        for it in obj: vals.extend(deep_find_strings(it,keys))
    return vals

def extract_next_data(html):
    m=re.search(r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>',html,re.S|re.I)
    if not m: return None
    try: return json.loads(m.group(1))
    except: return None

def extract_embedded_json_objects(html):
    objs=[]
    for m in re.findall(r'<script[^>]*>(\{.+?\}|\[.+?\])</script>',html,re.S|re.I):
        s=m.strip()
        if len(s)<10: continue
        try: objs.append(json.loads(s))
        except: pass
    return objs

def extract_jsonld_product(html):
    for m in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',html,re.S|re.I):
        try: obj=json.loads(m.strip())
        except: continue
        q=[obj] if not isinstance(obj,list) else list(obj)
        while q:
            it=q.pop(0)
            if isinstance(it,dict):
                at=it.get('@type')
                is_product=(at=='Product') or (isinstance(at,list) and 'Product' in at)
                if is_product: return it
                if '@graph' in it and isinstance(it['@graph'],list): q.extend(it['@graph'])
                q.extend(v for v in it.values() if isinstance(v,(dict,list)))
            elif isinstance(it,list): q.extend(it)
    return None

def parse_store(html, seller):
    out={'price_current':None,'price_regular':None,'price_lowest_30_days':None,'currency':'PLN','availability':'unknown','seller':seller,'product_name':'','raw_source':'unknown'}
    p=extract_jsonld_product(html)
    if p:
        out['product_name']=str(p.get('name',''))
        offers=p.get('offers') or p.get('aggregateOffer') or {}
        if isinstance(offers,list): offers=offers[0] if offers else {}
        ps=offers.get('priceSpecification',{}) if isinstance(offers,dict) else {}
        out['price_current']=first_valid_price(offers.get('price'),offers.get('lowPrice'),offers.get('highPrice'),ps.get('price')) if isinstance(offers,dict) else None
        out['currency']=(offers.get('priceCurrency') if isinstance(offers,dict) else None) or 'PLN'
        out['availability']=normalize_availability((offers.get('availability') if isinstance(offers,dict) else None) or p.get('availability'))
        out['raw_source']='jsonld'
    if out['price_current'] is None:
        next_data=extract_next_data(html)
        if next_data:
            out['price_current']=first_valid_price(*deep_find_prices(next_data))
            out['product_name']=out['product_name'] or ' '.join(deep_find_strings(next_data,{'name','title'})[:1])
            out['raw_source']='__NEXT_DATA__'
    if out['price_current'] is None:
        for obj in extract_embedded_json_objects(html):
            out['price_current']=first_valid_price(*deep_find_prices(obj))
            if out['price_current'] is not None:
                out['raw_source']='embedded_json'; break
    if out['price_current'] is None:
        soup=BeautifulSoup(html,'lxml')
        out['product_name']=out['product_name'] or (soup.title.text.strip() if soup.title else '')
        for pat in [r'"price"\s*:\s*"?([0-9\s.,]+)"?',r'itemprop="price"[^>]*content="([0-9\s.,]+)"',r'content="([0-9\s.,]+)"[^>]*itemprop="price"']:
            m=re.search(pat,html,re.I)
            if m:
                out['price_current']=parse_price(m.group(1)); out['raw_source']='dom'; break
    if out['availability']=='unknown' and re.search(r'niedostęp|brak w magazynie',html,re.I): out['availability']='out_of_stock'
    return out

def normalize_text_for_match(text):
    t=unicodedata.normalize('NFKD',str(text or '')).encode('ascii','ignore').decode('ascii').lower()
    t=t.replace('+',' plus ').replace('pro plus','pro+').replace('gb',' gb ').replace('5 g','5g')
    t=re.sub(r'\s+',' ',t)
    return t.strip()

def model_matches(product, parsed, html):
    soup=BeautifulSoup(html,'lxml')
    bits=[parsed.get('product_name',''), soup.title.text if soup.title else '']
    h1=soup.find('h1');
    if h1: bits.append(h1.get_text(' ',strip=True))
    can=soup.find('link',attrs={'rel':'canonical'})
    if can and can.get('href'): bits.append(can['href'])
    og=soup.find('meta',attrs={'property':'og:title'})
    if og and og.get('content'): bits.append(og['content'])
    p=extract_jsonld_product(html)
    if p: bits.append(str(p.get('name','')))
    n=extract_next_data(html)
    if n: bits.extend(deep_find_strings(n,{'name','title'})[:5])
    txt=normalize_text_for_match(' '.join(bits))
    model=normalize_text_for_match(product.get('model_name',''))
    tokens=[t for t in re.split(r'\W+',model) if len(t)>=2 and t not in {'xiaomi','smartfon','phone','redmi','poco'}]
    hit=sum(1 for t in tokens if t in txt)
    ram,sto=product.get('ram_gb'),product.get('storage_gb')
    variant_ok = bool(re.search(fr'\b{ram}\s*(gb)?\s*[/\-]\s*{sto}\s*(gb)?\b',txt) or re.search(fr'\b{ram}\s*gb\b.*\b{sto}\s*gb\b',txt)) if ram and sto else True
    accessory=any(k in txt for k in ['etui','case','szklo','folia','ladowarka','kabel','abonament'])
    return (hit>=max(2, int(len(tokens)*0.6)) and variant_ok and not accessory)

def parse_mi(html): return parse_store(html,'Mi.com Polska')
def parse_media_expert(html): return parse_store(html,'Media Expert')
def parse_media_markt(html): return parse_store(html,'Media Markt')
def parse_rtv(html): return parse_store(html,'RTV Euro AGD')
def parse_morele(html): return parse_store(html,'Morele')
def parse_xkom(html): return parse_store(html,'x-kom')
PARSERS={'mi-com':parse_mi,'mi-home':parse_mi,'mi-store':parse_mi,'media-expert':parse_media_expert,'media-markt':parse_media_markt,'rtv-euro-agd':parse_rtv,'morele':parse_morele,'x-kom':parse_xkom}

def clean_history(rows): return [r for r in rows if validate_price(parse_price(r.get('price_current')))]

def main():
    now=datetime.now(timezone.utc).isoformat(); day=now[:10]
    products=load_json(CONFIG_PRODUCTS); stores={s['store_id']:s for s in load_json(CONFIG_STORES)}
    old=clean_history(list(csv.DictReader(DATA_PRICES.open(encoding='utf-8')))) if DATA_PRICES.exists() else []
    errs=[]; new=[]; latest=[]
    for p in sorted(products,key=lambda x:x['display_order']):
        offers=[]; summary=[]
        for s in sorted(p.get('sources',[]),key=lambda s:PRIORITY.get(s.get('store_id'),999)):
            sid=s.get('store_id'); store=stores.get(sid,{}); url=s.get('url'); st_name=store.get('store_name',s.get('store_name',sid))
            status='ok'; msg=''; price=None; avail=None; parser_name=sid; fetch_method='requests'; http_status=None; parsed_name=None; extracted_raw=None
            if not s.get('scrape_enabled',False): status='source_disabled'
            elif not store.get('scrape_enabled',False): status='store_disabled'
            elif sid not in PARSERS: status='parser_not_implemented'
            elif not url: status='price_missing'; msg='missing url'
            else:
                html,fs,fe,http_status=fetch_http(url)
                if html is None: status=fs; msg=fe or ''
                else:
                    parsed=PARSERS[sid](html); parsed_name=parsed.get('product_name'); price=parse_price(parsed.get('price_current')); avail=normalize_availability(parsed.get('availability')); extracted_raw=parsed.get('price_current')
                    if price is None and sid in TARGET_PLAYWRIGHT:
                        html2,fs2,fe2,_=fetch_playwright(url); fetch_method='playwright'
                        if html2 is not None:
                            parsed=PARSERS[sid](html2); parsed_name=parsed.get('product_name'); price=parse_price(parsed.get('price_current')); avail=normalize_availability(parsed.get('availability')); extracted_raw=parsed.get('price_current')
                        else: status=fs2; msg=fe2 or ''
                    if status=='ok':
                        if avail=='withdrawn': status='withdrawn'
                        elif price is None and avail=='out_of_stock': status='out_of_stock'
                        elif price is None: status='price_missing'
                        elif not model_matches(p,parsed,html): status='product_mismatch'
                        elif not validate_price(price): status='suspicious_price'
                        else:
                            row={"timestamp":now,"date":day,"display_order":p['display_order'],"model_id":p['model_id'],"model_name":p['model_name'],"store_id":sid,"store_name":st_name,"price_current":price,"price_regular":parsed.get('price_regular'),"price_lowest_30_days":parsed.get('price_lowest_30_days'),"currency":parsed.get('currency') or 'PLN',"availability":avail,"color":s.get('color'),"source_url":url,"seller":parsed.get('seller') or st_name,"is_marketplace":store.get('source_type')=='marketplace',"status":'ok',"notes":f'parser:{sid};src:{parsed.get("raw_source")}' }
                            new.append(row); offers.append(row)
            if status!='ok': errs.append({"timestamp":now,"model_id":p['model_id'],"model_name":p['model_name'],"store_id":sid,"store_name":st_name,"url":url,"error_type":status,"error_message":msg or status,"status":status,"parser_name":parser_name,"fetch_method":fetch_method,"http_status":http_status,"product_name":parsed_name,"extracted_price_raw":extracted_raw})
            summary.append({'store_id':sid,'store_name':st_name,'status':status,'price':price,'availability':avail,'url':url})
        best=min(offers,key=lambda x:(x['price_current'],PRIORITY.get(x['store_id'],999))) if offers else None
        latest.append({'display_order':p['display_order'],'model_id':p['model_id'],'model_name':p['model_name'],'ram_gb':p.get('ram_gb'),'storage_gb':p.get('storage_gb'),'best_price':best['price_current'] if best else None,'best_store':best['store_name'] if best else None,'best_url':best['source_url'] if best else None,'currency':best['currency'] if best else 'PLN','availability':best['availability'] if best else None,'status':'ok' if best else 'no_data','sources_summary':summary,'sources_checked':len(summary),'sources_ok':sum(1 for x in summary if x.get('status')=='ok' and x.get('price') is not None)})
    with DATA_PRICES.open('w',encoding='utf-8',newline='') as h:
        w=csv.DictWriter(h,fieldnames=FIELDS); w.writeheader(); w.writerows(old+new)
    DATA_PRICES_JSON.write_text(json.dumps({'generated_at':now,'rows':old+new},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    DATA_LATEST.write_text(json.dumps({'generated_at':now,'items':latest},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    DATA_ERRORS.write_text(json.dumps({'generated_at':now,'errors':errs},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__': main()
