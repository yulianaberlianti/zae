"""
SKRIP 5 - GENERATE WEBGIS HTML
ZAE Kecamatan Umbulharjo, Kota Yogyakarta
------------------------------------------
Input  : output/zae_zones.geojson
Output : output/index.html

WebGIS Features:
  - Peta interaktif Leaflet.js
  - Layer ZAE per zona dengan warna berbeda
  - Klik zona → popup info lengkap (karakteristik + komoditas)
  - Layer control (basemap toggle: OSM / Satellite)
  - Legend
  - Simulasi filter komoditas (user pilih komoditas → highlight zona)
  - Info panel kanan
  - Responsive design
"""

import json
import os

# ── Path ──────────────────────────────────────────────────────────────
GEOJSON_PATH = "output/zae_zones.geojson"
OUT_HTML     = "output/index.html"

# ── Baca GeoJSON ───────────────────────────────────────────────────────
print("Membaca GeoJSON...")
with open(GEOJSON_PATH, 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)

geojson_str = json.dumps(geojson_data, ensure_ascii=False)
print(f"  Total fitur: {len(geojson_data['features'])}")

# ── Komoditas master list (untuk fitur simulasi) ───────────────────────
all_komoditas = set()
for feat in geojson_data['features']:
    kmd = feat['properties'].get('komoditas', '')
    if kmd:
        for k in kmd.split(', '):
            all_komoditas.add(k.strip())
all_komoditas = sorted(all_komoditas)
komoditas_options = '\n'.join(
    f'<option value="{k}">{k}</option>' for k in all_komoditas
)

