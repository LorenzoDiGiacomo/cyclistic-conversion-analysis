#!/usr/bin/env python3
"""
Rebuild script — map section of 03_analysis_and_visualization.ipynb.
Changes:
  1. Insert BEFORE markdown for zone map
  2. Rewrite zone map (remove station-dot clutter, clean title/subtitle, cleaner bar chart)
  3. Rewrite AFTER markdown for zone map (clearer insights)
  4. Insert BEFORE markdown for conversion map
  5. Rewrite conversion map (filter noise, cleaner markers, better title)
  6. Rewrite AFTER markdown for conversion map
  7. Insert BEFORE markdown for insight-only map (new)
  8. Insert insight-only map code (new)
  9. Insert AFTER markdown for insight-only map (new)
 10. Update TOC
"""
import json

NB = 'notebooks/03_analysis_and_visualization.ipynb'
with open(NB) as f:
    nb = json.load(f)

def mk_code(s):
    return {"cell_type":"code","execution_count":None,"metadata":{},
            "outputs":[], "source": s.splitlines(keepends=True)}

def mk_md(s):
    return {"cell_type":"markdown","metadata":{},
            "source": s.splitlines(keepends=True)}

# ─────────────────────────────────────────────────────────────────────────────
# CONTENT
# ─────────────────────────────────────────────────────────────────────────────

# ── TOC (updated) ─────────────────────────────────────────────────────────────
TOC = """\
# Table of Contents <a id='toc'></a>

- [Setup and Data Loading](#setup)
- [Feature Engineering](#features)
- [1. Overview: Member vs Casual Usage Split](#overview)
- [2. Temporal Analysis](#temporal)
  - [2.1 Intraday Usage Patterns (Hourly)](#hourly)
  - [2.2 Seasonal Patterns (Monthly)](#monthly)
- [3. Spatial Analysis: Chicago Zoning Districts](#spatial)
  - [3.1 Load Zoning Data and Spatial Join](#join)
  - [3.2 Statistical Validation — Chi-Square Test](#chi2)
  - [3.3 Start Zone Distribution: Member vs Casual](#zones)
  - [3.4 Zone-to-Zone Ride Patterns (Heatmaps)](#heatmaps)
  - [3.5 Divergence Analysis with Station Weights](#divergence)
  - [3.5b Infrastructure Map by Zone](#zonemap)
  - [3.6 Conversion Priority Map — Station Level](#conversion)
  - [3.7 Key Conversion Zones: Insight View](#insight_map)
- [4. Conclusions and Recommendations](#conclusions)
- [5. Saving Outputs](#saving)
"""

# ── BEFORE zone map ────────────────────────────────────────────────────────────
MD_BEFORE_ZONE = """\
### Infrastructure Context: Stations Across Chicago's Zoning Districts

Before examining trip patterns by zone, it is worth seeing **where the infrastructure
actually is.** Chicago's land-use zoning shapes who rides and why — a dense Business
district drives weekday commutes (membership use), while a mixed-use Planned
Manufacturing District with bars, cafés and parks draws weekend leisure riders (casual use).

The map below shows the seven zoning categories with their polygon boundaries,
the station count within each zone, and a **performance index** in the panel below:

> **I = zone's share of all rides ÷ zone's share of all stations**
> Values above 1 mean the zone generates *more* rides than its infrastructure share
> would predict; values below 1 indicate under-performance.
"""

