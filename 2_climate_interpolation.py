"""
SKRIP 2 - CLIMATE INTERPOLATION (IDW)
ZAE Kecamatan Umbulharjo, Kota Yogyakarta
------------------------------------------
Input  : data/curah_hujan_2025.csv
         output/slope.tif (sebagai referensi grid)
Output : output/rainfall_interpolated.tif
         output/rainfall_classified.tif

Format CSV yang diharapkan:
  stasiun, lat, lon, jan, feb, mar, apr, mei, jun,
           jul, agu, sep, okt, nov, des
"""

import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_bounds
import os

# ── Path ──────────────────────────────────────────────────────────────
CSV_PATH       = "data/curah_hujan_2025.csv"
REF_RASTER     = "output/slope.tif"          # referensi resolusi & extent
OUT_RAIN       = "output/rainfall_interpolated.tif"
OUT_RAIN_CLS   = "output/rainfall_classified.tif"

# ── Baca CSV ──────────────────────────────────────────────────────────
print("Membaca data curah hujan...")
df = pd.read_csv(CSV_PATH)
print(f"  Kolom ditemukan: {list(df.columns)}")
print(df.head())

# Deteksi kolom otomatis (fleksibel)
# Cari kolom lat/lon (case-insensitive)
col_lower = {c.lower(): c for c in df.columns}

lat_col = next((col_lower[k] for k in col_lower if 'lat' in k), None)
lon_col = next((col_lower[k] for k in col_lower if 'lon' in k or 'lng' in k), None)

if lat_col is None or lon_col is None:
    raise ValueError(
        "Kolom lat/lon tidak ditemukan di CSV!\n"
        f"Kolom tersedia: {list(df.columns)}\n"
        "Pastikan ada kolom bernama 'lat'/'latitude' dan 'lon'/'longitude'/'lng'"
    )

print(f"  Kolom lat: '{lat_col}', Kolom lon: '{lon_col}'")

# Hitung total curah hujan tahunan
bulan_cols = [c for c in df.columns if c.lower() not in
              [lat_col.lower(), lon_col.lower(), 'stasiun', 'station', 'nama', 'name', 'id']]
df['curah_hujan_tahunan'] = df[bulan_cols].sum(axis=1)
print(f"\n  Kolom bulan terdeteksi: {bulan_cols}")
print(f"  Curah hujan tahunan per stasiun:")
print(df[[lat_col, lon_col, 'curah_hujan_tahunan']].to_string(index=False))

# ── Baca referensi grid dari raster DEM ───────────────────────────────
print("\nMembaca referensi grid dari DEM...")
with rasterio.open(REF_RASTER) as src:
    meta     = src.meta.copy()
    height   = src.height
    width    = src.width
    transform = src.transform
    bounds   = src.bounds

# Buat grid koordinat
cols_idx = np.arange(width)
rows_idx = np.arange(height)
xs = bounds.left  + (cols_idx + 0.5) * transform.a
ys = bounds.top   + (rows_idx + 0.5) * transform.e  # e negatif
grid_x, grid_y = np.meshgrid(xs, ys)

# ── IDW Interpolation ─────────────────────────────────────────────────
print("Melakukan interpolasi IDW...")

station_lats = df[lat_col].values
station_lons = df[lon_col].values
station_vals = df['curah_hujan_tahunan'].values

power = 2  # IDW power parameter

rain_grid = np.zeros((height, width), dtype=np.float32)

for i in range(height):
    for j in range(width):
        px, py = grid_x[i, j], grid_y[i, j]
        dists = np.sqrt((station_lons - px)**2 + (station_lats - py)**2)

        # Jika tepat di lokasi stasiun
        if np.any(dists == 0):
            rain_grid[i, j] = station_vals[dists == 0][0]
        else:
            weights = 1.0 / (dists ** power)
            rain_grid[i, j] = np.sum(weights * station_vals) / np.sum(weights)

    if i % (height // 10) == 0:
        print(f"  Progress: {i/height*100:.0f}%")

print("  Interpolasi selesai.")

# ── Simpan raster curah hujan ──────────────────────────────────────────
meta_rain = meta.copy()
meta_rain.update(dtype='float32', nodata=-9999)
with rasterio.open(OUT_RAIN, 'w', **meta_rain) as dst:
    dst.write(rain_grid, 1)
print(f"  → Rainfall raster disimpan: {OUT_RAIN}")

# ── Klasifikasi Curah Hujan ────────────────────────────────────────────
"""
Kelas Curah Hujan ZAE:
  1 (Rendah) : <1000 mm/tahun
  2 (Sedang) : 1000–2000 mm/tahun
  3 (Tinggi) : >2000 mm/tahun
"""
print("Mengklasifikasikan curah hujan...")
rain_cls = np.full(rain_grid.shape, -9999, dtype=np.int16)
rain_cls[rain_grid < 1000]                          = 1  # Rendah
rain_cls[(rain_grid >= 1000) & (rain_grid <= 2000)] = 2  # Sedang
rain_cls[rain_grid > 2000]                          = 3  # Tinggi

meta_cls = meta.copy()
meta_cls.update(dtype='int16', nodata=-9999)
with rasterio.open(OUT_RAIN_CLS, 'w', **meta_cls) as dst:
    dst.write(rain_cls, 1)
print(f"  → Rainfall classified disimpan: {OUT_RAIN_CLS}")

# ── Statistik ─────────────────────────────────────────────────────────
print("\n── STATISTIK CURAH HUJAN ──────────────────────────")
print(f"  Min  : {rain_grid.min():.1f} mm/tahun")
print(f"  Max  : {rain_grid.max():.1f} mm/tahun")
print(f"  Rata : {rain_grid.mean():.1f} mm/tahun")

labels = {1: "Rendah (<1000)", 2: "Sedang (1000-2000)", 3: "Tinggi (>2000)"}
unique, counts = np.unique(rain_cls[rain_cls != -9999], return_counts=True)
print("\n  Distribusi Kelas Curah Hujan:")
for u, c in zip(unique, counts):
    pct = c / counts.sum() * 100
    print(f"    {labels.get(u, u)}: {pct:.1f}%")

print("\nSkrip 2 selesai ✓")
