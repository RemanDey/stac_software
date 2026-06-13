# Lunar XRF Dashboard

A Flask-based geochemical data analysis workstation for visualising and analysing Lunar X-ray Fluorescence (XRF) data. Features a dark-themed interactive dashboard and analysis suite with server-side statistical computation.

---

## Architecture

```
stac_software/
├── app.py                  ← Flask routes, API endpoints, upload handling
├── data_processing.py      ← Data ingestion, schema parsing, Plotly figure generation, analysis engine
├── requirements.txt        ← Python dependencies
├── README.md               ← Project documentation
├── uploads/                ← Uploaded or generated CSV datasets
├── static/
│   ├── css/style.css       ← Dark-theme glass-morphism styles
│   └── js/
│       ├── dashboard.js    ← Dashboard: schema fetch, plot rendering, filter controls
│       └── analysis.js     ← Analysis: stat rendering, Data Browser, Distribution Explorer, Pair Correlation (all client-side)
└── templates/
    ├── base.html           ← Layout, nav bar, CDN links (Tailwind, Plotly, Font Awesome)
    ├── index.html          ← Home page with CSV upload / sample data
    ├── dashboard.html      ← Interactive dashboard with maps and plots
    ├── analysis.html       ← Statistical analysis with summary table and charts
    └── about.html          ← About the project and creator
```

### Separation of Concerns

| Layer | File | Responsibility |
|-------|------|----------------|
| **Routes** | `app.py` | Page rendering, CSV upload, sample data generation, JSON API endpoints |
| **Data core** | `data_processing.py` | Data loading, synthetic generation, schema inference, Plotly payload building, typed-array decoding |
| **Dashboard UI** | `static/js/dashboard.js` | Fetch schema and plot payloads, render Plotly charts, handle filter controls |
| **Analysis UI** | `static/js/analysis.js` | Fetch analysis stats + raw data, render KPI cards, summary table, Data Browser, Distribution Explorer, Pair Correlation scatter |
| **Templates** | `templates/*.html` | Page layout and script/style injection |

---

## Local Deployment

### Prerequisites

- Python 3.9 or higher
- pip

### Steps

