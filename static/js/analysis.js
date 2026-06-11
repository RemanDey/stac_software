// static/js/analysis.js

document.addEventListener('DOMContentLoaded', () => {
    const refreshBtn = document.getElementById('refresh-analysis');
    refreshBtn.addEventListener('click', () => loadAnalysis(true));
    loadAnalysis();
});

function loadAnalysis(force = false) {
    fetch('/api/data')
        .then(response => response.json())
        .then(data => {
            renderAnalysisCards(data);
            renderSummaryTable(data);
            renderMeanChart(data);
            renderCorrelationHeatmap(data);
        })
        .catch(err => console.error('Error loading analysis data:', err));
}

function renderAnalysisCards(data) {
    const cards = document.getElementById('analysis-cards');
    cards.innerHTML = '';

    const numericColumns = data.numeric_columns || [];
    const rows = data.rows || [];
    const totals = {};
    const means = {};
    const medians = {};
    const variances = {};

    numericColumns.forEach(col => {
        const values = rows.map(r => Number(r[col])).filter(v => !Number.isNaN(v));
        totals[col] = values.reduce((sum, v) => sum + v, 0);
        means[col] = values.length ? totals[col] / values.length : 0;
        medians[col] = calculateMedian(values);
        variances[col] = values.length ? calculateVariance(values, means[col]) : 0;
    });

    const correlations = [];
    for (let i = 0; i < numericColumns.length; i += 1) {
        for (let j = i + 1; j < numericColumns.length; j += 1) {
            const colA = numericColumns[i];
            const colB = numericColumns[j];
            const pairs = rows
                .map(r => ({ x: Number(r[colA]), y: Number(r[colB]) }))
                .filter(pair => !Number.isNaN(pair.x) && !Number.isNaN(pair.y));
            if (!pairs.length) continue;
            const xVals = pairs.map(pair => pair.x);
            const yVals = pairs.map(pair => pair.y);
            correlations.push({
                pair: `${colA} / ${colB}`,
                value: calculateCorrelation(xVals, yVals),
            });
        }
    }
    const topCorrelation = correlations
        .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))[0];

    const cardsData = [
        { title: 'Total Records', value: rows.length },
        { title: 'Tracked Numeric Fields', value: numericColumns.length },
        { title: 'Highest Mean', value: formatNumeric(findBestColumn(means)) },
        { title: 'Highest Median', value: formatNumeric(findBestColumn(medians)) },
        { title: 'Top Correlated Pair', value: topCorrelation ? `${topCorrelation.pair}: ${topCorrelation.value.toFixed(2)}` : 'n/a' },
    ];

    cardsData.forEach(card => {
        cards.appendChild(createCard(card.title, card.value));
    });
}

