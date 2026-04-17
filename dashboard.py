import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from streamlit_autorefresh import st_autorefresh
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
# AUTO REFRESH EVERY 5 SECONDS
# =====================================================
st_autorefresh(interval=5000, key="refresh")

# =====================================================
# GOOGLE SHEET LIVE CONFIG
# =====================================================
FILE_ID = "1W50dZdRyBuUeUH89GneNnovXDv_dp0NqFV31XKz08Pc"

CSV_URL = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv&t={int(time.time())}"

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

div.stButton > button{
width:100%;
height:70px;
border-radius:14px;
font-size:18px;
font-weight:bold;
background:#111827;
color:white;
border:1px solid #374151;
}

div.stButton > button:hover{
background:#2563eb;
color:white;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# LOAD LIVE DATA (NO CACHE)
# =====================================================
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

    return df

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
<p>Real-Time HR Analytics Dashboard</p>
</div>
""", unsafe_allow_html=True)

# =====================================================
# KPI FILTERS
# =====================================================
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "all"

c1, c2, c3 = st.columns(3)

with c1:
    if st.button(f"👥 Total Employees\n{len(df)}"):
        st.session_state.view_mode = "all"

with c2:
    if st.button(f"🏢 Departments\n{df['department'].nunique()}"):
        st.session_state.view_mode = "department"

with c3:
    if st.button(f"🧩 Sub Sections\n{df['sub_section'].nunique()}"):
        st.session_state.view_mode = "sub"

# =====================================================
# SEARCH
# =====================================================
search = st.text_input("🔍 Search by Employee ID / Name")

if search:
    df = df[
        df["name"].astype(str).str.contains(search, case=False, na=False)
        |
        df["emp_id"].astype(str).str.contains(search, case=False, na=False)
    ]

# =====================================================
# FILTERS
# =====================================================
if st.session_state.view_mode == "department":
    dept = st.selectbox(
        "Select Department",
        sorted(df["department"].dropna().unique())
    )
    df = df[df["department"] == dept]

elif st.session_state.view_mode == "sub":
    sub = st.selectbox(
        "Select Sub Section",
        sorted(df["sub_section"].dropna().unique())
    )
    df = df[df["sub_section"] == sub]

# =====================================================
# MAP
# =====================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("🌍 Live Employee Map")

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
        <div style='width:260px'>
        <h4>{row['name']}</h4>
        <b>ID:</b> {row['emp_id']}<br>
        <b>Department:</b> {row['department']}<br>
        <b>Sub Section:</b> {row['sub_section']}<br>
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

st.dataframe(
    df[show_cols],
    use_container_width=True
)

st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# FOOTER
# =====================================================
st.caption("🔄 Live updating every 5 seconds | Google Sheet Connected")
