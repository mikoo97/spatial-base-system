# 🌐 Spatial Base System Indonesia

> Pipeline geodata dan interactive map explorer untuk analisis spasial-ekonomi Indonesia.
> Bagian dari ekosistem **Spatial Economic Intelligence Indonesia**.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![GeoPandas](https://img.shields.io/badge/GeoPandas-0.14-139C5A)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-FF4B4B?logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Problem Statement

Analisis spasial Indonesia menghadapi masalah mendasar: **tidak ada satu sumber geodata
yang sempurna**. GADM punya geometri presisi tinggi tapi tidak punya kode BPS. Shapefile
BPS punya kode resmi tapi geometrinya sering bermasalah.

Project ini membangun pipeline yang **transparan dan reproducible** — mendokumentasikan
trade-off setiap sumber data, bukan menyembunyikannya.

---
## Live Demo
🔗 [Indonesia Base Map Explorer](https://spatial-base-system-djchhbqwfuuaxisszefkwp.streamlit.app)

## Quick Start

```bash
# 1. Clone repo
git clone https://github.com/mikoo97/spatial-base-system.git
cd spatial-base-system

# 2. Setup environment
conda env create -f environment.yml
conda activate sei-env

# 3. Download geodata (~468MB)
python src/download_gadm.py

# 4. Jalankan pipeline processing
python src/process_geodata.py

# 5. Jalankan Streamlit app
streamlit run app/app.py
```

---

## Output

| Layer | Features | Invalid Geometry | CRS |
|-------|----------|-----------------|-----|
| Provinsi | 34 | 0 | EPSG:4326 |
| Kabupaten/Kota | 502 | 0 | EPSG:4326 |
| Kecamatan | 6.695 | 0 | EPSG:4326 |

---

## Key Findings

- **Total luas Indonesia:** 1,912,139 km² (dari 34 provinsi)
- **Provinsi terluas:** Papua — 318,295 km²
- **Kabupaten terkecil:** Sibolga, Sumatera Utara — 10.94 km²
- **Anomali data:** "Danau Limboto" dan "Waduk Kedungombo" masuk sebagai
  entitas kabupaten di GADM — badan air, bukan unit administrasi.
  Ini menunjukkan pentingnya validasi data sebelum analisis.

---

## Struktur Project
