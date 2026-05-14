# Data Sources — Spatial Base System Indonesia

| Nama | URL | Lisensi | Tahun | Level | Format | Catatan |
|------|-----|---------|-------|-------|--------|---------|
| GADM v4.1 | https://gadm.org/download_country.html | Non-commercial | 2023 | Provinsi, Kab/Kota, Kec | GPKG / SHP | Geometri presisi tinggi — gunakan sebagai base geometri |
| BPS Kode Wilayah | https://sig.bps.go.id/bridging-kode/index | Terbuka | 2023 | Semua level | XLSX/CSV | Kode resmi BPS — join ke GADM |
| Ina-Geoportal BIG | https://tanahair.indonesia.go.id/portal-web | Terbuka | 2023 | Semua level | SHP | Alternatif jika butuh kode BPS di geodata langsung |
| OpenStreetMap ID | https://download.geofabrik.de/asia/indonesia.html | ODbL | Harian | Jalan, POI | PBF/SHP | Bukan untuk batas admin — untuk network analysis |

## Keputusan Metodologi

**Mengapa GADM sebagai base geometri?**
GADM v4.1 adalah sumber data batas administrasi dengan kualitas geometri terbaik yang tersedia secara gratis untuk Indonesia. Akurasi batas lebih tinggi dibanding shapefile BPS yang sering memiliki self-intersection dan gap antar poligon.

**Mengapa join kode BPS secara terpisah?**
GADM tidak menyimpan kode administrasi BPS (kode_prov, kode_kab, kode_kec). Kode BPS adalah standar resmi Indonesia dan diperlukan untuk join dengan data statistik apapun dari BPS. Proses join ini didokumentasikan secara eksplisit untuk transparansi metodologi.

**Limitasi yang diketahui**
- GADM tidak boleh digunakan untuk keperluan komersial
- Batas kecamatan di GADM mungkin tidak mencerminkan pemekaran wilayah terbaru (post-2022)
- Kode BPS perlu divalidasi manual untuk wilayah-wilayah yang mengalami pemekaran
