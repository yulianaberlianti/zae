# WebGIS ZAE – Kecamatan Umbulharjo, Kota Yogyakarta
## Zona Agro-Ekologi untuk Smart Agriculture Perkotaan

---

## Struktur Folder
```
project_zae/
├── data/
│   ├── DEMNAS_1408-22_v1.0.tif       ← taruh di sini (dari BIG)
│   └── curah_hujan_2025.csv          ← sudah tersedia (5 stasiun DIY)
├── output/                            ← auto-generated saat skrip dijalankan
│   ├── slope.tif
│   ├── slope_classified.tif
│   ├── elevation_classified.tif
│   ├── rainfall_interpolated.tif
│   ├── rainfall_classified.tif
│   ├── zae_final.tif
│   ├── zae_info.json
│   ├── zae_zones.geojson
│   └── index.html                    ← WebGIS final (buka di browser)
├── 1_terrain_analysis.py
├── 2_climate_interpolation.py
├── 3_zae_classification.py
├── 4_export_geojson.py
├── 5_webgis.py
└── README.md
```

---

## Instalasi Library

```bash
pip install geopandas rasterio numpy pandas matplotlib folium scipy shapely
```

> Untuk environment Conda:
> ```bash
> conda install -c conda-forge geopandas rasterio numpy pandas scipy shapely
> ```

---

## Format CSV Curah Hujan

File `data/curah_hujan_2025.csv` sudah disiapkan dengan **5 stasiun wilayah DIY**:

| Kolom | Keterangan |
|-------|-----------|
| `stasiun` | Nama stasiun |
| `lat` | Lintang (desimal, negatif = selatan) |
| `lon` | Bujur (desimal) |
| `jan`–`des` | Curah hujan bulanan (mm) |

Minimal **3 stasiun** dibutuhkan untuk interpolasi IDW.

Jika ingin menggunakan data BMKG sendiri, pastikan format kolomnya sama.

---

## Cara Menjalankan (urutan wajib)

```bash
# 1. Analisis terrain DEM → slope + elevasi
python 1_terrain_analysis.py

# 2. Interpolasi curah hujan IDW
python 2_climate_interpolation.py

# 3. Klasifikasi ZAE (overlay 3 layer)
python 3_zae_classification.py

# 4. Export ZAE raster → GeoJSON
python 4_export_geojson.py

# 5. Generate WebGIS HTML
python 5_webgis.py

# Buka hasil di browser:
# → output/index.html
```

---

## Zonasi ZAE

### Zona berdasarkan lereng (prioritas utama)

| Kode | Nama | Lereng | Keterangan |
|------|------|--------|-----------|
| 1 | Kawasan Lindung | >40% | Konservasi, tidak untuk pertanian |
| 2 | Perkebunan Tahunan | 16–40% | Tanaman keras pengikat tanah |
| 3 | Wanatani/Agroforestri | 8–15% | Campuran pohon + tanaman pangan |

### Zona dataran (lereng <8%) berdasarkan Elevasi × Curah Hujan

| Kode | Nama | Elevasi | Curah Hujan |
|------|------|---------|------------|
| 4 | Dataran Rendah Basah | <350 m | >2000 mm |
| 5 | **Dataran Rendah Agak Basah** ← *Umbulharjo* | <350 m | 1000–2000 mm |
| 6 | Dataran Rendah Kering | <350 m | <1000 mm |
| 7 | Dataran Menengah Basah | 350–700 m | >2000 mm |
| 8 | Dataran Menengah Agak Basah | 350–700 m | 1000–2000 mm |
| 9 | Dataran Menengah Kering | 350–700 m | <1000 mm |
| 10 | Dataran Tinggi Basah | >700 m | >2000 mm |
| 11 | Dataran Tinggi Agak Basah | >700 m | 1000–2000 mm |
| 12 | Dataran Tinggi Kering | >700 m | <1000 mm |

> **Umbulharjo diperkirakan dominan Zona 5** (topografi datar perkotaan, elevasi ~110 mdpl, CH ~1800–2300 mm/tahun).

---

## Asumsi Data Tanah (Literatur)

- **Jenis tanah**: Regosol (pasiran vulkanik Merapi)
- **pH**: 5.5–6.5 (agak asam–netral)
- **Tekstur**: Pasir berlempung
- **Drainase**: Cepat–sedang
- **Sumber**: BBSDLP (2014), Peta Tanah Tinjau DIY

> Data tanah menggunakan asumsi literatur. Validasi lapangan disarankan sebelum implementasi pertanian.

---

## Fitur WebGIS (output/index.html)

- ✅ Peta interaktif Leaflet.js
- ✅ Toggle basemap: OSM ↔ Satelit (Esri World Imagery)
- ✅ Klik zona → popup info lengkap (karakteristik + komoditas)
- ✅ **Simulasi komoditas**: pilih komoditas → highlight zona yang cocok
- ✅ Info panel sidebar real-time
- ✅ Legenda interaktif (klik → tampilkan info zona)
- ✅ Statistik jumlah zona & komoditas

---

## Deploy ke GitHub Pages

1. Buat repo GitHub baru (public)
2. Upload **seluruh isi folder `output/`** ke root repo
3. Buka **Settings → Pages → Deploy from branch → main → / (root)**
4. Tunggu ~1–2 menit, akses: `https://username.github.io/nama-repo/`

---

## Troubleshooting

| Error | Solusi |
|-------|--------|
| `FileNotFoundError: DEMNAS...tif` | Letakkan file DEMNAS di folder `data/` |
| `ValueError: Kolom lat/lon tidak ditemukan` | Cek format CSV: harus ada kolom `lat` dan `lon` |
| `ValueError: Minimal 3 stasiun` | CSV harus punya minimal 3 baris data stasiun |
| `rasterio.errors.NotGeoreferencedWarning` | Cek CRS raster dengan `gdalinfo data/DEMNAS...tif` |
| `output/slope.tif not found` di skrip 2 | Jalankan skrip 1 dulu |
| GeoJSON kosong / WebGIS peta tidak muncul | Cek apakah skrip 1–4 berhasil semua |
| IDW lambat | Sudah dioptimasi di v2 (vectorized numpy) |

---

## Tim

| Nama | Peran |
|------|-------|
| Tyas Wijayanti | Koordinator & Laporan |
| Yuliana Berlianti | Analisis Parameter (Terrain + Iklim + Tanah) |
| Tuhfatul Atiqoh | GIS Analyst & Spatial Overlay |
| Shalna | Map Layout & Cartographer |
| Gita | WebGIS Developer |
| Afiqoh Izzah Aliyah | Verifikasi & Metodologi |
| Hilaliyyah Hafidz | Komoditas & Strategi |

---

*ZAE Umbulharjo | Smart Agriculture Platform | Teknik Geomatika UPNYK 2025*
