// static/js/dashboard.js

document.addEventListener("DOMContentLoaded", () => {
    // 1. Initialize schema and boundaries
    fetch('/api/schema')
        .then(response => response.json())
        .then(schema => {
            populateUI(schema);
            fetchPlots(); // Load initial plots
        })
        .catch(err => console.error("Error loading schema:", err));

    // 2. Attach Event Listeners
    document.getElementById('apply-filters').addEventListener('click', event => {
        event.preventDefault();
        fetchPlots();
    });
    document.getElementById('apply-custom').addEventListener('click', event => {
        event.preventDefault();
        fetchPlots(true);
    });
});

function populateUI(schema) {
    const elementSelect = document.getElementById('element-select');
    const xSelect = document.getElementById('custom-x');
    const ySelect = document.getElementById('custom-y');
    
    // Populate Elements Dropdown
    schema.elements.forEach(el => {
        const option = document.createElement('option');
        option.value = el;
        option.textContent = el;
        elementSelect.appendChild(option);

        const xOption = document.createElement('option');
        xOption.value = el;
        xOption.textContent = el;
        xSelect.appendChild(xOption);

        const yOption = document.createElement('option');
        yOption.value = el;
        yOption.textContent = el;
        ySelect.appendChild(yOption);
    });

    // Populate Bounds
    if (schema.bounds) {
        document.getElementById('lat-min').value = Math.floor(schema.bounds.lat_min);
        document.getElementById('lat-max').value = Math.ceil(schema.bounds.lat_max);
        document.getElementById('lon-min').value = Math.floor(schema.bounds.lon_min);
        document.getElementById('lon-max').value = Math.ceil(schema.bounds.lon_max);
    }
}

function renderPlot(containerId, fig) {
    if (!fig) {
        return;
    }

    const gd = document.getElementById(containerId);
    if (!gd) {
        console.error(`Plot container not found: ${containerId}`);
        return;
    }

    if (gd.data && gd.data.length) {
        Plotly.react(containerId, fig.data, fig.layout, {responsive: true});
    } else {
        Plotly.newPlot(containerId, fig.data, fig.layout, {responsive: true});
    }
}

function fetchPlots(isCustom = false) {
    const payload = {
        element: document.getElementById('element-select').value,
        lat_range: [
            document.getElementById('lat-min').value,
            document.getElementById('lat-max').value
        ],
        lon_range: [
            document.getElementById('lon-min').value,
            document.getElementById('lon-max').value
        ]
    };

    if (isCustom) {
        payload.custom_graph = {
            type: document.getElementById('custom-graph-type').value,
            x: document.getElementById('custom-x').value,
            y: document.getElementById('custom-y').value,
            agg: document.getElementById('custom-agg').value,
        };
    }

    fetch('/api/plots', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`Plot API ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('Plot payload:', data);
        renderPlot('map-plot', data.map_json);
        renderPlot('hist-plot', data.hist_json);
        renderPlot('summary-plot', data.summary_json);
        renderPlot('trend-plot', data.trend_json);
        renderPlot('mean-chart', data.mean_chart);
        renderPlot('box-plot', data.box_plot);
        renderPlot('correlation-heatmap', data.correlation_heatmap);
        renderPlot('distribution-histogram', data.distribution_histogram);
        renderPlot('custom-plot', data.custom_json);

        const prompt = document.getElementById('custom-plot-prompt');
        if (prompt) {
            prompt.style.display = data.custom_json ? 'none' : 'flex';
        }
    })
    .catch(err => console.error('Error fetching plots:', err));
}