"""
SKRIP 3 - ZAE CLASSIFICATION & OVERLAY (REVISI)
ZAE Kecamatan Umbulharjo, Kota Yogyakarta
------------------------------------------
Input  : output/slope_classified.tif
         output/elevation_classified.tif
         output/rainfall_classified.tif
Output : output/zae_final.tif
         output/zae_info.json

Dasar ilmiah rekomendasi komoditas:
  2 faktor utama = Ketinggian Tempat + Curah Hujan/Tahun
  (suhu turun ±0.6°C per 100 mdpl naik → menentukan jenis tanaman)

Referensi:
  - Modul AEZ 2010 (BBSDLP)
  - Acuan komoditas Indonesia per ketinggian + curah hujan
  - Asumsi tanah Umbulharjo: Regosol pasiran vulkanik Merapi
    (pH 5.5–6.5, tekstur pasir berlempung, drainase cepat–sedang)
    Sumber: BBSDLP 2014, Peta Tanah Tinjau DIY
"""

import numpy as np
import rasterio
from rasterio.enums import Resampling
import json
import os

# ── Path ──────────────────────────────────────────────────────────────
SLOPE_CLS   = "output/slope_classified.tif"
ELEV_CLS    = "output/elevation_classified.tif"
RAIN_CLS    = "output/rainfall_classified.tif"
OUT_ZAE     = "output/zae_final.tif"
OUT_INFO    = "output/zae_info.json"

os.makedirs("output", exist_ok=True)

# ── Baca semua layer ───────────────────────────────────────────────────
print("Membaca layer terklasifikasi...")

def read_raster(path):
    with rasterio.open(path) as src:
        return src.read(1), src.meta.copy()

slope_arr, meta = read_raster(SLOPE_CLS)
elev_arr,  _    = read_raster(ELEV_CLS)
rain_arr,  _    = read_raster(RAIN_CLS)

# Resample curah hujan ke dimensi slope jika beda
if rain_arr.shape != slope_arr.shape:
    print("  Resampling curah hujan ke dimensi DEM...")
    with rasterio.open(RAIN_CLS) as src:
        rain_arr = src.read(
            1, out_shape=slope_arr.shape,
            resampling=Resampling.nearest
        )

# ── Kode Kelas (dari skrip 1 & 2) ────────────────────────────────────
# slope_arr : 1=Zona I (>40%), 2=Zona II (16-40%), 3=Zona III (8-15%), 4=datar (<8%)
# elev_arr  : 1=<350 mdpl, 2=350-700 mdpl, 3=>700 mdpl
# rain_arr  : 1=Rendah (<1000mm), 2=Sedang (1000-2000mm), 3=Tinggi (>2000mm)

# ── Matriks Komoditas: Ketinggian × Curah Hujan ───────────────────────
"""
TABEL ACUAN KOMODITAS (digunakan untuk zona datar/landai = slope kelas 4)

Elevasi kelas 1 (<350 mdpl) = dataran rendah panas, suhu 26-30°C
  CH Tinggi (>2000mm) : Padi sawah, karet, kelapa sawit, pisang, kelapa, kakao → 2-3x tanam
  CH Sedang (1000-2000mm): Padi+palawija, jagung, kedelai, tebu, mangga, durian
  CH Rendah (<1000mm) : Jagung, kacang tanah, kacang hijau, sorgum, singkong, mete

Elevasi kelas 2 (350-700 mdpl) = dataran rendah-menengah sejuk, suhu 23-26°C
  CH Tinggi : Padi gogo, kopi robusta, kakao, durian, salak
  CH Sedang : Jagung, kacang tanah, tembakau, kopi robusta, salak, durian
  CH Rendah : Singkong, kacang tanah, tembakau

Elevasi kelas 3 (>700 mdpl) = dataran menengah-tinggi, suhu 17-23°C
  CH Tinggi : Tomat, kentang, kubis, wortel, kopi arabika, teh, jeruk, alpukat
  CH Sedang : Sayur dataran tinggi, kopi arabika, stroberi, apel, markisa
  CH Rendah : Bawang daun, kentang, wortel, kol

Zona khusus lereng (slope 1-3):
  Zona I (>40%)  : kawasan lindung/hutan
  Zona II (16-40%): perkebunan tahunan sesuai elevasi
  Zona III (8-15%): wanatani/agroforestri
"""

