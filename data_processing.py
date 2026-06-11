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
        'Al_wt_pct': np.random.exponential(12, n),
        'Si_wt_pct': np.random.normal(21, 2, n),
        'Mg_wt_pct': np.random.normal(6, 1.5, n),
        'Fe_wt_pct': np.random.normal(10, 4, n)
    })
    df['Fe_wt_pct'] = 25 - df['Al_wt_pct'] + np.random.normal(0, 2, n)
    df.to_csv(data_file, index=False)


def get_current_data(data_file: str = 'uploads/current_data.csv') -> pd.DataFrame:
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


def build_plot_payloads(
    df: pd.DataFrame,
    lat_col: str,
    lon_col: str,
    selected_element: str,
    elements: list,
    custom_graph: dict = None,
):
    """Build the dashboard plot payloads for the frontend."""
    payload = {}

    # Spatial distribution map
    if lat_col and lon_col and selected_element:
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
        payload['map_json'] = decode_plotly_bdata(json.loads(fig_map.to_json()))
    else:
        payload['map_json'] = None

    # Frequency histogram
    if selected_element:
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
        payload['hist_json'] = decode_plotly_bdata(json.loads(fig_hist.to_json()))
    else:
        payload['hist_json'] = None

    # Summary bar chart for all elements
    if elements:
        element_summaries = df[elements].median().sort_values(ascending=False)
        fig_summary = px.bar(
            x=element_summaries.index,
            y=element_summaries.values,
            title="Median Element Abundance",
            labels={'x': 'Element', 'y': 'Median Value'},
            template="plotly_dark",
            color=element_summaries.index,
            color_discrete_sequence=px.colors.qualitative.Dark24
        )
        fig_summary.update_layout(
            xaxis_tickangle=-45,
            margin=dict(l=20, r=20, t=40, b=80),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        payload['summary_json'] = decode_plotly_bdata(json.loads(fig_summary.to_json()))
    else:
        payload['summary_json'] = None

    # Longitude trend line plot
    if selected_element and lon_col:
        trend_df = df[[lon_col, selected_element]].dropna().sort_values(by=lon_col)
        fig_trend = px.line(
            trend_df,
            x=lon_col,
            y=selected_element,
            title=f"{selected_element} Trend Across Longitude",
            template="plotly_dark",
        )
        fig_trend.update_layout(
            margin=dict(l=20, r=20, t=40, b=40),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        payload['trend_json'] = decode_plotly_bdata(json.loads(fig_trend.to_json()))
    else:
        payload['trend_json'] = None

    # Custom graph support
    if custom_graph and isinstance(custom_graph, dict):
        graph_type = custom_graph.get('type')
        x_col = custom_graph.get('x')
        y_col = custom_graph.get('y')
        agg = custom_graph.get('agg')

        try:
            if graph_type == 'scatter' and x_col and y_col:
                fig_custom = px.scatter(
                    df,
                    x=x_col,
                    y=y_col,
                    color=selected_element if selected_element in df.columns else None,
                    title=f"Custom Scatter: {x_col} vs {y_col}",
                    template="plotly_dark",
                )
            elif graph_type == 'line' and x_col and y_col:
                fig_custom = px.line(
                    df.sort_values(by=x_col),
                    x=x_col,
                    y=y_col,
                    title=f"Custom Line: {x_col} vs {y_col}",
                    template="plotly_dark",
                )
            elif graph_type == 'bar' and x_col and y_col:
                df_bar = df[[x_col, y_col]].dropna()
                if agg in ['sum', 'mean', 'median']:
                    df_bar = df_bar.groupby(x_col)[y_col].agg(agg).reset_index()
                fig_custom = px.bar(
                    df_bar,
                    x=x_col,
                    y=y_col,
                    title=f"Custom Bar: {x_col} vs {y_col}",
                    template="plotly_dark",
                )
            else:
                fig_custom = px.scatter(
                    df,
                    x=lon_col if lon_col in df.columns else df.columns[0] if len(df.columns) else None,
                    y=lat_col if lat_col in df.columns else df.columns[1] if len(df.columns) > 1 else None,
                    title="Custom Graph Configuration Invalid",
                    template="plotly_dark",
                )

            if fig_custom is not None:
                fig_custom.update_layout(
                    margin=dict(l=20, r=20, t=40, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                payload['custom_json'] = decode_plotly_bdata(json.loads(fig_custom.to_json()))
            else:
                payload['custom_json'] = None
        except Exception:
            payload['custom_json'] = None
    else:
        payload['custom_json'] = None

    return payload
