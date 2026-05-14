"""
spatial_utils.py
================
Core spatial utility library untuk Spatial Economic Intelligence Indonesia.
Dipakai oleh semua project (P1–P6).

Author  : [Namamu]
Version : 1.0.0
Updated : 2025-05
"""

import os
import json
import warnings
from pathlib import Path
from typing import Optional, Union, Dict, Tuple

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import folium
from shapely.validation import make_valid
from tqdm import tqdm

warnings.filterwarnings("ignore", category=UserWarning)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

CRS_WGS84   = "EPSG:4326"   # Lon/Lat — default untuk output dan visualisasi
CRS_WEBMERC = "EPSG:3857"   # Web Mercator — untuk tile maps
CRS_UTM49S  = "EPSG:32749"  # UTM Zone 49S — untuk area calculation (Jawa-Bali)
CRS_UTM47N  = "EPSG:32647"  # UTM Zone 47N — untuk area calculation (Sumatera barat)

# Bounding box seluruh Indonesia (lon_min, lat_min, lon_max, lat_max)
INDONESIA_BBOX = (94.97, -11.01, 141.02, 6.08)

# Nama kolom standar setelah normalisasi
STD_COLS = {
    "provinsi" : ["NAME_1", "PROVINSI", "nama_prov",  "province"],
    "kabupaten": ["NAME_2", "KAB_KOTA",  "nama_kab",  "district"],
    "kecamatan": ["NAME_3", "KECAMATAN", "nama_kec",  "subdistrict"],
    "desa"     : ["NAME_4", "DESA",      "nama_desa", "village"],
}

# ─────────────────────────────────────────────────────────────────────────────
# 1. DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

