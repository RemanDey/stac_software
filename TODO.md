# Role & Objective**Role:** Senior Full-Stack Developer & Data Engineer  **Task:** Build a modular, multi-page web dashboard using Flask and Plotly to visualize and analyze lunar X-ray fluorescence (XRF) or any user-provided planetary geochemical datasets.

---## Context
Planetary scientists use X-ray fluorescence (XRF) data to determine the elemental composition (e.g., Mg, Al, Si, Ca, Fe) of the Moon's surface to map its crustal history. Because different space missions and research groups use varying column naming conventions, this application must be dynamic—capable of accepting, parsing, and visualizing **any valid geochemical CSV file** provided by the user without crashing.

---## Project Structure & Modularity Constraints
To keep the project lightweight yet highly maintainable, follow a **flat directory structure**. However, the internal code within `app.py` must be highly modular. Isolate data ingestion, dynamic schema parsing, visualization logic, and route handling into clear, decoupled functions or classes so future developers can easily modify or extend the app.### Required Directory Layout:```text
lunar_xrf_dashboard/
│
├── app.py                 # Main application (Modular routes, data parsing, & plotting logic)
├── templates/
│   ├── base.html          # Global layout template (Navbar, footer, and common scripts/styles)
│   ├── index.html         # Page 1: Home page with file upload dropzone and mission overview
│   ├── dashboard.html     # Page 2: Interactive analysis dashboard with sidebar and charts
│   └── analysis.html      # Page 3: Scientific context and data interpretation guide
└── static/
    ├── css/style.css      # Space/Dark-mode theme custom styling
    └── js/dashboard.js    # Vanilla JS handling AJAX/Fetch requests for dynamic updatesTechnical Stack
Backend: Python 3.x, Flask
Frontend: HTML5, CSS3, Tailwind CSS (via CDN) for rapid responsive design, Vanilla JavaScript (Fetch API)
Data & Visualization: Pandas, Plotly (Python library rendering JSON to the frontend)
Core Features & Requirements
1. Multi-Page Architecture
Home Page (index.html): Features a stylized file dropzone for CSV uploads, basic mission documentation, and a "Use Sample Data" option.
Dashboard Page (dashboard.html): The primary data workspace holding the interactive sidebar controls and the rendering grids for the plots.
Analysis Page (analysis.html): A dedicated, clean reading layout explaining the science behind XRF ratios (e.g., Al/Si and Mg/Si ratios) used to distinguish between lunar maria and highlands.
2. Dynamic CSV Ingestion & Schema Mapping
The backend must dynamically read the uploaded CSV via Pandas and automatically detect:
Spatial Coordinates: Look for column patterns matching latitude/longitude (e.g., lat, latitude, lon, long, longitude - case-insensitive).
Elemental Columns: Extract all numeric columns representing elements or elemental ratios to populate UI options automatically.
Fallback State: If no file is uploaded yet, the app must automatically generate and use a default synthetic dataset so the user can explore the dashboard immediately.
3. Data Visualization (Minimum 2 Dynamic Plots via Plotly)
Plot 1 (Spatial Map): An interactive scatter plot mapping the detected spatial coordinates (Longitude vs. Latitude). Data points must color-code dynamically based on the element selected in the sidebar. Include rich hover tooltips showing coordinates and absolute values.
Plot 2 (Distribution/Correlation): A dynamic histogram showing the frequency distribution of the selected element, OR an interactive correlation heatmap matrix showing relationships between all detected elements.
Both charts must natively support Plotly features like panning, zooming, and responsive window resizing.
4. Interactive Filtering Sidebar (Dynamic AJAX Updates)
Implement a filtering system via JavaScript fetch(). When sidebar variables change, the plots must update instantly without a full page reload.
Dynamic Element Dropdown: Automatically populates with whatever numeric element columns were discovered in the uploaded CSV.
Auto-Adjusting Coordinate Sliders: Range sliders for Latitude and Longitude that dynamically set their minimum and maximum boundaries based on the actual range found in the current dataset.
5. UI/UX & Responsiveness
Apply a sleek, ultra-modern, dark-mode/space aesthetic (using deep slates, dark blues, and high-contrast glowing neon data indicators).
The application layout must use responsive CSS grids/flexbox to collapse gracefully into a single-column layout on mobile and tablet devices.
Deliverables
Complete Codebase: Provide the full, clean, and well-commented code for all files outlined in the layout.
Synthetic Data Generator: Build a utility function inside app.py that automatically creates and saves a sample_lunar_data.csv file on the first environment launch so the application runs completely out-of-the-box.
Setup Guide: Provide clear, straightforward instructions on how to install dependencies (pip install flask pandas plotly) and start the local development server.