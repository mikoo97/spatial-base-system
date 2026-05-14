"""
download_gadm.py
================
Script untuk download dan ekstrak GADM v4.1 Indonesia.

Cara pakai:
    python src/download_gadm.py

Output:
    data/spatial/raw/gadm41_IDN.gpkg
"""

import os
import sys
import zipfile
import hashlib
import requests
from pathlib import Path
from tqdm import tqdm

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

# GADM v4.1 Indonesia — file GPKG (semua level dalam 1 file, ~120MB)
GADM_URL      = "https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_IDN.gpkg"
GADM_ZIP_URL  = "https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_IDN_shp.zip"

RAW_DIR       = Path("data/spatial/raw")
OUTPUT_GPKG   = RAW_DIR / "gadm41_IDN.gpkg"
OUTPUT_ZIP    = RAW_DIR / "gadm41_IDN_shp.zip"

# ─────────────────────────────────────────────────────────────────────────────
# FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def download_file(url: str, dest: Path, chunk_size: int = 8192) -> Path:
    """
    Download file dengan progress bar.
    Skip download jika file sudah ada.
    """
    if dest.exists():
        print(f"  ✓ File sudah ada: {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
        return dest

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print(f"  Downloading: {url}")
    print(f"  → Destination: {dest}")

    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))

        with open(dest, "wb") as f, tqdm(
            desc=dest.name,
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=chunk_size):
                f.write(chunk)
                pbar.update(len(chunk))

        print(f"  ✓ Download selesai: {dest.stat().st_size / 1e6:.1f} MB")
        return dest

    except requests.exceptions.ConnectionError:
        print(f"  ✗ Koneksi gagal. Coba download manual dari:")
        print(f"    {url}")
        print(f"    Simpan ke: {dest}")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"  ✗ HTTP Error: {e}")
        print(f"    Coba download manual dari: {url}")
        sys.exit(1)


def extract_shp_zip(zip_path: Path, extract_dir: Path) -> list:
    """
    Ekstrak shapefile ZIP GADM.
    Return list path file yang diekstrak.
    """
    print(f"\n  Extracting {zip_path.name}...")
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        files = zf.namelist()
        zf.extractall(extract_dir)

    shp_files = [extract_dir / f for f in files if f.endswith(".shp")]
    print(f"  ✓ Extracted {len(files)} files, {len(shp_files)} shapefiles")
    return shp_files


def verify_gpkg(gpkg_path: Path) -> bool:
    """
    Verifikasi file GPKG bisa dibuka dan punya layer yang diharapkan.
    """
    try:
        import fiona
        layers = fiona.listlayers(str(gpkg_path))
        expected = ["ADM_ADM_0", "ADM_ADM_1", "ADM_ADM_2", "ADM_ADM_3"]
        found = [l for l in expected if l in layers]
        print(f"\n  GPKG Verification:")
        print(f"  Layers found: {layers}")
        print(f"  Expected layers present: {len(found)}/{len(expected)}")
        return len(found) == len(expected)
    except Exception as e:
        print(f"  ✗ Verifikasi gagal: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  GADM v4.1 Indonesia — Downloader")
    print("=" * 60)
    print()

    # Opsi 1: Download GPKG langsung (semua level, ~120MB)
    print("Opsi download:")
    print("  1. GPKG (semua level dalam 1 file) — DIREKOMENDASIKAN")
    print("  2. Shapefile ZIP (terpisah per level)")
    print()

    # Cek apakah sudah ada
    if OUTPUT_GPKG.exists():
        size_mb = OUTPUT_GPKG.stat().st_size / 1e6
        print(f"✓ GADM GPKG sudah ada: {OUTPUT_GPKG}")
        print(f"  Size: {size_mb:.1f} MB")
        if verify_gpkg(OUTPUT_GPKG):
            print("\n✅ File valid dan siap digunakan!")
            print(f"\nLangkah berikutnya:")
            print(f"  python src/process_geodata.py")
        return

    print(f"  Target file: {OUTPUT_GPKG}")
    print(f"  Estimasi ukuran: ~120–150 MB")
    print()

    # Download
    download_file(GADM_URL, OUTPUT_GPKG)

    # Verifikasi
    print()
    if verify_gpkg(OUTPUT_GPKG):
        print("\n✅ Download dan verifikasi selesai!")
        print(f"\nLangkah berikutnya:")
        print(f"  python src/process_geodata.py")
    else:
        print("\n⚠ File mungkin rusak. Coba hapus dan download ulang.")
        print(f"  Atau download manual dari: {GADM_URL}")


if __name__ == "__main__":
    # Pastikan dijalankan dari root project
    if not Path("environment.yml").exists():
        print("⚠ Jalankan script ini dari root folder project:")
        print("  cd spatial-base-system")
        print("  python src/download_gadm.py")
        sys.exit(1)

    main()
