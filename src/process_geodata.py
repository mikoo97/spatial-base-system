"""
process_geodata.py
==================
Pipeline utama: proses GADM raw → layer standar SEI siap pakai.

Cara pakai:
    python src/process_geodata.py

    # Atau dengan argumen spesifik:
    python src/process_geodata.py --levels 1 2    # provinsi + kabupaten saja
    python src/process_geodata.py --province "Jawa Timur"  # fokus 1 provinsi

Output di data/spatial/processed/:
    idn_provinsi_2023_gadm.gpkg
    idn_kabupaten_2023_gadm.gpkg
    idn_kecamatan_2023_gadm.gpkg
    summary_report.csv
"""

import sys
import argparse
from pathlib import Path

# Tambahkan src ke path
sys.path.insert(0, str(Path(__file__).parent))
from spatial_utils import (
    process_gadm_indonesia,
    get_indonesia_summary,
    save_geodata,
    clip_to_province,
    quick_map,
    plot_indonesia,
)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

GADM_INPUT    = Path("data/spatial/raw/gadm41_IDN.gpkg")
OUTPUT_DIR    = Path("data/spatial/processed")
ASSETS_DIR    = Path("assets/screenshots")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(levels: list = [1, 2, 3], province: str = None):
    """
    Jalankan full processing pipeline.

    Parameters
    ----------
    levels   : GADM levels yang diproses [1=provinsi, 2=kabupaten, 3=kecamatan]
    province : filter ke 1 provinsi saja (opsional, untuk testing cepat)
    """

    print("\n" + "═" * 60)
    print("  SPATIAL BASE SYSTEM — Processing Pipeline")
    print("  Spatial Economic Intelligence Indonesia")
    print("═" * 60)

    # ── Step 1: Cek input file ────────────────────────────────────────────
    print("\n[STEP 1] Checking input file...")

    if not GADM_INPUT.exists():
        print(f"\n✗ File GADM tidak ditemukan: {GADM_INPUT}")
        print(f"\nJalankan download dulu:")
        print(f"  python src/download_gadm.py")
        sys.exit(1)

    size_mb = GADM_INPUT.stat().st_size / 1e6
    print(f"  ✓ Input: {GADM_INPUT.name} ({size_mb:.1f} MB)")

    # ── Step 2: Process GADM ─────────────────────────────────────────────
    print("\n[STEP 2] Processing GADM layers...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    layers = process_gadm_indonesia(
        gadm_gpkg_path=GADM_INPUT,
        output_dir=OUTPUT_DIR,
        levels=levels,
    )

    if not layers:
        print("✗ Tidak ada layer yang berhasil diproses.")
        sys.exit(1)

    # ── Step 3: Province filter (opsional) ───────────────────────────────
    if province:
        print(f"\n[STEP 3] Filtering ke provinsi: {province}...")
        if "provinsi" not in layers:
            print("  ✗ Layer provinsi tidak tersedia untuk filter.")
        else:
            filtered = {}
            for level_name, gdf in layers.items():
                if level_name == "provinsi":
                    filtered[level_name] = layers["provinsi"][
                        layers["provinsi"]["nama_prov"].str.lower() == province.lower()
                    ]
                else:
                    try:
                        filtered[level_name] = clip_to_province(
                            gdf, layers["provinsi"], province
                        )
                        print(f"  ✓ {level_name}: {len(filtered[level_name]):,} features")
                    except Exception as e:
                        print(f"  ⚠ Clip {level_name} gagal: {e}")
                        filtered[level_name] = gdf
            layers = filtered

    # ── Step 4: Generate summary ─────────────────────────────────────────
    print("\n[STEP 4] Generating summary...")
    summary = get_indonesia_summary(layers)
    print(f"\n{summary.to_string(index=False)}\n")

    summary_path = OUTPUT_DIR / "summary_report.csv"
    summary.to_csv(summary_path, index=False)
    print(f"  ✓ Summary saved: {summary_path}")

    # ── Step 5: Generate static visualizations ───────────────────────────
    print("\n[STEP 5] Generating static maps...")
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    if "provinsi" in layers:
        gdf = layers["provinsi"]
        fig = plot_indonesia(
            gdf,
            title="Provinsi Indonesia — Spatial Base System",
            save_path=str(ASSETS_DIR / "provinsi_base.png"),
        )
        import matplotlib.pyplot as plt
        plt.close(fig)
        print(f"  ✓ Provinsi map saved")

    if "kabupaten" in layers:
        gdf = layers["kabupaten"]
        fig = plot_indonesia(
            gdf,
            column="area_km2",
            title="Kabupaten/Kota Indonesia — Luas Wilayah (km²)",
            save_path=str(ASSETS_DIR / "kabupaten_area.png"),
        )
        import matplotlib.pyplot as plt
        plt.close(fig)
        print(f"  ✓ Kabupaten area map saved")

    # ── Step 6: Generate interactive maps ────────────────────────────────
    print("\n[STEP 6] Generating interactive maps...")

    if "provinsi" in layers:
        m = quick_map(
            layers["provinsi"],
            title="Indonesia — Batas Provinsi",
            tooltip_cols=["nama_prov", "area_km2"],
        )
        map_path = ASSETS_DIR / "provinsi_interactive.html"
        m.save(str(map_path))
        print(f"  ✓ Saved: {map_path}")

    # ── Done ─────────────────────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  ✅ PIPELINE SELESAI")
    print("═" * 60)
    print(f"\n  Output files di: {OUTPUT_DIR.resolve()}")
    print(f"  Maps di        : {ASSETS_DIR.resolve()}")
    print(f"\n  Langkah berikutnya:")
    print(f"  1. Review output di QGIS: buka file .gpkg dari {OUTPUT_DIR}")
    print(f"  2. Jalankan notebook EDA: jupyter notebook notebooks/01_eda.ipynb")
    print(f"  3. Run Streamlit app    : streamlit run app/app.py")
    print()

    return layers


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Spatial Base System — Geodata Processing Pipeline"
    )
    parser.add_argument(
        "--levels", nargs="+", type=int, default=[1, 2, 3],
        help="GADM levels to process: 1=provinsi, 2=kabupaten, 3=kecamatan (default: all)"
    )
    parser.add_argument(
        "--province", type=str, default=None,
        help="Filter output ke satu provinsi saja (untuk testing)"
    )

    # Pastikan dijalankan dari root project
    if not Path("environment.yml").exists():
        print("⚠ Jalankan dari root folder project:")
        print("  cd spatial-base-system")
        print("  python src/process_geodata.py")
        sys.exit(1)

    args = parser.parse_args()
    run_pipeline(levels=args.levels, province=args.province)
