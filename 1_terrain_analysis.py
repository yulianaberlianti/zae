"""
SKRIP 1 - TERRAIN ANALYSIS
ZAE Kecamatan Umbulharjo, Kota Yogyakarta
------------------------------------------
Input  : data/DEMNAS_1408-22_v1.0.tif
Output : output/slope.tif
         output/slope_classified.tif
         output/elevation_classified.tif

PERUBAHAN dari v1:
  - Koreksi konversi resolusi derajat → meter (pakai cos(lat))
  - Validasi file input sebelum proses
  - Statistik lebih lengkap
"""

import numpy as np
import rasterio
import os
import sys

# ── Path ──────────────────────────────────────────────────────────────
DEM_PATH      = "data/DEMNAS_1408-22_v1.0.tif"
OUT_SLOPE     = "output/slope.tif"
OUT_SLOPE_CLS = "output/slope_classified.tif"
OUT_ELEV_CLS  = "output/elevation_classified.tif"

os.makedirs("output", exist_ok=True)

# ── Validasi file ─────────────────────────────────────────────────────
if not os.path.exists(DEM_PATH):
    print(f"ERROR: File DEM tidak ditemukan: {DEM_PATH}")
    print("Pastikan file DEMNAS sudah diletakkan di folder data/")
    sys.exit(1)

# ── Baca DEM ──────────────────────────────────────────────────────────
print("Membaca DEM...")
with rasterio.open(DEM_PATH) as src:
    dem       = src.read(1).astype(np.float32)
    meta      = src.meta.copy()
    transform = src.transform
    crs       = src.crs
    nodata    = src.nodata if src.nodata is not None else -9999
    bounds    = src.bounds

print(f"  Dimensi: {dem.shape[1]} × {dem.shape[0]} piksel")
print(f"  CRS: {crs}")
print(f"  Bounds: {bounds}")

# Ganti nodata jadi NaN
dem[dem == nodata] = np.nan

# ── Hitung Slope (persen) ─────────────────────────────────────────────
print("Menghitung kemiringan lereng (slope)...")

res_x = abs(transform.a)
res_y = abs(transform.e)

# Konversi resolusi derajat → meter (koreksi cos(lat))
if crs and crs.is_geographic:
    lat_center = (bounds.bottom + bounds.top) / 2
    res_x = res_x * 111320 * np.cos(np.radians(lat_center))
    res_y = res_y * 111320
    print(f"  Resolusi spasial: {res_x:.2f} m × {res_y:.2f} m (setelah koreksi lat)")

dz_dy, dz_dx = np.gradient(dem, res_y, res_x)
slope_pct = np.sqrt(dz_dx**2 + dz_dy**2) * 100  # persen

# Simpan slope
meta_slope = meta.copy()
meta_slope.update(dtype='float32', nodata=-9999)
slope_out = slope_pct.copy()
slope_out[np.isnan(slope_out)] = -9999
with rasterio.open(OUT_SLOPE, 'w', **meta_slope) as dst:
    dst.write(slope_out.astype(np.float32), 1)
print(f"  → Slope disimpan: {OUT_SLOPE}")

# ── Klasifikasi Slope ─────────────────────────────────────────────────
"""
Klasifikasi ZAE (Modul AEZ / BBSDLP):
  Zona I   : >40%  → Sangat Curam (kawasan lindung)
  Zona II  : 16–40% → Curam (perkebunan/hutan)
  Zona III : 8–15%  → Agak Curam (agroforestri)
  Zona IV–VII : <8% → Datar/Landai (pertanian/urban farming)
"""
print("Mengklasifikasikan slope...")
mask = ~np.isnan(slope_pct)
slope_cls = np.full(slope_pct.shape, -9999, dtype=np.int16)
slope_cls[mask & (slope_pct > 40)]                        = 1
slope_cls[mask & (slope_pct > 16) & (slope_pct <= 40)]   = 2
slope_cls[mask & (slope_pct > 8)  & (slope_pct <= 16)]   = 3
slope_cls[mask & (slope_pct <= 8)]                        = 4

meta_cls = meta.copy()
meta_cls.update(dtype='int16', nodata=-9999)
with rasterio.open(OUT_SLOPE_CLS, 'w', **meta_cls) as dst:
    dst.write(slope_cls, 1)
print(f"  → Slope classified disimpan: {OUT_SLOPE_CLS}")

# ── Klasifikasi Elevasi ───────────────────────────────────────────────
"""
Sub-Zona Elevasi:
  1 : <350 mdpl  → Dataran Rendah
  2 : 350–700 mdpl → Dataran Sedang
  3 : >700 mdpl  → Dataran Tinggi
"""
print("Mengklasifikasikan elevasi...")
elev_cls = np.full(dem.shape, -9999, dtype=np.int16)
elev_cls[mask & (dem < 350)]               = 1
elev_cls[mask & (dem >= 350) & (dem < 700)] = 2
elev_cls[mask & (dem >= 700)]              = 3

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

labels_slope = {1: "Zona I  (>40%)",
                2: "Zona II (16-40%)",
                3: "Zona III (8-15%)",
                4: "Zona IV-VII (<8%)"}
unique, counts = np.unique(slope_cls[slope_cls != -9999], return_counts=True)
print("\n  Distribusi Zona Lereng:")
for u, c in zip(unique, counts):
    pct = c / counts.sum() * 100
    print(f"    {labels_slope.get(u, str(u))}: {c:,} piksel ({pct:.1f}%)")

labels_elev = {1: "Dataran Rendah (<350 m)",
               2: "Dataran Sedang (350-700 m)",
               3: "Dataran Tinggi (>700 m)"}
unique_e, counts_e = np.unique(elev_cls[elev_cls != -9999], return_counts=True)
print("\n  Distribusi Sub-Zona Elevasi:")
for u, c in zip(unique_e, counts_e):
    pct = c / counts_e.sum() * 100
    print(f"    {labels_elev.get(u, str(u))}: {c:,} piksel ({pct:.1f}%)")

print("\nSkrip 1 selesai ✓")