```bash
cd /home/remandey/my-programs/stac/stac_software
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

---

## Pages

| Route | Description |
|-------|-------------|
| `/` | Home — upload a CSV or generate synthetic sample data |
| `/dashboard` | Interactive dashboard — spatial map, histograms, trend lines, custom graphs |
| `/analysis` | Statistical analysis — KPI cards, summary table, Data Browser, Distribution Explorer, Element Pair Correlation scatter |
| `/about` | Project documentation and creator info |

---

## REST API Reference

### `GET /api/schema`

Returns dataset schema (lat/lon columns, element lists, coordinate bounds).

### `POST /api/plots`

Generates Plotly chart payloads based on current filters.

**Request body:**

```json
{
  "element": "Fe_wt_pct",
  "lat_range": ["-30", "30"],
  "lon_range": ["-60", "60"],
  "custom_graph": {
    "type": "scatter",
    "x": "Al_wt_pct",
    "y": "Fe_wt_pct",
    "agg": "mean"
  }
}
```

**Response:** `{ "map_json": {...}, "hist_json": {...}, "summary_json": {...}, "trend_json": {...}, "mean_chart": {...}, "box_plot": {...}, "correlation_heatmap": {...}, "distribution_histogram": {...}, "custom_json": {...} }`

### `POST /api/analysis`

Computes statistical summaries and generates analysis chart payloads server-side.

**Request body:**

```json
{
  "element": "Fe_wt_pct"
}
```

**Response:**

```json
{
  "stats": {
    "total_records": 2000,
    "numeric_fields": 12,
    "summary": [
      {
        "column": "Fe_wt_pct",
        "count": 2000,
        "mean": 12.43,
        "median": 12.18,
        "std_dev": 5.21,
        "variance": 27.14,
        "min": 2.0,
        "max": 27.5,
        "skewness": 0.34,
        "kurtosis": -0.67,
        "q1": 8.15,
        "q3": 16.72
      }
    ],
    "highest_mean": { "column": "Si_wt_pct", "value": 20.97 },
    "highest_median": { "column": "Si_wt_pct", "value": 21.04 },
    "top_correlation": { "pair": "Al_wt_pct / Fe_wt_pct", "value": -0.98 }
  },
  "plots": {
    "mean_chart": {...},
    "correlation_heatmap": {...},
    "histogram": {...},
    "box_plot": {...},
    "correlation_data": {...}
  }
}
```

### `GET /api/data`

Returns the full dataset as JSON (used by the original client-side analysis).

---

## Data Generation

When no CSV is uploaded, the app generates a synthetic lunar XRF dataset with **2,000 samples** and **12 geochemical elements**:

| Element | Distribution | Notes |
|---------|-------------|-------|
| Al_wt_pct | Normal (anorthosite), Exponential (others) | High in anorthosite crust |
| Si_wt_pct | Normal ~21% | Consistent across rock types |
| Mg_wt_pct | Normal (basalt), Exponential (others) | Elevated in mare basalts |
| Fe_wt_pct | Anti-correlated with Al | Plagioclase effect |
| Ca_wt_pct | Normal (anorthosite), Exponential (others) | High in anorthosite |
| Na_wt_pct | Normal ~3% | Moderate variation |
| K_wt_pct | Normal (regolith), Exponential (others) | Enriched in regolith |
| Ti_wt_pct | Correlated with Fe | Mafic mineral association |
| Mn_wt_pct | Correlated with Fe | Trace in mafic minerals |
| P_wt_pct | Exponential ~0.2% | Trace element |
| Cr_wt_pct | Normal (basalt), Exponential (others) | Compatible in basalt |
| Ni_wt_pct | Correlated with Cr | Compatible element pairing |

Additional columns: `Latitude`, `Longitude`, `Elevation_m`, `Rock_Type` (Basalt, Anorthosite, Gabbro, Norite, Troctolite, Regolith), `Region`.

Geochemical rules are encoded via rock-type-dependent distributions and intentional element correlations.

---

## Frontend Features

### Dashboard
- **Spatial Distribution Map** — scatter plot coloured by selected element
- **Frequency Histogram** — distribution of the selected element
- **Median Abundance Bar Chart** — median values across all elements
- **Longitude Trend Line** — element variation across longitude
- **Mean Abundance Bar Chart** — mean values across all elements
- **Correlation Matrix Heatmap** — pair-wise Pearson correlation
- **Element Value Distributions** — box plot showing all element ranges
- **Element Distribution Histogram** — distribution of the selected element
- **Custom Graph** — user-configured scatter, line, or bar chart
- **Bounding-box filter** — lat/lon range sliders

### Analysis
- **KPI Cards** — total records, numeric fields, highest mean/median, top correlated pair
- **Summary Statistics Table** — count, mean, median, std dev, variance, min, max, skewness, kurtosis per element
- **Data Browser** — paginated, searchable, sortable table of raw data rows (client-side)
- **Distribution Explorer** — interactive histogram with adjustable bins, mean/median/std overlay lines (client-side)
- **Element Pair Correlation** — scatter plot with trend line and Pearson coefficient, optional categorical coloring (client-side)

---

## Design Decisions

- **Hybrid server/client architecture** — heavy statistical computations (summary stats, correlations, Plotly chart payloads) are computed server-side in Pandas for performance. Interactive exploratory tools (Data Browser, Distribution Explorer, Pair Correlation scatter) run client-side on the fetched raw data for instant responsiveness without server round-trips.
- **Plotly JSON payloads** — figures are built server-side with Plotly Express, serialised to JSON, decoded from typed arrays, and rendered with `Plotly.react()` for smooth updates and full interactivity.
- **Dark glass-morphism theme** — translucent panels, radial gradient background, neon green accents. Tailwind CSS handles responsive layout; a small custom CSS file adds backdrop blur and scrollbar styling.

---

## UI Design

- **Palette**: `#0b0f19` (space) backgrounds, `#151b2b` (panel) cards, `#00e676` (neon) accents
- **Effects**: glass-panel backdrop blur, orbital background gradient, neon text glow
- **Responsiveness**: `max-w-6xl` content width, 2-column grid layouts on large screens, single column on mobile

---

## Performance Notes

- All API endpoints return JSON only — no server-side HTML rendering for interactive content
- `Plotly.react()` is used for all chart updates (efficient diff-based redraw)
- `decode_plotly_bdata()` converts Plotly typed arrays to plain Python lists for clean JSON serialisation
- The 2,000-record DataFrame is held in memory — no database I/O per request

---

## License

MIT — free to use, modify, and distribute.
