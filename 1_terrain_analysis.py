"""
SKRIP 1 - TERRAIN ANALYSIS
ZAE Kecamatan Umbulharjo, Kota Yogyakarta
------------------------------------------
Input  : DEMNAS_1408-22_v1.0.tif
Output : output/slope.tif
         output/slope_classified.tif
         output/elevation_classified.tif
"""

import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio import features
from scipy.ndimage import generic_filter
import os

# ── Path ──────────────────────────────────────────────────────────────
DEM_PATH  = "data/DEMNAS_1408-22_v1.0.tif"
OUT_SLOPE = "output/slope.tif"
OUT_SLOPE_CLS = "output/slope_classified.tif"
OUT_ELEV_CLS  = "output/elevation_classified.tif"

os.makedirs("output", exist_ok=True)

# ── Baca DEM ──────────────────────────────────────────────────────────
print("Membaca DEM...")
with rasterio.open(DEM_PATH) as src:
    dem    = src.read(1).astype(np.float32)
    meta   = src.meta.copy()
    transform = src.transform
    crs    = src.crs
    nodata = src.nodata if src.nodata is not None else -9999

# Ganti nodata jadi NaN
dem[dem == nodata] = np.nan

# ── Hitung Slope (derajat) ─────────────────────────────────────────────
print("Menghitung kemiringan lereng (slope)...")

# Resolusi piksel dalam meter (approx dari transform)
res_x = abs(transform.a)
res_y = abs(transform.e)

# Konversi resolusi derajat ke meter jika CRS geografis
if crs and crs.is_geographic:
    res_x = res_x * 111320  # 1 derajat ≈ 111.32 km
    res_y = res_y * 111320

# Hitung gradient
dz_dx, dz_dy = np.gradient(dem, res_x, res_y)
slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
slope_pct = np.tan(slope_rad) * 100  # dalam persen

# Simpan slope (persen)
meta_slope = meta.copy()
meta_slope.update(dtype='float32', nodata=-9999)
with rasterio.open(OUT_SLOPE, 'w', **meta_slope) as dst:
    slope_out = slope_pct.copy()
    slope_out[np.isnan(slope_out)] = -9999
    dst.write(slope_out.astype(np.float32), 1)
print(f"  → Slope disimpan: {OUT_SLOPE}")

# ── Klasifikasi Slope → Zona Lereng ───────────────────────────────────
"""
Klasifikasi ZAE (Modul AEZ 2010):
  Zona I   : >40%  → Sangat Curam (kawasan lindung)
  Zona II  : 16–40% → Curam (perkebunan/hutan)
  Zona III : 8–15%  → Agak Curam (perkebunan)
  Zona IV–VII : <8% → Datar/Landai (pertanian/urban farming)
"""
print("Mengklasifikasikan slope...")
slope_cls = np.full(slope_pct.shape, -9999, dtype=np.int16)
mask = ~np.isnan(slope_pct)

slope_cls[mask & (slope_pct > 40)]              = 1  # Zona I
slope_cls[mask & (slope_pct > 16) & (slope_pct <= 40)] = 2  # Zona II
slope_cls[mask & (slope_pct > 8)  & (slope_pct <= 16)] = 3  # Zona III
slope_cls[mask & (slope_pct <= 8)]              = 4  # Zona IV-VII (datar)

meta_cls = meta.copy()
meta_cls.update(dtype='int16', nodata=-9999)
with rasterio.open(OUT_SLOPE_CLS, 'w', **meta_cls) as dst:
    dst.write(slope_cls, 1)
print(f"  → Slope classified disimpan: {OUT_SLOPE_CLS}")

# ── Klasifikasi Elevasi → Sub-Zona ────────────────────────────────────
"""
Sub-Zona Elevasi:
  'a' (1) : <350 mdpl  → Dataran Rendah
  'b' (2) : 350–700 mdpl → Dataran Sedang
  'c' (3) : >700 mdpl  → Dataran Tinggi
"""
print("Mengklasifikasikan elevasi...")
elev_cls = np.full(dem.shape, -9999, dtype=np.int16)

elev_cls[mask & (dem < 350)]              = 1  # sub-zona 'a'
elev_cls[mask & (dem >= 350) & (dem < 700)] = 2  # sub-zona 'b'
elev_cls[mask & (dem >= 700)]             = 3  # sub-zona 'c'

with rasterio.open(OUT_ELEV_CLS, 'w', **meta_cls) as dst:
    dst.write(elev_cls, 1)
print(f"  → Elevasi classified disimpan: {OUT_ELEV_CLS}")

# ── Statistik ─────────────────────────────────────────────────────────
print("\n── STATISTIK TERRAIN ──────────────────────────────")
print(f"  Elevasi min  : {np.nanmin(dem):.1f} mdpl")
print(f"  Elevasi max  : {np.nanmax(dem):.1f} mdpl")
print(f"  Elevasi rata : {np.nanmean(dem):.1f} mdpl")
print(f"  Slope max    : {np.nanmax(slope_pct):.1f}%")
print(f"  Slope rata   : {np.nanmean(slope_pct):.1f}%")

unique, counts = np.unique(slope_cls[slope_cls != -9999], return_counts=True)
labels = {1: "Zona I (>40%)", 2: "Zona II (16-40%)", 3: "Zona III (8-15%)", 4: "Zona IV-VII (<8%)"}
print("\n  Distribusi Zona Lereng:")
for u, c in zip(unique, counts):
    pct = c / counts.sum() * 100
    print(f"    {labels.get(u, u)}: {c} piksel ({pct:.1f}%)")

print("\nSkrip 1 selesai ✓")