function renderSummaryTable(data) {
    const tableContainer = document.getElementById('analysis-table');
    const numericColumns = data.numeric_columns || [];
    const rows = data.rows || [];

    const stats = numericColumns.map(col => {
        const values = rows.map(r => Number(r[col])).filter(v => !Number.isNaN(v));
        const mean = values.length ? values.reduce((sum, v) => sum + v, 0) / values.length : 0;
        return {
            column: col,
            count: values.length,
            mean: mean,
            median: calculateMedian(values),
            stdDev: Math.sqrt(calculateVariance(values, mean)),
            min: values.length ? Math.min(...values) : 0,
            max: values.length ? Math.max(...values) : 0,
        };
    });

    const rowsHtml = stats.map(stat => `
        <tr class="border-b border-gray-800 hover:bg-gray-800">
            <td class="px-4 py-3 text-sm text-gray-200">${stat.column}</td>
            <td class="px-4 py-3 text-sm text-gray-200">${stat.count}</td>
            <td class="px-4 py-3 text-sm text-gray-200">${stat.mean.toFixed(2)}</td>
            <td class="px-4 py-3 text-sm text-gray-200">${stat.median.toFixed(2)}</td>
            <td class="px-4 py-3 text-sm text-gray-200">${stat.stdDev.toFixed(2)}</td>
            <td class="px-4 py-3 text-sm text-gray-200">${stat.min.toFixed(2)}</td>
            <td class="px-4 py-3 text-sm text-gray-200">${stat.max.toFixed(2)}</td>
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
                    <th class="px-4 py-3">Min</th>
                    <th class="px-4 py-3">Max</th>
                </tr>
            </thead>
            <tbody>${rowsHtml}</tbody>
        </table>
    `;
}

function renderMeanChart(data) {
    const chartContainer = document.getElementById('analysis-chart');
    const numericColumns = data.numeric_columns || [];
    const rows = data.rows || [];
    const means = numericColumns.map(col => {
        const values = rows.map(r => Number(r[col])).filter(v => !Number.isNaN(v));
        return values.length ? values.reduce((sum, v) => sum + v, 0) / values.length : 0;
    });

    const fig = {
        data: [{
            x: numericColumns,
            y: means,
            type: 'bar',
            marker: { color: '#00e676' }
        }],
        layout: {
            title: 'Mean Abundance by Element',
            template: 'plotly_dark',
            margin: { l: 40, r: 20, t: 50, b: 80 },
            xaxis: { tickangle: -45 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)'
        }
    };

    if (chartContainer.data && chartContainer.data.length) {
        Plotly.react(chartContainer, fig.data, fig.layout, { responsive: true });
    } else {
        Plotly.newPlot(chartContainer, fig.data, fig.layout, { responsive: true });
    }
}

function renderCorrelationHeatmap(data) {
    const container = document.getElementById('analysis-heatmap');
    const numericColumns = data.numeric_columns || [];
    const rows = data.rows || [];
    const matrix = numericColumns.map(col => {
        return numericColumns.map(other => {
            const values = rows
                .map(r => ({ x: Number(r[col]), y: Number(r[other]) }))
                .filter(pair => !Number.isNaN(pair.x) && !Number.isNaN(pair.y));
            if (!values.length) return 0;
            const xVals = values.map(pair => pair.x);
            const yVals = values.map(pair => pair.y);
            return calculateCorrelation(xVals, yVals);
        });
    });

    const fig = {
        data: [{
            z: matrix,
            x: numericColumns,
            y: numericColumns,
            type: 'heatmap',
            colorscale: 'Viridis',
            zmin: -1,
            zmax: 1,
            hovertemplate: '%%{x} vs %%{y}: %%{z:.2f}<extra></extra>'
        }],
        layout: {
            title: 'Correlation Matrix',
            template: 'plotly_dark',
            margin: { l: 80, r: 20, t: 50, b: 80 },
            xaxis: { tickangle: -45 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)'
        }
    };

    if (container.data && container.data.length) {
        Plotly.react(container, fig.data, fig.layout, { responsive: true });
    } else {
        Plotly.newPlot(container, fig.data, fig.layout, { responsive: true });
    }
}

function calculateCorrelation(x, y) {
    if (!x.length || x.length !== y.length) return 0;
    const meanX = x.reduce((sum, v) => sum + v, 0) / x.length;
    const meanY = y.reduce((sum, v) => sum + v, 0) / y.length;
    const numerator = x.reduce((sum, v, idx) => sum + (v - meanX) * (y[idx] - meanY), 0);
    const denomX = Math.sqrt(x.reduce((sum, v) => sum + Math.pow(v - meanX, 2), 0));
    const denomY = Math.sqrt(y.reduce((sum, v) => sum + Math.pow(v - meanY, 2), 0));
    const denom = denomX * denomY;
    return denom ? numerator / denom : 0;
}

function calculateMedian(values) {
    if (!values.length) return 0;
    const sorted = values.slice().sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

function calculateVariance(values, mean) {
    if (!values.length) return 0;
    return values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
}

function createCard(title, value) {
    const wrapper = document.createElement('div');
    wrapper.className = 'bg-gray-900 p-5 rounded-xl border border-gray-800 shadow-sm';
    wrapper.innerHTML = `
        <div class="text-sm text-gray-400 mb-2">${title}</div>
        <div class="text-3xl font-bold text-white">${value}</div>
    `;
    return wrapper;
}

function findBestColumn(values) {
    const sorted = Object.entries(values).sort((a, b) => b[1] - a[1]);
    return sorted.length ? `${sorted[0][0]} (${sorted[0][1].toFixed(2)})` : 'n/a';
}

function formatNumeric(value) {
    return value || 'n/a';
}