# ── HTML ───────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>WebGIS ZAE - Kecamatan Umbulharjo, Kota Yogyakarta</title>

  <!-- Leaflet CSS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>

  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}

    body {{
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: #0f1117;
      color: #e0e0e0;
      height: 100vh;
      display: flex;
      flex-direction: column;
    }}

    /* ── Header ── */
    header {{
      background: linear-gradient(135deg, #1a2f1a, #2d4a2d);
      padding: 12px 20px;
      display: flex;
      align-items: center;
      gap: 14px;
      border-bottom: 2px solid #4a7c4a;
      flex-shrink: 0;
    }}
    header .logo {{
      width: 36px; height: 36px;
      background: #4a7c4a;
      border-radius: 8px;
      display: flex; align-items: center; justify-content: center;
      font-size: 20px;
    }}
    header h1 {{
      font-size: 16px;
      font-weight: 700;
      color: #a8d5a2;
      line-height: 1.2;
    }}
    header p {{
      font-size: 11px;
      color: #6b9e6b;
    }}
    .header-right {{
      margin-left: auto;
      font-size: 11px;
      color: #6b9e6b;
      text-align: right;
    }}

    /* ── Main layout ── */
    .main {{
      display: flex;
      flex: 1;
      overflow: hidden;
    }}

    /* ── Sidebar kiri ── */
    .sidebar {{
      width: 300px;
      background: #161b22;
      border-right: 1px solid #2d3748;
      display: flex;
      flex-direction: column;
      overflow-y: auto;
      flex-shrink: 0;
    }}

    .sidebar-section {{
      padding: 14px;
      border-bottom: 1px solid #2d3748;
    }}
    .sidebar-section h3 {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #6b9e6b;
      margin-bottom: 10px;
    }}

    /* Filter komoditas */
    .filter-select {{
      width: 100%;
      padding: 8px 10px;
      background: #1f2937;
      border: 1px solid #374151;
      border-radius: 6px;
      color: #e0e0e0;
      font-size: 13px;
      margin-bottom: 8px;
    }}
    .btn {{
      width: 100%;
      padding: 8px;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 600;
      transition: all 0.2s;
    }}
    .btn-primary {{
      background: #4a7c4a;
      color: white;
    }}
    .btn-primary:hover {{ background: #5a9c5a; }}
    .btn-secondary {{
      background: #374151;
      color: #9ca3af;
      margin-top: 4px;
    }}
    .btn-secondary:hover {{ background: #4b5563; }}

    /* Legenda */
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 5px 0;
      font-size: 12px;
      cursor: pointer;
      border-radius: 4px;
      padding: 5px 6px;
      transition: background 0.15s;
    }}
    .legend-item:hover {{ background: #1f2937; }}
    .legend-color {{
      width: 16px; height: 16px;
      border-radius: 3px;
      flex-shrink: 0;
      border: 1px solid rgba(255,255,255,0.2);
    }}
    .legend-label {{ font-size: 11px; line-height: 1.3; color: #d1d5db; }}

    /* Info panel */
    #info-panel {{
      background: #1f2937;
      border-radius: 8px;
      padding: 12px;
      font-size: 12px;
      line-height: 1.6;
      min-height: 80px;
      color: #9ca3af;
    }}
    #info-panel.active {{ color: #e0e0e0; }}
    #info-panel h4 {{
      color: #a8d5a2;
      font-size: 13px;
      margin-bottom: 8px;
    }}
    #info-panel .info-row {{
      display: flex;
      gap: 6px;
      margin-bottom: 4px;
    }}
    #info-panel .info-label {{
      color: #6b9e6b;
      min-width: 90px;
      font-weight: 600;
    }}
    .komoditas-tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      margin-top: 6px;
    }}
    .tag {{
      background: #374151;
      border: 1px solid #4a7c4a;
      color: #a8d5a2;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 11px;
    }}
    .tag.highlight {{ background: #4a7c4a; color: white; }}

    /* Map */
    #map {{
      flex: 1;
      z-index: 1;
    }}

    /* Leaflet popup custom */
    .leaflet-popup-content-wrapper {{
      background: #1f2937;
      color: #e0e0e0;
      border: 1px solid #374151;
      border-radius: 10px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    }}
    .leaflet-popup-tip {{ background: #1f2937; }}
    .popup-title {{
      font-size: 14px;
      font-weight: 700;
      color: #a8d5a2;
      margin-bottom: 10px;
      padding-bottom: 8px;
      border-bottom: 1px solid #374151;
    }}
    .popup-row {{
      display: flex;
      gap: 8px;
      margin-bottom: 5px;
      font-size: 12px;
    }}
    .popup-label {{
      color: #6b9e6b;
      min-width: 90px;
      font-weight: 600;
    }}
    .popup-komoditas {{
      margin-top: 8px;
      padding-top: 8px;
      border-top: 1px solid #374151;
    }}
    .popup-komoditas-label {{
      color: #6b9e6b;
      font-size: 11px;
      font-weight: 600;
      margin-bottom: 4px;
    }}

    /* Loading overlay */
    #loading {{
      position: fixed;
      inset: 0;
      background: #0f1117;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      z-index: 9999;
    }}
    .spinner {{
      width: 48px; height: 48px;
      border: 4px solid #2d4a2d;
      border-top-color: #4a7c4a;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      margin-bottom: 16px;
    }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

    /* Stats bar */
    .stats-bar {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .stat-chip {{
      background: #1f2937;
      border: 1px solid #374151;
      border-radius: 6px;
      padding: 6px 10px;
      font-size: 11px;
      text-align: center;
      flex: 1;
    }}
    .stat-chip .val {{
      font-size: 16px;
      font-weight: 700;
      color: #a8d5a2;
      display: block;
    }}
  </style>
</head>
<body>

<!-- Loading -->
<div id="loading">
  <div class="spinner"></div>
  <p style="color:#6b9e6b; font-size:14px;">Memuat WebGIS ZAE Umbulharjo...</p>
</div>

<!-- Header -->
<header>
  <div class="logo">🌿</div>
  <div>
    <h1>WebGIS Zona Agro-Ekologi (ZAE)</h1>
    <p>Kecamatan Umbulharjo, Kota Yogyakarta | Smart Agriculture Platform</p>
  </div>
  <div class="header-right">
    <div>Data: DEMNAS BIG + BMKG 2025</div>
    <div>Metode: Overlay Multi-Parameter</div>
  </div>
</header>

<!-- Main -->
<div class="main">

  <!-- Sidebar -->
  <div class="sidebar">

    <!-- Statistik -->
    <div class="sidebar-section">
      <h3>Statistik Wilayah</h3>
      <div class="stats-bar">
        <div class="stat-chip">
          <span class="val" id="stat-zona">-</span>
          Zona
        </div>
        <div class="stat-chip">
          <span class="val" id="stat-komoditas">-</span>
          Komoditas
        </div>
        <div class="stat-chip">
          <span class="val">7</span>
          Kelurahan
        </div>
      </div>
    </div>

    <!-- Simulasi Komoditas -->
    <div class="sidebar-section">
      <h3>🔍 Simulasi Komoditas</h3>
      <p style="font-size:11px; color:#6b9e6b; margin-bottom:8px;">
        Pilih komoditas untuk highlight zona yang sesuai
      </p>
      <select class="filter-select" id="komoditas-select">
        <option value="">— Pilih Komoditas —</option>
        {komoditas_options}
      </select>
      <button class="btn btn-primary" onclick="filterKomoditas()">Tampilkan Zona</button>
      <button class="btn btn-secondary" onclick="resetFilter()">Reset</button>
    </div>

    <!-- Info Panel -->
    <div class="sidebar-section">
      <h3>📍 Info Zona</h3>
      <div id="info-panel">
        <p>Klik zona di peta untuk melihat detail karakteristik lahan dan rekomendasi komoditas.</p>
      </div>
    </div>

    <!-- Legenda -->
    <div class="sidebar-section">
      <h3>Legenda Zona ZAE</h3>
      <div id="legend-container"></div>
    </div>

    <!-- Catatan -->
    <div class="sidebar-section">
      <h3>⚠️ Catatan</h3>
      <p style="font-size:11px; color:#6b9e6b; line-height:1.6;">
        Data tanah menggunakan asumsi literatur (Regosol, BBSDLP 2014).
        Validasi lapangan disarankan sebelum implementasi.
      </p>
    </div>

  </div>

  <!-- Map -->
  <div id="map"></div>
</div>

<!-- Leaflet JS -->
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<script>
// ── Data GeoJSON ───────────────────────────────────────────────────────
const geojsonData = {geojson_str};

// ── Inisialisasi Peta ──────────────────────────────────────────────────
const map = L.map('map', {{
  center: [-7.82, 110.39],  // Umbulharjo
  zoom: 14,
  zoomControl: true
}});

// Basemap
const osmLayer = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  attribution: '© OpenStreetMap contributors',
  maxZoom: 19
}});

