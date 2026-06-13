let allRows = [];
let allColumns = [];
let numericColumns = [];

document.addEventListener('DOMContentLoaded', () => {
    const refreshBtn = document.getElementById('refresh-analysis');
    refreshBtn.addEventListener('click', () => loadAnalysis());

    document.getElementById('data-search').addEventListener('input', renderDataBrowser);
    document.getElementById('data-column-filter').addEventListener('change', renderDataBrowser);

    document.getElementById('dist-element').addEventListener('change', renderDistChart);
    document.getElementById('dist-bins').addEventListener('input', () => {
        document.getElementById('dist-bins-value').textContent = document.getElementById('dist-bins').value;
        renderDistChart();
    });

    document.getElementById('pair-x').addEventListener('change', renderPairChart);
    document.getElementById('pair-y').addEventListener('change', renderPairChart);
    document.getElementById('pair-color').addEventListener('change', renderPairChart);

    loadAnalysis();
});

// ── Data Loading ──

function loadAnalysis() {
    Promise.all([
        fetch('/api/analysis', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }).then(r => r.json()),
        fetch('/api/data').then(r => r.json()),
    ])
        .then(([analysis, data]) => {
            allColumns = data.columns || [];
            allRows = data.rows || [];
            numericColumns = data.numeric_columns || [];

            renderAnalysisCards(analysis.stats);
            renderSummaryTable(analysis.stats);

            populateSelect('dist-element', numericColumns, numericColumns[0] || '');
            populateSelect('pair-x', numericColumns, numericColumns[0] || '');
            populateSelect('pair-y', numericColumns, numericColumns[1] || '');

            const colFilter = document.getElementById('data-column-filter');
            colFilter.innerHTML = '<option value="">All Columns</option>';
            allColumns.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c;
                opt.textContent = c;
                colFilter.appendChild(opt);
            });

            const colorSelect = document.getElementById('pair-color');
            const categorical = allColumns.filter(c => !numericColumns.includes(c) && c !== 'Latitude' && c !== 'Longitude');
            categorical.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c;
                opt.textContent = c;
                colorSelect.appendChild(opt);
            });

            renderDataBrowser();
            renderDistChart();
            renderPairChart();
        })
        .catch(err => console.error('Error loading analysis:', err));
}

// ── Stats Cards ──

function renderAnalysisCards(stats) {
    const cards = document.getElementById('analysis-cards');
    cards.innerHTML = '';
    const items = [
        { title: 'Total Records', value: stats.total_records },
        { title: 'Tracked Numeric Fields', value: stats.numeric_fields },
        { title: 'Highest Mean', value: stats.highest_mean ? `${stats.highest_mean.column} (${stats.highest_mean.value})` : 'n/a' },
        { title: 'Highest Median', value: stats.highest_median ? `${stats.highest_median.column} (${stats.highest_median.value})` : 'n/a' },
        { title: 'Top Correlated Pair', value: stats.top_correlation ? `${stats.top_correlation.pair}: ${stats.top_correlation.value}` : 'n/a' },
    ];
    items.forEach(card => {
        const w = document.createElement('div');
        w.className = 'bg-gray-900 p-5 rounded-xl border border-gray-800 shadow-sm';
        w.innerHTML = `<div class="text-sm text-gray-400 mb-2">${card.title}</div><div class="text-3xl font-bold text-white">${card.value}</div>`;
        cards.appendChild(w);
    });
}

// ── Summary Table ──

