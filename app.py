# app.py
import os
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
from werkzeug.utils import secure_filename

from data_processing import (
    build_plot_payloads,
    filter_by_bounds,
    generate_synthetic_data,
    get_current_data,
    parse_schema,
)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 512 * 1024 * 1024  # 512 MB max

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
DATA_FILE = os.path.join(app.config['UPLOAD_FOLDER'], 'current_data.csv')

# --- FLASK ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename != '':
        filename = secure_filename(file.filename)
        file.save(DATA_FILE)
    return redirect(url_for('dashboard'))

@app.route('/use_sample', methods=['POST'])
def use_sample():
    generate_synthetic_data(DATA_FILE)
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

@app.route('/api/data', methods=['GET'])
def api_data():
    """Return the current dataset as JSON for client-side analysis."""
    df = get_current_data(DATA_FILE)
    _, _, elements = parse_schema(df)
    return jsonify({
        'columns': df.columns.tolist(),
        'numeric_columns': elements,
        'rows': df.to_dict(orient='records'),
    })

# --- API ENDPOINTS FOR AJAX ---

@app.route('/api/schema', methods=['GET'])
def api_schema():
    """Returns dataset schema and bounds to initialize the frontend."""
    df = get_current_data()
    lat_col, lon_col, elements = parse_schema(df)
    
    bounds = {}
    if lat_col and lon_col:
        bounds = {
            'lat_min': float(df[lat_col].min()), 'lat_max': float(df[lat_col].max()),
            'lon_min': float(df[lon_col].min()), 'lon_max': float(df[lon_col].max())
        }
        
    return jsonify({
        'lat_col': lat_col,
        'lon_col': lon_col,
        'elements': elements,
        'bounds': bounds
    })

@app.route('/api/plots', methods=['POST'])
def api_plots():
    """Generate Plotly payloads for the frontend based on current filters."""
    data = request.get_json(silent=True) or {}
    selected_element = data.get('element')
    lat_range = data.get('lat_range')
    lon_range = data.get('lon_range')
    custom_graph = data.get('custom_graph')

    df = get_current_data(DATA_FILE)
    lat_col, lon_col, elements = parse_schema(df)

    if not selected_element:
        selected_element = elements[0] if elements else None

    filtered_df = filter_by_bounds(df, lat_col, lon_col, lat_range, lon_range)
    plot_payloads = build_plot_payloads(
        filtered_df,
        lat_col,
        lon_col,
        selected_element,
        elements,
        custom_graph=custom_graph,
    )

    return jsonify(plot_payloads)

if __name__ == '__main__':
    app.run(debug=True)