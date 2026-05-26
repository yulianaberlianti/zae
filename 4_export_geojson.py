"""
SKRIP 4 - EXPORT ZAE → GEOJSON
ZAE Kecamatan Umbulharjo, Kota Yogyakarta
------------------------------------------
Input  : output/zae_final.tif
         output/zae_info.json
Output : output/zae_zones.geojson

PERUBAHAN dari v1:
  - Validasi file input
  - Toleransi simplify disesuaikan ke ~5m (0.00005°)
  - Estimasi luas menggunakan proyeksi UTM (lebih akurat)
  - Log lebih detail
"""

import numpy as np
import rasterio
from rasterio.features import shapes
import geopandas as gpd
from shapely.geometry import shape
import json
import os
import sys

# ── Path ──────────────────────────────────────────────────────────────
ZAE_TIF     = "output/zae_final.tif"
INFO_JSON   = "output/zae_info.json"
OUT_GEOJSON = "output/zae_zones.geojson"

# ── Validasi ──────────────────────────────────────────────────────────
for f in [ZAE_TIF, INFO_JSON]:
    if not os.path.exists(f):
        print(f"ERROR: File tidak ditemukan: {f}")
        print("Pastikan skrip 1-3 sudah dijalankan terlebih dahulu.")
        sys.exit(1)

# ── Load info zona ─────────────────────────────────────────────────────
print("Membaca info zona...")
with open(INFO_JSON, 'r', encoding='utf-8') as f:
    zae_info = json.load(f)
print(f"  {len(zae_info)} zona dimuat.")

# ── Vectorize raster → polygon ─────────────────────────────────────────
print("Mengkonversi raster ZAE ke vektor...")
with rasterio.open(ZAE_TIF) as src:
    zae_arr   = src.read(1)
    crs       = src.crs
    transform = src.transform

mask = zae_arr != -9999
results = []
for geom, val in shapes(zae_arr, mask=mask.astype(np.uint8), transform=transform):
    if int(val) != -9999:
        results.append({
            "geometry":   shape(geom),
            "zona_kode":  int(val)
        })

print(f"  Total polygon awal: {len(results):,}")

if not results:
    print("ERROR: Tidak ada polygon yang dihasilkan. Cek raster ZAE.")
    sys.exit(1)

# ── GeoDataFrame & dissolve ────────────────────────────────────────────
print("Membuat GeoDataFrame...")
gdf = gpd.GeoDataFrame(results, crs=crs)

print("Dissolving per zona...")
gdf_dissolved = gdf.dissolve(by='zona_kode').reset_index()
print(f"  {len(gdf_dissolved)} zona setelah dissolve.")

# Simplifikasi geometri (toleransi ~5m ≈ 0.00005°)
print("Menyederhanakan geometri (toleransi ~5m)...")
gdf_dissolved['geometry'] = gdf_dissolved['geometry'].simplify(
    tolerance=0.00005,
    preserve_topology=True
)

# ── Reprojekcsi ke WGS84 ──────────────────────────────────────────────
if crs and crs.to_epsg() != 4326:
    print(f"  Reprojekcting dari EPSG:{crs.to_epsg()} ke WGS84...")
    gdf_dissolved = gdf_dissolved.to_crs(epsg=4326)
else:
    print("  CRS sudah WGS84.")

# ── Tambahkan atribut ──────────────────────────────────────────────────
print("Menambahkan atribut zona...")

def get_info(kode, field):
    return zae_info.get(str(kode), {}).get(field, "")

for field in ['nama', 'lereng', 'elevasi', 'curah_hujan', 'tanah',
              'rekomendasi', 'dasar_rekomendasi', 'warna']:
    gdf_dissolved[field] = gdf_dissolved['zona_kode'].apply(
        lambda x, f=field: get_info(x, f)
    )

gdf_dissolved['komoditas'] = gdf_dissolved['zona_kode'].apply(
    lambda x: ", ".join(get_info(x, 'komoditas'))
)

# ── Simpan GeoJSON ─────────────────────────────────────────────────────
print("Menyimpan GeoJSON...")
gdf_dissolved.to_file(OUT_GEOJSON, driver='GeoJSON')
print(f"  → GeoJSON disimpan: {OUT_GEOJSON}")

# ── Ringkasan ──────────────────────────────────────────────────────────
# Estimasi luas: reproject ke UTM-49S untuk akurasi
try:
    gdf_utm = gdf_dissolved.to_crs(epsg=32749)  # UTM Zone 49S
    print("\n── RINGKASAN GEOJSON ───────────────────────────────")
    print(f"  Total zona : {len(gdf_dissolved)}")
    print(f"  CRS output : EPSG:4326 (WGS84)")
    print(f"  Bounding box: {gdf_dissolved.total_bounds.round(4)}")
    print("\n  Zona yang dihasilkan:")
    for _, row in gdf_utm.iterrows():
        area_km2 = row.geometry.area / 1_000_000
        nama = get_info(row['zona_kode'], 'nama') or f"Zona {row['zona_kode']}"
        print(f"    [{row['zona_kode']:2d}] {nama} — {area_km2:.3f} km²")
except Exception as e:
    print(f"  (Estimasi luas UTM gagal: {e})")

print("\nSkrip 4 selesai ✓")
print("→ Siap untuk skrip 5 (WebGIS)")
