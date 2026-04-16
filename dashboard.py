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
# 🔑 GOOGLE API KEY (FIXED)
# ================================
GOOGLE_API_KEY = "https://maps.googleapis.com/maps/api/geocode/json?latlng=40.714224,-73.961452&key=YOUR_API_KEY"  # ⚠️ Put actual API key here

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
    df = pd.DataFrame(res.data)

    if df.empty:
        return df

    # ✅ FIX COLUMN ISSUES PERMANENTLY
    df.columns = df.columns.str.strip().str.lower()

    return df

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
# HANDLE EMPTY DATA
# ================================
if df.empty:
    st.warning("No employee data found. Please add employees.")
    st.stop()

# ================================
# SAFE COLUMN ACCESS (NO MORE ERRORS)
# ================================
def safe_col(df, col):
    return col if col in df.columns else None

col_name = safe_col(df, "name")
col_dept = safe_col(df, "department")
col_sub = safe_col(df, "sub_section")
col_lat = safe_col(df, "lat")
col_lon = safe_col(df, "lon")
col_addr = safe_col(df, "address")

# ================================
# KPI FILTER
# ================================
if "filter_type" not in st.session_state:
    st.session_state.filter_type = "All"

c1, c2, c3 = st.columns(3)

if c1.button(f"👥 Total\n{len(df)}"):
    st.session_state.filter_type = "All"

dept_count = df[col_dept].nunique() if col_dept else 0
sub_count = df[col_sub].nunique() if col_sub else 0

if c2.button(f"🏢 Dept\n{dept_count}"):
    st.session_state.filter_type = "Department"

if c3.button(f"🧩 Sub\n{sub_count}"):
    st.session_state.filter_type = "Sub"

# ================================
# FILTER
# ================================
filtered_df = df.copy()

if st.session_state.filter_type == "Department" and col_dept:
    dept = st.selectbox("Department", df[col_dept].dropna().unique())
    filtered_df = df[df[col_dept] == dept]

elif st.session_state.filter_type == "Sub" and col_sub:
    sub = st.selectbox("Sub Section", df[col_sub].dropna().unique())
    filtered_df = df[df[col_sub] == sub]

# ================================
# SEARCH
# ================================
search = st.text_input("🔍 Search")

if search and col_name:
    filtered_df = filtered_df[
        filtered_df[col_name].astype(str).str.contains(search, case=False)
    ]

# ================================
# 🌍 MAP
# ================================
st.subheader("🌍 Employee Map")

m = folium.Map(location=[17.6868, 83.2185], zoom_start=7)

from folium.plugins import MarkerCluster
cluster = MarkerCluster().add_to(m)

if col_lat and col_lon:
    for _, row in filtered_df.iterrows():
        if pd.notna(row[col_lat]):
            popup_html = f"""
            <b>{row.get(col_name, '')}</b><br>
            Dept: {row.get(col_dept, '')}<br>
            Sub: {row.get(col_sub, '')}<br>
            Address: {row.get(col_addr, '')}
            """
            folium.Marker(
                [row[col_lat], row[col_lon]],
                popup=popup_html
            ).add_to(cluster)

st_folium(m, width=None, height=700)

# ================================
# 📊 GRAPH
# ================================
if col_dept:
    dept_counts = filtered_df[col_dept].value_counts().reset_index()
    dept_counts.columns = ["Department", "Count"]

    fig = px.bar(dept_counts, x="Department", y="Count", color="Department")
    st.plotly_chart(fig, use_container_width=True)

# ================================
# 📋 TABLE
# ================================
st.dataframe(filtered_df, use_container_width=True)
