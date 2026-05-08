const PLN = new Intl.NumberFormat('pl-PL',{style:'currency',currency:'PLN'});
const DT = new Intl.DateTimeFormat('pl-PL',{dateStyle:'medium',timeStyle:'short'});
let state = { items: [], stores: [], history: [], errors: [] };

async function loadJson(path, fallback){ try { const r = await fetch(path); return r.ok ? await r.json() : fallback; } catch { return fallback; } }
const fmtDate=v=>v?DT.format(new Date(v)):'-';
const fmtPrice=v=>v==null?'<span class="badge no_data">Brak danych</span>':PLN.format(v);

function statusBadge(item){ if(item.status==='future_or_not_yet_available') return '<span class="badge future">Czekamy na oferty</span>'; if(item.best_price==null) return '<span class="badge no_data">Brak danych</span>'; return '<span class="badge ok">OK</span>'; }

function applyFilters(){
  const q=document.getElementById('search').value.toLowerCase(); const sf=document.getElementById('store-filter').value; const st=document.getElementById('status-filter').value; const sort=document.getElementById('sort-by').value;
  let items=[...state.items].filter(i=>i.model_name.toLowerCase().includes(q));
  if(sf!=='all') items=items.filter(i=>i.best_store===sf);
  if(st==='with_price') items=items.filter(i=>i.best_price!=null);
  if(st==='no_data') items=items.filter(i=>i.best_price==null || i.status==='no_data');
  if(st==='error') items=items.filter(i=>i.status==='error');
  items.sort((a,b)=> sort==='best_price' ? ((a.best_price??1e12)-(b.best_price??1e12)) : sort==='price_change' ? ((a.price_change??0)-(b.price_change??0)) : sort==='model_name' ? a.model_name.localeCompare(b.model_name,'pl') : a.display_order-b.display_order);
  renderTable(items);
}

function renderSummary(data){
  const withData=data.items.filter(i=>i.best_price!=null).length;
  document.getElementById('models-count').textContent=data.items.length;
  document.getElementById('models-with-data').textContent=withData;
  document.getElementById('generated-at').textContent=fmtDate(data.generated_at);
  document.getElementById('sources-count').textContent=state.stores.length;
}
function renderCards(){ document.getElementById('cards').innerHTML='<article class="card"><h3>Najtańszy model</h3><p>'+ (state.items.filter(i=>i.best_price!=null).sort((a,b)=>a.best_price-b.best_price)[0]?.model_name ?? 'Brak danych')+'</p></article>'; }
function renderTable(items){ const tbody=document.querySelector('#prices-table tbody'); tbody.innerHTML=''; items.forEach(i=>{ const tr=document.createElement('tr'); tr.innerHTML=`<td><details><summary>${i.model_name}</summary><div class="details">${statusBadge(i)} · źródeł OK: ${i.sources_ok ?? 0}/${i.sources_checked ?? 0}</div></details></td><td>${i.ram_gb ?? '-'} / ${i.storage_gb ?? '-'} GB</td><td>${fmtPrice(i.best_price)}</td><td>${i.best_store ?? '-'}</td><td>${i.price_change!=null?PLN.format(i.price_change):'-'}</td><td>${fmtPrice(i.historical_min_price)}</td><td>${fmtPrice(i.historical_max_price)}</td><td>${i.availability ?? '-'}</td><td>${fmtDate(i.last_success_at)}</td><td>${i.best_url?`<a href="${i.best_url}" target="_blank" rel="noopener">Oferta</a>`:'-'}</td>`; tbody.appendChild(tr); }); }
function renderFilters(){ const stores=[...new Set(state.items.map(i=>i.best_store).filter(Boolean))]; const sel=document.getElementById('store-filter'); sel.innerHTML='<option value="all">Wszystkie sklepy</option>'+stores.map(s=>`<option>${s}</option>`).join(''); ['search','store-filter','status-filter','sort-by'].forEach(id=>document.getElementById(id).addEventListener('input',applyFilters)); }
function renderChart(){ const sel=document.getElementById('chart-model'); sel.innerHTML=state.items.map(i=>`<option value="${i.model_id}">${i.model_name}</option>`).join(''); const canvas=document.getElementById('history-chart'); const msg=document.getElementById('chart-empty'); if(!state.history.length){ msg.classList.remove('hidden'); return; } msg.classList.add('hidden'); const draw=()=>{ const model=sel.value; const rows=state.history.filter(r=>r.model_id===model && r.price_current); const labels=rows.map(r=>r.date); const data=rows.map(r=>Number(r.price_current)); if(window.priceChart) window.priceChart.destroy(); window.priceChart=new Chart(canvas,{type:'line',data:{labels,datasets:[{label:'Cena',data,borderColor:'#2f6fed'}]}}); }; sel.addEventListener('change',draw); draw(); }

(async function(){
  const [latest,products,stores,errors,pricesJson]=await Promise.all([loadJson('data/latest.json',{items:[]}),loadJson('config/products.json',[]),loadJson('config/stores.json',[]),loadJson('data/errors.json',{errors:[]}),loadJson('data/prices.json',{rows:[]})]);
  const map=Object.fromEntries(products.map(p=>[p.model_id,p]));
  state.items=(latest.items||[]).map(i=>({...map[i.model_id],...i})); state.stores=stores; state.errors=errors.errors||[]; state.history=pricesJson.rows||[];
  renderSummary(latest); renderCards(); renderFilters(); applyFilters(); renderChart();
})();