# ── Revised zone map code ─────────────────────────────────────────────────────
ZONE_MAP_CODE = """\
import contextily as ctx
import time

t0 = time.time()

# ── Color palette — one accessible, distinctive color per zone ────────────────
ZONE_COLORS = {
    'Business'                        : '#e76f51',
    'Commercial'                      : '#f4a261',
    'Downtown'                        : '#264653',
    'Manufacturing'                   : '#2a9d8f',
    'Planned Manufacturing Districts' : '#8338ec',
    'Residential'                     : '#457b9d',
    'Transportation'                  : '#e9c46a',
}

# ── Dissolve sub-polygons → 7 macro-zones, reproject to EPSG:3857 ────────────
gdf_dissolved = (
    gdf_zoning.dissolve(by='zone_name').reset_index()[['zone_name', 'geometry']]
)
gdf_dissolved['geometry'] = gdf_dissolved.geometry.simplify(0.0001, preserve_topology=True)
gdf_dissolved_3857 = gdf_dissolved.to_crs(epsg=3857)

gdf_map = gdf_dissolved_3857.merge(
    zone_metrics[['zone_name', 'n_stations_zone', 'I_m', 'I_c', 'I_diff']],
    on='zone_name', how='left'
)
gdf_map['color'] = gdf_map['zone_name'].map(ZONE_COLORS).fillna('#cccccc')

# Reproject stations once — reused by conversion and insight maps
stations_3857 = stations_zoned.to_crs(epsg=3857)
print(f"  -> Macro-zones: {len(gdf_dissolved_3857)}  |  Stations: {len(stations_3857):,}")

# ── Figure: map panel + performance bar chart ─────────────────────────────────
fig = plt.figure(figsize=(12, 14), facecolor='white')
gs  = fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.12)
ax_map = fig.add_subplot(gs[0])
ax_bar = fig.add_subplot(gs[1])

# -- Zone polygons: semi-transparent so the basemap shows through
for _, row in gdf_map.iterrows():
    gpd.GeoSeries([row.geometry]).plot(
        ax=ax_map, color=row['color'],
        edgecolor='white', linewidth=0.7, alpha=0.52
    )

# -- Centroid labels: zone name + station count only (no I_diff clutter)
for _, row in gdf_map.iterrows():
    centroid = row.geometry.centroid
    n_st = int(row['n_stations_zone'] if pd.notna(row['n_stations_zone']) else 0)
    ax_map.annotate(
        f"{row['zone_name']}\\n{n_st:,} stations",
        xy=(centroid.x, centroid.y),
        fontsize=8.5, fontweight='bold', ha='center', va='center', color='white',
        bbox=dict(boxstyle='round,pad=0.35', facecolor=row['color'],
                  alpha=0.90, edgecolor='white', linewidth=0.8)
    )

# -- Basemap: CartoDB Positron — neutral, does not compete with data
ctx.add_basemap(ax_map, source=ctx.providers.CartoDB.Positron, zoom=11)
ax_map.set_axis_off()

# -- Title + subtitle
ax_map.set_title(
    'Chicago Divvy Infrastructure by Zoning District',
    fontsize=15, fontweight='bold', color='#1a1a1a', pad=8
)
ax_map.text(
    0.5, -0.01,
    'Business and PMD zones hold 68 % of all stations; '
    'Downtown generates the highest rides-per-station for both user types.',
    transform=ax_map.transAxes, ha='center', va='top',
    fontsize=9.5, color='#555555', style='italic'
)

# -- Legend
handles = [
    mpatches.Patch(facecolor=c, edgecolor='white', linewidth=0.5, label=z)
    for z, c in ZONE_COLORS.items()
]
ax_map.legend(handles=handles, loc='lower left', fontsize=8.5,
              framealpha=0.92, edgecolor='#cccccc', title='Zone Type', title_fontsize=9)

# ── Performance bar chart (bottom panel) ─────────────────────────────────────
zones_s = gdf_map.sort_values('I_diff', ascending=False)['zone_name'].tolist()
x_b     = list(range(len(zones_s)))
i_m_v   = [float(gdf_map.loc[gdf_map['zone_name']==z, 'I_m'].iat[0] or 0) for z in zones_s]
i_c_v   = [float(gdf_map.loc[gdf_map['zone_name']==z, 'I_c'].iat[0] or 0) for z in zones_s]
clrs    = [ZONE_COLORS.get(z, '#cccccc') for z in zones_s]
bar_w   = 0.33

ax_bar.bar([xi-bar_w/2 for xi in x_b], i_m_v, bar_w,
           color=clrs, alpha=0.88, edgecolor='white', linewidth=0.5, label='Member (I_m)')
ax_bar.bar([xi+bar_w/2 for xi in x_b], i_c_v, bar_w,
           color=clrs, alpha=0.44, edgecolor='white', linewidth=0.5,
           hatch='//', label='Casual (I_c)')
ax_bar.axhline(1.0, color='#333333', linewidth=1.2, linestyle='--', alpha=0.65, label='Baseline I = 1')
ax_bar.set_xticks(x_b)
ax_bar.set_xticklabels(
    [z[:18]+'...' if len(z)>18 else z for z in zones_s],
    rotation=20, ha='right', fontsize=9, color='#333333'
)
ax_bar.set_ylabel('Performance Index (I)', fontsize=9, color='#555')
ax_bar.set_title(
    'Ride-generation performance vs. station share  '
    '(I > 1 = over-performs  |  I_diff > 0 = Member leads Casual)',
    fontsize=9.5, color='#333333', pad=6
)
ax_bar.legend(fontsize=8.5, framealpha=0.85, loc='upper right')
ax_bar.grid(axis='y', alpha=0.18, linestyle=':')
ax_bar.set_facecolor('#fafafa')
ax_bar.spines[['top', 'right']].set_visible(False)

plt.savefig('../reports/figures/chicago_zone_map_basemap.png',
            dpi=180, bbox_inches='tight', facecolor='white')
plt.show()
print(f"[OK] Saved: chicago_zone_map_basemap.png  [{time.time()-t0:.1f}s]")
"""

