import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import gspread
from google.oauth2.service_account import Credentials
from geopy.geocoders import Nominatim

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
SHEET_ID = "10w4-LNlg0QtB45kYXMQuTzPURRt9wx-5_TiYkgdrY00"
WORKSHEET_NAME = "Sheet1"   # change if needed

# =====================================================
# GOOGLE SERVICE ACCOUNT JSON
# Put credentials in .streamlit/secrets.toml
# =====================================================
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = dict(st.secrets["gcp_service_account"])

credentials = Credentials.from_service_account_info(
    creds_dict,
    scopes=scope
)

gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)

# =====================================================
# GEOCODER
# =====================================================
geolocator = Nominatim(user_agent="teejay_hr_dashboard")

def get_lat_lon(address):
    try:
        loc = geolocator.geocode(address, timeout=10)
        if loc:
            return loc.latitude, loc.longitude
    except:
        pass
    return None, None

# =====================================================
# LOAD DATA
# =====================================================
@st.cache_data(ttl=30)
def load_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

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

# =====================================================
# SAVE HELPERS
# =====================================================
def append_employee(row):
    sheet.append_row(row)

def update_employee(row_number, row):
    rng = f"A{row_number}:G{row_number}"
    sheet.update(rng, [row])

def delete_employee(row_number):
    sheet.delete_rows(row_number)

# =====================================================
# UI STYLE
# =====================================================
st.markdown("""
<style>
.stApp{
background:linear-gradient(135deg,#020617,#0f172a);
color:white;
}
.header{
padding:22px;
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
section[data-testid="stSidebar"]{
background:#111827;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# HEADER
# =====================================================
st.markdown("""
<div class="header">
<h1>🏢 Teejay India Pvt Ltd</h1>
<p>Live HR Dashboard with Employee Management</p>
</div>
""", unsafe_allow_html=True)

# =====================================================
# LOAD DATA
# =====================================================
df = load_data()

# =====================================================
# SIDEBAR CRUD
# =====================================================
st.sidebar.title("⚙ Employee Management")

mode = st.sidebar.radio(
    "Choose Action",
    ["Add Employee", "Edit Employee", "Delete Employee"]
)

# ---------------- ADD ----------------
if mode == "Add Employee":
    with st.sidebar.form("add_form"):
        emp_id = st.text_input("Employee ID")
        name = st.text_input("Name")
        dept = st.text_input("Department")
        sub = st.text_input("Sub Section")
        addr = st.text_area("Address")

        if st.form_submit_button("Add"):
            lat, lon = get_lat_lon(addr)

            row = [
                emp_id,
                name,
                dept,
                sub,
                addr,
                lat,
                lon
            ]

            append_employee(row)
            st.success("Employee Added")
            st.cache_data.clear()
            st.rerun()

# ---------------- EDIT ----------------
elif mode == "Edit Employee":
    ids = df["emp_id"].astype(str).tolist()

    selected = st.sidebar.selectbox("Select Employee ID", ids)

    row_df = df[df["emp_id"].astype(str) == selected].iloc[0]
    idx = df[df["emp_id"].astype(str) == selected].index[0]
    row_number = idx + 2   # header row + 1

    with st.sidebar.form("edit_form"):
        name = st.text_input("Name", row_df["name"])
        dept = st.text_input("Department", row_df["department"])
        sub = st.text_input("Sub Section", row_df["sub_section"])
        addr = st.text_area("Address", row_df["address"])

        if st.form_submit_button("Update"):
            lat, lon = get_lat_lon(addr)

            row = [
                selected,
                name,
                dept,
                sub,
                addr,
                lat,
                lon
            ]

            update_employee(row_number, row)
            st.success("Updated")
            st.cache_data.clear()
            st.rerun()

# ---------------- DELETE ----------------
elif mode == "Delete Employee":
    ids = df["emp_id"].astype(str).tolist()

    selected = st.sidebar.selectbox("Select Employee ID", ids)

    idx = df[df["emp_id"].astype(str) == selected].index[0]
    row_number = idx + 2

    if st.sidebar.button("Delete Employee"):
        delete_employee(row_number)
        st.success("Deleted")
        st.cache_data.clear()
        st.rerun()

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
search = st.text_input("🔍 Search by ID / Name")

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
st.subheader("🌍 Employee Map")

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
# GRAPH
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
