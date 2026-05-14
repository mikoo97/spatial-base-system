# Methodology — Spatial Base System Indonesia

## Ringkasan

Pipeline ini membangun layer administrasi Indonesia standar dari GADM v4.1 sebagai sumber geometri utama, dengan kode wilayah BPS sebagai atribut tambahan melalui proses join.

---

## Keputusan Metodologi

### 1. Mengapa GADM sebagai sumber geometri utama?

GADM (Database of Global Administrative Areas) v4.1 dipilih karena:
- Geometri presisi tinggi — jauh lebih baik dibanding shapefile BPS yang sering punya self-intersection
- Konsistensi topologi antar level (provinsi → kabupaten → kecamatan tidak overlap)
- Update rutin dan terdokumentasi dengan baik
- Tersedia dalam format GeoPackage (satu file untuk semua level)

**Trade-off:** GADM tidak memiliki kode administrasi BPS, dan tidak boleh digunakan untuk keperluan komersial.

### 2. Mengapa kode BPS di-join secara terpisah?

Kode BPS adalah standar resmi Indonesia yang digunakan di semua data statistik (PDRB, sensus, program Dana Desa, dll). Tanpa kode BPS, layer ini tidak bisa di-join dengan data statistik apapun.

Join dilakukan berdasarkan kesamaan nama wilayah, dengan dua tahap:
1. **Exact match** — normalisasi nama (uppercase, hapus karakter khusus, standarisasi "KAB." vs "KABUPATEN")
2. **Manual review** — wilayah yang tidak ter-match dilog ke `docs/bps-join-unmatched.csv` untuk review manual

### 3. CRS (Coordinate Reference System)

Semua output disimpan dalam **EPSG:4326 (WGS84)** karena:
- Kompatibilitas universal dengan semua tools (QGIS, Leaflet, Folium, Power BI)
- Standard de facto untuk data web dan visualisasi

Untuk kalkulasi area, reprojeksi ke Web Mercator (EPSG:3857) dilakukan on-the-fly dan tidak disimpan.

### 4. Geometry Validation

Semua geometri divalidasi menggunakan `shapely.validation.make_valid()`. Geometri yang tidak bisa diperbaiki dan hasilnya empty/null dihapus dan dicatat.

---

## Keterbatasan yang Diketahui

1. **Pemekaran wilayah terbaru** — GADM v4.1 (2023) mungkin belum mencerminkan DOB (Daerah Otonomi Baru) yang disahkan setelah 2022. Verifikasi manual diperlukan untuk kabupaten/kecamatan yang baru dimekarkan.

2. **Batas kecamatan** — Presisi batas kecamatan lebih rendah dibanding provinsi/kabupaten karena sumber data yang lebih terbatas di level ini.

3. **Kepulauan kecil** — Beberapa pulau kecil di Indonesia mungkin tidak terwakili atau memiliki geometri yang disederhanakan.

---

## Reproducibility

Untuk mereproduksi seluruh pipeline dari awal:

```bash
conda env create -f environment.yml
conda activate sei-env
python src/download_gadm.py    # download ~120MB
python src/process_geodata.py  # proses semua level
```

Semua parameter dan versi library tercatat di `environment.yml`.

---

*Dokumen ini diperbarui setiap kali ada perubahan metodologi yang signifikan.*
