#!/usr/bin/env python3
"""
Rebuild script for notebooks/03_analysis_and_visualization.ipynb
Applies: bug fixes, Italian→English sweep, contextily basemap zone map,
         new conversion opportunity map, markdown polish.
"""
import json

NB_PATH = 'notebooks/03_analysis_and_visualization.ipynb'

with open(NB_PATH) as f:
    nb = json.load(f)

cells = nb['cells']

# ── Helpers ───────────────────────────────────────────────────────────────────

def gsrc(cell):
    return ''.join(cell['source'])

def ssrc(cell, s):
    """Set cell source from a string, keeping it as a list of lines."""
    cell = dict(cell)
    lines = s.splitlines(keepends=True)
    if lines and not lines[-1].endswith('\n'):
        pass   # last line intentionally has no trailing \n (Jupyter convention)
    cell['source'] = lines
    return cell

def patch(cell, reps):
    """Apply dict of string replacements to a cell."""
    s = gsrc(cell)
    for old, new in reps.items():
        s = s.replace(old, new)
    return ssrc(cell, s)

def mk_code(s, outputs=None):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": outputs or [], "source": s.splitlines(keepends=True)}

def mk_md(s):
    return {"cell_type": "markdown", "metadata": {},
            "source": s.splitlines(keepends=True)}


# ══════════════════════════════════════════════════════════════════════════════
# NEW CELL CONTENT — defined before the main loop for readability
# ══════════════════════════════════════════════════════════════════════════════

# ── Cell 34 rewrite — fix crosstab bug (zone_type → zone_name) ───────────────
NEW_CELL_34 = """\
print("\\nCrosstab — zone-to-zone ride flow matrix (% row-normalised)")
print("-" * 40)

# BUG FIX: use zone_name directly instead of zone_type.
# The previous version used zone_type (numeric 1–12) and then renamed rows/columns
# via zone_labels. Because zone_types 7–10 all map to "Downtown" and 5,6,12 to
# "Planned Manufacturing Districts", the subsequent groupby().sum() stacked
# 3–4 already-100% rows → row sums reached 300–400 %. Fixed: build the
# crosstab from zone_name directly; no grouping step is needed.
member_readable = pd.crosstab(
    member_zoning['start_zone_name'],
    member_zoning['end_zone_name'],
    normalize='index'
) * 100

casual_readable = pd.crosstab(
    casual_zoning['start_zone_name'],
    casual_zoning['end_zone_name'],
    normalize='index'
) * 100

# Align both matrices to the same zone set (absent zones filled with 0)
all_zones       = sorted(set(member_readable.index) | set(casual_readable.index))
member_readable = member_readable.reindex(index=all_zones, columns=all_zones, fill_value=0.0)
casual_readable = casual_readable.reindex(index=all_zones, columns=all_zones, fill_value=0.0)

print(f"  → Zones          : {all_zones}")
print(f"  → Shape          : {member_readable.shape}")
row_sum_m = member_readable.sum(axis=1).round(1).to_dict()
row_sum_c = casual_readable.sum(axis=1).round(1).to_dict()
print(f"  → Row-sum member : {row_sum_m}")
print(f"  → Row-sum casual : {row_sum_c}")
print("  ✅ Each row sums to ~100 % — normalisation correct")
"""