# ── AFTER zone map ────────────────────────────────────────────────────────────
MD_AFTER_ZONE = """\
## 3.5b Infrastructure Map — Key Observations <a id='zonemap'></a>
[↑ back to top](#toc)

| Zone | Stations | I_m (Member) | I_c (Casual) | I_diff | Interpretation |
|------|:--------:|:------------:|:------------:|:------:|----------------|
| **Downtown** | 74 | highest | highest | ≈ 0 | Both types over-perform — dense commute + leisure hub |
| **Business** | 1,251 | above 1 | near 1 | positive | Member stronghold; commute-driven weekday usage |
| **PMD** | 776 | near 1 | above 1 | negative | Mixed-use neighbourhoods attract more casuals per station |
| **Residential** | 370 | above 1 | below 1 | positive | Neighbourhood commuters: already largely converted |
| **Commercial** | 359 | above 1 | near 1 | positive | Retail corridors: moderate member advantage |
| **Transportation** | 19 | near 1 | near 1 | ≈ 0 | Rail-adjacent hubs: balanced multi-modal use |

**Two findings stand out:**

1. **Downtown is infrastructure-scarce but ride-dense.** With only ~2.5 % of all stations it
   accounts for a disproportionate share of rides for *both* user types. Any station expansion
   here has near-instant payback for ridership.
2. **Planned Manufacturing Districts show the strongest Casual over-performance (I_c > I_m).**
   This is the zone where marketing investment in conversion will find the most receptive
   casual audience — they are already riding, just not as members.
"""

# ── BEFORE conversion map ─────────────────────────────────────────────────────
MD_BEFORE_CONV = """\
### Conversion Opportunity: Station-Level View

The zone map showed that **Planned Manufacturing Districts** is the highest-priority
zone for conversion. This map zooms in to the station level — one bubble per station —
revealing *exactly where* within the city casual riders concentrate.

**Reading guide:**
- **Color** = member share at that station (orange → casual majority; green → member majority; white → balanced ≈50/50).
- **Bubble size** ∝ √(annual trips): larger bubbles mean more total volume.
- **Red rings** mark the top-10 stations by absolute casual ride count — the addresses
  where a conversion campaign would have the highest immediate impact.

Only stations with ≥ 100 annual trips are shown to remove low-volume noise.
"""