# ── ZAE Kode Akhir ────────────────────────────────────────────────────
# Kode 1  : Zona I — Kawasan Lindung (lereng >40%)
# Kode 2  : Zona II — Perkebunan Tahunan (lereng 16-40%)
# Kode 3  : Zona III — Wanatani/Agroforestri (lereng 8-15%)
# Kode 4  : Dataran Rendah Basah (<350m, CH >2000mm)
# Kode 5  : Dataran Rendah Agak Basah (<350m, CH 1000-2000mm) ← DOMINAN Umbulharjo
# Kode 6  : Dataran Rendah Kering (<350m, CH <1000mm)
# Kode 7  : Dataran Menengah Basah (350-700m, CH >2000mm)
# Kode 8  : Dataran Menengah Agak Basah (350-700m, CH 1000-2000mm)
# Kode 9  : Dataran Menengah Kering (350-700m, CH <1000mm)
# Kode 10 : Dataran Tinggi Basah (>700m, CH >2000mm)
# Kode 11 : Dataran Tinggi Agak Basah (>700m, CH 1000-2000mm)
# Kode 12 : Dataran Tinggi Kering (>700m, CH <1000mm)

print("Melakukan overlay dan zonasi ZAE...")

zae = np.full(slope_arr.shape, -9999, dtype=np.int16)
valid = (slope_arr != -9999) & (elev_arr != -9999) & (rain_arr != -9999)

# ── Zona berdasarkan lereng (prioritas utama) ─────────────────────────
zae[valid & (slope_arr == 1)] = 1  # Zona I: lindung
zae[valid & (slope_arr == 2)] = 2  # Zona II: perkebunan tahunan
zae[valid & (slope_arr == 3)] = 3  # Zona III: wanatani

# ── Zona datar (slope == 4): matriks elevasi × curah hujan ───────────
flat = valid & (slope_arr == 4)

# Elevasi rendah <350 mdpl
zae[flat & (elev_arr == 1) & (rain_arr == 3)] = 4   # rendah basah
zae[flat & (elev_arr == 1) & (rain_arr == 2)] = 5   # rendah agak basah ← Umbulharjo
zae[flat & (elev_arr == 1) & (rain_arr == 1)] = 6   # rendah kering

# Elevasi menengah 350-700 mdpl
zae[flat & (elev_arr == 2) & (rain_arr == 3)] = 7   # menengah basah
zae[flat & (elev_arr == 2) & (rain_arr == 2)] = 8   # menengah agak basah
zae[flat & (elev_arr == 2) & (rain_arr == 1)] = 9   # menengah kering

# Elevasi tinggi >700 mdpl
zae[flat & (elev_arr == 3) & (rain_arr == 3)] = 10  # tinggi basah
zae[flat & (elev_arr == 3) & (rain_arr == 2)] = 11  # tinggi agak basah
zae[flat & (elev_arr == 3) & (rain_arr == 1)] = 12  # tinggi kering

# Fallback: piksel valid yang belum terklasifikasi → kode 5 (default Umbulharjo)
zae[valid & (zae == -9999)] = 5

# ── Simpan ZAE ────────────────────────────────────────────────────────
meta_zae = meta.copy()
meta_zae.update(dtype='int16', nodata=-9999)
with rasterio.open(OUT_ZAE, 'w', **meta_zae) as dst:
    dst.write(zae, 1)
print(f"  → ZAE final disimpan: {OUT_ZAE}")

