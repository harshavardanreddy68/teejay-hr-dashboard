import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
from supabase import create_client
import requests

st.set_page_config(page_title="HR AI Dashboard", layout="wide")

# ================================
# 🔑 SUPABASE CONFIG
# ================================
SUPABASE_URL = "https://bkwbntrfwakiecdckhyf.supabase.co"
SUPABASE_KEY = "sb_publishable_HFpU9onQmxoRXVoAK-dykA_zXXwUILH"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================================
# 🔑 GOOGLE API (OPTIONAL)
# ================================
GOOGLE_API_KEY = "https://maps.googleapis.com/maps/api/geocode/json?latlng=40.714224,-73.961452&key=YOUR_API_KEY"

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
# LOAD DATA
# ================================
def load_data():
    res = supabase.table("employees").select("*").execute()
    return pd.DataFrame(res.data)

df = load_data()

# ================================
# ➕ ADD EMPLOYEE
# ================================
st.sidebar.title("➕ Add Employee")

with st.sidebar.form("add"):
    name = st.text_input("Name")
    dept = st.text_input("Department")
    sub = st.text_input("Sub Section")
    addr = st.text_area("Address")

    if st.form_submit_button("Add"):
        lat, lon = get_lat_lon(addr)

        supabase.table("employees").insert({
            "name": name,
            "department": dept,
            "sub_section": sub,
            "address": addr,
            "lat": lat,
            "lon": lon
        }).execute()

        st.success("Added ✅")
        st.rerun()

# ================================
# KPI FILTER
# ================================
if "filter_type" not in st.session_state:
    st.session_state.filter_type = "All"

c1, c2, c3 = st.columns(3)

if c1.button(f"👥 Total\n{len(df)}"):
    st.session_state.filter_type = "All"

if c2.button(f"🏢 Dept\n{df['department'].nunique()}"):
    st.session_state.filter_type = "Department"

if c3.button(f"🧩 Sub\n{df['sub_section'].nunique()}"):
    st.session_state.filter_type = "Sub"

# ================================
# FILTER
# ================================
filtered_df = df.copy()

if st.session_state.filter_type == "Department":
    dept = st.selectbox("Department", df["department"].unique())
    filtered_df = df[df["department"] == dept]

elif st.session_state.filter_type == "Sub":
    sub = st.selectbox("Sub Section", df["sub_section"].unique())
    filtered_df = df[df["sub_section"] == sub]

# ================================
# SEARCH
# ================================
search = st.text_input("🔍 Search")

if search:
    filtered_df = filtered_df[
        filtered_df["name"].str.contains(search, case=False)
    ]

# ================================
# 🌍 MAP
# ================================
st.subheader("🌍 Employee Map")

m = folium.Map(location=[17.6868, 83.2185], zoom_start=7)

from folium.plugins import MarkerCluster
cluster = MarkerCluster().add_to(m)

for _, row in filtered_df.iterrows():
    if pd.notna(row["lat"]):
        popup_html = f"""
        <b>{row['name']}</b><br>
        Dept: {row['department']}<br>
        Sub: {row['sub_section']}<br>
        Address: {row['address']}
        """
        folium.Marker(
            [row["lat"], row["lon"]],
            popup=popup_html
        ).add_to(cluster)

st_folium(m, width=None, height=700)

# ================================
# 📊 GRAPH
# ================================
dept_counts = filtered_df["department"].value_counts().reset_index()
dept_counts.columns = ["Department","Count"]

fig = px.bar(dept_counts, x="Department", y="Count", color="Department")
st.plotly_chart(fig, use_container_width=True)

# ================================
# 📋 TABLE
# ================================
st.dataframe(filtered_df, use_container_width=True)