def load_geodata(
    filepath: Union[str, Path],
    target_crs: str = CRS_WGS84,
    fix_geometry: bool = True,
    layer: Optional[str] = None,
) -> gpd.GeoDataFrame:
    """
    Load geodata dari file ke GeoDataFrame yang sudah divalidasi.

    Parameters
    ----------
    filepath    : path ke file (.gpkg, .shp, .geojson, .parquet)
    target_crs  : CRS target, default EPSG:4326
    fix_geometry: otomatis perbaiki invalid geometries
    layer       : nama layer untuk file GPKG multi-layer

    Returns
    -------
    GeoDataFrame yang sudah divalidasi dan di-reproject

    Example
    -------
    >>> gdf = load_geodata("data/spatial/processed/idn_provinsi_2023_gadm.gpkg")
    >>> print(gdf.crs, len(gdf))
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {filepath}")

    # Load berdasarkan ekstensi
    ext = filepath.suffix.lower()
    if ext in (".gpkg", ".gdb"):
        gdf = gpd.read_file(filepath, layer=layer) if layer else gpd.read_file(filepath)
    elif ext in (".shp", ".geojson", ".json"):
        gdf = gpd.read_file(filepath)
    elif ext == ".parquet":
        gdf = gpd.read_parquet(filepath)
    else:
        raise ValueError(f"Format tidak didukung: {ext}")

    # CRS handling
    if gdf.crs is None:
        warnings.warn(f"CRS tidak ditemukan di {filepath.name}. Diasumsikan {CRS_WGS84}.")
        gdf = gdf.set_crs(CRS_WGS84)
    elif gdf.crs.to_epsg() != int(target_crs.split(":")[1]):
        gdf = gdf.to_crs(target_crs)

    # Geometry fix
    if fix_geometry:
        gdf = fix_invalid_geometries(gdf)

    return gdf


def load_indonesia_levels(
    data_dir: Union[str, Path],
    levels: list = ["provinsi", "kabupaten", "kecamatan"],
) -> Dict[str, gpd.GeoDataFrame]:
    """
    Load semua level administrasi Indonesia sekaligus.

    Parameters
    ----------
    data_dir : direktori yang berisi file geodata (spatial/processed/)
    levels   : list level yang ingin diload

    Returns
    -------
    dict dengan key = level name, value = GeoDataFrame

    Example
    -------
    >>> layers = load_indonesia_levels("data/spatial/processed/")
    >>> layers["provinsi"].head()
    """
    data_dir = Path(data_dir)
    result = {}

    # Pattern nama file standar: idn_[level]_[tahun]_[sumber].gpkg
    patterns = {
        "provinsi" : "idn_provinsi_*.gpkg",
        "kabupaten": "idn_kabupaten_*.gpkg",
        "kecamatan": "idn_kecamatan_*.gpkg",
        "desa"     : "idn_desa_*.gpkg",
    }

    for level in levels:
        if level not in patterns:
            warnings.warn(f"Level '{level}' tidak dikenal, dilewati.")
            continue

        matches = list(data_dir.glob(patterns[level]))
        if not matches:
            warnings.warn(f"File untuk level '{level}' tidak ditemukan di {data_dir}")
            continue

        # Ambil file terbaru jika ada lebih dari satu
        filepath = sorted(matches)[-1]
        print(f"Loading {level}: {filepath.name} ...", end=" ")
        gdf = load_geodata(filepath)
        result[level] = gdf
        print(f"✓ ({len(gdf)} features)")

    return result


# ─────────────────────────────────────────────────────────────────────────────
# 2. GEOMETRY VALIDATION & CLEANING
# ─────────────────────────────────────────────────────────────────────────────

def fix_invalid_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Perbaiki invalid geometries menggunakan shapely make_valid.
    Hapus geometry yang kosong (None/empty) setelah fixing.

    Returns GeoDataFrame yang sudah bersih.
    """
    n_invalid = (~gdf.geometry.is_valid).sum()

    if n_invalid > 0:
        print(f"  → Fixing {n_invalid} invalid geometries...")
        gdf = gdf.copy()
        gdf["geometry"] = gdf["geometry"].apply(
            lambda geom: make_valid(geom) if geom is not None and not geom.is_valid else geom
        )

    # Hapus empty/null geometries
    n_empty = gdf.geometry.is_empty.sum() + gdf.geometry.isna().sum()
    if n_empty > 0:
        print(f"  → Dropping {n_empty} empty/null geometries...")
        gdf = gdf[~(gdf.geometry.is_empty | gdf.geometry.isna())].copy()

    return gdf


def validate_geodata(gdf: gpd.GeoDataFrame, level: str = "") -> dict:
    """
    Validasi komprehensif GeoDataFrame. Return laporan sebagai dict.

    Example
    -------
    >>> report = validate_geodata(gdf, level="kabupaten")
    >>> print(report)
    """
    report = {
        "level"           : level,
        "total_features"  : len(gdf),
        "crs"             : str(gdf.crs),
        "geometry_types"  : gdf.geometry.geom_type.value_counts().to_dict(),
        "invalid_geom"    : int((~gdf.geometry.is_valid).sum()),
        "null_geom"       : int(gdf.geometry.isna().sum()),
        "empty_geom"      : int(gdf.geometry.is_empty.sum()),
        "bbox"            : gdf.total_bounds.tolist(),
        "columns"         : list(gdf.columns),
        "null_per_column" : gdf.isnull().sum().to_dict(),
    }

    # Cek apakah ada duplikat nama (warning saja, tidak error)
    for col_candidates in STD_COLS.get(level, []):
        if col_candidates in gdf.columns:
            n_dup = gdf[col_candidates].duplicated().sum()
            report["duplicate_names"] = int(n_dup)
            break

    return report


