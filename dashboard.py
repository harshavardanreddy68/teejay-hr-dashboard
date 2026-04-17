import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Teejay HR Dashboard",
    layout="wide",
    page_icon="🏢"
)

# =====================================================
# GOOGLE SHEET CONFIG
# =====================================================
# Replace with your Google Sheet File ID
FILE_ID = "https://docs.google.com/spreadsheets/d/1F0BAUs5nt1knAtbazPyw3hydvDgl2yHI/edit?usp=sharing&ouid=109821000672586326690&rtpof=true&sd=true"

CSV_URL = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv"

# =====================================================
# UI STYLE
# =====================================================
st.markdown("""
<style>
.stApp{
    background:linear-gradient(135deg,#020617,#0f172a);
    color:white;
}

section[data-testid="stSidebar"]{
    background:#111827;
}

.block-container{
    padding-top:1rem;
}

.header{
    padding:22px;
    border-radius:18px;
    background:linear-gradient(135deg,#2563eb,#1d4ed8);
    text-align:center;
    margin-bottom:18px;
}

.card{
    background:rgba(255,255,255,0.05);
    padding:18px;
    border-radius:15px;
    text-align:center;
    border:1px solid rgba(255,255,255,0.06);
}

.section{
    background:rgba(255,255,255,0.03);
    padding:16px;
    border-radius:15px;
    margin-top:14px;
}

div.stButton > button{
    width:100%;
    height:55px;
    border-radius:12px;
}
</style>
""", unsafe_allow_html=True)

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

# =====================================================
# MAIN LOAD
# =====================================================
try:
    df = load_data()
except:
    st.error("Google Sheet connection failed. Check File ID / Sharing Access.")
    st.stop()

# =====================================================
# HEADER
# =====================================================
st.markdown("""
<div class="header">
<h1>🏢 Teejay India Pvt Ltd</h1>
<p>Live HR Analytics Dashboard</p>
</div>
""", unsafe_allow_html=True)

# =====================================================
# KPI FILTER BUTTONS
# =====================================================
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "all"

c1, c2, c3 = st.columns(3)

with c1:
    if st.button(f"👥 Total Employees\n{len(df)}"):
        st.session_state.view_mode = "all"

with c2:
    if st.button(f"🏢 Departments\n{df['department'].nunique()}"):
        st.session_state.view_mode = "dept"

with c3:
    if st.button(f"🧩 Sub Sections\n{df['sub_section'].nunique()}"):
        st.session_state.view_mode = "sub"

# =====================================================
# FILTERING
# =====================================================
filtered_df = df.copy()

if st.session_state.view_mode == "dept":
    opts = sorted(df["department"].dropna().unique())
    if opts:
        pick = st.selectbox("Select Department", opts)
        filtered_df = df[df["department"] == pick]

elif st.session_state.view_mode == "sub":
    opts = sorted(df["sub_section"].dropna().unique())
    if opts:
        pick = st.selectbox("Select Sub Section", opts)
        filtered_df = df[df["sub_section"] == pick]

# =====================================================
# SEARCH
# =====================================================
search = st.text_input("🔍 Search Employee")

if search:
    filtered_df = filtered_df[
        filtered_df["name"].astype(str).str.contains(
            search,
            case=False,
            na=False
        )
    ]

# =====================================================
# MAP
# =====================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("🌍 Employee Location Map")

m = folium.Map(
    location=[17.6868, 83.2185],
    zoom_start=6
)

cluster = MarkerCluster().add_to(m)

for _, row in filtered_df.iterrows():
    try:
        lat = float(row["lat"])
        lon = float(row["lon"])

        popup = f"""
        <div style='width:240px'>
        <h4>{row['name']}</h4>
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
# GRAPH
# =====================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("📊 Department Analytics")

chart = (
    filtered_df["department"]
    .value_counts()
    .reset_index()
)

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

st.dataframe(
    filtered_df,
    use_container_width=True
)

st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# FOOTER
# =====================================================
st.caption("🔄 Auto refresh every 60 seconds from Google Sheets")
