import base64
import json
import os

import numpy as np
import pandas as pd
import plotly.express as px


def generate_synthetic_data(data_file: str) -> None:
    """Create a synthetic lunar XRF dataset when no upload exists."""
    np.random.seed(42)
    n = 2000

    rock_types = ['Basalt', 'Anorthosite', 'Gabbro', 'Norite', 'Troctolite', 'Regolith']
    rock_weights = [0.35, 0.25, 0.15, 0.10, 0.08, 0.07]
    regions = ['Mare Tranquillitatis', 'Mare Imbrium', 'Mare Serenitatis',
               'Highlands', 'South Pole-Aitken', 'Oceanus Procellarum']

    rock = np.random.choice(rock_types, n, p=rock_weights)
    region_idx = np.random.choice(len(regions), n)

    lat = np.random.uniform(-30, 30, n)
    lon = np.random.uniform(-60, 60, n)

    al = np.where(rock == 'Anorthosite',
                  np.random.normal(18, 2, n),
                  np.random.exponential(10, n))
    al = np.clip(al, 2, 28)
    si = np.random.normal(21, 3, n)
    si = np.clip(si, 10, 35)
    mg = np.where(rock == 'Basalt',
                  np.random.normal(8, 2, n),
                  np.random.exponential(4, n))
    mg = np.clip(mg, 0.5, 18)
    fe = 28 - al * 0.85 + np.random.normal(0, 1.5, n)
    fe = np.clip(fe, 2, 30)
    ca = np.where(rock == 'Anorthosite',
                  np.random.normal(14, 2, n),
                  np.random.exponential(7, n))
    ca = np.clip(ca, 1, 20)
    na = np.random.normal(3, 1.2, n)
    na = np.clip(na, 0.1, 8)
    k = np.where(rock == 'Regolith',
                 np.random.normal(0.8, 0.4, n),
                 np.random.exponential(0.3, n))
    k = np.clip(k, 0.01, 3)
    ti = 0.5 + fe * 0.04 + np.random.normal(0, 0.3, n)
    ti = np.clip(ti, 0.05, 5)
    mn = 0.05 + fe * 0.008 + np.random.normal(0, 0.05, n)
    mn = np.clip(mn, 0.01, 1)
    p = np.random.exponential(0.2, n)
    p = np.clip(p, 0.01, 1.5)
    cr = np.where(rock == 'Basalt',
                  np.random.normal(0.3, 0.15, n),
                  np.random.exponential(0.1, n))
    cr = np.clip(cr, 0.005, 1)
    ni = cr * 0.3 + np.random.normal(0, 0.02, n)
    ni = np.clip(ni, 0.001, 0.5)

    df = pd.DataFrame({
        'Latitude': lat,
        'Longitude': lon,
        'Elevation_m': np.random.normal(0, 500, n),
        'Rock_Type': rock,
        'Region': [regions[i] for i in region_idx],
        'Al_wt_pct': np.round(al, 3),
        'Si_wt_pct': np.round(si, 3),
        'Mg_wt_pct': np.round(mg, 3),
        'Fe_wt_pct': np.round(fe, 3),
        'Ca_wt_pct': np.round(ca, 3),
        'Na_wt_pct': np.round(na, 3),
        'K_wt_pct': np.round(k, 3),
        'Ti_wt_pct': np.round(ti, 3),
        'Mn_wt_pct': np.round(mn, 3),
        'P_wt_pct': np.round(p, 3),
        'Cr_wt_pct': np.round(cr, 3),
        'Ni_wt_pct': np.round(ni, 3),
    })

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

    non_element_patterns = ['elevation', 'depth', 'index', 'id', 'sample']
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    elements = [
        c for c in numeric_cols
        if c not in [lat_col, lon_col]
        and not any(p in c.lower() for p in non_element_patterns)
    ]

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
        if isinstance(obj.get('bdata'), str) and isinstance(obj.get('dtype'), str):
            try:
                raw = base64.b64decode(obj['bdata'])
                arr = np.frombuffer(raw, dtype=np.dtype(obj['dtype']))
                if 'shape' in obj:
                    try:
                        shape = tuple(int(s) for s in obj['shape'].split(','))
                        arr = arr.reshape(shape)
                    except Exception:
                        pass
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


