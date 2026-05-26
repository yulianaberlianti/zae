"""
SKRIP 4 - EXPORT ZAE → GEOJSON
ZAE Kecamatan Umbulharjo, Kota Yogyakarta
------------------------------------------
Input  : output/zae_final.tif
         output/zae_info.json
Output : output/zae_zones.geojson

Proses: rasterio.features.shapes → vectorize piksel → dissolve per zona
"""

import numpy as np
import rasterio
from rasterio.features import shapes
from rasterio.warp import calculate_default_transform, reproject, Resampling
import geopandas as gpd
from shapely.geometry import shape
import json
import os

# ── Path ──────────────────────────────────────────────────────────────
ZAE_TIF   = "output/zae_final.tif"
INFO_JSON  = "output/zae_info.json"
OUT_GEOJSON = "output/zae_zones.geojson"

# ── Load info zona ─────────────────────────────────────────────────────
print("Membaca info zona...")
with open(INFO_JSON, 'r', encoding='utf-8') as f:
    zae_info = json.load(f)

# ── Vectorize raster → polygon ─────────────────────────────────────────
print("Mengkonversi raster ZAE ke vektor...")

with rasterio.open(ZAE_TIF) as src:
    zae_arr = src.read(1)
    crs     = src.crs
    transform = src.transform

    # Vectorize
    mask = zae_arr != -9999
    results = []
    for geom, val in shapes(zae_arr, mask=mask.astype(np.uint8), transform=transform):
        if val != -9999:
            results.append({
                "geometry": shape(geom),
                "zona_kode": int(val)
            })

print(f"  Total polygon awal: {len(results)}")

# ── Buat GeoDataFrame ──────────────────────────────────────────────────
print("Membuat GeoDataFrame...")
gdf = gpd.GeoDataFrame(results, crs=crs)

# Dissolve per zona (gabungkan piksel yang sama)
print("Dissolving per zona...")
gdf_dissolved = gdf.dissolve(by='zona_kode').reset_index()

# Simplifikasi geometri untuk performa WebGIS (toleransi ~5m)
print("Menyederhanakan geometri...")
gdf_dissolved['geometry'] = gdf_dissolved['geometry'].simplify(
    tolerance=0.0001,  # dalam derajat (~11m di equator)
    preserve_topology=True
)

# ── Konversi ke WGS84 jika perlu ──────────────────────────────────────
if crs and not crs.to_epsg() == 4326:
    print(f"  Reprojekcting dari {crs} ke WGS84...")
    gdf_dissolved = gdf_dissolved.to_crs(epsg=4326)
else:
    print("  CRS sudah WGS84, tidak perlu reproject.")

# ── Tambahkan atribut info zona ────────────────────────────────────────
print("Menambahkan atribut zona...")

def get_info(kode, field):
    return zae_info.get(str(kode), {}).get(field, "")

gdf_dissolved['nama']         = gdf_dissolved['zona_kode'].apply(lambda x: get_info(x, 'nama'))
gdf_dissolved['lereng']       = gdf_dissolved['zona_kode'].apply(lambda x: get_info(x, 'lereng'))
gdf_dissolved['elevasi']      = gdf_dissolved['zona_kode'].apply(lambda x: get_info(x, 'elevasi'))
gdf_dissolved['curah_hujan']  = gdf_dissolved['zona_kode'].apply(lambda x: get_info(x, 'curah_hujan'))
gdf_dissolved['tanah']        = gdf_dissolved['zona_kode'].apply(lambda x: get_info(x, 'tanah'))
gdf_dissolved['rekomendasi']  = gdf_dissolved['zona_kode'].apply(lambda x: get_info(x, 'rekomendasi'))
gdf_dissolved['komoditas']    = gdf_dissolved['zona_kode'].apply(
    lambda x: ", ".join(get_info(x, 'komoditas'))
)
gdf_dissolved['warna']        = gdf_dissolved['zona_kode'].apply(lambda x: get_info(x, 'warna'))

# ── Simpan GeoJSON ─────────────────────────────────────────────────────
print(f"Menyimpan GeoJSON...")
gdf_dissolved.to_file(OUT_GEOJSON, driver='GeoJSON')
print(f"  → GeoJSON disimpan: {OUT_GEOJSON}")

# ── Ringkasan ──────────────────────────────────────────────────────────
print("\n── RINGKASAN GEOJSON ───────────────────────────────")
print(f"  Total zona : {len(gdf_dissolved)}")
print(f"  CRS        : {gdf_dissolved.crs}")
print(f"  Bounding box: {gdf_dissolved.total_bounds}")
print("\n  Zona yang dihasilkan:")
for _, row in gdf_dissolved.iterrows():
    area_km2 = row.geometry.area * (111.32**2)  # approx km2
    print(f"    [{row.zona_kode}] {row.nama} — ±{area_km2:.2f} km²")

print("\nSkrip 4 selesai ✓")
print("→ Siap untuk skrip 5 (WebGIS)")
