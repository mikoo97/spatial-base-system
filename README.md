# 🌐 Spatial Base System Indonesia

> Fondasi geodata dan utility library untuk analisis spasial-ekonomi Indonesia — bagian dari ekosistem [Spatial Economic Intelligence Indonesia](https://github.com/[username]/sei-ecosystem).

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![GeoPandas](https://img.shields.io/badge/GeoPandas-0.14-139C5A)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-FF4B4B?logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## Problem Statement

Analisis spasial Indonesia menghadapi satu masalah mendasar yang jarang diakui secara eksplisit: **tidak ada satu sumber geodata pun yang sempurna**. GADM memiliki geometri presisi tinggi tapi tidak punya kode BPS. Shapefile BPS memiliki kode resmi tapi geometrinya sering bermasalah. Ina-Geoportal lengkap tapi aksesnya tidak selalu konsisten.

Project ini membangun **pipeline yang transparan** — mendokumentasikan trade-off setiap sumber data, bukan menyembunyikannya — dan menghasilkan layer standar yang bisa dipakai ulang di semua project analisis spasial Indonesia.

## Komponen

```
spatial-base-system/
├── src/
│   ├── spatial_utils.py      ← Core library (load, validate, visualize, export)
│   ├── download_gadm.py      ← Download otomatis GADM v4.1 Indonesia
│   └── process_geodata.py    ← Pipeline lengkap: raw → processed
├── notebooks/
│   └── 01_eda.ipynb          ← Eksplorasi dan validasi hasil processing
├── data/spatial/processed/   ← Output: layer siap pakai (.gpkg)
├── assets/screenshots/       ← Visualisasi output
└── docs/
    ├── methodology.md        ← Keputusan metodologi + trade-off
    └── data-sources.md       ← Sumber data + lisensi
```

## Quick Start

```bash
# 1. Clone repo
git clone https://github.com/[username]/spatial-base-system.git
cd spatial-base-system

# 2. Setup environment
conda env create -f environment.yml
conda activate sei-env

# 3. Download geodata (~120MB)
python src/download_gadm.py

# 4. Jalankan pipeline processing
python src/process_geodata.py

# 5. Eksplorasi hasil di notebook
jupyter notebook notebooks/01_eda.ipynb

# 6. Jalankan Streamlit app
streamlit run app/app.py
```

## Live Demo

🔗 [Indonesia Base Map Explorer](https://[app-url].streamlit.app) *(tersedia setelah deployment)*

## Output yang Dihasilkan

| File | Level | Features | Format |
|------|-------|----------|--------|
| `idn_provinsi_2023_gadm.gpkg` | Provinsi | 34 | GeoPackage |
| `idn_kabupaten_2023_gadm.gpkg` | Kabupaten/Kota | ~514 | GeoPackage |
| `idn_kecamatan_2023_gadm.gpkg` | Kecamatan | ~7.000+ | GeoPackage |

## Methodology

**Sumber data utama:** GADM v4.1 (geometri) + kode BPS via join  
**CRS standar:** EPSG:4326 (WGS84) untuk semua output  
**Geometry validation:** Shapely `make_valid()` untuk semua invalid geometry  
Detail lengkap: [docs/methodology.md](docs/methodology.md)

## Key Findings

*(Diisi setelah EDA selesai)*

## Data Sources

| Sumber | URL | Lisensi | Tahun |
|--------|-----|---------|-------|
| GADM v4.1 | [gadm.org](https://gadm.org) | Non-commercial | 2023 |
| BPS Kode Wilayah | [sig.bps.go.id](https://sig.bps.go.id) | Terbuka | 2023 |

## Penggunaan sebagai Library

```python
# Import di project lain (P2–P6)
import sys
sys.path.insert(0, 'path/to/spatial-base-system/src')
from spatial_utils import load_indonesia_levels, quick_map

# Load semua layer
layers = load_indonesia_levels("path/to/data/spatial/processed/")

# Quick interactive map
m = quick_map(layers['provinsi'], title="Provinsi Indonesia")
m.save("output.html")
```

## Tech Stack

- **Python 3.11** — core language
- **GeoPandas 0.14** — spatial data processing
- **Shapely 2.0** — geometry operations
- **Folium** — interactive maps
- **Streamlit** — web app
- **QGIS** — visual validation

---

*Bagian dari [Spatial Economic Intelligence Indonesia](https://github.com/[username]/sei-ecosystem) ecosystem.*