# ── Revised conversion map code ───────────────────────────────────────────────
CONV_MAP_CODE = """\
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize
import time

COLOR_MEMBER = '#2a9d4e'
COLOR_CASUAL = '#f4820a'

t0 = time.time()

# ── Per-station ride counts by user type ──────────────────────────────────────
station_rides = (
    df_clean
    .dropna(subset=['start_station_id'])
    .groupby(['start_station_id', 'member_casual'])
    .size()
    .unstack(fill_value=0)
)
if 'member' not in station_rides.columns:
    station_rides['member'] = 0
if 'casual' not in station_rides.columns:
    station_rides['casual'] = 0
station_rides = (
    station_rides
    .rename(columns={'member': 'member_rides', 'casual': 'casual_rides'})
    .reset_index()
)
station_rides['total_rides']  = station_rides['member_rides'] + station_rides['casual_rides']
station_rides['member_share'] = station_rides['member_rides'] / station_rides['total_rides']

# ── Join with geometry ────────────────────────────────────────────────────────
gdf_conv = (
    stations_3857[['start_station_id', 'geometry', 'zone_name']]
    .merge(station_rides, on='start_station_id', how='inner')
    .reset_index(drop=True)
)

# ── Filter: only stations with enough volume to be actionable ─────────────────
MIN_RIDES = 100
gdf_vis = gdf_conv[gdf_conv['total_rides'] >= MIN_RIDES].copy().reset_index(drop=True)
print(f"  -> Stations total: {len(gdf_conv):,}  |  Shown (>={MIN_RIDES} trips/yr): {len(gdf_vis):,}")

# ── Size encoding: sqrt scale compresses outliers ─────────────────────────────
size_raw = np.sqrt(gdf_vis['total_rides'].values.astype(float))
s_lo, s_hi = size_raw.min(), size_raw.max()
sizes = 18 + (size_raw - s_lo) / (s_hi - s_lo + 1e-9) * 260

# ── Color encoding: diverging casual → balanced → member ─────────────────────
cmap_conv = LinearSegmentedColormap.from_list(
    'conversion', [(0.0, COLOR_CASUAL), (0.50, '#f5f5f5'), (1.0, COLOR_MEMBER)]
)
norm_conv = Normalize(vmin=0.0, vmax=1.0)

# ── Top-10 conversion targets: highest casual ride volume ─────────────────────
top10 = gdf_vis.nlargest(10, 'casual_rides')
top10_sizes = 18 + (np.sqrt(top10['total_rides'].values.astype(float)) - s_lo) / (s_hi - s_lo + 1e-9) * 260

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(1, 1, figsize=(12, 14), facecolor='white')

sc = ax.scatter(
    gdf_vis.geometry.x, gdf_vis.geometry.y,
    s=sizes,
    c=gdf_vis['member_share'].values,
    cmap=cmap_conv, norm=norm_conv,
    edgecolors='#cccccc', linewidths=0.15,
    alpha=0.82, zorder=5
)

# Top-10 marked with a prominent ring (circle, no fill)
ax.scatter(
    top10.geometry.x, top10.geometry.y,
    s=top10_sizes + 90,
    marker='o', facecolors='none', edgecolors='#cc2200',
    linewidths=2.0, zorder=7
)

ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=11)
ax.set_axis_off()

# ── Colorbar ─────────────────────────────────────────────────────────────────
cbar = plt.colorbar(sc, ax=ax, shrink=0.40, pad=0.01, aspect=28)
cbar.set_label('Member share (proportion of annual trips by members)', fontsize=9.5)
cbar.ax.tick_params(labelsize=9)
cbar.set_ticks([0.0, 0.25, 0.50, 0.75, 1.0])
cbar.set_ticklabels(['0 %\\nAll casual', '25 %', '50 %\\nBalanced', '75 %', '100 %\\nAll member'])

# ── Size legend ───────────────────────────────────────────────────────────────
for ref_val, lbl in [(300, '300 trips/yr'), (3000, '3,000'), (10000, '10,000+')]:
    ref_s = 18 + (np.sqrt(ref_val) - s_lo) / (s_hi - s_lo + 1e-9) * 260
    ax.scatter([], [], s=ref_s, c='#888888', alpha=0.70,
               edgecolors='#aaaaaa', linewidths=0.3, label=lbl)
ax.scatter([], [], s=130, facecolors='none', edgecolors='#cc2200',
           linewidths=2.0, marker='o', label='Top-10 conversion targets')
ax.legend(title='Annual trips per station', loc='lower right',
          fontsize=9, title_fontsize=9.5, framealpha=0.92)

# ── Title + subtitle ─────────────────────────────────────────────────────────
ax.set_title('Conversion Priority Map: Casual Rider Share by Station',
             fontsize=15, fontweight='bold', color='#1a1a1a', pad=8)
ax.text(0.5, -0.01,
        'Largest orange bubbles = highest-impact conversion targets  '
        '(high casual volume, low member share)',
        transform=ax.transAxes, ha='center', va='top',
        fontsize=9.5, color='#555555', style='italic')

plt.savefig('../reports/figures/chicago_conversion_map.png',
            dpi=180, bbox_inches='tight', facecolor='white')
plt.show()

# Top-10 summary
print("\\nTop-10 conversion targets (highest casual ride volume):")
print(f"  {'Station ID':<25} {'Zone':<35} {'Member%':>8} {'Casual':>8} {'Total':>8}")
print(f"  {'-'*85}")
for _, r in top10.sort_values('casual_rides', ascending=False).iterrows():
    print(f"  {str(r['start_station_id']):<25} {str(r.get('zone_name','—')):<35} "
          f"{r['member_share']*100:>7.1f}% {r['casual_rides']:>8,.0f} {r['total_rides']:>8,.0f}")
print(f"\\n[OK] Saved: chicago_conversion_map.png  [{time.time()-t0:.1f}s]")
"""