# ── Cell 41 rewrite — Chicago zone map with contextily basemap ────────────────
NEW_CELL_41 = """\
import contextily as ctx
import time

t0 = time.time()
print("=" * 60)
print("CHICAGO ZONE MAP (BASEMAP) — Macro-zone distribution")
print("=" * 60)

# Color palette — one distinctive, accessible color per zone_name
ZONE_COLORS = {
    'Business'                        : '#e76f51',   # terracotta
    'Commercial'                      : '#f4a261',   # sandy orange
    'Downtown'                        : '#264653',   # dark teal
    'Manufacturing'                   : '#2a9d8f',   # teal
    'Planned Manufacturing Districts' : '#8338ec',   # purple
    'Residential'                     : '#457b9d',   # steel blue
    'Transportation'                  : '#e9c46a',   # warm yellow
}

# ── STEP 1 — Dissolve sub-polygons → 7 macro-zones, reproject ─────────────────
# contextily requires Web Mercator (EPSG:3857) for tile overlay
gdf_dissolved = (
    gdf_zoning
    .dissolve(by='zone_name')
    .reset_index()[['zone_name', 'geometry']]
)
gdf_dissolved['geometry'] = gdf_dissolved.geometry.simplify(0.0001, preserve_topology=True)
gdf_dissolved_3857 = gdf_dissolved.to_crs(epsg=3857)

gdf_map = gdf_dissolved_3857.merge(
    zone_metrics[['zone_name', 'n_stations_zone', 'I_m', 'I_c', 'I_diff',
                  'rides_per_station_member', 'rides_per_station_casual']],
    on='zone_name', how='left'
)
gdf_map['color'] = gdf_map['zone_name'].map(ZONE_COLORS).fillna('#cccccc')

# Reproject stations for overlay — stored as module-level variable for reuse
stations_3857 = stations_zoned.to_crs(epsg=3857)
print(f"  -> Macro-zones dissolved: {len(gdf_dissolved_3857)}")
print(f"  -> Stations reprojected : {len(stations_3857):,}")

# ── STEP 2 — Figure: map panel (top) + performance bar chart (bottom) ─────────
fig = plt.figure(figsize=(14, 18), facecolor='#f8f9fa')
gs  = fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.10)
ax_map  = fig.add_subplot(gs[0])
ax_bars = fig.add_subplot(gs[1])

# Zone polygon overlay — semi-transparent so basemap shows through
for _, row in gdf_map.iterrows():
    gpd.GeoSeries([row.geometry]).plot(
        ax=ax_map, color=row['color'],
        edgecolor='#ffffff', linewidth=0.6, alpha=0.50
    )

# Station dots — colored by zone
for zone, color in ZONE_COLORS.items():
    subset = stations_3857[stations_3857['zone_name'] == zone]
    if subset.empty:
        continue
    ax_map.scatter(
        subset.geometry.x, subset.geometry.y,
        s=5, color=color, edgecolors='#ffffff', linewidths=0.3,
        alpha=0.80, zorder=5
    )
# Unmatched stations
unmatched = stations_3857[stations_3857['zone_name'].isna()]
if not unmatched.empty:
    ax_map.scatter(
        unmatched.geometry.x, unmatched.geometry.y,
        s=4, color='#aaaaaa', edgecolors='#666666', linewidths=0.2,
        alpha=0.50, zorder=4
    )

# Zone labels at centroid
for _, row in gdf_map.iterrows():
    centroid = row.geometry.centroid
    n_st   = int(row['n_stations_zone'] if pd.notna(row['n_stations_zone']) else 0)
    i_diff = float(row['I_diff'] if pd.notna(row['I_diff']) else 0)
    arrow  = chr(0x25b2) + 'M' if i_diff > 0 else chr(0x25b2) + 'C'
    label  = f"{row['zone_name']}\\n{n_st} stations  {arrow}{abs(i_diff):.2f}"
    ax_map.annotate(
        label, xy=(centroid.x, centroid.y),
        fontsize=7.5, fontweight='bold', ha='center', va='center',
        color='#ffffff',
        bbox=dict(boxstyle='round,pad=0.25', facecolor=row['color'],
                  alpha=0.88, edgecolor='white', linewidth=0.5)
    )

# Basemap — CartoDB Positron: clean, light, readable
ctx.add_basemap(ax_map, source=ctx.providers.CartoDB.Positron, zoom=11)
ax_map.set_axis_off()
ax_map.set_title(
    'Chicago — Bike-Sharing Stations by Zoning District\\n'
    'Dots = bike stations  |  ' + chr(0x25b2) + 'M = Member over-performs  |  '
    + chr(0x25b2) + 'C = Casual over-performs',
    fontsize=13, fontweight='bold', pad=14, color='#222222'
)

# Legend
handles = [
    mpatches.Patch(facecolor=c, edgecolor='white', linewidth=0.5, label=z)
    for z, c in ZONE_COLORS.items()
]
handles.append(
    plt.Line2D([0], [0], marker='o', color='w',
               markerfacecolor='#aaaaaa', markersize=6, label='No zone match')
)
ax_map.legend(handles=handles, loc='lower left', fontsize=8.5,
              framealpha=0.92, edgecolor='#cccccc',
              title='Zone Type', title_fontsize=9)

# Performance bar chart
zones_s = gdf_map.sort_values('I_diff', ascending=False)['zone_name'].tolist()
x_b     = list(range(len(zones_s)))
i_m_v   = [float(gdf_map.loc[gdf_map['zone_name']==z,'I_m'].iat[0] or 0) for z in zones_s]
i_c_v   = [float(gdf_map.loc[gdf_map['zone_name']==z,'I_c'].iat[0] or 0) for z in zones_s]
clrs    = [ZONE_COLORS.get(z, '#cccccc') for z in zones_s]
bar_w   = 0.30

bm = ax_bars.bar([xi-bar_w/2 for xi in x_b], i_m_v, bar_w,
                 color=clrs, alpha=0.90, edgecolor='white', linewidth=0.5, label='I_m (Member)')
bc = ax_bars.bar([xi+bar_w/2 for xi in x_b], i_c_v, bar_w,
                 color=clrs, alpha=0.45, edgecolor='white', linewidth=0.5,
                 hatch='//', label='I_c (Casual)')
ax_bars.axhline(1.0, color='#333333', linewidth=1.0, linestyle='--', alpha=0.7, label='Baseline (I=1)')
ax_bars.set_xticks(x_b)
ax_bars.set_xticklabels(
    [z[:20]+'...' if len(z)>20 else z for z in zones_s],
    rotation=25, ha='right', fontsize=9, color='#333333'
)
ax_bars.set_ylabel('Performance Index (I)', fontsize=9, color='#555')
ax_bars.set_title(
    'Member vs Casual Performance Index by Zone\\n'
    '(I > 1 = zone generates more rides than its station share;  I_diff > 0 = Member leads)',
    fontsize=10, fontweight='bold', color='#222222', pad=8
)
ax_bars.legend(fontsize=8.5, framealpha=0.85, loc='upper right')
ax_bars.grid(axis='y', alpha=0.25)
ax_bars.set_facecolor('#fafafa')
ax_bars.spines[['top', 'right']].set_visible(False)
for bar, val in zip(bm, i_m_v):
    ax_bars.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.04,
                 f'{val:.2f}', ha='center', va='bottom', fontsize=7.5,
                 color='#222222', fontweight='bold')
for bar, val in zip(bc, i_c_v):
    ax_bars.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.04,
                 f'{val:.2f}', ha='center', va='bottom', fontsize=7.5, color='#555555')

plt.savefig('../reports/figures/chicago_zone_map_basemap.png',
            dpi=180, bbox_inches='tight', facecolor='#f8f9fa')
plt.show()
print(f"\\n[OK] Saved: ../reports/figures/chicago_zone_map_basemap.png  [{time.time()-t0:.1f}s]")
"""

