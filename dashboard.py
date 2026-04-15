import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import requests

st.set_page_config(page_title="HR AI Dashboard", layout="wide")

# ================================
# 🔑 GOOGLE API KEY (PUT HERE)
# ================================
GOOGLE_API_KEY = "https://maps.googleapis.com/maps/api/geocode/json?latlng=40.714224,-73.961452&key=YOUR_API_KEY"

# ================================
# 🌍 GOOGLE FUNCTION
# ================================
def get_lat_lon(address):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": GOOGLE_API_KEY}

    try:
        res = requests.get(url, params=params)
        data = res.json()

        if data["status"] == "OK":
            loc = data["results"][0]["geometry"]["location"]
            return loc["lat"], loc["lng"]
    except:
        pass

    return None, None

# ================================
# 🌌 UI STYLE
# ================================
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top, #020617, #000000);
    color: #e2e8f0;
}
.header {
    padding: 25px;
    border-radius: 20px;
    background: linear-gradient(135deg, #0ea5e9, #2563eb);
    text-align: center;
}
div.stButton > button {
    width: 100%;
    height: 90px;
    font-size: 18px;
    border-radius: 15px;
}
.section {
    background: rgba(255,255,255,0.03);
    padding: 15px;
    border-radius: 15px;
    margin-top: 15px;
}
</style>
""", unsafe_allow_html=True)

# ================================
# HEADER
# ================================
st.markdown("""
<div class="header">
<h1>🚀 Teejay India Pvt Ltd</h1>
<p>AI HR Dashboard</p>
</div>
""", unsafe_allow_html=True)

# ================================
# LOAD DATA
# ================================
df = pd.read_excel("employees_with_coords.xlsx")

# ================================
# ➕ ADD EMPLOYEE (WITH AUTO LOCATION)
# ================================
st.sidebar.title("➕ Add Employee")

with st.sidebar.form("add"):
    name = st.text_input("Name")
    dept = st.text_input("Department")
    sub = st.text_input("Sub Section")
    addr = st.text_area("Address")

    if st.form_submit_button("Add"):
        lat, lon = get_lat_lon(addr)

        new = {
            "Name": name,
            "Department": dept,
            "Sub Section": sub,
            "Address": addr,
            "lat": lat,
            "lon": lon
        }

        df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
        df.to_excel("employees_with_coords.xlsx", index=False)

        st.success("Added with location")
        st.rerun()

# ================================
# KPI FILTER
# ================================
if "filter_type" not in st.session_state:
    st.session_state.filter_type = "All"

c1, c2, c3 = st.columns(3)

if c1.button(f"👥 Total\n{len(df)}"):
    st.session_state.filter_type = "All"

if c2.button(f"🏢 Dept\n{df['Department'].nunique()}"):
    st.session_state.filter_type = "Department"

if c3.button(f"🧩 Sub\n{df['Sub Section'].nunique()}"):
    st.session_state.filter_type = "Sub"

# ================================
# FILTER LOGIC
# ================================
filtered_df = df.copy()

if st.session_state.filter_type == "Department":
    dept = st.selectbox("Select Department", df["Department"].unique())
    filtered_df = df[df["Department"] == dept]

elif st.session_state.filter_type == "Sub":
    sub = st.selectbox("Select Sub Section", df["Sub Section"].unique())
    filtered_df = df[df["Sub Section"] == sub]

# ================================
# SEARCH
# ================================
search = st.text_input("🔍 Search Employee")

if search:
    filtered_df = filtered_df[
        filtered_df["Name"].str.contains(search, case=False, na=False)
    ]

# ================================
# 🌍 MAP
# ================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("🌍 Employee Map")

m = folium.Map(location=[17.6868, 83.2185], zoom_start=7)

from folium.plugins import MarkerCluster
cluster = MarkerCluster().add_to(m)

for _, row in filtered_df.iterrows():
    if pd.notna(row["lat"]):

        popup_html = f"""
        <div style="width:250px;">
            <h4>👤 {row['Name']}</h4>
            <b>Dept:</b> {row['Department']}<br>
            <b>Sub:</b> {row['Sub Section']}<br>
            <b>Address:</b> {row['Address']}
        </div>
        """

        folium.Marker(
            [row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(cluster)

st_folium(m, width=None, height=750)
st.markdown('</div>', unsafe_allow_html=True)

# ================================
# 📊 GRAPH
# ================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("📊 Department Analytics")

dept_counts = filtered_df["Department"].value_counts().reset_index()
dept_counts.columns = ["Department","Count"]

fig = px.bar(dept_counts, x="Department", y="Count", color="Department")
st.plotly_chart(fig, use_container_width=True)

# ================================
# 📋 TABLE
# ================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("📋 Employee Table")
st.dataframe(filtered_df, use_container_width=True)