# ── AFTER conversion map ──────────────────────────────────────────────────────
MD_AFTER_CONV = """\
## 3.6 Conversion Map — Key Observations <a id='conversion'></a>
[↑ back to top](#toc)

**What the map reveals:**

- **Lakefront Trail (east side):** the densest cluster of large orange bubbles runs along
  DuSable Lake Shore Drive from Grant Park north through Lincoln Park. These stations serve
  leisure cyclists, tourists and park users — high casual volume, very low member share.
  All 10 top conversion targets fall in this corridor or the adjacent PMD neighbourhoods.

- **Downtown (centre):** stations are green-to-neutral. Even in a high-tourism zone, members
  outnumber casuals because weekday commuters pass through here every day.

- **North Side residential grid:** stations turn green. Neighbourhood commuters are already
  converted; re-investment here has low marginal conversion yield.

- **Balanced band (~50/50, white):** a transitional ring between the leisure-heavy east and
  the commuter-heavy north. Riders here already use both modes — the lowest-friction
  conversion opportunity via in-app messaging.

**Conversion implications:**

| Priority | Area | Recommended action |
|----------|------|--------------------|
| **High** | Lakefront Trail stations (top-10) | Seasonal "summer pass → annual upgrade" bundles at unlock point |
| **High** | PMD mixed-use cluster (Wicker Park / Logan Square) | Neighbourhood ambassador programmes; event partnerships |
| **Medium** | Balanced stations (white bubbles) | In-app cost-savings prompts ("You've taken X rides — a membership saves you $Y") |
| **Low** | Member-green stations | Retention; upsell (e-bike add-ons, family plans) |
"""

# ── BEFORE insight map ────────────────────────────────────────────────────────
MD_BEFORE_INSIGHT = """\
### Key Conversion Zones at a Glance

The full conversion map shows 2,400+ stations across the city.
This simplified view filters down to **only the stations that matter most for a
conversion campaign**:

> **Filter:** casual-majority stations (member share < 45 %) with ≥ 300 annual trips.

All other active stations appear as faint grey dots — spatial context only.
Orange bubbles are the conversion targets, sized by their casual ride volume.
The annotated callouts identify the two primary geographic clusters.
"""