def print_validation_report(report: dict):
    """Pretty-print laporan validasi."""
    print(f"\n{'─'*50}")
    print(f"  VALIDATION REPORT: {report.get('level', 'Unknown').upper()}")
    print(f"{'─'*50}")
    print(f"  Total features   : {report['total_features']:,}")
    print(f"  CRS              : {report['crs']}")
    print(f"  Geometry types   : {report['geometry_types']}")
    print(f"  Invalid geom     : {report['invalid_geom']}")
    print(f"  Null geom        : {report['null_geom']}")
    print(f"  Bounding box     : {[round(x,2) for x in report['bbox']]}")
    if "duplicate_names" in report:
        print(f"  Duplicate names  : {report['duplicate_names']}")
    print(f"{'─'*50}\n")


# ─────────────────────────────────────────────────────────────────────────────
# 3. COLUMN NORMALIZATION
# ─────────────────────────────────────────────────────────────────────────────

def normalize_columns(
    gdf: gpd.GeoDataFrame,
    level: str,
    rename_map: Optional[Dict[str, str]] = None,
) -> gpd.GeoDataFrame:
    """
    Normalisasi nama kolom ke standar SEI.

    Kolom standar hasil normalisasi:
    - provinsi  → nama_prov, kode_prov
    - kabupaten → nama_kab,  kode_kab,  nama_prov, kode_prov
    - kecamatan → nama_kec,  kode_kec,  nama_kab,  kode_kab,  nama_prov, kode_prov

    Parameters
    ----------
    gdf        : GeoDataFrame input
    level      : 'provinsi', 'kabupaten', atau 'kecamatan'
    rename_map : dict custom {col_lama: col_baru} — override deteksi otomatis
    """
    gdf = gdf.copy()

    # Auto-detect nama kolom jika tidak ada rename_map
    if rename_map is None:
        rename_map = {}
        cols_upper = {c.upper(): c for c in gdf.columns}

        if level == "provinsi":
            for candidate in STD_COLS["provinsi"]:
                if candidate.upper() in cols_upper:
                    rename_map[cols_upper[candidate.upper()]] = "nama_prov"
                    break

        elif level == "kabupaten":
            for candidate in STD_COLS["provinsi"]:
                if candidate.upper() in cols_upper:
                    rename_map[cols_upper[candidate.upper()]] = "nama_prov"
                    break
            for candidate in STD_COLS["kabupaten"]:
                if candidate.upper() in cols_upper:
                    rename_map[cols_upper[candidate.upper()]] = "nama_kab"
                    break

        elif level == "kecamatan":
            for level_key, std_col in [
                ("provinsi", "nama_prov"),
                ("kabupaten", "nama_kab"),
                ("kecamatan", "nama_kec"),
            ]:
                for candidate in STD_COLS[level_key]:
                    if candidate.upper() in cols_upper:
                        rename_map[cols_upper[candidate.upper()]] = std_col
                        break

    gdf = gdf.rename(columns=rename_map)

    # Title case nama wilayah
    for col in ["nama_prov", "nama_kab", "nama_kec", "nama_desa"]:
        if col in gdf.columns:
            gdf[col] = gdf[col].str.title().str.strip()

    return gdf


# ─────────────────────────────────────────────────────────────────────────────
# 4. GADM PROCESSING — Pipeline utama P1
# ─────────────────────────────────────────────────────────────────────────────

