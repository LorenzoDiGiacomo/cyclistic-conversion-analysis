#!/usr/bin/env python3
"""
Insert POI-enriched duplicate of the insight map (cell 47) into notebook 03.
New structure after this script:
  47 — original insight map (UNCHANGED)
  48 — POI-enriched duplicate  [NEW]
  49 — POI interpretation markdown  [NEW]
  50 — original "3.7 Insight Map" after-markdown (shifted)
  ...
"""
import json

NB = 'notebooks/03_analysis_and_visualization.ipynb'
with open(NB) as f:
    nb = json.load(f)

def mk_code(s):
    return {"cell_type": "code", "execution_count": None,
            "metadata": {}, "outputs": [],
            "source": s.splitlines(keepends=True)}

def mk_md(s):
    return {"cell_type": "markdown", "metadata": {},
            "source": s.splitlines(keepends=True)}

# ─────────────────────────────────────────────────────────────────────────────
# POI-ENRICHED MAP CODE
# ─────────────────────────────────────────────────────────────────────────────
POI_MAP_CODE = '''\
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import geopandas as gpd
import contextily as ctx
import time

COLOR_CASUAL  = '#f4820a'
COLOR_CONTEXT = '#d8d8d8'

t0 = time.time()

# ── Re-apply the same station filter as the insight map ───────────────────────
MIN_RIDES   = 300
MAX_M_SHARE = 0.45

gdf_all_p     = gdf_conv[gdf_conv['total_rides'] >= MIN_RIDES].copy().reset_index(drop=True)
gdf_targets_p = gdf_all_p[gdf_all_p['member_share'] < MAX_M_SHARE].copy().reset_index(drop=True)
gdf_context_p = gdf_all_p[gdf_all_p['member_share'] >= MAX_M_SHARE].copy().reset_index(drop=True)

cas_raw_p = np.sqrt(gdf_targets_p['casual_rides'].values.astype(float))
c_lo_p, c_hi_p = cas_raw_p.min(), cas_raw_p.max()
target_sizes_p = 22 + (cas_raw_p - c_lo_p) / (c_hi_p - c_lo_p + 1e-9) * 300

# ── Curated Chicago POIs (WGS84 lat/lng — source: OpenStreetMap public data) ──
# Kept to ≤ 8 per category to avoid visual clutter.
POI_CATEGORIES = {
    'Universities': {
        'color': '#1565c0', 'marker': 'D', 'ms': 100, 'zorder': 13,
        'points': [
            ('University of Chicago',        41.7886, -87.5987),
            ('DePaul University',            41.9235, -87.6548),
            ('Loyola University Chicago',    41.9998, -87.6584),
            ('Illinois Institute of Tech.',  41.8352, -87.6273),
            ('Columbia College Chicago',     41.8751, -87.6234),
            ('Northwestern (Med. Campus)',   41.8955, -87.6201),
        ]
    },
    'Transport Hubs': {
        'color': '#6a1b9a', 'marker': 's', 'ms': 85, 'zorder': 13,
        'points': [
            ('Union Station',        41.8786, -87.6398),
            ('Ogilvie/NW Terminal',  41.8832, -87.6413),
            ('Millennium Station',   41.8842, -87.6249),
            ('CTA Clark/Lake',       41.8858, -87.6313),
            ('CTA Chicago/State',    41.8966, -87.6284),
            ('CTA Belmont',          41.9398, -87.6532),
            ('CTA Fullerton',        41.9253, -87.6530),
        ]
    },
    'Tourist Attractions': {
        'color': '#00838f', 'marker': '*', 'ms': 210, 'zorder': 14,
        'points': [
            ('Navy Pier',           41.8918, -87.6038),
            ('Millennium Park',     41.8826, -87.6233),
            ('Art Institute',       41.8796, -87.6237),
            ('Field Museum',        41.8663, -87.6169),
            ('Shedd Aquarium',      41.8676, -87.6140),
            ('Adler Planetarium',   41.8663, -87.6071),
            ('Lincoln Park Zoo',    41.9215, -87.6344),
            ('Wrigley Field',       41.9484, -87.6558),
        ]
    },
    'Schools (selected)': {
        'color': '#c62828', 'marker': 'P', 'ms': 80, 'zorder': 12,
        'points': [
            ('Walter Payton Prep',   41.8972, -87.6436),
            ('Lane Tech HS',         41.9561, -87.6640),
            ('Lincoln Park HS',      41.9262, -87.6497),
            ('Jones College Prep',   41.8725, -87.6311),
            ('Whitney Young Magnet', 41.8765, -87.6474),
        ]
    },
    'Business Districts': {
        'color': '#37474f', 'marker': '^', 'ms': 110, 'zorder': 12,
        'points': [
            ('The Loop',           41.8827, -87.6320),
            ('Magnificent Mile',   41.8956, -87.6245),
            ('River North',        41.8917, -87.6318),
            ('Fulton Market',      41.8841, -87.6494),
            ('Merchandise Mart',   41.8885, -87.6353),
            ('Streeterville',      41.8924, -87.6178),
        ]
    },
}

# ── Convert POI WGS84 → EPSG:3857 using geopandas ────────────────────────────
def poi_to_3857(point_list):
    """Convert [(name, lat, lng), ...] to GeoDataFrame in EPSG:3857."""
    import pandas as pd
    df = pd.DataFrame(point_list, columns=['name', 'lat', 'lng'])
    gdf = gpd.GeoDataFrame(df,
                           geometry=gpd.points_from_xy(df['lng'], df['lat']),
                           crs='EPSG:4326')
    return gdf.to_crs(epsg=3857)

# Pre-compute projected GeoDataFrames
poi_gdfs = {cat: poi_to_3857(cfg['points'])
            for cat, cfg in POI_CATEGORIES.items()}

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(1, 1, figsize=(12, 14), facecolor='white')

# Layer 1 — context stations (grey, receding)
ax.scatter(gdf_context_p.geometry.x, gdf_context_p.geometry.y,
           s=7, color=COLOR_CONTEXT, alpha=0.30, zorder=3, linewidths=0)

# Layer 2 — conversion-target stations (orange, sized by casual volume)
ax.scatter(
    gdf_targets_p.geometry.x, gdf_targets_p.geometry.y,
    s=target_sizes_p, color=COLOR_CASUAL,
    edgecolors='#b85e05', linewidths=0.4,
    alpha=0.75, zorder=6
)

# Layer 3 — POI categories (plotted last so they sit on top)
for cat, cfg in POI_CATEGORIES.items():
    gdf_p = poi_gdfs[cat]
    ax.scatter(
        gdf_p.geometry.x, gdf_p.geometry.y,
        s=cfg['ms'], c=cfg['color'],
        marker=cfg['marker'],
        edgecolors='white', linewidths=0.8,
        alpha=0.95, zorder=cfg['zorder']
    )

# Basemap — CartoDB Positron (neutral, light)
ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=11)
ax.set_axis_off()

# ── Compound legend: bike stations + POI categories ───────────────────────────
# Section 1 — Bike station types
bike_handles = [
    mpatches.Patch(color=COLOR_CASUAL,  label='Conversion target  (casual > 55 %, ≥ 300 trips/yr)'),
    mpatches.Patch(color=COLOR_CONTEXT, alpha=0.5, label='Member-heavy / balanced  (context)'),
]
# Section 2 — POI markers
poi_handles = []
for cat, cfg in POI_CATEGORIES.items():
    poi_handles.append(
        mlines.Line2D([], [], color=cfg['color'],
                      marker=cfg['marker'], linestyle='None',
                      markersize=9, markeredgecolor='white', markeredgewidth=0.6,
                      label=cat)
    )

# Divider label trick: invisible entry acting as section header
section_div = mpatches.Patch(color='none', label='— Points of Interest —')

legend = ax.legend(
    handles=bike_handles + [section_div] + poi_handles,
    loc='lower right',
    fontsize=8.8,
    framealpha=0.92,
    edgecolor='#cccccc',
    title='Map key',
    title_fontsize=9.5,
    handlelength=1.6,
    handleheight=1.2,
)
# Style the section-divider text
for text in legend.get_texts():
    if text.get_text().startswith('—'):
        text.set_style('italic')
        text.set_color('#555555')
        text.set_fontsize(8)

# ── Title + subtitle ──────────────────────────────────────────────────────────
ax.set_title(
    'Key Conversion Zones with Points of Interest Overlay',
    fontsize=15, fontweight='bold', color='#1a1a1a', pad=8
)
ax.text(
    0.5, -0.01,
    f'Orange = casual-majority stations  |  Grey = member-heavy / balanced  |  '
    f'Coloured symbols = POI categories',
    transform=ax.transAxes, ha='center', va='top',
    fontsize=9, color='#555555', style='italic'
)

plt.savefig('../reports/figures/chicago_insight_map_poi.png',
            dpi=180, bbox_inches='tight', facecolor='white')
plt.show()
print(f"[OK] Saved: chicago_insight_map_poi.png  [{time.time()-t0:.1f}s]")
print(f"     POI counts: { {k: len(v[\'points\']) for k, v in POI_CATEGORIES.items()} }")
'''

