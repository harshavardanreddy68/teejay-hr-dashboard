import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import os
import requests

st.set_page_config(page_title="Teejay HR Dashboard", layout="wide")

# ================================
# 🎨 PREMIUM UI STYLING
# ================================

st.markdown("""
<style>
/* Background */
.stApp {
    background: linear-gradient(to right, #0f172a, #020617);
    color: white;
}

/* Header */
.header {
    padding: 20px;
    border-radius: 15px;
    background: linear-gradient(135deg, #2563eb, #1e3a8a);
    color: white;
    text-align: center;
    margin-bottom: 20px;
}

/* KPI Cards */
.card {
    background: rgba(255,255,255,0.05);
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.1);
}

/* Section Box */
.section {
    background: rgba(255,255,255,0.03);
    padding: 15px;
    border-radius: 15px;
    margin-top: 10px;
}

/* Sidebar */
.css-1d391kg {
    background-color: #020617;
}
</style>
""", unsafe_allow_html=True)

# ================================
# 🎯 HEADER
# ================================

st.markdown("""
<div class="header">
    <h1>🏢 Teejay India Pvt Ltd</h1>
    <p>Smart HR Analytics Dashboard</p>
</div>
""", unsafe_allow_html=True)

FILE_PATH = "employees_with_coords.xlsx"
GOOGLE_API_KEY = "https://maps.googleapis.com/maps/api/geocode/json?latlng=40.714224,-73.961452&key=YOUR_API_KEY"

# ================================
# 🔹 GOOGLE FUNCTION
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
# 🔹 LOAD DATA
# ================================

if os.path.exists(FILE_PATH):
    df = pd.read_excel(FILE_PATH)
else:
    df = pd.read_excel("employees.xlsx")
    df["lat"] = None
    df["lon"] = None


# ================================
# 🛠️ SIDEBAR (CLEAN)
# ================================

st.sidebar.title("⚙ Manage Employees")

action = st.sidebar.selectbox("Action", ["Add", "Edit", "Delete"])

# ➕ ADD
if action == "Add":
    with st.sidebar.form("add"):
        emp_id = st.text_input("Employee ID")
        name = st.text_input("Name")
        dept = st.text_input("Department")
        sub = st.text_input("Sub Section")
        addr = st.text_area("Address")

        if st.form_submit_button("Add"):
            lat, lon = get_lat_lon(addr)

            df = pd.concat([df, pd.DataFrame([{
                "Emp Id": emp_id,
                "Name": name,
                "Department": dept,
                "Sub Section": sub,
                "Address": addr,
                "lat": lat,
                "lon": lon
            }])])

            df.to_excel(FILE_PATH, index=False)
            st.success("Added")
            st.rerun()

# ✏️ EDIT
elif action == "Edit":
    emp = st.sidebar.selectbox("Select Employee", df["Name"])
    row = df[df["Name"] == emp].iloc[0]

    with st.sidebar.form("edit"):
        name = st.text_input("Name", row["Name"])
        dept = st.text_input("Dept", row["Department"])
        sub = st.text_input("Sub", row["Sub Section"])
        addr = st.text_area("Address", row["Address"])

        if st.form_submit_button("Update"):
            lat, lon = get_lat_lon(addr)

            df.loc[df["Name"] == emp,
                   ["Name","Department","Sub Section","Address","lat","lon"]] = [
                name, dept, sub, addr, lat, lon
            ]

            df.to_excel(FILE_PATH, index=False)
            st.success("Updated")
            st.rerun()

# ❌ DELETE
elif action == "Delete":
    emp = st.sidebar.selectbox("Delete Employee", df["Name"])
    if st.sidebar.button("Delete"):
        df = df[df["Name"] != emp]
        df.to_excel(FILE_PATH, index=False)
        st.success("Deleted")
        st.rerun()


# ================================
# 🔍 FILTERS
# ================================

st.sidebar.title("🔍 Filters")

dept = st.sidebar.selectbox("Department", ["All"] + list(df["Department"].dropna().unique()))
search = st.sidebar.text_input("Search")

filtered_df = df.copy()

if dept != "All":
    filtered_df = filtered_df[filtered_df["Department"] == dept]

if search:
    filtered_df = filtered_df[filtered_df["Name"].str.contains(search, case=False, na=False)]


# ================================
# 📊 KPI CARDS
# ================================

c1, c2, c3 = st.columns(3)

c1.markdown(f'<div class="card"><h3>{len(df)}</h3><p>Total Employees</p></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="card"><h3>{len(filtered_df)}</h3><p>Filtered</p></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="card"><h3>{df["Department"].nunique()}</h3><p>Departments</p></div>', unsafe_allow_html=True)


# ================================
# 🌍 MAP SECTION
# ================================

st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("🌍 Employee Map")

m = folium.Map(location=[17.6868, 83.2185], zoom_start=7)

from folium.plugins import MarkerCluster
cluster = MarkerCluster().add_to(m)

for _, row in filtered_df.iterrows():
    if pd.notna(row["lat"]):
        folium.Marker(
            [row["lat"], row["lon"]],
            popup=f"{row['Name']}<br>{row['Department']}"
        ).add_to(cluster)

st_folium(m, width="100%", height=750)
st.markdown('</div>', unsafe_allow_html=True)


# ================================
# 📋 TABLE
# ================================

st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("📋 Employee Directory")
st.dataframe(filtered_df, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)


# ================================
# 📊 GRAPH
# ================================

st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("📊 Department Insights")

dept_counts = df["Department"].value_counts().reset_index()
dept_counts.columns = ["Department","Count"]

fig = px.bar(
    dept_counts,
    x="Department",
    y="Count",
    color="Department",
    template="plotly_dark"
)

st.plotly_chart(fig, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)