def process_gadm_indonesia(
    gadm_gpkg_path: Union[str, Path],
    output_dir: Union[str, Path],
    levels: list = [1, 2, 3],
) -> Dict[str, gpd.GeoDataFrame]:
    """
    Proses file GADM Indonesia (gadm41_IDN.gpkg) menjadi layer standar SEI.

    GADM level mapping:
    - Level 0 → Indonesia (national boundary)
    - Level 1 → Provinsi
    - Level 2 → Kabupaten/Kota
    - Level 3 → Kecamatan

    Parameters
    ----------
    gadm_gpkg_path : path ke file gadm41_IDN.gpkg
    output_dir     : direktori output (data/spatial/processed/)
    levels         : GADM levels yang diproses, default [1, 2, 3]

    Returns
    -------
    dict {level_name: GeoDataFrame}

    Example
    -------
    >>> layers = process_gadm_indonesia(
    ...     "data/spatial/raw/gadm41_IDN.gpkg",
    ...     "data/spatial/processed/"
    ... )
    """
    gadm_path = Path(gadm_gpkg_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    level_names = {0: "nasional", 1: "provinsi", 2: "kabupaten", 3: "kecamatan"}
    output_files = {
        1: "idn_provinsi_2023_gadm.gpkg",
        2: "idn_kabupaten_2023_gadm.gpkg",
        3: "idn_kecamatan_2023_gadm.gpkg",
    }

    results = {}

    for lvl in levels:
        layer_name = f"ADM_ADM_{lvl}"
        level_label = level_names.get(lvl, f"level{lvl}")

        print(f"\n{'='*55}")
        print(f"  Processing GADM Level {lvl} — {level_label.upper()}")
        print(f"{'='*55}")

        # Load layer dari GPKG
        print(f"  Loading layer '{layer_name}'...")
        try:
            gdf = gpd.read_file(gadm_path, layer=layer_name)
        except Exception as e:
            print(f"  ✗ Gagal load layer {layer_name}: {e}")
            continue

        print(f"  ✓ Loaded: {len(gdf):,} features")

        # Reproject ke WGS84
        if gdf.crs is None:
            gdf = gdf.set_crs(CRS_WGS84)
        elif gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(CRS_WGS84)
            print(f"  ✓ Reprojected ke WGS84")

        # Fix geometri
        n_invalid = (~gdf.geometry.is_valid).sum()
        if n_invalid > 0:
            print(f"  → Fixing {n_invalid} invalid geometries...")
            gdf["geometry"] = gdf["geometry"].apply(
                lambda g: make_valid(g) if g is not None and not g.is_valid else g
            )

        # Pilih dan rename kolom standar berdasarkan level
        col_mapping = _get_gadm_column_mapping(lvl)
        cols_to_keep = [c for c in col_mapping.keys() if c in gdf.columns] + ["geometry"]
        gdf = gdf[cols_to_keep].rename(columns=col_mapping)

        # Tambah kolom area (dalam km²)
        gdf_proj = gdf.to_crs(CRS_WEBMERC)
        gdf["area_km2"] = (gdf_proj.geometry.area / 1e6).round(2)

        # Simpan ke GPKG
        if lvl in output_files:
            out_path = output_dir / output_files[lvl]
            gdf.to_file(out_path, driver="GPKG")
            print(f"  ✓ Saved: {out_path.name}")

        # Validasi akhir
        report = validate_geodata(gdf, level=level_label)
        print_validation_report(report)

        results[level_label] = gdf

    print("\n✅ GADM processing selesai!\n")
    return results


def _get_gadm_column_mapping(gadm_level: int) -> dict:
    """Return mapping kolom GADM → nama standar SEI."""
    if gadm_level == 1:
        return {
            "GID_1"  : "gid_prov",
            "NAME_1" : "nama_prov",
            "VARNAME_1": "nama_alt_prov",
            "TYPE_1" : "tipe_admin",
            "CC_1"   : "kode_iso_prov",
        }
    elif gadm_level == 2:
        return {
            "GID_1"  : "gid_prov",
            "GID_2"  : "gid_kab",
            "NAME_1" : "nama_prov",
            "NAME_2" : "nama_kab",
            "VARNAME_2": "nama_alt_kab",
            "TYPE_2" : "tipe_admin",
            "CC_2"   : "kode_iso_kab",
        }
    elif gadm_level == 3:
        return {
            "GID_1"  : "gid_prov",
            "GID_2"  : "gid_kab",
            "GID_3"  : "gid_kec",
            "NAME_1" : "nama_prov",
            "NAME_2" : "nama_kab",
            "NAME_3" : "nama_kec",
            "TYPE_3" : "tipe_admin",
        }
    return {}


# ─────────────────────────────────────────────────────────────────────────────
# 5. BPS CODE JOINING
# ─────────────────────────────────────────────────────────────────────────────

def join_bps_codes(
    gdf: gpd.GeoDataFrame,
    bps_csv_path: Union[str, Path],
    level: str,
    fuzzy_threshold: float = 0.85,
) -> gpd.GeoDataFrame:
    """
    Join kode BPS ke GeoDataFrame GADM berdasarkan nama wilayah.

    Strategi join (berurutan):
    1. Exact match (nama identik setelah normalisasi)
    2. Fuzzy match (untuk perbedaan ejaan minor)

    Parameters
    ----------
    gdf              : GeoDataFrame (output dari process_gadm_indonesia)
    bps_csv_path     : path ke file CSV kode BPS dari BPS
    level            : 'provinsi', 'kabupaten', atau 'kecamatan'
    fuzzy_threshold  : threshold similarity untuk fuzzy match (0–1)

    Returns
    -------
    GeoDataFrame dengan kolom kode BPS ditambahkan

    Notes
    -----
    File CSV BPS harus punya kolom:
    - 'nama' : nama wilayah
    - 'kode' : kode BPS (format string, e.g., '35', '3508', '350801')
    """
    bps_df = pd.read_csv(bps_csv_path, dtype={"kode": str})

    # Normalisasi nama untuk matching
    def normalize_name(name: str) -> str:
        if pd.isna(name):
            return ""
        return (
            name.upper()
            .strip()
            .replace("KABUPATEN ", "KAB. ")
            .replace("KOTA ADMINISTRATIF", "KOTA")
            .replace("KEPULAUAN", "KEP.")
        )

    # Pilih kolom nama yang tepat berdasarkan level
    name_col_map = {
        "provinsi" : "nama_prov",
        "kabupaten": "nama_kab",
        "kecamatan": "nama_kec",
    }
    name_col = name_col_map.get(level)
    if name_col not in gdf.columns:
        raise ValueError(f"Kolom '{name_col}' tidak ditemukan. Jalankan normalize_columns() dulu.")

    gdf = gdf.copy()
    gdf["_nama_norm"] = gdf[name_col].apply(normalize_name)
    bps_df["_nama_norm"] = bps_df["nama"].apply(normalize_name)

    # Exact match
    code_col = f"kode_bps_{level[:3]}"  # kode_bps_pro / kode_bps_kab / kode_bps_kec
    exact_map = bps_df.set_index("_nama_norm")["kode"].to_dict()
    gdf[code_col] = gdf["_nama_norm"].map(exact_map)

    n_matched = gdf[code_col].notna().sum()
    n_total   = len(gdf)
    n_unmatched = n_total - n_matched

    print(f"\n  BPS Code Join — {level.upper()}")
    print(f"  Exact match : {n_matched}/{n_total} ({n_matched/n_total*100:.1f}%)")

    if n_unmatched > 0:
        print(f"  Unmatched   : {n_unmatched} features")
        unmatched_names = gdf.loc[gdf[code_col].isna(), name_col].tolist()
        print(f"  → {unmatched_names[:10]}{'...' if len(unmatched_names) > 10 else ''}")
        print(f"  ⚠ Review unmatched di docs/bps-join-log.md")

    # Simpan log unmatched untuk review manual
    if n_unmatched > 0:
        log_df = gdf.loc[gdf[code_col].isna(), [name_col, "_nama_norm"]].copy()
        log_df.columns = ["nama_gadm", "nama_norm"]
        log_path = Path("docs") / "bps-join-unmatched.csv"
        log_df.to_csv(log_path, index=False)
        print(f"  → Log disimpan ke {log_path}")

    # Hapus kolom helper
    gdf = gdf.drop(columns=["_nama_norm"])

    return gdf


# ─────────────────────────────────────────────────────────────────────────────
# 6. VISUALIZATION
# ─────────────────────────────────────────────────────────────────────────────

def quick_map(
    gdf: gpd.GeoDataFrame,
    column: Optional[str] = None,
    title: str = "",
    tooltip_cols: Optional[list] = None,
    cmap: str = "YlOrRd",
    zoom_start: int = 5,
) -> folium.Map:
    """
    Buat interactive Folium map dari GeoDataFrame.

    Parameters
    ----------
    gdf          : GeoDataFrame (harus dalam EPSG:4326)
    column       : kolom untuk choropleth coloring (opsional)
    title        : judul map
    tooltip_cols : kolom yang muncul saat hover
    cmap         : matplotlib colormap name
    zoom_start   : zoom level awal

    Returns
    -------
    folium.Map yang bisa di-display di Jupyter atau Streamlit

    Example
    -------
    >>> m = quick_map(provinsi_gdf, column="area_km2", title="Luas Provinsi Indonesia")
    >>> m.save("assets/screenshots/provinsi_area.html")
    """
    # Center map di centroid Indonesia
    center_lat = (gdf.geometry.bounds["miny"].min() + gdf.geometry.bounds["maxy"].max()) / 2
    center_lon = (gdf.geometry.bounds["minx"].min() + gdf.geometry.bounds["maxx"].max()) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles="CartoDB positron",
    )

    # Tentukan tooltip fields
    if tooltip_cols is None:
        tooltip_cols = [c for c in ["nama_prov", "nama_kab", "nama_kec", "area_km2"] if c in gdf.columns]

    if column and column in gdf.columns:
        # Choropleth
        folium.Choropleth(
            geo_data=gdf.__geo_interface__,
            data=gdf,
            columns=[gdf.index.name or gdf.index.astype(str), column]
            if gdf.index.name
            else [gdf.reset_index().columns[0], column],
            key_on="feature.id",
            fill_color=cmap,
            fill_opacity=0.7,
            line_opacity=0.3,
            legend_name=column,
            name=column,
        ).add_to(m)
    else:
        # Simple boundary
        folium.GeoJson(
            gdf,
            style_function=lambda x: {
                "fillColor": "#3388ff",
                "color": "#ffffff",
                "weight": 0.8,
                "fillOpacity": 0.5,
            },
            tooltip=folium.GeoJsonTooltip(
                fields=tooltip_cols,
                aliases=[c.replace("_", " ").title() for c in tooltip_cols],
                sticky=True,
            ),
        ).add_to(m)

    if title:
        title_html = f"""
        <div style="position:fixed; top:10px; left:50%; transform:translateX(-50%);
             z-index:1000; background:white; padding:8px 16px; border-radius:4px;
             box-shadow:0 2px 8px rgba(0,0,0,0.2); font-family:sans-serif;
             font-size:14px; font-weight:600;">
            {title}
        </div>"""
        m.get_root().html.add_child(folium.Element(title_html))

    folium.LayerControl().add_to(m)
    return m