# ── Info Zona (untuk WebGIS) ──────────────────────────────────────────
zae_info = {
    "1": {
        "nama": "Zona I — Kawasan Lindung",
        "lereng": ">40%", "elevasi": "Bervariasi", "suhu_estimasi": "Bervariasi",
        "curah_hujan": "—",
        "tanah": "Regosol (asumsi literatur)",
        "rekomendasi": "Tidak untuk pertanian. Kawasan lindung, hutan konservasi, reboisasi.",
        "komoditas": [],
        "dasar_rekomendasi": "Lereng >40% → risiko erosi sangat tinggi, mekanisasi tidak memungkinkan.",
        "warna": "#8B0000"
    },
    "2": {
        "nama": "Zona II — Perkebunan Tahunan",
        "lereng": "16–40%", "elevasi": "Bervariasi", "suhu_estimasi": "Bervariasi",
        "curah_hujan": "—",
        "tanah": "Regosol (asumsi literatur)",
        "rekomendasi": "Tanaman keras & tahunan yang mampu mengikat tanah secara permanen.",
        "komoditas": ["Sawit", "Karet", "Kelapa", "Kopi Arabika", "Kayu Manis", "Teh", "Kakao", "Jarak", "Mete"],
        "dasar_rekomendasi": "Lereng 16–40% → hanya tanaman tahunan bisa mencegah erosi permanen.",
        "warna": "#228B22"
    },
    "3": {
        "nama": "Zona III — Sistem Wanatani (Agroforestri)",
        "lereng": "8–15%", "elevasi": "Bervariasi", "suhu_estimasi": "Bervariasi",
        "curah_hujan": "—",
        "tanah": "Regosol (asumsi literatur)",
        "rekomendasi": "Sistem wanatani campuran untuk menjaga tanah dari erosi sekaligus mempertahankan pendapatan petani.",
        "komoditas": ["Pisang", "Pepaya", "Singkong", "Jagung", "Kacang Tanah"],
        "dasar_rekomendasi": "Lereng 8–15% → agroforestri menjaga produktivitas sekaligus konservasi.",
        "warna": "#6B8E23"
    },
    "4": {
        "nama": "Zona IVa — Dataran Rendah Basah",
        "lereng": "<8%", "elevasi": "<350 mdpl", "suhu_estimasi": "26–30°C",
        "curah_hujan": ">2000 mm/tahun (Tipe A-B, 7–9 bulan basah)",
        "tanah": "Regosol pasiran, pH 5.5–6.5 (asumsi literatur)",
        "rekomendasi": "Padi sawah irigasi 2–3x tanam/tahun. Lahan basah produktif.",
        "komoditas": ["Padi Sawah", "Karet", "Kelapa Sawit", "Pisang", "Kelapa", "Kakao"],
        "dasar_rekomendasi": "Dataran rendah panas (26-30°C) + CH tinggi → optimal untuk padi sawah intensif.",
        "warna": "#1E90FF"
    },
    "5": {
        "nama": "Zona IVb — Dataran Rendah Agak Basah (Urban Farming)",
        "lereng": "<8%", "elevasi": "<350 mdpl", "suhu_estimasi": "26–30°C",
        "curah_hujan": "1000–2000 mm/tahun (Tipe C-D, 5–7 bulan basah)",
        "tanah": "Regosol pasiran, pH 5.5–6.5 (asumsi literatur)",
        "rekomendasi": "Urban farming, sayuran hortikultura lahan sempit, tanaman obat (toga), hidroponik. Padi 2x + palawija 1x.",
        "komoditas": ["Padi", "Jagung", "Kedelai", "Tebu", "Mangga", "Durian", "Cabai", "Tomat", "Terong", "Kangkung", "Bayam", "Kemangi", "Jahe", "Kunyit"],
        "dasar_rekomendasi": "Dataran rendah panas (26-30°C) + CH agak basah → dominan di Umbulharjo. Cocok urban farming & hortikultura.",
        "warna": "#ADFF2F"
    },
    "6": {
        "nama": "Zona IVc — Dataran Rendah Kering",
        "lereng": "<8%", "elevasi": "<350 mdpl", "suhu_estimasi": "26–30°C",
        "curah_hujan": "<1000 mm/tahun (Tipe F-G, <3 bulan basah)",
        "tanah": "Regosol pasiran, drainase cepat (asumsi literatur)",
        "rekomendasi": "Tanaman toleran kering. Hanya 1x tanam per tahun. Butuh irigasi untuk padi.",
        "komoditas": ["Jagung Tahan Kering", "Kacang Tanah", "Kacang Hijau", "Sorgum", "Singkong", "Mete"],
        "dasar_rekomendasi": "CH rendah (<1000mm) → hanya tanaman toleran kekeringan yang feasible.",
        "warna": "#DAA520"
    },
    "7": {
        "nama": "Zona Va — Dataran Menengah Basah",
        "lereng": "<8%", "elevasi": "350–700 mdpl", "suhu_estimasi": "23–26°C",
        "curah_hujan": ">2000 mm/tahun",
        "tanah": "Regosol (asumsi literatur)",
        "rekomendasi": "Padi gogo, perkebunan basah, tanaman dataran menengah.",
        "komoditas": ["Padi Gogo", "Kopi Robusta", "Kakao", "Durian", "Salak", "Pisang"],
        "dasar_rekomendasi": "Suhu 23-26°C + CH tinggi → kopi robusta & tanaman perkebunan dataran menengah optimal.",
        "warna": "#00CED1"
    },
    "8": {
        "nama": "Zona Vb — Dataran Menengah Agak Basah",
        "lereng": "<8%", "elevasi": "350–700 mdpl", "suhu_estimasi": "23–26°C",
        "curah_hujan": "1000–2000 mm/tahun",
        "tanah": "Regosol (asumsi literatur)",
        "rekomendasi": "Perkebunan campuran, sayuran dataran menengah, tanaman industri.",
        "komoditas": ["Jagung", "Kacang Tanah", "Tembakau", "Kopi Robusta", "Salak", "Durian"],
        "dasar_rekomendasi": "Suhu 23-26°C + CH sedang → Sleman Utara tipikal zona ini (salak pondoh, kopi robusta).",
        "warna": "#40E0D0"
    },
    "9": {
        "nama": "Zona Vc — Dataran Menengah Kering",
        "lereng": "<8%", "elevasi": "350–700 mdpl", "suhu_estimasi": "23–26°C",
        "curah_hujan": "<1000 mm/tahun",
        "tanah": "Regosol (asumsi literatur)",
        "rekomendasi": "Tanaman toleran kering, tegalan.",
        "komoditas": ["Singkong", "Kacang Tanah", "Tembakau"],
        "dasar_rekomendasi": "CH rendah di dataran menengah → pilihan komoditas terbatas, fokus tegalan.",
        "warna": "#B8860B"
    },
    "10": {
        "nama": "Zona VIa — Dataran Tinggi Basah",
        "lereng": "<8%", "elevasi": ">700 mdpl", "suhu_estimasi": "17–23°C",
        "curah_hujan": ">2000 mm/tahun",
        "tanah": "Regosol (asumsi literatur)",
        "rekomendasi": "Sayuran dataran tinggi, kopi arabika, teh. Sangat produktif.",
        "komoditas": ["Tomat", "Kentang", "Kubis", "Wortel", "Kopi Arabika", "Teh", "Jeruk", "Alpukat"],
        "dasar_rekomendasi": "Suhu 17-23°C + CH tinggi → optimal untuk sayuran dataran tinggi & kopi arabika.",
        "warna": "#9370DB"
    },
    "11": {
        "nama": "Zona VIb — Dataran Tinggi Agak Basah",
        "lereng": "<8%", "elevasi": ">700 mdpl", "suhu_estimasi": "17–23°C",
        "curah_hujan": "1000–2000 mm/tahun",
        "tanah": "Regosol (asumsi literatur)",
        "rekomendasi": "Sayuran dataran tinggi, buah subtropis, kopi arabika.",
        "komoditas": ["Kentang", "Wortel", "Kol", "Bawang Daun", "Kopi Arabika", "Stroberi", "Apel", "Markisa"],
        "dasar_rekomendasi": "Suhu 17-23°C → zona ideal sayuran premium dan buah subtropis.",
        "warna": "#8A2BE2"
    },
    "12": {
        "nama": "Zona VIc — Dataran Tinggi Kering",
        "lereng": "<8%", "elevasi": ">700 mdpl", "suhu_estimasi": "17–23°C",
        "curah_hujan": "<1000 mm/tahun",
        "tanah": "Regosol (asumsi literatur)",
        "rekomendasi": "Sayuran toleran kering, tanaman rempah dataran tinggi.",
        "komoditas": ["Bawang Daun", "Wortel", "Kol", "Kentang"],
        "dasar_rekomendasi": "CH rendah di dataran tinggi → terbatas, butuh irigasi.",
        "warna": "#DDA0DD"
    }
}

with open(OUT_INFO, 'w', encoding='utf-8') as f:
    json.dump(zae_info, f, ensure_ascii=False, indent=2)
print(f"  → Info zona disimpan: {OUT_INFO}")

# ── Statistik ─────────────────────────────────────────────────────────
print("\n── DISTRIBUSI ZONA ZAE ─────────────────────────────")
unique, counts = np.unique(zae[zae != -9999], return_counts=True)
total = counts.sum()
for u, c in zip(unique, counts):
    nama = zae_info.get(str(u), {}).get("nama", f"Zona {u}")
    pct  = c / total * 100
    print(f"  [{u:2d}] {nama}: {pct:.1f}%")

print(f"\n  → Prediksi Umbulharjo: dominan Zona 5 (dataran rendah, CH sedang)")
print(f"     Suhu estimasi: 26–30°C | CH: 1800–2200 mm/tahun")
print("\nSkrip 3 selesai ✓")