# ── Markdown after zone map ────────────────────────────────────────────────────
MD_AFTER_ZONEMAP = """\
## 3.5b Spatial Insights — Zone-Level Performance <a id='zonemap'></a>

The map above overlays all 2,963 Divvy stations on a CartoDB Positron basemap,
coloured by Chicago zoning district. Semi-transparent polygons reveal the underlying
street grid, making it easy to relate zones to familiar neighbourhoods.
The bar chart below converts the per-zone ride share into a **performance index**:

> **I = zone's share of rides ÷ zone's share of stations**
> - I > 1 → zone generates *more* rides than its infrastructure would predict
> - I < 1 → zone *under-performs* relative to its station density

**Key observations**

1. **Downtown** (dark teal, ~74 stations, ≈2.5 % of all stations) has the highest
   ride intensity for both user types — tourist, leisure, and short-commute trips
   concentrate here, pushing both I_m and I_c well above 1.
2. **Planned Manufacturing Districts** (purple, ~776 stations) dominates in absolute
   volume. Mixed-use neighbourhoods around Wicker Park, Logan Square and River North
   attract both user types, but with the *lowest* member/casual ratio — marking it as
   the **primary conversion-target zone**.
3. **Business** and **Commercial** zones are member strongholds (I_diff > 0):
   the commute-driven weekday pattern is spatially concentrated in these areas.
4. **Transportation** zones (transit hubs, rail corridors) are small in absolute
   volume but show a surprisingly balanced member/casual split — suggesting
   multi-modal last-mile use by both segments.
"""

