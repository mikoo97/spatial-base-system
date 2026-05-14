import sys
sys.path.insert(0, '../src')

import streamlit as st
import geopandas as gpd
import pyogrio
gpd.options.io_engine = "pyogrio"
import folium
from streamlit_folium import folium_static
from pathlib import Path

st.set_page_config(
    page_title="Indonesia Base Map Explorer",
    page_icon="🗺️",
    layout="wide"
)

DATA_DIR = Path("data/spatial/processed")

@st.cache_data
def load_layer(level):
    files = {
        "Provinsi"  : "idn_provinsi_2023_gadm.gpkg",
        "Kabupaten" : "idn_kabupaten_2023_gadm.gpkg",
        "Kecamatan" : "idn_kecamatan_2023_gadm.gpkg",
    }
    return gpd.read_file(DATA_DIR / files[level])

# Sidebar
st.sidebar.title("🗺️ Indonesia Base Map")
st.sidebar.markdown("**Spatial Economic Intelligence Indonesia**")
st.sidebar.divider()
level = st.sidebar.selectbox("Pilih Level Administrasi", ["Provinsi", "Kabupaten", "Kecamatan"])
st.sidebar.divider()
st.sidebar.markdown("### Tentang")
st.sidebar.markdown("Peta dasar administrasi Indonesia berbasis GADM v4.1.")

# Main
st.title("🗺️ Indonesia Base Map Explorer")
st.markdown(f"Menampilkan: **{level}** | Sumber: GADM v4.1")

with st.spinner(f"Memuat data {level}..."):
    gdf = load_layer(level)

name_col = {"Provinsi": "nama_prov", "Kabupaten": "nama_kab", "Kecamatan": "nama_kec"}[level]

# Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric(f"Total {level}", f"{len(gdf):,}")
col2.metric("Total Area (km²)", f"{gdf['area_km2'].sum():,.0f}")
col3.metric("Terluas (km²)", f"{gdf['area_km2'].max():,.0f}")
col4.metric("Terkecil (km²)", f"{gdf['area_km2'].min():,.2f}")

st.divider()

# Peta — full width
st.subheader("🗺️ Peta Interaktif")

m = folium.Map(location=[-2.5, 118], zoom_start=5, tiles="CartoDB positron")

tooltip_fields = [name_col, "area_km2"]
tooltip_aliases = ["Nama", "Luas (km²)"]
if level == "Kabupaten":
    tooltip_fields = ["nama_kab", "nama_prov", "area_km2"]
    tooltip_aliases = ["Kabupaten", "Provinsi", "Luas (km²)"]
elif level == "Kecamatan":
    tooltip_fields = ["nama_kec", "nama_kab", "area_km2"]
    tooltip_aliases = ["Kecamatan", "Kabupaten", "Luas (km²)"]

folium.GeoJson(
    gdf,
    style_function=lambda x: {
        "fillColor": "#2196F3",
        "color": "#ffffff",
        "weight": 0.8,
        "fillOpacity": 0.5,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=tooltip_fields,
        aliases=tooltip_aliases,
        sticky=True,
    ),
).add_to(m)

folium_static(m, width=1100, height=550)

st.divider()

# Tabel di bawah peta
st.subheader(f"📋 Data {level}")
display_cols = [name_col, "area_km2"]
if level == "Kabupaten":
    display_cols = ["nama_kab", "nama_prov", "area_km2"]
elif level == "Kecamatan":
    display_cols = ["nama_kec", "nama_kab", "area_km2"]

search = st.text_input("🔍 Cari wilayah...")
df = gdf[display_cols].copy()
if search:
    df = df[df[name_col].str.contains(search, case=False, na=False)]

st.dataframe(df.sort_values("area_km2", ascending=False), use_container_width=True, height=400)

csv = gdf[display_cols].to_csv(index=False)
st.download_button(
    label=f"⬇️ Download data {level} (CSV)",
    data=csv,
    file_name=f"idn_{level.lower()}_data.csv",
    mime="text/csv"
)