const satelliteLayer = L.tileLayer(
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
  attribution: '© Esri World Imagery',
  maxZoom: 19
}});

osmLayer.addTo(map);

L.control.layers(
  {{ 'OpenStreetMap': osmLayer, 'Satelit': satelliteLayer }},
  {{}},
  {{ position: 'topright' }}
).addTo(map);

// ── State ──────────────────────────────────────────────────────────────
let zaeLayer = null;
let selectedKomoditas = '';
let selectedLayer = null;

// ── Fungsi Warna ───────────────────────────────────────────────────────
function getColor(props) {{
  return props.warna || '#888888';
}}

function getStyle(feature) {{
  const kmd = feature.properties.komoditas || '';
  const isHighlight = selectedKomoditas && kmd.includes(selectedKomoditas);
  const isNone      = selectedKomoditas && !kmd.includes(selectedKomoditas);
  return {{
    fillColor: getColor(feature.properties),
    weight: isHighlight ? 3 : 1,
    opacity: 1,
    color: isHighlight ? '#ffffff' : '#333333',
    fillOpacity: isNone ? 0.15 : 0.65
  }};
}}

// ── Popup ──────────────────────────────────────────────────────────────
function buildPopup(props) {{
  const tags = (props.komoditas || '').split(', ').map(k => {{
    const isMatch = selectedKomoditas && k === selectedKomoditas;
    return `<span class="tag ${{isMatch ? 'highlight' : ''}}">${{k}}</span>`;
  }}).join('');

  return `
    <div style="min-width:240px">
      <div class="popup-title">${{props.nama}}</div>
      <div class="popup-row"><span class="popup-label">Lereng</span><span>${{props.lereng}}</span></div>
      <div class="popup-row"><span class="popup-label">Elevasi</span><span>${{props.elevasi}}</span></div>
      <div class="popup-row"><span class="popup-label">Curah Hujan</span><span>${{props.curah_hujan}}</span></div>
      <div class="popup-row"><span class="popup-label">Tanah</span><span>${{props.tanah}}</span></div>
      <div class="popup-row"><span class="popup-label">Rekomendasi</span><span style="font-size:11px">${{props.rekomendasi}}</span></div>
      ${{props.komoditas ? `
      <div class="popup-komoditas">
        <div class="popup-komoditas-label">🌱 Komoditas yang Sesuai</div>
        <div class="komoditas-tags">${{tags}}</div>
      </div>` : ''}}
    </div>
  `;
}}

// ── Info Panel (sidebar) ───────────────────────────────────────────────
function updateInfoPanel(props) {{
  const tags = (props.komoditas || '').split(', ').map(k => {{
    const isMatch = selectedKomoditas && k === selectedKomoditas;
    return `<span class="tag ${{isMatch ? 'highlight' : ''}}">${{k}}</span>`;
  }}).join('');

  document.getElementById('info-panel').className = 'active';
  document.getElementById('info-panel').innerHTML = `
    <h4>${{props.nama}}</h4>
    <div class="info-row"><span class="info-label">Lereng</span><span>${{props.lereng}}</span></div>
    <div class="info-row"><span class="info-label">Elevasi</span><span>${{props.elevasi}}</span></div>
    <div class="info-row"><span class="info-label">Curah Hujan</span><span>${{props.curah_hujan}}</span></div>
    <div class="info-row"><span class="info-label">Tanah</span><span>${{props.tanah}}</span></div>
    <div class="info-row"><span class="info-label">Rekomendasi</span><span style="font-size:11px">${{props.rekomendasi}}</span></div>
    ${{props.komoditas ? `
    <div style="margin-top:8px;">
      <div style="color:#6b9e6b; font-size:11px; font-weight:600; margin-bottom:4px;">🌱 Komoditas</div>
      <div class="komoditas-tags">${{tags}}</div>
    </div>` : ''}}
  `;
}}

