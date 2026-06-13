document.addEventListener('DOMContentLoaded', () => {
    const refreshBtn = document.getElementById('refresh-analysis');
    refreshBtn.addEventListener('click', () => loadAnalysis());

    const elementSelect = document.getElementById('element-select');
    elementSelect.addEventListener('change', () => loadAnalysis());

    fetch('/api/schema')
        .then(r => r.json())
        .then(schema => {
            elementSelect.innerHTML = '<option value="">All Elements</option>';
            schema.elements.forEach(el => {
                const opt = document.createElement('option');
                opt.value = el;
                opt.textContent = el;
                elementSelect.appendChild(opt);
            });
            loadAnalysis();
        })
        .catch(err => console.error('Error loading schema:', err));
});

function getSelectedElement() {
    const el = document.getElementById('element-select').value;
    return el || null;
}

function loadAnalysis() {
    const payload = { element: getSelectedElement() };

    fetch('/api/analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    })
        .then(r => {
            if (!r.ok) {
                return r.text().then(t => { throw new Error(`Analysis API ${r.status}: ${t}`); });
            }
            return r.json();
        })
        .then(data => {
            renderAnalysisCards(data.stats);
            renderSummaryTable(data.stats);
            renderPlot('analysis-chart', data.plots.mean_chart);
            renderPlot('analysis-boxplot', data.plots.box_plot);
            renderPlot('analysis-heatmap', data.plots.correlation_heatmap);
            renderPlot('analysis-histogram', data.plots.histogram);
        })
        .catch(err => console.error('Error loading analysis:', err));
}

function renderPlot(containerId, fig) {
    if (!fig) return;
    const gd = document.getElementById(containerId);
    if (!gd) { console.error(`Container not found: ${containerId}`); return; }
    if (gd.data && gd.data.length) {
        Plotly.react(containerId, fig.data, fig.layout, { responsive: true });
    } else {
        Plotly.newPlot(containerId, fig.data, fig.layout, { responsive: true });
    }
}

function renderAnalysisCards(stats) {
    const cards = document.getElementById('analysis-cards');
    cards.innerHTML = '';

    const cardsData = [
        { title: 'Total Records', value: stats.total_records },
        { title: 'Tracked Numeric Fields', value: stats.numeric_fields },
        { title: 'Highest Mean', value: stats.highest_mean ? `${stats.highest_mean.column} (${stats.highest_mean.value})` : 'n/a' },
        { title: 'Highest Median', value: stats.highest_median ? `${stats.highest_median.column} (${stats.highest_median.value})` : 'n/a' },
        { title: 'Top Correlated Pair', value: stats.top_correlation ? `${stats.top_correlation.pair}: ${stats.top_correlation.value}` : 'n/a' },
    ];

    cardsData.forEach(card => {
        const wrapper = document.createElement('div');
        wrapper.className = 'bg-gray-900 p-5 rounded-xl border border-gray-800 shadow-sm';
        wrapper.innerHTML = `
            <div class="text-sm text-gray-400 mb-2">${card.title}</div>
            <div class="text-3xl font-bold text-white">${card.value}</div>
        `;
        cards.appendChild(wrapper);
    });
}

function renderSummaryTable(stats) {
    const tableContainer = document.getElementById('analysis-table');
    const summary = stats.summary || [];

    const rowsHtml = summary.map(s => `
        <tr class="border-b border-gray-800 hover:bg-gray-800">
            <td class="px-4 py-3 text-sm text-gray-200 font-medium">${s.column}</td>
            <td class="px-4 py-3 text-sm text-gray-200">${s.count}</td>
            <td class="px-4 py-3 text-sm text-gray-200">${s.mean.toFixed(2)}</td>
            <td class="px-4 py-3 text-sm text-gray-200">${s.median.toFixed(2)}</td>
            <td class="px-4 py-3 text-sm text-gray-200">${s.std_dev.toFixed(2)}</td>
            <td class="px-4 py-3 text-sm text-gray-200">${s.variance.toFixed(2)}</td>
            <td class="px-4 py-3 text-sm text-gray-200">${s.min.toFixed(2)}</td>
            <td class="px-4 py-3 text-sm text-gray-200">${s.max.toFixed(2)}</td>
            <td class="px-4 py-3 text-sm text-gray-200">${s.skewness.toFixed(2)}</td>
            <td class="px-4 py-3 text-sm text-gray-200">${s.kurtosis.toFixed(2)}</td>
        </tr>
    `).join('');

    tableContainer.innerHTML = `
        <table class="min-w-full text-left text-sm text-gray-300">
            <thead>
                <tr class="border-b border-gray-700 text-xs uppercase tracking-wide text-gray-400">
                    <th class="px-4 py-3">Measure</th>
                    <th class="px-4 py-3">Count</th>
                    <th class="px-4 py-3">Mean</th>
                    <th class="px-4 py-3">Median</th>
                    <th class="px-4 py-3">Std Dev</th>
                    <th class="px-4 py-3">Variance</th>
                    <th class="px-4 py-3">Min</th>
                    <th class="px-4 py-3">Max</th>
                    <th class="px-4 py-3">Skewness</th>
                    <th class="px-4 py-3">Kurtosis</th>
                </tr>
            </thead>
            <tbody>${rowsHtml}</tbody>
        </table>
    `;
}
