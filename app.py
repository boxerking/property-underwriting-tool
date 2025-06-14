import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
from geopy.distance import geodesic
import numpy as np
from fpdf import FPDF
import io

st.set_page_config(page_title="Indian Property Insurance Underwriting Tool", layout="wide")

st.title("Indian Property Insurance Underwriting Risk Analysis Tool")

# --- Elevation API ---
def get_elevation(lat, lon):
    try:
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
        r = requests.get(url)
        r.raise_for_status()
        results = r.json().get("results")
        if results and len(results) > 0:
            return results[0].get("elevation")
    except Exception as e:
        st.error(f"Error fetching elevation data: {e}")
    return None

# --- Flood risk classification ---
def classify_flood_risk(elevation):
    if elevation is None:
        return "Unknown"
    if elevation < 5:
        return "High Flood Risk"
    elif elevation < 15:
        return "Medium Flood Risk"
    else:
        return "Low Flood Risk"

# --- Indian urban flooding zones (major metros) ---
flood_zones = [
    {"name": "Mumbai Flood Zone", "bounds": [(18.90, 72.75), (19.15, 72.95)]},
    {"name": "Chennai Flood Zone", "bounds": [(13.00, 80.20), (13.15, 80.30)]},
    {"name": "Kolkata Flood Zone", "bounds": [(22.45, 88.30), (22.60, 88.45)]},
    {"name": "Delhi Flood Zone", "bounds": [(28.55, 77.15), (28.75, 77.35)]},
    {"name": "Bengaluru Flood Zone", "bounds": [(12.90, 77.50), (13.05, 77.65)]},
]

def point_in_bounds(lat, lon, bounds):
    (lat_min, lon_min), (lat_max, lon_max) = bounds
    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max

def check_urban_flood_risk(lat, lon):
    for zone in flood_zones:
        if point_in_bounds(lat, lon, zone["bounds"]):
            return f"High Urban Flood Risk ({zone['name']})"
    return "Low Urban Flood Risk"

# --- Indian Fire Stations sample data ---
fire_stations = pd.DataFrame([
    {"name": "Mumbai Fire Station 1", "lat": 19.015, "lon": 72.85},
    {"name": "Mumbai Fire Station 2", "lat": 18.975, "lon": 72.81},
    {"name": "Chennai Fire Station 1", "lat": 13.080, "lon": 80.275},
    {"name": "Chennai Fire Station 2", "lat": 13.065, "lon": 80.250},
    {"name": "Kolkata Fire Station 1", "lat": 22.57, "lon": 88.36},
    {"name": "Kolkata Fire Station 2", "lat": 22.53, "lon": 88.38},
    {"name": "Delhi Fire Station 1", "lat": 28.65, "lon": 77.20},
    {"name": "Delhi Fire Station 2", "lat": 28.62, "lon": 77.22},
    {"name": "Bengaluru Fire Station 1", "lat": 12.98, "lon": 77.58},
    {"name": "Bengaluru Fire Station 2", "lat": 12.95, "lon": 77.60},
])

def estimate_response_time(lat, lon):
    min_time = None
    closest_station = None
    for _, fs in fire_stations.iterrows():
        dist_km = geodesic((lat, lon), (fs.lat, fs.lon)).km
        time_min = dist_km / 40 * 60  # Assuming avg 40 km/h speed to minutes
        if min_time is None or time_min < min_time:
            min_time = time_min
            closest_station = fs["name"]
    return closest_station, round(min_time, 1) if min_time else None

def generate_surrounding_exposure(lat, lon, num_points=5):
    np.random.seed(42)
    lats = lat + (np.random.rand(num_points) - 0.5) / 100
    lons = lon + (np.random.rand(num_points) - 0.5) / 100
    risk_levels = np.random.choice(["Low", "Medium", "High"], num_points)
    df = pd.DataFrame({"lat": lats, "lon": lons, "risk": risk_levels})
    return df