function renderSummaryTable(stats) {
    const container = document.getElementById('analysis-table');
    const summary = stats.summary || [];
    const rows = summary.map(s => `
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
    container.innerHTML = `
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
            <tbody>${rows}</tbody>
        </table>`;
}

// ── Data Browser (client-side paginated, searchable, sortable table) ──

let sortCol = null;
let sortDir = 'asc';
let page = 0;
const PAGE_SIZE = 50;

function renderDataBrowser() {
    const search = document.getElementById('data-search').value.toLowerCase();
    const colFilter = document.getElementById('data-column-filter').value;

    let filtered = allRows.filter(r => {
        if (search) {
            const match = Object.values(r).some(v => String(v).toLowerCase().includes(search));
            if (!match) return false;
        }
        return true;
    });

    if (sortCol) {
        filtered.sort((a, b) => {
            const va = a[sortCol], vb = b[sortCol];
            if (va == null || vb == null) return 0;
            const cmp = typeof va === 'number' ? va - vb : String(va).localeCompare(String(vb));
            return sortDir === 'asc' ? cmp : -cmp;
        });
    }

    const total = filtered.length;
    const totalPages = Math.ceil(total / PAGE_SIZE);
    if (page >= totalPages) page = Math.max(0, totalPages - 1);
    const start = page * PAGE_SIZE;
    const slice = filtered.slice(start, start + PAGE_SIZE);

    document.getElementById('data-row-count').textContent = `${start + 1}–${Math.min(start + PAGE_SIZE, total)} of ${total} rows`;

    const displayCols = colFilter ? [colFilter] : allColumns;
    const thead = displayCols.map(c => {
        const arrow = sortCol === c ? (sortDir === 'asc' ? ' &#9650;' : ' &#9660;') : '';
        return `<th class="px-3 py-2 text-xs uppercase tracking-wide text-gray-400 cursor-pointer hover:text-neon select-none" data-col="${c}">${c}${arrow}</th>`;
    }).join('');

    const tbody = slice.map(r => {
        return '<tr class="border-b border-gray-800 hover:bg-gray-800">' +
            displayCols.map(c => `<td class="px-3 py-2 text-sm text-gray-200">${r[c] != null ? r[c] : ''}</td>`).join('') +
            '</tr>';
    }).join('');

    const tableHtml = `<table class="min-w-full text-left"><thead><tr class="border-b border-gray-700">${thead}</tr></thead><tbody>${tbody}</tbody></table>`;
    document.getElementById('data-table-container').innerHTML = tableHtml;

    document.querySelectorAll('#data-table-container th[data-col]').forEach(th => {
        th.addEventListener('click', () => {
            const col = th.dataset.col;
            if (sortCol === col) sortDir = sortDir === 'asc' ? 'desc' : 'asc';
            else { sortCol = col; sortDir = 'asc'; }
            page = 0;
            renderDataBrowser();
        });
    });

    const pagination = document.getElementById('data-pagination');
    const prevDisabled = page <= 0;
    const nextDisabled = page >= totalPages - 1;
    pagination.innerHTML = `
        <button class="px-3 py-1 rounded ${prevDisabled ? 'text-gray-600 cursor-not-allowed' : 'text-gray-300 hover:text-neon hover:bg-gray-800'}" ${prevDisabled ? 'disabled' : ''} data-page="prev">&#8592; Prev</button>
        <span class="text-gray-500">Page ${totalPages ? page + 1 : 0} of ${totalPages}</span>
        <button class="px-3 py-1 rounded ${nextDisabled ? 'text-gray-600 cursor-not-allowed' : 'text-gray-300 hover:text-neon hover:bg-gray-800'}" ${nextDisabled ? 'disabled' : ''} data-page="next">Next &#8594;</button>
    `;
    pagination.querySelectorAll('button:not([disabled])').forEach(btn => {
        btn.addEventListener('click', () => {
            if (btn.dataset.page === 'prev') page--;
            else page++;
            renderDataBrowser();
        });
    });
}

// ── Distribution Explorer (client-side histogram) ──

function renderDistChart() {
    const col = document.getElementById('dist-element').value;
    const bins = parseInt(document.getElementById('dist-bins').value);
    if (!col || !allRows.length) return;

    const values = allRows.map(r => Number(r[col])).filter(v => !Number.isNaN(v));
    if (!values.length) return;

    const mean = values.reduce((s, v) => s + v, 0) / values.length;
    const sorted = values.slice().sort((a, b) => a - b);
    const median = sorted.length % 2 ? sorted[Math.floor(sorted.length / 2)] : (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2;
    const std = Math.sqrt(values.reduce((s, v) => s + (v - mean) ** 2, 0) / values.length);

    document.getElementById('dist-stats').innerHTML =
        `n: <b class="text-gray-200">${values.length}</b> &middot; mean: <b class="text-gray-200">${mean.toFixed(2)}</b> &middot; median: <b class="text-gray-200">${median.toFixed(2)}</b> &middot; std: <b class="text-gray-200">${std.toFixed(2)}</b>`;

    const fig = {
        data: [{
            x: values,
            type: 'histogram',
            nbinsx: bins,
            marker: { color: '#00e676', line: { color: '#0b0f19', width: 1 } },
            name: col,
        }],
        layout: {
            title: `${col} Distribution (${bins} bins)`,
            template: 'plotly_dark',
            margin: { l: 40, r: 20, t: 40, b: 40 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            bargap: 0.05,
            xaxis: { title: col },
            yaxis: { title: 'Frequency' },
            shapes: [
                { type: 'line', x0: mean, x1: mean, y0: 0, y1: 1, yref: 'paper', line: { color: '#ff6b6b', width: 2, dash: 'dash' } },
                { type: 'line', x0: median, x1: median, y0: 0, y1: 1, yref: 'paper', line: { color: '#ffd93d', width: 2, dash: 'dot' } },
            ],
            annotations: [
                { x: mean, y: 1, xref: 'x', yref: 'paper', text: 'mean', showarrow: false, textangle: -90, font: { color: '#ff6b6b', size: 10 }, yshift: 5 },
                { x: median, y: 0.95, xref: 'x', yref: 'paper', text: 'median', showarrow: false, textangle: -90, font: { color: '#ffd93d', size: 10 }, yshift: 5 },
            ],
        },
    };

    const gd = document.getElementById('dist-chart');
    if (gd.data && gd.data.length) Plotly.react(gd, fig.data, fig.layout, { responsive: true });
    else Plotly.newPlot(gd, fig.data, fig.layout, { responsive: true });
}

// ── Element Pair Correlation (client-side scatter + trend line) ──

function renderPairChart() {
    const xCol = document.getElementById('pair-x').value;
    const yCol = document.getElementById('pair-y').value;
    const colorCol = document.getElementById('pair-color').value;
    if (!xCol || !yCol || !allRows.length) return;

    const pairs = allRows
        .map(r => ({ x: Number(r[xCol]), y: Number(r[yCol]), c: r[colorCol] }))
        .filter(p => !Number.isNaN(p.x) && !Number.isNaN(p.y));
    if (!pairs.length) return;

    const n = pairs.length;
    const meanX = pairs.reduce((s, p) => s + p.x, 0) / n;
    const meanY = pairs.reduce((s, p) => s + p.y, 0) / n;
    const num = pairs.reduce((s, p) => s + (p.x - meanX) * (p.y - meanY), 0);
    const denX = Math.sqrt(pairs.reduce((s, p) => s + (p.x - meanX) ** 2, 0));
    const denY = Math.sqrt(pairs.reduce((s, p) => s + (p.y - meanY) ** 2, 0));
    const rVal = denX && denY ? num / (denX * denY) : 0;

    const slope = num / (denX * denX || 1);
    const intercept = meanY - slope * meanX;

    const xMin = Math.min(...pairs.map(p => p.x));
    const xMax = Math.max(...pairs.map(p => p.x));
    const trendX = [xMin, xMax];
    const trendY = trendX.map(x => slope * x + intercept);

    const hasColor = colorCol && pairs[0].c != null;
    const isNumericColor = hasColor && !Number.isNaN(Number(pairs[0].c));

    const traceMain = {
        x: pairs.map(p => p.x),
        y: pairs.map(p => p.y),
        mode: 'markers',
        type: 'scatter',
        name: `${xCol} vs ${yCol}`,
        marker: {
            size: 5,
            color: hasColor ? (isNumericColor ? pairs.map(p => Number(p.c)) : pairs.map(p => p.c)) : '#00e676',
            colorscale: 'Viridis',
            showscale: isNumericColor,
            line: { width: 0.5, color: '#0b0f19' },
        },
        hovertemplate: `${xCol}: %{x:.2f}<br>${yCol}: %{y:.2f}<extra></extra>`,
    };

    const traceTrend = {
        x: trendX,
        y: trendY,
        mode: 'lines',
        type: 'scatter',
        name: `Trend (r = ${rVal.toFixed(3)})`,
        line: { color: '#ff6b6b', width: 2, dash: 'dash' },
        hoverinfo: 'none',
    };

    document.getElementById('pair-stats').innerHTML =
        `n: <b class="text-gray-200">${n}</b> &middot; Pearson r: <b class="text-gray-200">${rVal.toFixed(4)}</b> &middot; r&sup2;: <b class="text-gray-200">${(rVal * rVal).toFixed(4)}</b>`;

    const fig = {
        data: [traceMain, traceTrend],
        layout: {
            title: `${xCol} vs ${yCol}`,
            template: 'plotly_dark',
            margin: { l: 40, r: 20, t: 40, b: 40 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            xaxis: { title: xCol },
            yaxis: { title: yCol },
            showlegend: true,
            legend: { x: 1, xanchor: 'right', y: 1, font: { size: 10 } },
        },
    };

    const gd = document.getElementById('pair-chart');
    if (gd.data && gd.data.length) Plotly.react(gd, fig.data, fig.layout, { responsive: true });
    else Plotly.newPlot(gd, fig.data, fig.layout, { responsive: true });
}

// ── Helpers ──

function populateSelect(id, options, selected) {
    const sel = document.getElementById(id);
    sel.innerHTML = '';
    options.forEach(o => {
        const opt = document.createElement('option');
        opt.value = o;
        opt.textContent = o;
        if (o === selected) opt.selected = true;
        sel.appendChild(opt);
    });
}