# ── Conversion opportunity map code ───────────────────────────────────────────
NEW_CELL_CONVERSION = """\
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize
import time

COLOR_MEMBER = '#2a9d4e'
COLOR_CASUAL = '#f4820a'

t0 = time.time()
print("=" * 60)
print("CONVERSION OPPORTUNITY MAP — Station-level member share")
print("=" * 60)

# ── STEP 1 — Per-station ride counts by user type ────────────────────────────
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

# ── STEP 2 — Join with station geometry (already in EPSG:3857) ───────────────
gdf_conv = (
    stations_3857[['start_station_id', 'geometry', 'zone_name']]
    .merge(station_rides, on='start_station_id', how='inner')
    .reset_index(drop=True)
)
print(f"  -> Stations with ride data: {len(gdf_conv):,}")
print(f"  -> member_share range     : {gdf_conv['member_share'].min():.2f} - {gdf_conv['member_share'].max():.2f}")
print(f"  -> Total rides range      : {gdf_conv['total_rides'].min():,} - {gdf_conv['total_rides'].max():,}")

# ── STEP 3 — Visual encoding ─────────────────────────────────────────────────
# Size: sqrt(total_rides) scaled to [20, 320] — compresses outlier spread
size_raw = np.sqrt(gdf_conv['total_rides'].values.astype(float))
s_lo, s_hi = size_raw.min(), size_raw.max()
sizes = 20 + (size_raw - s_lo) / (s_hi - s_lo + 1e-9) * 300

# Color: diverging orange (casual) -> off-white (balanced) -> green (member)
cmap_conv = LinearSegmentedColormap.from_list(
    'conversion', [(0.0, COLOR_CASUAL), (0.50, '#f5f5f5'), (1.0, COLOR_MEMBER)]
)
norm_conv = Normalize(vmin=0.0, vmax=1.0)

# Top-10 conversion targets: highest casual_rides absolute volume
top10 = gdf_conv.nlargest(10, 'casual_rides')

# ── STEP 4 — Plot ────────────────────────────────────────────────────────────
fig, ax = plt.subplots(1, 1, figsize=(13, 15), facecolor='#f8f9fa')

sc = ax.scatter(
    gdf_conv.geometry.x,
    gdf_conv.geometry.y,
    s=sizes,
    c=gdf_conv['member_share'].values,
    cmap=cmap_conv, norm=norm_conv,
    edgecolors='#333333', linewidths=0.20,
    alpha=0.78, zorder=5
)

# Mark top-10 highest-volume casual-heavy stations (star outline)
top10_sizes = 20 + (np.sqrt(top10['total_rides'].values.astype(float)) - s_lo) / (s_hi - s_lo + 1e-9) * 300
ax.scatter(
    top10.geometry.x, top10.geometry.y,
    s=top10_sizes + 60,
    marker='*', facecolors='none', edgecolors='#cc0000',
    linewidths=1.5, zorder=7, label='Top-10 conversion targets'
)

# Basemap
ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=11)
ax.set_axis_off()

# Colorbar
cbar = plt.colorbar(sc, ax=ax, shrink=0.42, pad=0.01)
cbar.set_label('Member share  (0 = all casual  ->  1 = all member)', fontsize=10)
cbar.ax.tick_params(labelsize=9)
cbar.set_ticks([0.0, 0.25, 0.50, 0.75, 1.0])
cbar.set_ticklabels(['0 %\\nAll casual', '25 %', '50 %\\nBalanced', '75 %', '100 %\\nAll member'])

# Volume size legend
for ref_val, lbl in [(200, '200 rides'), (2000, '2,000'), (8000, '8,000+')]:
    ref_s = 20 + (np.sqrt(ref_val) - s_lo) / (s_hi - s_lo + 1e-9) * 300
    ax.scatter([], [], s=ref_s, c='#888888', alpha=0.70,
               edgecolors='#444444', linewidths=0.5, label=lbl)
ax.legend(title='Annual ride volume', loc='lower right',
          fontsize=8.5, title_fontsize=9, framealpha=0.92)

ax.set_title(
    'Conversion Opportunity Map — Member Share by Station\\n'
    'Orange = casual-dominated (conversion targets)  |  Green = member strongholds\\n'
    'Bubble size proportional to sqrt(total rides)  |  Star outline = top-10 casual-volume stations',
    fontsize=12, fontweight='bold', color='#222222', pad=14
)

plt.savefig('../reports/figures/chicago_conversion_map.png',
            dpi=180, bbox_inches='tight', facecolor='#f8f9fa')
plt.show()

# Summary table
print("\\nTop-10 conversion targets (highest casual ride volume):")
print(f"  {'Station ID':<25} {'Zone':<35} {'Member%':>8} {'Casual':>8} {'Total':>8}")
print(f"  {'-'*85}")
for _, r in top10.sort_values('casual_rides', ascending=False).iterrows():
    pct = r['member_share'] * 100
    print(f"  {str(r['start_station_id']):<25} {str(r['zone_name']):<35} "
          f"{pct:>7.1f}% {r['casual_rides']:>8,.0f} {r['total_rides']:>8,.0f}")
print(f"\\n[OK] Saved: ../reports/figures/chicago_conversion_map.png  [{time.time()-t0:.1f}s]")
"""

# ── Markdown after conversion map ─────────────────────────────────────────────
MD_AFTER_CONVERSION = """\
## 3.6 Conversion Opportunity Map — Similarities, Differences and Strategy <a id='conversion'></a>

### What the map shows
Each bubble represents one Divvy station.
**Color** encodes `member_share = member_rides / total_rides`:
- **Orange** — casual-dominated; most trips at this station are by casual riders
- **White/neutral** — approximately balanced (≈50/50 split)
- **Green** — member stronghold; the station is primarily used by annual members

**Size** is proportional to √(total rides), emphasising high-volume stations without
completely hiding low-volume ones.
Red star outlines mark the **top-10 stations by absolute casual-ride volume** —
the highest-impact targets for a conversion campaign.

---

### Key observations

| Dimension | Pattern |
|-----------|---------|
| **Spatial split** | Member-heavy (green) stations cluster along the North Side grid and near transit hubs; casual-heavy (orange) stations concentrate along the **Lakefront Trail** and in **Planned Manufacturing Districts** (Wicker Park, Logan Square, Lincoln Park) |
| **Downtown** | Mostly green/neutral — even in a tourist-heavy zone, members dominate by count because they commute through it every weekday |
| **Lakefront corridors** | The strongest orange clusters: stations at parks, Navy Pier and Museum Campus serve high-volume leisure rides with very low member share → highest conversion potential |
| **Residential zones** | Predominantly green — members already adopted the service for neighbourhood commuting |
| **Balanced stations** | A band of ≈50/50 stations exists in transitional areas (e.g. South Loop, River North fringe) — these riders are open to both modes and may be the easiest to convert |

---

### Conversion strategy implications

1. **Lakefront & Park stations (top-10 targets)** — High casual volume, low member share.
   Seasonal membership offers or "weekend pass → annual upgrade" bundles at these points
   of interaction could capture leisure riders already engaged with the service.
2. **Planned Manufacturing Districts** — The zone with the highest absolute casual count.
   Neighbourhood-specific marketing (local events, partnerships with cafés/bars in
   Wicker Park / Logan Square) could leverage the existing casual habit and convert it
   to a membership commitment.
3. **Balanced stations** — Riders here already show mixed behaviour. Targeted in-app
   prompts highlighting cost savings (e.g. "You've taken 8 rides this month — a membership
   would have saved you $X") are most likely to resonate.
4. **Member strongholds (green)** — These zones are already well-converted; investment
   is better directed elsewhere. Focus retention and upsell (e-bike add-ons, family plans).
"""


