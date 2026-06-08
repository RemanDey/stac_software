"""
Lunar XRF Telemetry Dashboard — Flask Backend
Inspired by ISRO CLASS (Chandrayaan-2 Large Area Soft X-ray Spectrometer)
"""

import json
import io
import math
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, render_template, make_response

app = Flask(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# 1.  PROCEDURAL DATA GENERATION
# ──────────────────────────────────────────────────────────────────────────────

def generate_telemetry(n: int = 700, seed: int = 42) -> pd.DataFrame:
    """
    Procedurally generates a realistic Lunar XRF observation dataset.

    Scientific rules encoded:
      • Mare plains (|lat| < 30°) → higher Fe + Mg (volcanic basalt)
      • Highlands   (|lat| > 45°) → higher Al + Si (anorthosite crust)
      • CPS scales linearly with solar_flux + Gaussian noise
      • solar_flux follows a smooth sinusoidal cycle across orbit passes
    """
    rng = np.random.default_rng(seed)

    # ── Timestamps ────────────────────────────────────────────────────────────
    t0 = datetime(2019, 9, 6, 0, 0, 0)
    timestamps = [t0 + timedelta(minutes=int(i * 2.5)) for i in range(n)]

    # ── Orbital geometry ──────────────────────────────────────────────────────
    orbit_numbers = np.repeat(np.arange(101, 116), math.ceil(n / 15))[:n]

    # Ground-track: latitude oscillates ±85° as spacecraft passes over poles
    phase_offset = rng.uniform(0, 2 * math.pi, 15)
    lat_raw = np.concatenate([
        85 * np.sin(np.linspace(phase_offset[o], phase_offset[o] + 2 * math.pi,
                                math.ceil(n / 15)))
        for o in range(15)
    ])[:n]
    latitude = np.clip(lat_raw + rng.normal(0, 1.5, n), -90, 90)

    # Longitude drifts monotonically as Moon rotates under the spacecraft
    longitude = ((np.linspace(-180, 180, n) + rng.normal(0, 2, n)) % 360) - 180

    # ── Solar flux (W m⁻²) ────────────────────────────────────────────────────
    solar_flux = (
        3.5
        + 1.2 * np.sin(np.linspace(0, 6 * math.pi, n))          # solar cycle
        + 0.4 * np.cos(np.linspace(0, 14 * math.pi, n))          # flare envelope
        + rng.normal(0, 0.15, n)                                  # measurement noise
    ).clip(0.5, 6.5)

    # ── Counts per second (proportional to solar_flux) ────────────────────────
    cps_base = 80 + 45 * solar_flux
    counts_per_second = (cps_base + rng.normal(0, 12, n)).clip(10, 550).astype(int)

    # ── Elemental abundances (weight %) — must sum ≈ 100 with other oxides ────
    abs_lat = np.abs(latitude)

    # Mare signature: high Fe/Mg at equatorial band
    fe_base = 12 + 8 * np.exp(-abs_lat / 20) + rng.normal(0, 1.2, n)
    mg_base = 7  + 5 * np.exp(-abs_lat / 25) + rng.normal(0, 0.8, n)

    # Highland signature: high Al/Si at high latitudes
    al_base = 8  + 10 * (abs_lat / 90) ** 1.4 + rng.normal(0, 1.0, n)
    si_base = 18 + 6  * (abs_lat / 90) ** 0.8 + rng.normal(0, 1.3, n)

    # Normalise loosely so they sit in realistic absolute ranges
    fe = np.clip(fe_base, 1.0, 22.0)
    mg = np.clip(mg_base, 1.0, 14.0)
    al = np.clip(al_base, 5.0, 20.0)
    si = np.clip(si_base, 14.0, 28.0)

    df = pd.DataFrame({
        "timestamp":        [t.isoformat() for t in timestamps],
        "orbit_number":     orbit_numbers,
        "latitude":         np.round(latitude, 4),
        "longitude":        np.round(longitude, 4),
        "solar_flux":       np.round(solar_flux, 4),
        "counts_per_second": counts_per_second,
        "mg_pct":           np.round(mg, 3),
        "al_pct":           np.round(al, 3),
        "si_pct":           np.round(si, 3),
        "fe_pct":           np.round(fe, 3),
    })
    return df


# Build the in-memory DataFrame once at startup
DF = generate_telemetry(700)
ORBIT_LIST = sorted(DF["orbit_number"].unique().tolist())


# ──────────────────────────────────────────────────────────────────────────────
# 2.  ROUTES
# ──────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the single-page telemetry workstation."""
    return render_template("index.html", orbits=ORBIT_LIST)


@app.route("/api/data", methods=["GET"])
def api_data():
    """
    Filtered telemetry endpoint.

    GET params
    ----------
    min_lat   float  default -90
    max_lat   float  default  90
    min_lon   float  default -180
    max_lon   float  default  180
    orbits    str    comma-separated orbit numbers; default all
    """
    # ── Parse & validate query parameters ─────────────────────────────────────
    try:
        min_lat = float(request.args.get("min_lat", -90))
        max_lat = float(request.args.get("max_lat",  90))
        min_lon = float(request.args.get("min_lon", -180))
        max_lon = float(request.args.get("max_lon",  180))
    except ValueError:
        return jsonify({"error": "Invalid numeric parameter"}), 400

    orbits_param = request.args.get("orbits", "")
    if orbits_param.strip():
        try:
            selected_orbits = [int(o) for o in orbits_param.split(",") if o.strip()]
        except ValueError:
            return jsonify({"error": "Invalid orbit list"}), 400
    else:
        selected_orbits = ORBIT_LIST

    # ── Pandas slice ──────────────────────────────────────────────────────────
    mask = (
        (DF["latitude"]     >= min_lat) & (DF["latitude"]     <= max_lat) &
        (DF["longitude"]    >= min_lon) & (DF["longitude"]    <= max_lon) &
        (DF["orbit_number"].isin(selected_orbits))
    )
    filtered = DF[mask].copy()

    # ── Server-side aggregations ───────────────────────────────────────────────
    if len(filtered) == 0:
        stats = {
            "sample_count":    0,
            "mean_solar_flux": 0.0,
            "peak_cps":        0,
            "dominant_element": "N/A",
        }
        records = []
    else:
        element_means = {
            "Mg": filtered["mg_pct"].mean(),
            "Al": filtered["al_pct"].mean(),
            "Si": filtered["si_pct"].mean(),
            "Fe": filtered["fe_pct"].mean(),
        }
        dominant = max(element_means, key=element_means.get)

        stats = {
            "sample_count":    int(len(filtered)),
            "mean_solar_flux": round(float(filtered["solar_flux"].mean()), 4),
            "peak_cps":        int(filtered["counts_per_second"].max()),
            "dominant_element": dominant,
        }
        records = filtered.to_dict(orient="records")

    return jsonify({"stats": stats, "records": records})


@app.route("/api/export", methods=["GET"])
def api_export():
    """
    Returns the current filtered slice as a downloadable CSV.
    Accepts the same GET parameters as /api/data.
    """
    # Re-use the filtering logic by proxying into api_data's internals
    resp = api_data()
    if isinstance(resp, tuple):          # error case
        return resp
    payload = resp.get_json()

    if not payload["records"]:
        return make_response("No data for current filters.", 204)

    df_out = pd.DataFrame(payload["records"])
    csv_buffer = io.StringIO()
    df_out.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    response = make_response(csv_bytes)
    response.headers["Content-Type"]        = "text/csv"
    response.headers["Content-Disposition"] = 'attachment; filename="lunar_xrf_export.csv"'
    return response


@app.route("/api/orbits", methods=["GET"])
def api_orbits():
    """Returns the list of available orbit numbers."""
    return jsonify({"orbits": ORBIT_LIST})


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
