# WebGIS ZAE - Kecamatan Umbulharjo, Kota Yogyakarta
## Zona Agro-Ekologi untuk Smart Agriculture Perkotaan

---

## Struktur Folder
```
project_zae/
├── data/
│   ├── DEMNAS_1408-22_v1.0.tif       ← taruh di sini
│   └── curah_hujan_2025.csv          ← taruh di sini
├── output/                            ← auto-generated
│   ├── slope.tif
│   ├── slope_classified.tif
│   ├── elevation_classified.tif
│   ├── rainfall_interpolated.tif
│   ├── rainfall_classified.tif
│   ├── zae_final.tif
│   ├── zae_info.json
│   ├── zae_zones.geojson
│   └── index.html                    ← WebGIS final
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

---

## Format CSV yang Diharapkan
```
stasiun,lat,lon,jan,feb,mar,apr,mei,jun,jul,agu,sep,okt,nov,des
Stasiun Mlati,-7.73,110.35,320,280,250,200,150,80,60,40,90,200,280,310
Stasiun Jetis,-7.78,110.37,310,270,240,190,140,75,55,38,85,195,270,300
...
```
**Minimal butuh 3 stasiun** untuk interpolasi IDW yang representatif.

---

## Cara Menjalankan (urutan)

```bash
# 1. Analisis terrain DEM
python 1_terrain_analysis.py

# 2. Interpolasi curah hujan
python 2_climate_interpolation.py

# 3. Klasifikasi ZAE
python 3_zae_classification.py

# 4. Export ke GeoJSON
python 4_export_geojson.py

# 5. Generate WebGIS HTML
python 5_webgis.py

# Buka hasil
# → output/index.html (buka di browser)
```

---

## Penjelasan Zonasi ZAE

| Kode | Nama Zona | Lereng | Elevasi | Rekomendasi |
|------|-----------|--------|---------|-------------|
| 1 | Kawasan Lindung | >40% | Bervariasi | Konservasi |
| 2 | Hutan/Perkebunan | 16–40% | Bervariasi | Jati, Sengon |
| 3 | Agroforestri | 8–15% | Bervariasi | Pisang, Singkong |
| 4 | Pertanian Intensif | <8% | <350 mdpl | Padi, Jagung (CH tinggi) |
| 5 | Urban Farming | <8% | <350 mdpl | Sayuran, Toga, Hidroponik |
| 6 | Pertanian Kering | <8% | <350 mdpl | Ubi, Kacang (CH rendah) |
| 7 | Rooftop/Vertikal | <8% | 350–700 mdpl | Selada, Pakcoy, Microgreens |

> Umbulharjo diperkirakan **dominan Zona 5 (Urban Farming)** karena topografi datar perkotaan.

---

## Asumsi Data Tanah (Literatur)
- **Jenis tanah**: Regosol (pasiran vulkanik Merapi)
- **pH**: 5.5–6.5 (agak asam–netral)
- **Tekstur**: Pasir berlempung
- **Drainase**: Cepat–sedang
- **Sumber**: BBSDLP (2014), Peta Tanah Tinjau DIY

---

## Fitur WebGIS
- ✅ Peta interaktif Leaflet.js
- ✅ Toggle basemap OSM ↔ Satelit
- ✅ Klik zona → popup info lengkap
- ✅ **Simulasi komoditas**: pilih komoditas → highlight zona yang sesuai
- ✅ Info panel sidebar real-time
- ✅ Legenda interaktif
- ✅ Statistik zona & komoditas

---

## Deploy ke GitHub Pages
1. Buat repo GitHub baru (public)
2. Upload semua file di folder `output/`
3. **Settings → Pages → Deploy from branch → main → / (root)**
4. Akses: `https://username.github.io/nama-repo/`

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
*ZAE Umbulharjo | Smart Agriculture Platform | UPNYK 2025*