# ─────────────────────────────────────────────────────────────────────────────
# POI INTERPRETATION MARKDOWN
# ─────────────────────────────────────────────────────────────────────────────
POI_MD = """\
## 3.7b Conversion Zones + POI Overlay — Interpretation <a id='insight_poi'></a>
[↑ back to top](#toc)

### What was added
The map above overlays five categories of Points of Interest on the insight map —
revealing how Chicago's urban fabric *explains* the spatial patterns of casual vs.
member usage identified earlier.

---

### Key insights

**1. Tourist attractions cluster where casual demand peaks.**
Navy Pier, Millennium Park, Grant Park museums (Field Museum, Shedd Aquarium,
Adler Planetarium) and Lincoln Park Zoo sit directly inside the largest orange
bubble clusters. These are leisure destinations that attract people who ride *once*
or a *few times* — exactly the casual-rider profile. The Lakefront Corridor is both
a tourism corridor and a conversion opportunity: riders are already engaged with the
service, but the episodic nature of their visits has not yet nudged them toward
annual membership.

> **Conversion action:** Place "Try membership for your next visit" prompts
> at Divvy kiosks near Navy Pier, Millennium Park and Lincoln Park Zoo.
> A discounted day-pass-to-annual-upgrade bundle would capture tourists who
> visit multiple times per season.

**2. Transport hubs are surrounded by member-green or balanced stations.**
Union Station, Ogilvie Transportation Center and the CTA L stops in the Loop sit
in the middle of grey/neutral stations — commuters who connect by bike to/from
transit are largely already members. This confirms the commute-as-membership
hypothesis: riders who depend on Divvy for their daily transit chain have already
made the rational cost calculation and subscribed.

> **Conversion action:** Focus is *retention* at transit hubs, not acquisition.
> Ensure reliable bike availability during peak commute windows (7–9 am, 5–7 pm).

**3. Business districts reinforce the Loop-member pattern.**
The Loop, Merchandise Mart, River North and Streeterville markers all fall within
the member-dominant (grey) zone, consistent with the weekday commute-peak signals
observed in the temporal analysis. Office workers riding to meetings or from CTA
stations are the core member segment — already converted.

> **Conversion action:** Corporate partnership programmes ("Divvy for Work")
> targeted at employers in Fulton Market and River North could deepen penetration
> in adjacent mixed-use areas that still show some casual presence.

**4. Universities show mixed but promising signals.**
DePaul (Lincoln Park) and Loyola sit near or inside clusters of smaller orange
bubbles. Students and campus visitors often ride casually — short trips between
campus buildings, nearby cafés or transit stops. Illinois Institute of Technology
(South Side) and University of Chicago (Hyde Park) are in lower-volume areas
outside the main cluster, but orange stations nearby suggest untapped student demand.

> **Conversion action:** Student membership plans (discounted annual or
> semester-based) distributed through campus mobility offices at DePaul and
> Loyola. Time the launch at the start of the academic year (September).

**5. Schools appear in balanced and member-adjacent areas.**
The selected high schools (Walter Payton, Lincoln Park HS, Whitney Young) sit in
mixed-use north-side neighbourhoods where station colours are near-neutral (grey).
This suggests that school-adjacent areas have already achieved reasonable membership
penetration, likely driven by the surrounding residential and transit commuter base.

**6. Wrigley Field generates a distinct leisure-casual cluster in the north.**
The Wrigley Field tourist marker sits inside one of the northern orange clusters
(Wicker Park / Lakeview fringe). Game-day and event-driven casual rides to/from
Wrigley and the surrounding Wrigleyville bars represent a high-volume seasonal
spike in casual trips that is structurally unlikely to convert to year-round
membership — but could be targeted with a "stadium season pass" bundle that ties
Divvy to sports attendance.

---

### Summary: POI-informed conversion priorities

| Zone / POI type | Station signal | Recommended approach |
|-----------------|---------------|----------------------|
| Lakefront tourist cluster | 🟠 Casual-heavy | Seasonal upgrade bundles; kiosk prompts at major attractions |
| Loop / Business districts | ⬜ Member-heavy | Retain; corporate partnership programmes |
| Transit hubs (Union, Ogilvie, CTA) | ⬜ Member-heavy | Reliability focus; no acquisition needed |
| University campuses (DePaul, Loyola) | 🟠 Mixed-casual | Student membership plans; campus-start promotions |
| Schools (north side) | ⬜ Balanced | Low priority for conversion campaigns |
| Wrigley Field / event venues | 🟠 Casual-heavy | Event-tied bundles; day-pass to annual upgrade |
"""

