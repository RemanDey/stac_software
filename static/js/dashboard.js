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

    // 2. Attach Event Listener to Filter Button
    document.getElementById('apply-filters').addEventListener('click', fetchPlots);
});

function populateUI(schema) {
    const elementSelect = document.getElementById('element-select');
    
    // Populate Elements Dropdown
    schema.elements.forEach(el => {
        let option = document.createElement('option');
        option.value = el;
        option.textContent = el;
        elementSelect.appendChild(option);
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

function fetchPlots() {
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
    })
    .catch(err => console.error('Error fetching plots:', err));
}