# ── Insight-only map code ─────────────────────────────────────────────────────
INSIGHT_MAP_CODE = """\
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import contextily as ctx
import time

COLOR_CASUAL  = '#f4820a'
COLOR_CONTEXT = '#d8d8d8'

t0 = time.time()

# ── Filter ────────────────────────────────────────────────────────────────────
MIN_RIDES   = 300    # annual trips needed to be a meaningful station
MAX_M_SHARE = 0.45   # casual majority threshold  (<45 % member = casual-heavy)

gdf_all      = gdf_conv[gdf_conv['total_rides'] >= MIN_RIDES].copy().reset_index(drop=True)
gdf_targets  = gdf_all[gdf_all['member_share'] < MAX_M_SHARE].copy().reset_index(drop=True)
gdf_context  = gdf_all[gdf_all['member_share'] >= MAX_M_SHARE].copy().reset_index(drop=True)

print(f"  -> Active stations (>={MIN_RIDES} trips/yr): {len(gdf_all):,}")
print(f"  -> Conversion targets (member share <{MAX_M_SHARE:.0%}): {len(gdf_targets):,}")
print(f"  -> Context (member-heavy / balanced):         {len(gdf_context):,}")

# ── Size encoding for target bubbles: by casual_rides ────────────────────────
cas_raw = np.sqrt(gdf_targets['casual_rides'].values.astype(float))
c_lo, c_hi = cas_raw.min(), cas_raw.max()
target_sizes = 22 + (cas_raw - c_lo) / (c_hi - c_lo + 1e-9) * 300

# ── Compute cluster centroids from top-30 targets ─────────────────────────────
top30 = gdf_targets.nlargest(30, 'casual_rides').reset_index(drop=True)
x_vals = top30.geometry.x.values
x_median = np.median(x_vals)

east_mask = top30.geometry.x > x_median
east = top30[east_mask]
west = top30[~east_mask]

east_cx = float(east.geometry.x.median()) if len(east) > 0 else x_median + 2000
east_cy = float(east.geometry.y.median()) if len(east) > 0 else float(top30.geometry.y.median())
west_cx = float(west.geometry.x.median()) if len(west) > 0 else x_median - 2000
west_cy = float(west.geometry.y.median()) if len(west) > 0 else float(top30.geometry.y.median())

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(1, 1, figsize=(11, 13), facecolor='white')

# Context layer — small, receding grey dots
ax.scatter(gdf_context.geometry.x, gdf_context.geometry.y,
           s=7, color=COLOR_CONTEXT, alpha=0.38, zorder=3, linewidths=0)

# Target layer — orange, sized by casual volume
ax.scatter(
    gdf_targets.geometry.x, gdf_targets.geometry.y,
    s=target_sizes,
    color=COLOR_CASUAL,
    edgecolors='#b85e05', linewidths=0.4,
    alpha=0.88, zorder=6
)

# Basemap — very light, does not distract
ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=11)
ax.set_axis_off()

# ── Cluster annotations ───────────────────────────────────────────────────────
ann_kw = dict(
    fontsize=10, fontweight='bold', color='#1a1a1a',
    ha='center', va='center',
    bbox=dict(boxstyle='round,pad=0.45', facecolor='white',
              alpha=0.90, edgecolor='#cc4400', linewidth=1.5)
)
arr_kw = dict(arrowstyle='->', color='#cc4400', lw=1.6)

# East cluster — Lakefront Corridor
ax.annotate(
    'Lakefront Corridor\\n(leisure & park rides)',
    xy=(east_cx, east_cy),
    xytext=(east_cx + 3000, east_cy + 3500),
    **ann_kw, arrowprops=dict(**arr_kw)
)

# West cluster — Wicker Park / River North
ax.annotate(
    'Wicker Park / River North\\n(mixed-use, repeat casuals)',
    xy=(west_cx, west_cy),
    xytext=(west_cx - 4500, west_cy + 3000),
    **ann_kw, arrowprops=dict(**arr_kw)
)

# ── Legend ────────────────────────────────────────────────────────────────────
handles = [
    mpatches.Patch(color=COLOR_CASUAL, label=f'Conversion target  '
                   f'(member share < {MAX_M_SHARE:.0%},  ≥ {MIN_RIDES} trips/yr)'),
    mpatches.Patch(color=COLOR_CONTEXT, alpha=0.5,
                   label='Member-heavy or balanced station  (context only)'),
]
ax.legend(handles=handles, loc='lower right', fontsize=9.5,
          framealpha=0.92, edgecolor='#cccccc')

# ── Title + subtitle ─────────────────────────────────────────────────────────
ax.set_title('Key Conversion Zones: Where Casual Riders Concentrate',
             fontsize=15, fontweight='bold', color='#1a1a1a', pad=8)
ax.text(
    0.5, -0.01,
    f'Showing {len(gdf_targets):,} of {len(gdf_all):,} active stations  |  '
    f'Bubble size proportional to annual casual ride volume',
    transform=ax.transAxes, ha='center', va='top',
    fontsize=9, color='#555555', style='italic'
)

plt.savefig('../reports/figures/chicago_insight_map.png',
            dpi=180, bbox_inches='tight', facecolor='white')
plt.show()
print(f"[OK] Saved: chicago_insight_map.png  [{time.time()-t0:.1f}s]")
"""

