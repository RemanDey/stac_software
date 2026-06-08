# ◈ CLASS XRF Lunar Telemetry Workstation

**Chandrayaan-2 · Large Area Soft X-ray Spectrometer (CLASS) · Simulation v2.1**

A production-grade telemetry analysis workstation for visualising and filtering
Lunar X-ray Fluorescence (XRF) data, inspired by ISRO's CLASS payload aboard
Chandrayaan-2.

---

## Architecture

```
lunar_xrf_dashboard/
├── app.py                  ← Flask backend (data generation, REST API)
├── requirements.txt        ← Python dependencies
├── README.md               ← This file
└── templates/
    └── index.html          ← Full single-page workstation (Tailwind + Plotly.js)
```

### Separation of Concerns

| Layer | Technology | Responsibility |
|-------|-----------|---------------|
| **Backend** | Python 3 + Flask | Procedural data generation, pandas DataFrame slicing, server-side statistics, REST JSON API |
| **Data core** | NumPy + pandas | In-memory matrix operations, spatial query filtering |
| **Frontend UI** | HTML5 + Tailwind CSS (CDN) | Immersive space-tech dashboard, responsive grid layout |
| **Visualisation** | Plotly.js (CDN, WebGL) | 2D scatter map, flux analysis chart, 3D globe projection |

---

## Local Deployment

### Prerequisites

- Python 3.9 or higher
- pip

### Steps

```bash
# 1 — Clone / unzip the project
cd lunar_xrf_dashboard

# 2 — (Optional but recommended) Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3 — Install dependencies
pip install -r requirements.txt

# 4 — Run the Flask development server
python app.py
```

Navigate to **http://127.0.0.1:5000** in your browser.

---

## REST API Reference

### `GET /api/data`

Returns a filtered telemetry slice with server-side statistics.

**Query parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_lat` | float | -90 | Minimum latitude bound |
| `max_lat` | float | +90 | Maximum latitude bound |
| `min_lon` | float | -180 | Minimum longitude bound |
| `max_lon` | float | +180 | Maximum longitude bound |
| `orbits`  | string | all | Comma-separated orbit numbers (e.g. `101,103,107`) |

**Response schema**

```json
{
  "stats": {
    "sample_count": 312,
    "mean_solar_flux": 3.7421,
    "peak_cps": 498,
    "dominant_element": "Si"
  },
  "records": [
    {
      "timestamp": "2019-09-06T00:00:00",
      "orbit_number": 101,
      "latitude": -12.3456,
      "longitude": 47.8901,
      "solar_flux": 3.9102,
      "counts_per_second": 257,
      "mg_pct": 8.412,
      "al_pct": 11.234,
      "si_pct": 21.567,
      "fe_pct": 14.088
    }
  ]
}
```

### `GET /api/orbits`

Returns the list of available orbit numbers.

### `GET /api/export`

Returns the filtered slice as a downloadable `lunar_xrf_export.csv`.
Accepts the same query parameters as `/api/data`.

---

## Data Model & Scientific Rules

The backend procedurally generates **700 observation vectors** at startup:

| Field | Description |
|-------|-------------|
| `timestamp` | ISO 8601 string, spaced 2.5 min apart from 2019-09-06T00:00:00 |
| `orbit_number` | Orbits 101–115 (15 passes, ~47 records each) |
| `latitude` | –90° to +90°, sinusoidal ground-track + Gaussian noise |
| `longitude` | –180° to +180°, monotonically drifting across all passes |
| `solar_flux` | 0.5–6.5 W m⁻², composite sinusoidal solar-cycle model |
| `counts_per_second` | Proportional to `solar_flux` × 45 + 80 + noise |
| `mg_pct` | Magnesium wt%: peaks near equator (volcanic basalt) |
| `al_pct` | Aluminum wt%: peaks at poles (anorthosite crust) |
| `si_pct` | Silicon wt%: elevated at high latitudes |
| `fe_pct` | Iron wt%: peaks near equator (Mare volcanic plains) |

### Geochemical Rules Encoded

```
|lat| < 30° → elevated Fe (12–22%) and Mg (7–14%)   # Mare basalt plains
|lat| > 45° → elevated Al (15–20%) and Si (22–28%)   # Highland anorthosite
```

---

## Frontend Features

### Control Sidebar
- **Element selector** — periodic-table shortcut buttons + dropdown
- **Spatial bounding sliders** — lat/lon range with live value labels
- **Orbit checkboxes** — ALL / NONE shortcuts + individual orbit selection
- **Science Briefing** — collapsible educational panel on XRF physics

### Metric Cards
Four live-updating KPI tiles: Sample Count, Mean Solar Flux, Peak CPS, Dominant Element

### Visualisations (Plotly.js)

1. **2D Spatial Distribution** — Longitude × Latitude scatter map; marker size = CPS, colour = selected element % via Viridis scale
2. **Spectral Flux Analysis** — Solar Flux vs CPS correlation scatter (Electric colorscale)
3. **3D Orbital Globe** — Lat/lon projected to spherical coordinates (R=1) with a low-resolution wireframe lunar mesh; full 3D rotation & zoom

### Data Export
**↓ EXPORT CSV** button downloads the current filtered slice as `lunar_xrf_export_<timestamp>.csv` directly from the browser without an extra server round-trip.

---

## UI Design

- **Palette**: deep `slate-950` / `zinc-900` backgrounds, `cyan-400` accents, `emerald`, `amber`, `rose` data ramps
- **Typography**: Orbitron (display / headers) + IBM Plex Mono (data / body)
- **Effects**: star-field radial-gradient background, scanline overlay, glowing sidebar headings
- **Responsiveness**: `grid-cols-1 lg:grid-cols-4` — sidebar collapses above the charts on mobile screens

---

## Performance Notes

- All fetch calls are debounced (160 ms) to prevent API flooding during slider drag
- `Plotly.react()` is used for all updates (efficient diff-based redraw, no full remount)
- The 700-record DataFrame is held entirely in memory — no database I/O per request
- WebGL-accelerated scatter rendering via Plotly's `scattergl` path (auto-selected on large datasets)

---

## License

MIT — free to use, modify, and distribute.