// ── Render Layer ZAE ───────────────────────────────────────────────────
function renderLayer() {{
  if (zaeLayer) map.removeLayer(zaeLayer);

  zaeLayer = L.geoJSON(geojsonData, {{
    style: getStyle,
    onEachFeature: function(feature, layer) {{
      const props = feature.properties;

      layer.on('click', function(e) {{
        layer.bindPopup(buildPopup(props)).openPopup(e.latlng);
        updateInfoPanel(props);
        L.DomEvent.stopPropagation(e);
      }});

      layer.on('mouseover', function() {{
        layer.setStyle({{ weight: 2.5, color: '#ffffff', fillOpacity: 0.8 }});
      }});
      layer.on('mouseout', function() {{
        zaeLayer.resetStyle(layer);
      }});
    }}
  }}).addTo(map);

  // Fit bounds ke data
  if (zaeLayer.getBounds().isValid()) {{
    map.fitBounds(zaeLayer.getBounds(), {{ padding: [20, 20] }});
  }}
}}

// ── Filter Komoditas ───────────────────────────────────────────────────
function filterKomoditas() {{
  selectedKomoditas = document.getElementById('komoditas-select').value;
  if (!selectedKomoditas) {{ alert('Pilih komoditas terlebih dahulu!'); return; }}
  renderLayer();

  // Cari zona yang cocok dan zoom ke sana
  let matchBounds = null;
  geojsonData.features.forEach(f => {{
    if ((f.properties.komoditas || '').includes(selectedKomoditas)) {{
      const b = L.geoJSON(f).getBounds();
      matchBounds = matchBounds ? matchBounds.extend(b) : b;
    }}
  }});
  if (matchBounds && matchBounds.isValid()) {{
    map.fitBounds(matchBounds, {{ padding: [30, 30] }});
  }}
}}

function resetFilter() {{
  selectedKomoditas = '';
  document.getElementById('komoditas-select').value = '';
  renderLayer();
  document.getElementById('info-panel').className = '';
  document.getElementById('info-panel').innerHTML =
    '<p>Klik zona di peta untuk melihat detail karakteristik lahan dan rekomendasi komoditas.</p>';
}}

// ── Legenda ────────────────────────────────────────────────────────────
function buildLegend() {{
  const container = document.getElementById('legend-container');
  const zones = {{}};
  geojsonData.features.forEach(f => {{
    const p = f.properties;
    if (!zones[p.zona_kode]) zones[p.zona_kode] = p;
  }});

  Object.keys(zones).sort().forEach(kode => {{
    const p = zones[kode];
    const div = document.createElement('div');
    div.className = 'legend-item';
    div.innerHTML = `
      <div class="legend-color" style="background:${{p.warna}}"></div>
      <span class="legend-label">${{p.nama}}</span>
    `;
    div.onclick = () => updateInfoPanel(p);
    container.appendChild(div);
  }});
}}

// ── Statistik ──────────────────────────────────────────────────────────
function updateStats() {{
  const zonaCount = new Set(geojsonData.features.map(f => f.properties.zona_kode)).size;
  const kmdSet = new Set();
  geojsonData.features.forEach(f => {{
    (f.properties.komoditas || '').split(', ').forEach(k => {{ if(k) kmdSet.add(k); }});
  }});
  document.getElementById('stat-zona').textContent = zonaCount;
  document.getElementById('stat-komoditas').textContent = kmdSet.size;
}}

// ── Init ───────────────────────────────────────────────────────────────
window.addEventListener('load', function() {{
  renderLayer();
  buildLegend();
  updateStats();
  document.getElementById('loading').style.display = 'none';
}});
</script>
</body>
</html>"""

# ── Simpan HTML ────────────────────────────────────────────────────────
with open(OUT_HTML, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"WebGIS HTML disimpan: {OUT_HTML}")
print(f"Buka file {OUT_HTML} di browser untuk melihat hasilnya.")
print("\n✓ Semua skrip selesai!")
print("\nCara deploy ke GitHub Pages:")
print("  1. Buat repo GitHub baru")
print("  2. Upload seluruh folder output/")
print("  3. Settings → Pages → Deploy from branch → main / root")
print("  4. Akses via https://username.github.io/nama-repo/")