def plot_indonesia(
    gdf: gpd.GeoDataFrame,
    column: Optional[str] = None,
    title: str = "Indonesia",
    figsize: Tuple = (16, 8),
    cmap: str = "YlOrRd",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Static matplotlib plot untuk quick visual check atau export.

    Example
    -------
    >>> fig = plot_indonesia(provinsi_gdf, title="Provinsi Indonesia")
    >>> fig.savefig("assets/screenshots/provinsi.png", dpi=150, bbox_inches="tight")
    """
    fig, ax = plt.subplots(figsize=figsize, facecolor="#f8f9fa")
    ax.set_facecolor("#d0e8f1")

    if column and column in gdf.columns:
        gdf.plot(
            column=column, ax=ax, cmap=cmap,
            legend=True, legend_kwds={"shrink": 0.6},
            missing_kwds={"color": "#cccccc", "label": "No data"},
            edgecolor="white", linewidth=0.3,
        )
    else:
        gdf.plot(ax=ax, color="#4a90d9", edgecolor="white", linewidth=0.3)

    ax.set_title(title, fontsize=16, fontweight="bold", pad=15)
    ax.set_xlabel("Longitude", fontsize=9)
    ax.set_ylabel("Latitude", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(True, alpha=0.3, linestyle="--")

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"  ✓ Saved: {save_path}")

    return fig


# ─────────────────────────────────────────────────────────────────────────────
# 7. EXPORT
# ─────────────────────────────────────────────────────────────────────────────

def save_geodata(
    gdf: gpd.GeoDataFrame,
    output_dir: Union[str, Path],
    filename: str,
    formats: list = ["gpkg", "geojson"],
) -> dict:
    """
    Simpan GeoDataFrame ke satu atau beberapa format sekaligus.

    Parameters
    ----------
    gdf        : GeoDataFrame yang akan disimpan
    output_dir : direktori output
    filename   : nama file TANPA ekstensi
    formats    : list format: 'gpkg', 'geojson', 'parquet', 'csv' (tanpa geometri)

    Returns
    -------
    dict {format: filepath}

    Example
    -------
    >>> paths = save_geodata(gdf, "data/spatial/processed/", "idn_provinsi_2023_gadm",
    ...                      formats=["gpkg", "geojson"])
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    saved = {}

    format_drivers = {
        "gpkg"   : ("GPKG",    ".gpkg"),
        "geojson": ("GeoJSON", ".geojson"),
        "shp"    : ("ESRI Shapefile", ".shp"),
    }

    for fmt in formats:
        if fmt == "parquet":
            path = output_dir / f"{filename}.parquet"
            gdf.to_parquet(path)
            saved["parquet"] = str(path)
            print(f"  ✓ Saved {fmt}: {path.name}")
        elif fmt == "csv":
            path = output_dir / f"{filename}.csv"
            gdf.drop(columns="geometry").to_csv(path, index=False)
            saved["csv"] = str(path)
            print(f"  ✓ Saved {fmt}: {path.name}")
        elif fmt in format_drivers:
            driver, ext = format_drivers[fmt]
            path = output_dir / f"{filename}{ext}"
            gdf.to_file(path, driver=driver)
            saved[fmt] = str(path)
            print(f"  ✓ Saved {fmt}: {path.name}")
        else:
            warnings.warn(f"Format tidak dikenal: {fmt}")

    return saved


# ─────────────────────────────────────────────────────────────────────────────
# 8. UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def clip_to_province(
    gdf: gpd.GeoDataFrame,
    provinsi_gdf: gpd.GeoDataFrame,
    province_name: str,
    name_col: str = "nama_prov",
) -> gpd.GeoDataFrame:
    """
    Clip GeoDataFrame ke batas satu provinsi.

    Example
    -------
    >>> jatim = clip_to_province(kabupaten_gdf, provinsi_gdf, "Jawa Timur")
    """
    mask = provinsi_gdf[provinsi_gdf[name_col].str.lower() == province_name.lower()]
    if len(mask) == 0:
        raise ValueError(f"Provinsi '{province_name}' tidak ditemukan. "
                         f"Cek nama: {provinsi_gdf[name_col].tolist()}")
    return gpd.clip(gdf, mask)


def get_indonesia_summary(layers: Dict[str, gpd.GeoDataFrame]) -> pd.DataFrame:
    """
    Buat summary table semua layer yang diload.

    Example
    -------
    >>> summary = get_indonesia_summary(layers)
    >>> print(summary.to_markdown())
    """
    rows = []
    for level, gdf in layers.items():
        rows.append({
            "Level"       : level,
            "Features"    : len(gdf),
            "CRS"         : str(gdf.crs.to_epsg()),
            "Columns"     : len(gdf.columns),
            "Invalid Geom": int((~gdf.geometry.is_valid).sum()),
            "Has Area"    : "area_km2" in gdf.columns,
        })
    return pd.DataFrame(rows)
