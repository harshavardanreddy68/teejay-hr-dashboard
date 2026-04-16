import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import plotly.express as px
from supabase import create_client
import requests

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Teejay HR Dashboard",
    layout="wide",
    page_icon="🏢"
)

# =====================================================
# CONFIG (PUT YOUR KEYS HERE)
# =====================================================
SUPABASE_URL = "https://bkwbntrfwakiecdckhyf.supabase.co"
SUPABASE_KEY = "sb_publishable_HFpU9onQmxoRXVoAK-dykA_zXXwUILH"
GOOGLE_API_KEY = "https://maps.googleapis.com/maps/api/geocode/json?latlng=40.714224,-73.961452&key=YOUR_API_KEY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================================
# UI STYLE
# =====================================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#020617,#0f172a);
    color: white;
}

section[data-testid="stSidebar"]{
    background:#111827;
}

.block-container{
    padding-top:1rem;
}

.title-box{
    padding:20px;
    border-radius:18px;
    background:linear-gradient(135deg,#2563eb,#1d4ed8);
    text-align:center;
    margin-bottom:20px;
}

.kpi{
    background:rgba(255,255,255,0.05);
    padding:18px;
    border-radius:16px;
    text-align:center;
    border:1px solid rgba(255,255,255,0.08);
}

.section{
    background:rgba(255,255,255,0.03);
    padding:16px;
    border-radius:16px;
    margin-top:14px;
}

div.stButton > button{
    width:100%;
    border-radius:12px;
    height:55px;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# HEADER
# =====================================================
st.markdown("""
<div class="title-box">
<h1>🏢 Teejay India Pvt Ltd</h1>
<p>Real-Time HR Intelligence Dashboard</p>
</div>
""", unsafe_allow_html=True)

# =====================================================
# GOOGLE GEOCODING
# =====================================================
def get_lat_lon(address):
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == "PASTE_YOUR_GOOGLE_API_KEY":
        return None, None

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
# LOAD DATA (FIXED COLUMN ISSUES)
# =====================================================
def load_data():
    try:
        res = supabase.table("employees").select("*").execute()
        df = pd.DataFrame(res.data)

        if df.empty:
            return pd.DataFrame(columns=[
                "id","name","department","sub_section",
                "address","lat","lon"
            ])

        # normalize columns
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

        # ensure required columns exist
        needed = [
            "id","name","department",
            "sub_section","address","lat","lon"
        ]

        for col in needed:
            if col not in df.columns:
                df[col] = None

        return df

    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame(columns=[
            "id","name","department","sub_section",
            "address","lat","lon"
        ])

# =====================================================
# SAVE / UPDATE / DELETE
# =====================================================
def add_employee(name, dept, sub, address):
    lat, lon = get_lat_lon(address)

    supabase.table("employees").insert({
        "name": name,
        "department": dept,
        "sub_section": sub,
        "address": address,
        "lat": lat,
        "lon": lon
    }).execute()

def update_employee(emp_id, name, dept, sub, address):
    lat, lon = get_lat_lon(address)

    supabase.table("employees").update({
        "name": name,
        "department": dept,
        "sub_section": sub,
        "address": address,
        "lat": lat,
        "lon": lon
    }).eq("id", emp_id).execute()

def delete_employee(emp_id):
    supabase.table("employees").delete().eq("id", emp_id).execute()

# =====================================================
# LOAD DATA
# =====================================================
df = load_data()

# =====================================================
# SIDEBAR CRUD
# =====================================================
st.sidebar.title("⚙ Employee Management")

mode = st.sidebar.selectbox(
    "Choose Action",
    ["Add Employee", "Edit Employee", "Delete Employee"]
)

# ---------------- ADD ----------------
if mode == "Add Employee":
    with st.sidebar.form("add_form"):
        name = st.text_input("Name")
        dept = st.text_input("Department")
        sub = st.text_input("Sub Section")
        addr = st.text_area("Address")

        if st.form_submit_button("Add Employee"):
            if name:
                add_employee(name, dept, sub, addr)
                st.success("Employee Added")
                st.rerun()

# ---------------- EDIT ----------------
elif mode == "Edit Employee":
    if not df.empty:
        names = df["name"].fillna("").tolist()
        selected = st.sidebar.selectbox("Select Employee", names)

        row = df[df["name"] == selected].iloc[0]

        with st.sidebar.form("edit_form"):
            name = st.text_input("Name", row["name"])
            dept = st.text_input("Department", row["department"])
            sub = st.text_input("Sub Section", row["sub_section"])
            addr = st.text_area("Address", row["address"])

            if st.form_submit_button("Update"):
                update_employee(row["id"], name, dept, sub, addr)
                st.success("Updated")
                st.rerun()

# ---------------- DELETE ----------------
elif mode == "Delete Employee":
    if not df.empty:
        names = df["name"].fillna("").tolist()
        selected = st.sidebar.selectbox("Select Employee", names)

        row = df[df["name"] == selected].iloc[0]

        if st.sidebar.button("Delete Employee"):
            delete_employee(row["id"])
            st.success("Deleted")
            st.rerun()

# =====================================================
# KPI BUTTON FILTERS
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
    if len(opts) > 0:
        pick = st.selectbox("Select Department", opts)
        filtered_df = df[df["department"] == pick]

elif st.session_state.view_mode == "sub":
    opts = sorted(df["sub_section"].dropna().unique())
    if len(opts) > 0:
        pick = st.selectbox("Select Sub Section", opts)
        filtered_df = df[df["sub_section"] == pick]

# =====================================================
# SEARCH
# =====================================================
search = st.text_input("🔍 Search Employee Name")

if search:
    filtered_df = filtered_df[
        filtered_df["name"].str.contains(search, case=False, na=False)
    ]

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

for _, row in filtered_df.iterrows():
    if pd.notna(row["lat"]) and pd.notna(row["lon"]):
        popup = f"""
        <div style='width:250px'>
        <h4>{row['name']}</h4>
        <b>Department:</b> {row['department']}<br>
        <b>Sub Section:</b> {row['sub_section']}<br>
        <b>Address:</b> {row['address']}
        </div>
        """

        folium.Marker(
            [row["lat"], row["lon"]],
            popup=folium.Popup(popup, max_width=300)
        ).add_to(cluster)

st_folium(m, width=None, height=700)
st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# GRAPH
# =====================================================
st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("📊 Department Distribution")

if not filtered_df.empty:
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

show_cols = [
    "id","name","department",
    "sub_section","address"
]

st.dataframe(
    filtered_df[show_cols],
    use_container_width=True
)

st.markdown("</div>", unsafe_allow_html=True)
