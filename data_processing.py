import base64
import json
import os

import numpy as np
import pandas as pd
import plotly.express as px


def generate_synthetic_data(data_file: str) -> None:
    """Create a synthetic lunar XRF dataset when no upload exists."""
    np.random.seed(42)
    n = 500
    df = pd.DataFrame({
        'Latitude': np.random.uniform(-30, 30, n),
        'Longitude': np.random.uniform(-60, 60, n),
        'Al_wt_pct': np.random.normal(12, 3, n),
        'Si_wt_pct': np.random.normal(21, 2, n),
        'Mg_wt_pct': np.random.normal(6, 1.5, n),
        'Fe_wt_pct': np.random.normal(10, 4, n)
    })
    df['Fe_wt_pct'] = 25 - df['Al_wt_pct'] + np.random.normal(0, 2, n)
    df.to_csv(data_file, index=False)


def get_current_data(data_file: str) -> pd.DataFrame:
    """Load the current dataset from disk, generating sample data if needed."""
    if not os.path.exists(data_file):
        generate_synthetic_data(data_file)
    return pd.read_csv(data_file)


def parse_schema(df: pd.DataFrame):
    """Detect latitude/longitude fields and available elemental columns."""
    cols = df.columns.tolist()

    lat_col = next((c for c in cols if c.lower() in ['lat', 'latitude']), None)
    lon_col = next((c for c in cols if c.lower() in ['lon', 'long', 'longitude']), None)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    elements = [c for c in numeric_cols if c not in [lat_col, lon_col]]

    return lat_col, lon_col, elements


def filter_by_bounds(df: pd.DataFrame, lat_col: str, lon_col: str, lat_range, lon_range) -> pd.DataFrame:
    """Apply the requested geographic bounding box to the dataset."""
    if lat_col and lon_col and lat_range and lon_range:
        return df[
            (df[lat_col] >= float(lat_range[0])) & (df[lat_col] <= float(lat_range[1])) &
            (df[lon_col] >= float(lon_range[0])) & (df[lon_col] <= float(lon_range[1]))
        ]
    return df


def decode_plotly_bdata(obj):
    """Convert Plotly typed-array objects (dtype/bdata) into plain Python lists."""
    if isinstance(obj, dict):
        if set(obj.keys()) == {'dtype', 'bdata'} and isinstance(obj['dtype'], str) and isinstance(obj['bdata'], str):
            try:
                raw = base64.b64decode(obj['bdata'])
                arr = np.frombuffer(raw, dtype=np.dtype(obj['dtype']))
                return arr.tolist()
            except Exception:
                return obj
        return {k: decode_plotly_bdata(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decode_plotly_bdata(v) for v in obj]
    return obj


def build_plot_payload(df: pd.DataFrame, lat_col: str, lon_col: str, selected_element: str):
    """Build the map and histogram payloads for the dashboard frontend."""
    fig_map = px.scatter(
        df,
        x=lon_col,
        y=lat_col,
        color=selected_element,
        title=f"Spatial Distribution of {selected_element}",
        color_continuous_scale="Viridis",
        template="plotly_dark",
        hover_data=[lat_col, lon_col, selected_element]
    )
    fig_map.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    fig_hist = px.histogram(
        df,
        x=selected_element,
        nbins=30,
        title=f"Frequency Distribution of {selected_element}",
        template="plotly_dark",
        color_discrete_sequence=['#00e676']
    )
    fig_hist.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    map_json = decode_plotly_bdata(json.loads(fig_map.to_json()))
    hist_json = decode_plotly_bdata(json.loads(fig_hist.to_json()))

    return map_json, hist_json
