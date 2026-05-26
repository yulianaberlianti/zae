"""
SKRIP 2 - CLIMATE INTERPOLATION (IDW) — REVISI
ZAE Kecamatan Umbulharjo, Kota Yogyakarta
------------------------------------------
Input  : data/curah_hujan_2025.csv
         output/slope.tif  (referensi grid)
Output : output/rainfall_interpolated.tif
         output/rainfall_classified.tif

Format CSV yang diharapkan:
  stasiun, lat, lon, jan, feb, mar, apr, mei, jun,
           jul, agu, sep, okt, nov, des

PERUBAHAN dari v1:
  - IDW vectorized (numpy meshgrid) → jauh lebih cepat
  - Deteksi kolom fleksibel (case-insensitive)
  - Validasi minimal 3 stasiun
  - Progress bar lebih informatif
"""

import numpy as np
import pandas as pd
import rasterio
import os

# ── Path ──────────────────────────────────────────────────────────────
CSV_PATH     = "data/curah_hujan_2025.csv"
REF_RASTER   = "output/slope.tif"
OUT_RAIN     = "output/rainfall_interpolated.tif"
OUT_RAIN_CLS = "output/rainfall_classified.tif"

os.makedirs("output", exist_ok=True)

# ── Baca CSV ──────────────────────────────────────────────────────────
print("Membaca data curah hujan...")
df = pd.read_csv(CSV_PATH)
print(f"  Kolom ditemukan: {list(df.columns)}")
print(df.to_string(index=False))

col_lower = {c.lower(): c for c in df.columns}

lat_col = next((col_lower[k] for k in col_lower if 'lat' in k), None)
lon_col = next((col_lower[k] for k in col_lower if 'lon' in k or 'lng' in k), None)

if lat_col is None or lon_col is None:
    raise ValueError(
        f"Kolom lat/lon tidak ditemukan!\n"
        f"Kolom tersedia: {list(df.columns)}\n"
        "Pastikan ada kolom bernama 'lat' dan 'lon'."
    )

print(f"\n  Kolom lat: '{lat_col}', Kolom lon: '{lon_col}'")

# Hitung total curah hujan tahunan
skip_cols = {'lat', 'lon', 'lng', 'latitude', 'longitude',
             'stasiun', 'station', 'nama', 'name', 'id'}
bulan_cols = [c for c in df.columns if c.lower() not in skip_cols]
df['curah_hujan_tahunan'] = df[bulan_cols].sum(axis=1)

print(f"\n  Kolom bulan: {bulan_cols}")
print("  Curah hujan tahunan per stasiun:")
for _, row in df.iterrows():
    nama = row.get('stasiun', row.get('station', f"Stasiun {_}"))
    print(f"    {nama}: {row['curah_hujan_tahunan']:.0f} mm")

if len(df) < 3:
    raise ValueError(
        f"Minimal 3 stasiun dibutuhkan untuk IDW! "
        f"Ditemukan: {len(df)} stasiun."
    )

# ── Baca referensi grid ───────────────────────────────────────────────
print("\nMembaca referensi grid dari DEM...")
with rasterio.open(REF_RASTER) as src:
    meta      = src.meta.copy()
    height    = src.height
    width     = src.width
    transform = src.transform
    bounds    = src.bounds

# Buat grid koordinat
xs = bounds.left + (np.arange(width) + 0.5) * transform.a
ys = bounds.top  + (np.arange(height) + 0.5) * transform.e  # e negatif
grid_x, grid_y = np.meshgrid(xs, ys)

print(f"  Grid: {height} × {width} piksel")

# ── IDW Interpolasi (VECTORIZED) ──────────────────────────────────────
print("Melakukan interpolasi IDW (vectorized)...")

st_lats = df[lat_col].values          # shape (N,)
st_lons = df[lon_col].values          # shape (N,)
st_vals = df['curah_hujan_tahunan'].values

power = 2  # IDW power parameter

# grid_x/y: (H, W) → expand ke (H, W, 1)
gx = grid_x[:, :, np.newaxis]
gy = grid_y[:, :, np.newaxis]

# Hitung jarak ke semua stasiun sekaligus: (H, W, N)
dists = np.sqrt((gx - st_lons)**2 + (gy - st_lats)**2)

# Tangani piksel tepat di atas stasiun
exact = np.any(dists == 0, axis=2)
weights = np.where(dists == 0, 0.0, 1.0 / (dists ** power))  # (H,W,N)

weights_sum = weights.sum(axis=2)  # (H,W)
rain_grid = np.sum(weights * st_vals, axis=2) / np.where(weights_sum == 0, 1, weights_sum)

# Isi piksel yang tepat di atas stasiun
for n in range(len(st_vals)):
    mask_exact = dists[:, :, n] == 0
    rain_grid[mask_exact] = st_vals[n]

rain_grid = rain_grid.astype(np.float32)
print(f"  Interpolasi selesai. Range: {rain_grid.min():.0f}–{rain_grid.max():.0f} mm/tahun")

# ── Simpan raster ─────────────────────────────────────────────────────
meta_rain = meta.copy()
meta_rain.update(dtype='float32', nodata=-9999)
with rasterio.open(OUT_RAIN, 'w', **meta_rain) as dst:
    dst.write(rain_grid, 1)
print(f"  → Rainfall raster disimpan: {OUT_RAIN}")

# ── Klasifikasi Curah Hujan ───────────────────────────────────────────
"""
Kelas Curah Hujan ZAE:
  1 (Rendah) : <1000 mm/tahun
  2 (Sedang) : 1000–2000 mm/tahun
  3 (Tinggi) : >2000 mm/tahun
"""
print("Mengklasifikasikan curah hujan...")
rain_cls = np.full(rain_grid.shape, -9999, dtype=np.int16)
rain_cls[rain_grid < 1000]                          = 1
rain_cls[(rain_grid >= 1000) & (rain_grid <= 2000)] = 2
rain_cls[rain_grid > 2000]                          = 3

meta_cls = meta.copy()
meta_cls.update(dtype='int16', nodata=-9999)
with rasterio.open(OUT_RAIN_CLS, 'w', **meta_cls) as dst:
    dst.write(rain_cls, 1)
print(f"  → Rainfall classified disimpan: {OUT_RAIN_CLS}")

# ── Statistik ─────────────────────────────────────────────────────────
labels = {1: "Rendah (<1000 mm)", 2: "Sedang (1000–2000 mm)", 3: "Tinggi (>2000 mm)"}
unique, counts = np.unique(rain_cls[rain_cls != -9999], return_counts=True)

print("\n── STATISTIK CURAH HUJAN ──────────────────────────")
print(f"  Min  : {rain_grid.min():.1f} mm/tahun")
print(f"  Max  : {rain_grid.max():.1f} mm/tahun")
print(f"  Rata : {rain_grid.mean():.1f} mm/tahun")
print("\n  Distribusi Kelas:")
for u, c in zip(unique, counts):
    pct = c / counts.sum() * 100
    print(f"    {labels.get(u, u)}: {pct:.1f}%")

print("\nSkrip 2 selesai ✓")