def build_analysis_payload(df, selected_element=None, elements=None):
    """Compute statistics and Plotly charts server-side for the analysis page."""
    if elements is None:
        _, _, elements = parse_schema(df)

    if not selected_element and elements:
        selected_element = elements[0]

    summary = []
    for col in elements:
        values = df[col].dropna()
        if len(values) == 0:
            continue
        s = {
            'column': col,
            'count': int(len(values)),
            'mean': _safe_float(values.mean()),
            'median': _safe_float(values.median()),
            'std_dev': _safe_float(values.std()),
            'variance': _safe_float(values.var()),
            'min': _safe_float(values.min()),
            'max': _safe_float(values.max()),
            'skewness': _safe_float(values.skew()),
            'kurtosis': _safe_float(values.kurtosis()),
            'q1': _safe_float(values.quantile(0.25)),
            'q3': _safe_float(values.quantile(0.75)),
        }
        summary.append(s)

    total_records = len(df)
    numeric_fields = len(elements)

    means = {s['column']: s['mean'] for s in summary}
    medians = {s['column']: s['median'] for s in summary}
    highest_mean_col = max(means, key=means.get) if means else None
    highest_median_col = max(medians, key=medians.get) if medians else None

    highest_mean = {
        'column': highest_mean_col,
        'value': _safe_float(round(means[highest_mean_col], 2)),
    } if highest_mean_col else None
    highest_median = {
        'column': highest_median_col,
        'value': _safe_float(round(medians[highest_median_col], 2)),
    } if highest_median_col else None

    corr_matrix = df[elements].corr()

    top_corr = None
    if len(elements) >= 2:
        corr_pairs = []
        for i in range(len(elements)):
            for j in range(i + 1, len(elements)):
                val = corr_matrix.iloc[i, j]
                corr_pairs.append((elements[i], elements[j], abs(val), val))
        corr_pairs.sort(key=lambda x: x[2], reverse=True)
        if corr_pairs:
            top_corr = {
                'pair': f"{corr_pairs[0][0]} / {corr_pairs[0][1]}",
                'value': _safe_float(round(corr_pairs[0][3], 2)),
            }

    stats = {
        'total_records': total_records,
        'numeric_fields': numeric_fields,
        'summary': summary,
        'highest_mean': highest_mean,
        'highest_median': highest_median,
        'top_correlation': top_corr,
    }

    payload = {}

    mean_values = df[elements].mean().sort_values(ascending=False)
    fig_mean = px.bar(
        x=mean_values.index,
        y=mean_values.values,
        title="Mean Abundance Across Elements",
        labels={'x': 'Element', 'y': 'Mean Value'},
        template="plotly_dark",
        color=mean_values.index,
        color_discrete_sequence=px.colors.qualitative.Dark24,
    )
    fig_mean.update_layout(
        xaxis_tickangle=-45,
        margin=dict(l=20, r=20, t=40, b=80),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
    )
    payload['mean_chart'] = decode_plotly_bdata(json.loads(fig_mean.to_json()))

    fig_heatmap = px.imshow(
        corr_matrix,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        title="Correlation Matrix Heatmap",
        color_continuous_scale="Viridis",
        zmin=-1, zmax=1,
        template="plotly_dark",
        aspect="auto",
    )
    fig_heatmap.update_layout(
        margin=dict(l=80, r=20, t=40, b=80),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    fig_heatmap.update_traces(
        hovertemplate='%{x} vs %{y}: %{z:.2f}<extra></extra>'
    )
    payload['correlation_heatmap'] = decode_plotly_bdata(
        json.loads(fig_heatmap.to_json())
    )

    if selected_element:
        fig_hist = px.histogram(
            df,
            x=selected_element,
            nbins=30,
            title=f"Distribution of {selected_element}",
            template="plotly_dark",
            color_discrete_sequence=['#00e676'],
        )
        fig_hist.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
        payload['histogram'] = decode_plotly_bdata(json.loads(fig_hist.to_json()))

    fig_box = px.box(
        df,
        y=elements,
        title="Element Value Distributions",
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Dark24,
    )
    fig_box.update_layout(
        margin=dict(l=20, r=20, t=40, b=80),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis_title="Value",
    )
    payload['box_plot'] = decode_plotly_bdata(json.loads(fig_box.to_json()))

    payload['correlation_data'] = {
        'columns': list(corr_matrix.columns),
        'data': corr_matrix.values.tolist(),
    }

    return {'stats': stats, 'plots': payload}


def _safe_float(val):
    """Convert a numpy or pandas scalar to plain float, handling NaN."""
    if pd.isna(val):
        return 0.0
    return float(val)