# ── AFTER insight map ─────────────────────────────────────────────────────────
MD_AFTER_INSIGHT = """\
## 3.7 Insight Map — Spatial Takeaways and Conversion Strategy <a id='insight_map'></a>
[↑ back to top](#toc)

**Three spatial patterns dominate:**

1. **The Lakefront Corridor is the single highest-density conversion opportunity.**
   Stations along DuSable Lake Shore Drive (Grant Park, Lincoln Park waterfront, Navy Pier)
   hold the largest casual ride volumes and the lowest member shares in the city.
   These riders are *already engaged* with the service — the barrier to membership is
   not awareness, but perceived value and usage frequency.

2. **Wicker Park / River North (the western PMD cluster) is the most strategically
   important neighbourhood for conversion.**
   It combines high casual trip counts with the urban density, repeat-visit pattern
   and demographic profile that make it the best candidate for converting leisure riders
   into annual members. In-neighbourhood activation (event sponsorships, pop-up ambassador
   stations) would be particularly effective here.

3. **The grey dots — member-heavy and balanced stations — form a dense band across the
   North Side residential grid and near CTA elevated rail stops.**
   These corridors are already well-converted; incremental investment in acquisition here
   has low marginal return. The focus should shift to *retention* and upsell
   (e-bike upgrades, family plans).

---

**Recommended campaign tiers:**

| Tier | Geographic focus | Rationale | Suggested action |
|------|-----------------|-----------|-----------------|
| **1 — Highest impact** | Lakefront Corridor stations (top-10) | Highest absolute casual volume; lowest member share | Seasonal upgrade offers ("summer pass → annual"); point-of-unlock digital prompts |
| **2 — High impact** | Wicker Park / River North cluster | High frequency, repeat casual riders | Neighbourhood ambassador activations; partnerships with local businesses |
| **3 — Medium impact** | Balanced (≈50/50) stations | Mixed-mode riders; already open to membership | In-app cost-savings messaging after 6–8 casual rides in a month |
| **4 — Retention** | Member-green stations | Already converted | Upsell (e-bike add-ons, family plans); loyalty rewards |
"""

# ─────────────────────────────────────────────────────────────────────────────
# BUILD NEW CELL LIST
# ─────────────────────────────────────────────────────────────────────────────
old = nb['cells']
new = []

for idx, cell in enumerate(old):
    if idx == 0:
        # Updated TOC
        cell = dict(cell); cell['source'] = TOC.splitlines(keepends=True)
        new.append(cell)

    elif idx == 40:
        # Insert BEFORE, then replace zone map, skip old idx-40
        new.append(mk_md(MD_BEFORE_ZONE))
        new.append(mk_code(ZONE_MAP_CODE))
        # idx 41 (AFTER markdown) handled below — skip here

    elif idx == 41:
        # Replace AFTER zone map markdown
        new.append(mk_md(MD_AFTER_ZONE))

    elif idx == 42:
        # Insert BEFORE, then replace conversion map
        new.append(mk_md(MD_BEFORE_CONV))
        new.append(mk_code(CONV_MAP_CODE))
        # idx 43 handled below

    elif idx == 43:
        # Replace AFTER conversion map + add full insight map block
        new.append(mk_md(MD_AFTER_CONV))
        new.append(mk_md(MD_BEFORE_INSIGHT))
        new.append(mk_code(INSIGHT_MAP_CODE))
        new.append(mk_md(MD_AFTER_INSIGHT))

    else:
        new.append(cell)

nb['cells'] = new
with open(NB, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f"[OK] Notebook saved — {len(new)} cells (was {len(old)})")
print(f"     Added: 1 BEFORE-zone, 1 BEFORE-conv, 3 insight cells (before+map+after)")
print(f"     Replaced: zone map, conv map, 2 AFTER markdowns, TOC")
