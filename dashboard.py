import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import requests
import time

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Teejay HR Dashboard",
    layout="wide",
    page_icon="🏢"
)

# =====================================================
# GOOGLE SHEET
# =====================================================
FILE_ID = "10w4-LNlg0QtB45kYXMQuTzPURRt9wx-5_TiYkgdrY00"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv"

# =====================================================
# GOOGLE MAPS API KEY (PUT YOUR KEY)
# =====================================================
GOOGLE_API_KEY = "PASTE_YOUR_GOOGLE_API_KEY"

# =====================================================
# STYLE
# =====================================================
st.markdown("""
<style>
.stApp{
background:linear-gradient(135deg,#020617,#0f172a);
color:white;
}
.header{
padding:24px;
border-radius:18px;
background:linear-gradient(135deg,#2563eb,#1d4ed8);
text-align:center;
margin-bottom:18px;
}
.section{
background:rgba(255,255,255,0.03);
padding:16px;
border-radius:15px;
margin-top:14px;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# GEOCODING
# =====================================================
def get_lat_lon(address):
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address,
            "key": GOOGLE_API_KEY
        }

        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        if data["status"] == "OK":
            loc = data["results"][0]["geometry"]["location"]
            return loc["lat"], loc["lng"]

    except:
        pass

    return None, None

# =====================================================
# LOAD DATA
# =====================================================
@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(CSV_URL)

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    needed = [
        "emp_id",
        "name",
        "department",
        "sub_section",
        "address",
        "lat",
        "lon"
    ]

    for col in needed:
        if col not in df.columns:
            df[col] = None

    # AUTO GEOCODE IF LAT/LON EMPTY
    for i, row in df.iterrows():

        lat_missing = pd.isna(row["lat"]) or row["lat"] == ""
        lon_missing = pd.isna(row["lon"]) or row["lon"] == ""

        if lat_missing or lon_missing:
            if pd.notna(row["address"]):
                lat, lon = get_lat_lon(row["address"])
                df.at[i, "lat"] = lat
                df.at[i, "lon"] = lon
                time.sleep(0.2)

    return df

# =====================================================
# LOAD
# =====================================================
try:
    df = load_data()
except:
    st.error("Google Sheet connection failed.")
    st.stop()

# =====================================================
# HEADER
# =====================================================
st.markdown("""
<div class="header">
<h1>🏢 Teejay India Pvt Ltd</h1>
<p>Auto Location HR Dashboard</p>
</div>
""", unsafe_allow_html=True)

# =====================================================
# KPI
# =====================================================
c1, c2, c3 = st.columns(3)

c1.metric("👥 Total Employees", len(df))
c2.metric("🏢 Departments", df["department"].nunique())
c3.metric("🧩 Sub Sections", df["sub_section"].nunique())

# =====================================================
# SEARCH
# =====================================================
search = st.text_input("🔍 Search Employee")

if search:
    df = df[
        df["name"].astype(str).str.contains(search, case=False, na=False)
        |
        df["emp_id"].astype(str).str.contains(search, case=False, na=False)
    ]

# =====================================================
# MAP
# =====================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("🌍 Employee Live Map")

m = folium.Map(
    location=[17.6868, 83.2185],
    zoom_start=6
)

cluster = MarkerCluster().add_to(m)

for _, row in df.iterrows():
    try:
        lat = float(row["lat"])
        lon = float(row["lon"])

        popup = f"""
        <div style='width:250px'>
        <h4>{row['name']}</h4>
        <b>ID:</b> {row['emp_id']}<br>
        <b>Dept:</b> {row['department']}<br>
        <b>Sub:</b> {row['sub_section']}<br>
        <b>Address:</b> {row['address']}
        </div>
        """

        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup, max_width=300)
        ).add_to(cluster)

    except:
        pass

st_folium(m, width=None, height=650)

st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# CHART
# =====================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("📊 Department Distribution")

chart = df["department"].value_counts().reset_index()
chart.columns = ["Department", "Count"]

fig = px.bar(
    chart,
    x="Department",
    y="Count",
    color="Department",
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# TABLE
# =====================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("📋 Employee Directory")

show_cols = [
    "emp_id",
    "name",
    "department",
    "sub_section",
    "address"
]

st.dataframe(df[show_cols], use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# FOOTER
# =====================================================
st.caption("🔄 Auto refresh every 30 sec | Address auto converts to map location")
