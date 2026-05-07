async function loadLatest() {
  const res = await fetch('data/latest.json');
  if (!res.ok) throw new Error('Nie można wczytać data/latest.json');
  return res.json();
}

function formatTimestamp(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('pl-PL', { timeZone: 'UTC' }) + ' UTC';
}

function renderSummary(data) {
  document.getElementById('models-count').textContent = data.items?.length ?? 0;
  document.getElementById('generated-at').textContent = formatTimestamp(data.generated_at);
}

function renderTable(data) {
  const tbody = document.querySelector('#prices-table tbody');
  tbody.innerHTML = '';
  data.items
    .sort((a, b) => a.display_order - b.display_order)
    .forEach(item => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${item.display_order}</td>
        <td>${item.model_name}</td>
        <td>${item.best_price ?? 'brak danych'}</td>
        <td>${item.best_store ?? '-'}</td>
        <td>${formatTimestamp(item.last_success_at)}</td>
      `;
      tbody.appendChild(tr);
    });
}

loadLatest()
  .then(data => {
    renderSummary(data);
    renderTable(data);
  })
  .catch(err => {
    console.error(err);
    const tbody = document.querySelector('#prices-table tbody');
    tbody.innerHTML = '<tr><td colspan="5">Błąd ładowania danych.</td></tr>';
  });