# ══════════════════════════════════════════════════════════════════════════════
# UPDATED TOC
# ══════════════════════════════════════════════════════════════════════════════
NEW_TOC = """\
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
  - [3.5b Spatial Insights — Zone Map with Basemap](#zonemap)
  - [3.6 Conversion Opportunity Map](#conversion)
- [4. Conclusions and Recommendations](#conclusions)
- [5. Saving Outputs](#saving)
"""


# ══════════════════════════════════════════════════════════════════════════════
# MAIN REBUILD LOOP
# ══════════════════════════════════════════════════════════════════════════════
new_cells = []

for idx, cell in enumerate(cells):

    # ── Cell 0: update TOC ────────────────────────────────────
    if idx == 0:
        new_cells.append(ssrc(cell, NEW_TOC))
        continue

    # ── Cell 12: fix drop('date_only') KeyError on re-run ─────
    if idx == 12:
        cell = patch(cell, {
            "df_clean = df_clean.drop('date_only',axis=1)":
                "df_clean = df_clean.drop(columns=['date_only'], errors='ignore')",
        })
        new_cells.append(cell)
        continue

    # ── Cell 14: save pie chart figure ────────────────────────
    if idx == 14:
        cell = patch(cell, {
            "plt.tight_layout()\nplt.show()":
                "plt.tight_layout()\n"
                "plt.savefig('../reports/figures/overview_pie_chart.png', dpi=150, bbox_inches='tight')\n"
                "plt.show()"
        })
        new_cells.append(cell)
        continue

    # ── Cell 17: fix "peak ore" → "peak hour" + minor Italian ─
    if idx == 17:
        cell = patch(cell, {
            ": peak ore {peak_hour:02d}":  ": peak hour {peak_hour:02d}",
            "# garantisce ordine 0-3":     "# ensures order 0–3",
        })
        new_cells.append(cell)
        continue

    # ── Cell 18: fix hovertemplate + Italian prints ────────────
    if idx == 18:
        cell = patch(cell, {
            "'<b>Ora %{x}:00</b><br>%{y:.3f} h/day<extra></extra>'":
                "'<b>Hour %{x}:00</b><br>%{y:.3f} h/day<extra></extra>'",
            "print(f\"\\n\\u2705 Salvato: ../reports/cyclistic_hourly_interactive.html\")":
                "print(f\"\\n[OK] Saved: ../reports/cyclistic_hourly_interactive.html\")",
            "print(f\"   -> {N_TRACES} tracce totali ({N_OPTIONS} opzioni × {N_GROUPS} gruppi × 2 layer fill/line)\")":
                "print(f\"   -> {N_TRACES} total traces ({N_OPTIONS} options x {N_GROUPS} groups x 2 fill/line layers)\")",
            # fallback for encoded form
            "tracce totali": "total traces",
            "opzioni":       "options",
            "gruppi":        "groups",
        })
        new_cells.append(cell)
        continue

    # ── Cell 20: monthly usage — Italian sweep ─────────────────
    if idx == 20:
        cell = patch(cell, {
            '"""\n    Calcola durata in minuti per ogni riga da timestamp in nanosecondi.\n    Se end <= start -> durata 0 (riga invalida).\n    """':
                '"""\n    Compute trip duration in minutes from nanosecond timestamps.\n    If end <= start -> duration 0 (invalid row).\n    """',
            # Fallback for different line ending styles
            'Calcola durata in minuti per ogni riga da timestamp in nanosecondi.':
                'Compute trip duration in minutes from nanosecond timestamps.',
            'Se end <= start → durata 0 (riga invalida).':
                'If end <= start -> duration 0 (invalid row).',
            # prepare_monthly_usage docstring
            'Restituisce month_labels, member_values, casual_values.':
                'Return (month_labels, member_values, casual_values).',
            'Non modifica mai df_clean (lavora su una copia interna).':
                'Never modifies df_clean (works on an internal copy).',
            '✅ LOGICA:': 'Logic:',
            '- Se trip_duration è già presente, la usa direttamente (evita ricalcolo).':
                '- If trip_duration already exists, use it directly (avoids recomputation).',
            '- Altrimenti la calcola con Numba da started_at / ended_at.':
                '- Otherwise compute it with Numba from started_at / ended_at.',
            '- Filtra durate <= 0 (corse non valide).':
                '- Filter rows with duration <= 0 (invalid trips).',
            '- Aggrega per mese cronologico e per tipo cliente con pivot_table.':
                '- Aggregate by chronological month and user type via pivot_table.',
            # Comments
            '# ✅ Lavora su copia — df_clean originale mai modificato':
                '# Work on a copy — df_clean original is never modified',
            '# ✅ Verifica che le colonne necessarie esistano':
                '# Verify required columns are present',
            '# ✅ Conversione datetime solo se necessario (evita overhead ridondante)':
                '# Convert datetime only if needed (skip if already datetime)',
            '# ✅ Usa trip_duration se già esiste, altrimenti ricalcola con Numba':
                '# Use trip_duration if present, otherwise recompute with Numba',
            '# ✅ Filtra righe con durata non valida':
                '# Filter rows with invalid duration',
            '# ✅ Crea colonna mese (Period ‘M’ garantisce ordine cronologico corretto)':
                "# Create month column (Period 'M' ensures correct chronological order)",
            "# ✅ Pivot: righe=mesi, colonne=member/casual, valori=somma minuti":
                '# Pivot: rows=months, columns=member/casual, values=total minutes',
            '.sort_index()   # garantisce ordine cronologico':
                '.sort_index()   # ensures chronological order',
            # Error messages
            'f"Colonne mancanti in df_clean: {missing}"':
                'f"Missing columns in df_clean: {missing}"',
            # Print strings
            "print(\"  ⚠️  'started_at' non è datetime → conversione in corso...\")":
                "print(\"  [!] 'started_at' is not datetime -> converting...\") ",
            "print(\"  ✅ 'started_at' già in formato datetime — conversione saltata\")":
                "print(\"  [OK] 'started_at' already datetime — skipping conversion\")",
            "print(\"  ✅ 'trip_duration' già presente — Numba non necessario\")":
                "print(\"  [OK] 'trip_duration' already present — Numba not needed\")",
            "print(\"  ⚠️  'trip_duration' assente → calcolo con Numba da started_at/ended_at\")":
                "print(\"  [!] 'trip_duration' absent -> computing with Numba\")",
            "print(f\"  ⚠️  {invalid_count:,} righe con durata <= 0 rimosse\")":
                "print(f\"  [!] {invalid_count:,} rows with duration <= 0 removed\")",
            "print(\"STEP 0 ✅ Funzione Numba 'compute_minutes' definita\")":
                "print(\"STEP 0 [OK] Numba function 'compute_minutes' defined\")",
            "print(f\"\\n  -> Mesi nel dataset    : {len(month_labels)}\")":
                "print(f\"\\n  -> Months in dataset  : {len(month_labels)}\")",
            "print(f\"  -> Periodo             : {month_labels[0]}  ->  {month_labels[-1]}\")":
                "print(f\"  -> Period             : {month_labels[0]}  ->  {month_labels[-1]}\")",
            "print(f\"  -> Ore totali member   : {member_hours.sum():>12,.0f}\")":
                "print(f\"  -> Total hours member  : {member_hours.sum():>12,.0f}\")",
            "print(f\"  -> Ore totali casual   : {casual_hours.sum():>12,.0f}\")":
                "print(f\"  -> Total hours casual  : {casual_hours.sum():>12,.0f}\")",
            "print(f\"  -> Ore totali combined : {(member_hours.sum() + casual_hours.sum()):>12,.0f}\")":
                "print(f\"  -> Total hours combined: {(member_hours.sum() + casual_hours.sum()):>12,.0f}\")",
            "print(\"STEP 3 ✅ Scala asse Y calcolata\")":
                "print(\"STEP 3 [OK] Y-axis scale computed\")",
            "print(f\"  -> Max ore in un mese  : {max_hours:>10,.0f}\")":
                "print(f\"  -> Max hours in a month: {max_hours:>10,.0f}\")",
            "print(f\"  -> Y max (arrotondato) : {y_max:>10,}  ({y_max // 10000} indici)\")":
                "print(f\"  -> Y max (rounded)     : {y_max:>10,}  ({y_max // 10000} indices)\")",
            "print(f\"  -> Scala               : 1 indice = 10,000 ore\")":
                "print(f\"  -> Scale               : 1 index = 10,000 hours\")",
            "print(\"STEP 4 ✅ Export completato\")":
                "print(\"STEP 4 [OK] Export complete\")",
            "print(\"\\n  Ultimi 5 mesi (più recenti):\")":
                "print(\"\\n  Last 5 months (most recent):\")",
            # Deprecated pandas parameter
            ", infer_datetime_format=True":  "",
        })
        new_cells.append(cell)
        continue

    # ── Cell 24: zoning check — Italian prints ─────────────────
    if idx == 24:
        cell = patch(cell, {
            '"\\nZone type -> numero di zone_name distinti"':
                '"\\nZone type -> distinct zone_name count"',
            '"\\nZone type -> zone_name associati"':
                '"\\nZone type -> associated zone_name values"',
        })
        new_cells.append(cell)
        continue

    # ── Cell 25: zoning preparation — Italian ─────────────────
    if idx == 25:
        cell = patch(cell, {
            'f"Colonne mancanti nel CSV: {sorted(missing)}"':
                'f"Missing columns in CSV: {sorted(missing)}"',
            'print(f"\U0001f4ca Zone caricate: {len(zoning):,} distretti")':
                'print(f"[OK] Zones loaded: {len(zoning):,} districts")',
            'print(f"   zone_name unici: {zoning[\'zone_name\'].nunique()}")':
                'print(f"   Unique zone_name: {zoning[\'zone_name\'].nunique()}")',
            'print(f"   zone_type unici: {zoning[\'zone_type\'].nunique()}")':
                'print(f"   Unique zone_type: {zoning[\'zone_type\'].nunique()}")',
            'print(f"   zone_type disponibili: {sorted(zoning[\'zone_type\'].unique())}")':
                'print(f"   Available zone_type: {sorted(zoning[\'zone_type\'].unique())}")',
            '# Crea GeoDataFrame con campi utili':
                '# Create GeoDataFrame with relevant fields',
            '# Info di controllo': '# Validation summary',
        })
        new_cells.append(cell)
        continue

    # ── Cell 26: redundant single-line print — REMOVE ──────────
    if idx == 26:
        continue  # skip entirely

    # ── Cell 27: prepare df_clean — Italian ────────────────────
    if idx == 27:
        cell = patch(cell, {
            'print(f"df_clean: {len(df_clean):,} rides, {len(df_clean.columns)} colonne")':
                'print(f"df_clean: {len(df_clean):,} rides, {len(df_clean.columns)} columns")',
            'f"   Coordinate bounds ({len(available_coords)}/4 disponibili):"':
                'f"   Coordinate bounds ({len(available_coords)}/4 available):"',
            'print("❌ Nessuna colonna coordinate trovata")':
                'print("[!] No coordinate columns found")',
            'print("❌ Colonna \'member_casual\' mancante")':
                'print("[!] Column \'member_casual\' missing")',
            'print(f"   Colonne totali: {list(df_clean.columns)}")':
                'print(f"   All columns: {list(df_clean.columns)}")',
        })
        new_cells.append(cell)
        continue

    # ── Cell 32: filter and segment — Italian ─────────────────
    if idx == 32:
        cell = patch(cell, {
            'print(f"   Rapporto Member/Casual: {len(member_zoning)/len(casual_zoning):.1f}x")':
                'print(f"   Member/Casual ratio: {len(member_zoning)/len(casual_zoning):.1f}x")',
        })
        new_cells.append(cell)
        continue

    # ── Cell 34: COMPLETE REWRITE — fix percentage > 100% bug ──
    if idx == 34:
        new_cells.append(mk_code(NEW_CELL_34))
        continue

    # ── Cell 36: chi-square — Italian ─────────────────────────
    if idx == 36:
        cell = patch(cell, {
            "'✅ SIGNIFICATIVA' if p_end<0.001 else '❌'":
                "'✅ SIGNIFICANT' if p_end<0.001 else '❌ not significant'",
        })
        new_cells.append(cell)
        continue

    # ── Cell 38: zone distribution chart — Italian ─────────────
    if idx == 38:
        cell = patch(cell, {
            "print(\"STEP 12 — Distribuzione ride per zona di partenza\")":
                "print(\"Start Zone Distribution — Member vs Casual\")",
            "print(f\"  -> Zona più usata (member)  : {member_pct.idxmax()}  ({member_pct.max():.1f}%)\")":
                "print(f\"  -> Most used zone (member): {member_pct.idxmax()}  ({member_pct.max():.1f}%)\") ",
            "print(f\"  -> Zona più usata (casual)  : {casual_pct.idxmax()}  ({casual_pct.max():.1f}%)\")":
                "print(f\"  -> Most used zone (casual): {casual_pct.idxmax()}  ({casual_pct.max():.1f}%)\") ",
            "print(f\"  -> Max divergenza member    : {divergence_pct.idxmax()}  ({divergence_pct.max():+.1f}%)\")":
                "print(f\"  -> Max divergence member  : {divergence_pct.idxmax()}  ({divergence_pct.max():+.1f}%)\") ",
            "print(f\"  -> Max divergenza casual    : {divergence_pct.idxmin()}  ({abs(divergence_pct.min()):+.1f}%)\")":
                "print(f\"  -> Max divergence casual  : {divergence_pct.idxmin()}  ({abs(divergence_pct.min()):+.1f}%)\") ",
            "ax1.set_ylabel('% ride sul totale per tipo utente', fontsize=11)":
                "ax1.set_ylabel('% of rides per user type', fontsize=11)",
            "ax1.set_title('Distribuzione ride per zona di partenza — Member vs Casual',":
                "ax1.set_title('Ride Distribution by Start Zone — Member vs Casual',",
            "ax2.set_ylabel('Divergenza %', fontsize=11)":
                "ax2.set_ylabel('Divergence %', fontsize=11)",
            "ax2.set_title('Divergenza per zona di partenza',":
                "ax2.set_title('Member − Casual Divergence by Start Zone',",
            "# ✅ Asse Y simmetrico — stesso spazio sopra e sotto lo zero":
                "# Symmetric Y axis — equal space above and below zero",
            "# ✅ Etichette divergenza:":
                "# Divergence bar labels:",
            "#    - valore sempre positivo con \"+\"":
                "#    - always positive value with \"+\"",
            "#    - colore nero":
                "#    - black text",
            "#    - indica chi prevale (Member / Casual)":
                "#    - indicates which group dominates",
            "print(\"\\n  Tabella riepilogativa (ordinata per divergenza):\")":
                "print(\"\\n  Summary table (sorted by divergence):\")",
            "'divergenza_%'": "'divergence_%'",
            "# ╔════════════════════════════════════════════════════════════\n# AX1 — barre affiancate member vs casual":
                "# AX1 — grouped bars member vs casual",
            "# ╔════════════════════════════════════════════════════════════\n# AX2 — divergenza simmetrica":
                "# AX2 — symmetric divergence bars",
            "# ╔═ Calcolo distribuzione ───────────────────────────────────────────":
                "# Ride distribution per zone",
            "# ╔═ Costanti visive ──────────────────────────────────────────────────":
                "# Visual constants",
            "# ╔═ Figure ──────────────────────────────────────────────────────────":
                "# Figure layout",
            "# ╔═ Tabella riepilogativa ────────────────────────────────────────────":
                "# Summary table",
            "LABEL_COLOR  = 'black'       # ✅ etichette sempre nere":
                "LABEL_COLOR  = 'black'",
        })
        new_cells.append(cell)
        continue

    # ── Cell 41: COMPLETE REWRITE — zone map with basemap ───────
    if idx == 41:
        new_cells.append(mk_code(NEW_CELL_41))
        new_cells.append(mk_md(MD_AFTER_ZONEMAP))
        new_cells.append(mk_code(NEW_CELL_CONVERSION))
        new_cells.append(mk_md(MD_AFTER_CONVERSION))
        continue

    # ── Cell 42: schema debug — fix paths + Italian ────────────
    if idx == 42:
        cell = patch(cell, {
            '"schema_df_clean.json"':   '"../output/schema_df_clean.json"',
            '"schema_zoning_df.json"':  '"../output/schema_zoning_df.json"',
            'print("\\nPrime 5 righe:")':
                'print("\\nFirst 5 rows:")',
            '# Dizionario schema per AI: {col: {dtype, examples: [...]}}':
                '# Schema dict: {col: {dtype, examples: [...]}}',
            '# prendo alcuni esempi non null per dare contesto':
                '# collect a few non-null examples for context',
            '# ESECUZIONE SUI TUOI DF':
                '# Run on both DataFrames',
            '# Se vuoi salvare gli schemi in JSON per passarli a un altro modello:':
                '# Save schemas as JSON',
        })
        new_cells.append(cell)
        continue

    # ── Cell 45: basic divergence heatmap — Italian ─────────────
    if idx == 45:
        cell = patch(cell, {
            "# ╔═ Verifica input ──────────────────────────────────────────────":
                "# Input validation",
            'f"Shape incompatibili: member={member_readable.shape} "':
                'f"Incompatible shapes: member={member_readable.shape} "',
            '"Index o colonne non coincidono tra member e casual"':
                '"Index or columns do not match between member and casual"',
            'print(f"\\n  -> Shape divergenza : {divergence.shape}")':
                'print(f"\\n  -> Divergence shape : {divergence.shape}")',
            "# ╔═ Colormap personalizzata (casual = arancione, member = verde) ─────":
                "# Custom diverging colormap (orange = casual, green = member)",
            "plt.title('DIVERGENZA: Member − Casual\\nStart Zone -> End Zone (100%)',":
                "plt.title('DIVERGENCE: Member − Casual\\nStart Zone -> End Zone',",
            'print("\\n  Top 5 divergenze assolute:")':
                'print("\\n  Top 5 absolute divergences:")',
            "print(f\"    {start} -> {end:<20} |{raw:+.1f}%  (più usato da {who})\")":
                "print(f\"    {start} -> {end:<20}  {raw:+.1f}%  -> more used by {who}\")",
            "# ╔═ Calcolo divergenza ──────────────────────────────────────────":
                "# Compute divergence",
            "# ╔═ Plot ────────────────────────────────────────────────────────":
                "# Plot",
            "# ╔═ Insight ──────────────────────────────────────────────────────────":
                "# Key insights",
        })
        new_cells.append(cell)
        continue

    # ── All other cells: pass through unchanged ────────────────
    new_cells.append(cell)


# ── Save rebuilt notebook ─────────────────────────────────────────────────────
nb['cells'] = new_cells
with open(NB_PATH, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f"[OK] Notebook saved — {len(new_cells)} cells total")
print(f"     (was {len(cells)} cells; removed 1, replaced 2, inserted 4)")