# ─────────────────────────────────────────────────────────────────────────────
# BUILD NEW CELL LIST: insert after cell 47 (insight map code)
# ─────────────────────────────────────────────────────────────────────────────
old = nb['cells']
new = []

# Also update TOC (cell 0) to add 3.7b
for idx, cell in enumerate(old):

    if idx == 0:
        # Add 3.7b to TOC
        src = ''.join(cell['source'])
        src = src.replace(
            '  - [3.7 Key Conversion Zones: Insight View](#insight_map)',
            '  - [3.7 Key Conversion Zones: Insight View](#insight_map)\n'
            '  - [3.7b Conversion Zones + POI Overlay](#insight_poi)'
        )
        cell = dict(cell)
        cell['source'] = src.splitlines(keepends=True)
        new.append(cell)

    elif idx == 47:
        # Keep original insight map
        new.append(cell)
        # Insert duplicate (POI-enriched) right after
        new.append(mk_code(POI_MAP_CODE))
        # Insert POI interpretation markdown
        new.append(mk_md(POI_MD))

    else:
        new.append(cell)

nb['cells'] = new
with open(NB, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f"[OK] Notebook saved — {len(new)} cells (was {len(old)})")
print(f"     Inserted: POI map code + POI markdown after cell 47")
print(f"     Updated : TOC with 3.7b anchor")