# --- PDF Report Generation ---
def create_pdf_report(lat, lon, elevation, flood_risk, urban_flood, fire_station, response_time, exposure_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Property Insurance Underwriting Risk Analysis Report", ln=True, align="C")

    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Location Coordinates: Latitude {lat:.6f}, Longitude {lon:.6f}", ln=True)
    pdf.cell(0, 10, f"Elevation: {elevation if elevation is not None else 'N/A'} meters", ln=True)
    pdf.cell(0, 10, f"Flood Risk (Elevation Based): {flood_risk}", ln=True)
    pdf.cell(0, 10, f"Urban Flood Risk Zone: {urban_flood}", ln=True)
    pdf.cell(0, 10, f"Nearest Fire Station: {fire_station}", ln=True)
    pdf.cell(0, 10, f"Fire Brigade Response Time Estimate: {response_time} minutes", ln=True)

    pdf.ln(10)
    pdf.cell(0, 10, "Nearby Properties Exposure Risk:", ln=True)

    pdf.set_font("Arial", "", 10)
    pdf.cell(40, 10, "Latitude", 1)
    pdf.cell(40, 10, "Longitude", 1)
    pdf.cell(40, 10, "Risk Level", 1)
    pdf.ln()

    for _, row in exposure_df.iterrows():
        pdf.cell(40, 10, f"{row['lat']:.6f}", 1)
        pdf.cell(40, 10, f"{row['lon']:.6f}", 1)
        pdf.cell(40, 10, row["risk"], 1)
        pdf.ln()

    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output

# --- Streamlit UI ---

st.write("**Click on the map or enter coordinates manually to analyze property insurance risk within India.**")

viewport = {
    "latitude": 20.5937,  # Center of India approx
    "longitude": 78.9629,
    "zoom": 5,
}

if "selected_location" not in st.session_state:
    st.session_state.selected_location = (
        viewport["latitude"], viewport["longitude"])

# Map layers for flood zones polygons
flood_zone_layers = []
for zone in flood_zones:
    (lat_min, lon_min), (lat_max, lon_max) = zone["bounds"]
    polygon = [
        [lon_min, lat_min],
        [lon_max, lat_min],
        [lon_max, lat_max],
        [lon_min, lat_max],
    ]
    flood_zone_layers.append(pdk.Layer(
        "PolygonLayer",
        data=[{"polygon": polygon}],
        get_polygon="polygon",
        get_fill_color=[255, 0, 0, 50],
        pickable=False,
    ))

# Fire station layer
fire_station_layer = pdk.Layer(
    "ScatterplotLayer",
    data=fire_stations,
    get_position=["lon", "lat"],
    get_fill_color=[255, 0, 0],
    get_radius=80,
    pickable=True,
)

# Selected location marker
selected_lat, selected_lon = st.session_state.selected_location
selected_point_layer = pdk.Layer(
    "ScatterplotLayer",
    data=[{"lat": selected_lat, "lon": selected_lon}],
    get_position=["lon", "lat"],
    get_color=[0, 128, 255],
    get_radius=150,
    pickable=False,
)

# Surrounding exposure points
exposure_df = generate_surrounding_exposure(selected_lat, selected_lon)
exposure_layer = pdk.Layer(
    "ScatterplotLayer",
    data=exposure_df,
    get_position=["lon", "lat"],
    get_fill_color=[255, 165, 0],
    get_radius=70,
    pickable=True,
)

layers = flood_zone_layers + [fire_station_layer, selected_point_layer, exposure_layer]

r = pdk.Deck(
    map_style="mapbox://styles/mapbox/streets-v11",
    initial_view_state=pdk.ViewState(
        latitude=viewport["latitude"],
        longitude=viewport["longitude"],
        zoom=viewport["zoom"],
    ),
    layers=layers,
)

st.pydeck_chart(r)

# Coordinate input manual override
with st.expander("Or enter coordinates manually"):
    lat_input = st.number_input("Latitude", value=selected_lat, format="%.6f", min_value=6.0, max_value=37.0)
    lon_input = st.number_input("Longitude", value=selected_lon, format="%.6f", min_value=68.0, max_value=97.5)
    if st.button("Update Location"):
        st.session_state.selected_location = (lat_input, lon_input)
        st.experimental_rerun()
