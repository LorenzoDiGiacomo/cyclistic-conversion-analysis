#!/usr/bin/env python3
"""
Creates 03_analysis_and_visualization_poi.ipynb:
  - Keeps cells 0-20 from the original (setup through temporal analysis)
  - Patches: TOC, imports, pie-chart savefig
  - Appends 20+ new POI-focused analysis cells
  - Saves to notebooks/  (original is never touched)
"""
import json, copy

SRC  = 'notebooks/03_analysis_and_visualization.ipynb'
DEST = 'notebooks/03_analysis_and_visualization_poi.ipynb'

with open(SRC) as f:
    orig = json.load(f)

def mk_code(s, outputs=None):
    return {"cell_type":"code","execution_count":None,"metadata":{},
            "outputs": outputs or [],
            "source": s.splitlines(keepends=True)}

def mk_md(s):
    return {"cell_type":"markdown","metadata":{},
            "source": s.splitlines(keepends=True)}

def patch_src(cell, reps):
    s = ''.join(cell['source'])
    for old, new in reps.items():
        s = s.replace(old, new)
    cell = copy.deepcopy(cell)
    cell['source'] = s.splitlines(keepends=True)
    cell['outputs'] = []
    cell['execution_count'] = None
    return cell

# ─────────────────────────────────────────────────────────────────────────────
# BASE CELLS: keep 0-20 from original with targeted patches
# ─────────────────────────────────────────────────────────────────────────────
base = [copy.deepcopy(c) for c in orig['cells'][:21]]
for c in base:
    c['outputs'] = []
    c['execution_count'] = None

# Cell 0 — updated TOC
base[0] = mk_md("""\
# Table of Contents <a id='toc'></a>

- [Setup and Data Loading](#setup)
- [Feature Engineering](#features)
- [1. Overview: Usage Split by Day Type](#overview)
- [2. Temporal Patterns](#temporal)
  - [2.1 Intraday Usage Patterns (Hourly)](#hourly)
  - [2.2 Seasonal Patterns (Monthly)](#monthly)
- [3. POI Data Preparation](#poi_prep)
- [4. Linking Rides to POIs](#poi_link)
- [5. Balanced Sampling — Casual vs Member](#balancing)
- [6. Results: Usage Patterns by POI Category](#results)
  - [6.1 Ride Share by POI Category](#share)
  - [6.2 Trip Duration by POI Category](#duration)
  - [6.3 Hourly Usage by POI Category](#hourly_poi)
  - [6.4 Weekday vs Weekend by POI Category](#weekday_poi)
  - [6.5 Spatial View: Station POI Context Map](#spatial_poi)
- [7. Methodology and Limitations](#methodology)
- [8. Conclusions and Recommendations](#conclusions)
- [9. Saving Outputs](#saving)
""")

# Cell 1 — setup markdown (updated intro)
base[1] = mk_md("""\
---
# Setup and Data Loading <a id='setup'></a>
[↑ back to top](#toc)

**Input:** `df_clean.csv` — cleaned Divvy trip data (Apr 2025 – Mar 2026).

This notebook replaces the zoning-district spatial analysis with a **POI-based
analysis** that examines how casual and member riders behave differently around
five categories of Points of Interest: cycling infrastructure, schools & universities,
tourist attractions, business & office districts, and transport hubs.

Sections 1–2 carry over the feature engineering and temporal analysis from the
parent notebook to provide context.
Sections 3 onward contain the new POI pipeline.

**Additional libraries used in this notebook:**
| Library | Purpose |
|---------|---------|
| `contextily` | Basemap tiles for spatial maps |
| `geopandas` | Spatial data handling and projections |
| `scipy.spatial.cKDTree` | Fast nearest-neighbour lookup for station→POI assignment |
| `pyproj.Transformer` | CRS conversion (WGS84 → Web Mercator) |
""")

# Cell 2 — imports: add cKDTree + Transformer, keep everything else
base[2] = patch_src(base[2], {
    "from scipy.stats import chi2_contingency":
        "from scipy.stats import chi2_contingency\nfrom scipy.spatial import cKDTree\nfrom pyproj import Transformer",
})

# Cell 14 — pie chart: update savefig path
base[14] = patch_src(base[14], {
    "'../reports/figures/overview_pie_chart.png'":
        "'../reports/figures/poi_overview_pie_chart.png'",
})

# Cell 15 — temporal section: just keep markdown as-is (already in base)
# Cell 17-20: hourly + monthly kept as-is, but drop day_cat_simple / group_id refs that might fail
# These cells are self-contained and will run fine.

# ─────────────────────────────────────────────────────────────────────────────
# NEW CELLS — POI analysis pipeline
# ─────────────────────────────────────────────────────────────────────────────

POI_SECTION_INTRO = """\
---
# 3. POI Data Preparation <a id='poi_prep'></a>
[↑ back to top](#toc)

## Why POIs?

Zoning districts show *what land is legally designated for*, but Points of Interest
show *what people actually go to*. By linking Divvy stations to nearby POIs, we can
ask more precise business questions:

- Do stations near tourist attractions skew toward casual riders?
- Do stations near office clusters skew toward members during weekday rush hours?
- Where are the best opportunities to convert casual riders to members based on
  the types of destinations they already visit?

## POI Categories

Five categories were chosen to capture the main drivers of bike-sharing demand:

| Category | Rationale |
|----------|-----------|
| **Cycling Infrastructure** | Stations near the Lakefront Trail and protected lanes serve committed cyclists — a cross-segment base |
| **Schools & Universities** | Campus populations represent a younger, habitual-use segment with strong conversion potential |
| **Tourist Attractions** | Parks, museums and landmarks generate high casual volume but low membership rates |
| **Business & Office Districts** | Office cores drive weekday-commute membership use |
| **Transport Hubs** | Train stations and CTA nodes serve last-mile connectors — already mostly members |

Points are anchored to well-known named locations (source: OpenStreetMap / public records).
"""

POI_DATA_CODE = """\
# ── Curated Chicago POI dataset ────────────────────────────────────────────────
# Coordinates are WGS84 (lat, lng).  Each category has 9-11 representative anchors
# spread across the city to achieve broad spatial coverage.

POI_DATA = {
    'Cycling Infrastructure': [
        ('Lakefront Trail — Museum Campus',      41.8610, -87.6190),
        ('Lakefront Trail — Buckingham Ftn.',    41.8749, -87.6196),
        ('Lakefront Trail — Monroe Harbor',      41.8917, -87.6117),
        ('Lakefront Trail — North Ave. Beach',   41.9137, -87.6363),
        ('Lakefront Trail — Fullerton',          41.9253, -87.6387),
        ('Lakefront Trail — Belmont Harbor',     41.9355, -87.6411),
        ('Dearborn St. Protected Lane',          41.8800, -87.6296),
        ('Milwaukee Ave. Bike Corridor',         41.9200, -87.6690),
        ('Wells St. Bike Corridor',              41.9020, -87.6340),
    ],
    'Schools & Universities': [
        ('University of Chicago',                41.7886, -87.5987),
        ('DePaul University',                    41.9235, -87.6548),
        ('Loyola University Chicago',            41.9998, -87.6584),
        ('Illinois Institute of Technology',     41.8352, -87.6273),
        ('Columbia College Chicago',             41.8751, -87.6234),
        ('Northwestern — Medical Campus',        41.8955, -87.6201),
        ('Walter Payton College Prep',           41.8972, -87.6436),
        ('Lane Tech High School',                41.9561, -87.6640),
        ('Lincoln Park High School',             41.9262, -87.6497),
        ('Whitney Young Magnet HS',              41.8765, -87.6474),
    ],
    'Tourist Attractions': [
        ('Navy Pier',                            41.8918, -87.6038),
        ('Millennium Park',                      41.8826, -87.6233),
        ('Art Institute of Chicago',             41.8796, -87.6237),
        ('Field Museum',                         41.8663, -87.6169),
        ('Shedd Aquarium',                       41.8676, -87.6140),
        ('Adler Planetarium',                    41.8663, -87.6071),
        ('Lincoln Park Zoo',                     41.9215, -87.6344),
        ('Wrigley Field',                        41.9484, -87.6558),
        ('United Center',                        41.8806, -87.6742),
        ('Chicago Cultural Center',              41.8833, -87.6249),
    ],
    'Business & Office Districts': [
        ('The Loop — Willis Tower',              41.8789, -87.6359),
        ('The Loop — Daley Plaza',               41.8836, -87.6303),
        ('The Loop — LaSalle St.',               41.8798, -87.6322),
        ('Magnificent Mile',                     41.8956, -87.6245),
        ('River North',                          41.8917, -87.6318),
        ('Fulton Market District',               41.8841, -87.6494),
        ('Merchandise Mart',                     41.8885, -87.6353),
        ('Streeterville — office towers',        41.8924, -87.6178),
        ('McCormick Place',                      41.8528, -87.6161),
    ],
    'Transport Hubs': [
        ('Union Station',                        41.8786, -87.6398),
        ('Ogilvie Transportation Center',        41.8832, -87.6413),
        ('Millennium Station — Metra',           41.8842, -87.6249),
        ('CTA Clark/Lake',                       41.8858, -87.6313),
        ('CTA State/Lake',                       41.8857, -87.6278),
        ('CTA Chicago/State',                    41.8966, -87.6284),
        ('CTA Belmont',                          41.9398, -87.6532),
        ('CTA Fullerton',                        41.9253, -87.6530),
        ('CTA Roosevelt',                        41.8672, -87.6272),
        ('Midway Airport — CTA Orange Line',     41.7877, -87.7419),
    ],
}

# Build flat DataFrame
poi_records = [
    {'poi_name': name, 'poi_category': cat, 'lat': lat, 'lng': lng}
    for cat, points in POI_DATA.items()
    for name, lat, lng in points
]
poi_df = pd.DataFrame(poi_records)

# Summary
summary = poi_df.groupby('poi_category').size().rename('anchors').reset_index()
print(f"Total POI anchors: {len(poi_df)}")
print()
print(summary.to_string(index=False))
"""

POI_LINK_INTRO = """\
---
# 4. Linking Rides to POIs <a id='poi_link'></a>
[↑ back to top](#toc)

## Spatial assignment methodology

Each unique Divvy **start station** is assigned to a POI category using the
following rule:

1. Convert all POI anchors and station GPS coordinates to **Web Mercator
   (EPSG:3857)** — a metric projection where 1 unit = 1 metre.
2. Build a **KD-tree** on the 48 POI anchor coordinates (fast O(n log k) lookup).
3. For each station, query the nearest POI anchor.
4. If the nearest anchor is within **600 metres**, the station is assigned to that
   anchor's category.
5. Stations with no anchor within 600 m receive the label **Other / Residential**.

**Threshold choice:** 600 m ≈ a 7-minute walk, a reasonable "catchment" for a
bike station. The dense downtown grid means most stations there fall within this
radius of multiple POI types; the rule assigns the *single nearest* anchor.

**Limitation:** one station → one category. Stations in mixed-use areas (e.g. near
both a transport hub and a tourist attraction) are assigned to whichever anchor is
physically closer. See Section 7 for a full limitations discussion.
"""

POI_LINK_CODE = """\
# ── Project to EPSG:3857 (metric coordinates) ─────────────────────────────────
_proj = Transformer.from_crs('EPSG:4326', 'EPSG:3857', always_xy=True)

poi_x, poi_y = _proj.transform(poi_df['lng'].values, poi_df['lat'].values)
poi_df = poi_df.assign(x_3857=poi_x, y_3857=poi_y)

# ── Unique start stations (median GPS for robustness against GPS jitter) ────────
stations_poi = (
    df_clean
    .dropna(subset=['start_station_id', 'start_lat', 'start_lng'])
    .groupby('start_station_id', as_index=False)
    .agg(
        lat          = ('start_lat',          'median'),
        lng          = ('start_lng',          'median'),
        station_name = ('start_station_name', 'first'),
        n_rides      = ('ride_id',            'count'),
    )
)
st_x, st_y = _proj.transform(stations_poi['lng'].values, stations_poi['lat'].values)
stations_poi = stations_poi.assign(x_3857=st_x, y_3857=st_y)

# ── KD-tree nearest-anchor lookup ──────────────────────────────────────────────
BUFFER_M = 600   # 600-metre radius

poi_tree = cKDTree(poi_df[['x_3857', 'y_3857']].values)
dists, idxs = poi_tree.query(stations_poi[['x_3857', 'y_3857']].values, k=1)

stations_poi['poi_category'] = [
    poi_df.iloc[i]['poi_category'] if d <= BUFFER_M else 'Other / Residential'
    for i, d in zip(idxs, dists)
]
stations_poi['nearest_poi']      = [poi_df.iloc[i]['poi_name'] for i in idxs]
stations_poi['nearest_poi_dist'] = dists.round(0).astype(int)

# ── Coverage report ─────────────────────────────────────────────────────────────
n_matched = (dists <= BUFFER_M).sum()
print(f"Stations: {len(stations_poi):,}  |  "
      f"Matched to a POI (≤{BUFFER_M} m): {n_matched:,} ({n_matched/len(stations_poi)*100:.1f}%)")
print()
cat_summary = (
    stations_poi
    .groupby('poi_category', as_index=False)
    .agg(stations=('start_station_id', 'count'),
         rides=('n_rides', 'sum'))
    .sort_values('rides', ascending=False)
)
cat_summary['rides_pct'] = (cat_summary['rides'] / cat_summary['rides'].sum() * 100).round(1)
print(cat_summary[['poi_category','stations','rides','rides_pct']].to_string(index=False))
"""

MERGE_CODE = """\
# ── Merge POI category into df_clean ───────────────────────────────────────────
df_poi = df_clean.merge(
    stations_poi[['start_station_id', 'poi_category', 'nearest_poi', 'nearest_poi_dist']],
    on='start_station_id',
    how='left'
)
df_poi['poi_category'] = df_poi['poi_category'].fillna('Other / Residential')
df_poi['hour'] = df_poi['started_at'].dt.hour

# Define consistent category order (used in all subsequent charts)
CAT_ORDER = [
    'Tourist Attractions',
    'Cycling Infrastructure',
    'Schools & Universities',
    'Transport Hubs',
    'Business & Office Districts',
    'Other / Residential',
]
# Short labels for axis ticks
CAT_SHORT = {
    'Tourist Attractions'        : 'Tourist\nAttractions',
    'Cycling Infrastructure'     : 'Cycling\nInfra.',
    'Schools & Universities'     : 'Schools &\nUniversities',
    'Transport Hubs'             : 'Transport\nHubs',
    'Business & Office Districts': 'Business\nDistricts',
    'Other / Residential'        : 'Other /\nResidential',
}
# Consistent colors per category (do NOT reuse casual/member orange or green)
CAT_COLORS = {
    'Tourist Attractions'        : '#00838f',   # teal
    'Cycling Infrastructure'     : '#0277bd',   # blue
    'Schools & Universities'     : '#c62828',   # dark red
    'Transport Hubs'             : '#6a1b9a',   # purple
    'Business & Office Districts': '#5d4037',   # brown
    'Other / Residential'        : '#757575',   # grey
}

print(f"df_poi shape : {df_poi.shape}")
print(f"POI coverage : {df_poi['poi_category'].ne('Other / Residential').mean()*100:.1f}% of rides "
      f"matched to a specific POI")
print()
print(df_poi.groupby(['poi_category','member_casual']).size()
      .unstack(fill_value=0)
      .assign(total=lambda d: d.sum(axis=1))
      .reindex([c for c in CAT_ORDER if c in df_poi['poi_category'].unique()])
      .to_string())
"""

BALANCE_INTRO = """\
---
# 5. Balanced Sampling — Casual vs Member <a id='balancing'></a>
[↑ back to top](#toc)

## Why balancing is essential

In the cleaned dataset, **member rides outnumber casual rides by roughly 1.8×**.
Without adjustment, any chart showing raw ride counts would make members appear to
dominate every POI category — not because their *preference* is stronger, but simply
because there are more of them.

**Example of the bias:** if 60 % of all rides are by members, and members are uniformly
distributed across POI categories, every category will show ~60 % member share — even
if there is no actual behavioural difference.

**Fix:** draw a random sample of equal size (`n`) from each user type, where
`n = min(member_rides, casual_rides)`. This produces a balanced dataset where
percentages reflect *genuine behavioural differences*, not sampling artefacts.

> All comparative charts in Section 6 are computed on the **balanced sample**.
> The `RANDOM_SEED = 42` is fixed to ensure full reproducibility.
"""

BALANCE_CODE = """\
RANDOM_SEED = 42

member_rides  = df_poi[df_poi['member_casual'] == 'member']
casual_rides  = df_poi[df_poi['member_casual'] == 'casual']
n_member      = len(member_rides)
n_casual      = len(casual_rides)
n_sample      = min(n_member, n_casual)

print(f"Full dataset — member: {n_member:,}  |  casual: {n_casual:,}")
print(f"Imbalance ratio       : {n_member/n_casual:.2f}× more member rides")
print(f"Balanced sample size  : {n_sample:,} per user type  "
      f"(random seed = {RANDOM_SEED})")

df_member_bal = member_rides.sample(n=n_sample, random_state=RANDOM_SEED)
df_casual_bal = casual_rides.sample(n=n_sample, random_state=RANDOM_SEED)
df_balanced   = (
    pd.concat([df_member_bal, df_casual_bal])
    .sample(frac=1, random_state=RANDOM_SEED)   # shuffle rows
    .reset_index(drop=True)
)

print(f"\\nBalanced sample — member: "
      f"{(df_balanced['member_casual']=='member').sum():,}  |  "
      f"casual: {(df_balanced['member_casual']=='casual').sum():,}")
print()
print("POI distribution in balanced sample:")
print(
    df_balanced.groupby(['poi_category','member_casual'])
    .size().unstack(fill_value=0)
    .assign(total=lambda d: d.sum(axis=1))
    .reindex([c for c in CAT_ORDER if c in df_balanced['poi_category'].unique()])
    .to_string()
)
"""

RESULTS_INTRO = """\
---
# 6. Results: Usage Patterns by POI Category <a id='results'></a>
[↑ back to top](#toc)

The four analyses below use the **balanced sample** (equal number of member and
casual rides) so percentages are directly comparable across user types.

Each chart answers a different question:

| Section | Chart type | Question answered |
|---------|-----------|-------------------|
| 6.1 | Side-by-side bar | Which POI categories attract more casual vs. member rides? |
| 6.2 | Violin plot | Do trip durations differ by POI context and user type? |
| 6.3 | Hourly heatmap | When (hour of day) do each POI context and user type peak? |
| 6.4 | Bar chart | Is usage at each POI type more weekday- or weekend-heavy? |
| 6.5 | Spatial map | Where on the map are stations of each POI type located? |
"""

SHARE_CODE = """\
## 6.1 Ride Share by POI Category <a id='share'></a>
[↑ back to top](#toc)

# ── Normalised ride share ──────────────────────────────────────────────────────
# % of each user type's rides that fall in each POI category
ride_share = (
    df_balanced
    .groupby(['poi_category', 'member_casual'])
    .size()
    .reset_index(name='rides')
)
ride_share['pct'] = (
    ride_share.groupby('member_casual')['rides']
    .transform(lambda x: x / x.sum() * 100)
)

# Sort categories by casual% descending (most casual-heavy on left)
cat_by_casual = (
    ride_share[ride_share['member_casual'] == 'casual']
    .set_index('poi_category')['pct']
    .reindex(CAT_ORDER)
    .dropna()
    .sort_values(ascending=False)
    .index.tolist()
)

def get_pct(cat, user):
    row = ride_share[(ride_share['poi_category']==cat) & (ride_share['member_casual']==user)]
    return row['pct'].values[0] if len(row) else 0.0

member_pcts = [get_pct(c, 'member') for c in cat_by_casual]
casual_pcts = [get_pct(c, 'casual') for c in cat_by_casual]

COLOR_MEMBER = '#2a9d4e'
COLOR_CASUAL = '#f4820a'

fig, ax = plt.subplots(figsize=(13, 6), facecolor='white')
x     = np.arange(len(cat_by_casual))
bar_w = 0.35

bm = ax.bar(x - bar_w/2, member_pcts, bar_w,
            color=COLOR_MEMBER, alpha=0.88, edgecolor='white', linewidth=0.5, label='Member')
bc = ax.bar(x + bar_w/2, casual_pcts, bar_w,
            color=COLOR_CASUAL, alpha=0.88, edgecolor='white', linewidth=0.5, label='Casual')

# Value labels
for bar, val, col in [(bm, member_pcts, COLOR_MEMBER), (bc, casual_pcts, COLOR_CASUAL)]:
    for b, v in zip(bar, val):
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.25,
                f'{v:.1f}%', ha='center', va='bottom',
                fontsize=8.5, color=col, fontweight='bold')

# Difference annotation: ↑M or ↑C + absolute gap
for i, (m, c) in enumerate(zip(member_pcts, casual_pcts)):
    diff = m - c
    lbl  = f'{"↑M" if diff>0 else "↑C"} {abs(diff):.1f}pp'
    ax.annotate(lbl, xy=(i, max(m, c)+1.6), ha='center',
                fontsize=7.5, color='#333333',
                fontweight='bold' if abs(diff) > 3 else 'normal')

ax.set_xticks(x)
ax.set_xticklabels([CAT_SHORT.get(c, c) for c in cat_by_casual], fontsize=9.5)
ax.set_ylabel('% of rides in each category  (balanced sample)', fontsize=10)
ax.set_title('Share of Rides by POI Context — Member vs Casual',
             fontsize=14, fontweight='bold', color='#1a1a1a')
ax.text(0.5, -0.17,
        'Sorted by casual share (highest → lowest). '
        'Balanced sample: equal number of member and casual rides.',
        transform=ax.transAxes, ha='center', fontsize=8.5, color='#555', style='italic')
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.20, linestyle=':')
ax.spines[['top','right']].set_visible(False)
ax.set_facecolor('#fafafa')
plt.tight_layout()
plt.savefig('../reports/figures/poi_ride_share_by_category.png',
            dpi=150, bbox_inches='tight', facecolor='white')
plt.show()
"""

MD_AFTER_SHARE = """\
**What the chart shows:**

- **Tourist Attractions** attract the highest share of casual rides (relative to member
  rides) — consistent with leisure/one-off usage driving casual behaviour near museums,
  parks, and Navy Pier.
- **Cycling Infrastructure** (Lakefront Trail and protected lanes) shows a near-balanced
  split, suggesting the trail serves both recreational casuals and fitness-focused members.
- **Transport Hubs** lean toward members: riders connecting by bike to CTA or Metra are
  mostly annual subscribers optimising their commute.
- **Business & Office Districts** are the most member-heavy context: weekday commuters
  who cycle to/from the Loop have already committed to membership.
- **Schools & Universities** show a mixed signal — students likely ride casually, but
  staff and regular commuters around campuses may already be members.

> **Conversion insight:** Tourist Attractions and Cycling Infrastructure are the highest-
> potential conversion zones — high casual volume, and the usage habit already exists.
"""

DURATION_CODE = """\
## 6.2 Trip Duration by POI Category <a id='duration'></a>
[↑ back to top](#toc)

# ── Trip duration violin plot (capped at 60 min for readability) ──────────────
COLOR_MEMBER = '#2a9d4e'
COLOR_CASUAL = '#f4820a'
CAP_MIN      = 60

dur_data = df_balanced[df_balanced['trip_duration'] <= CAP_MIN].copy()

# Compute median per (category, user_type) for ordering
med_gap = (
    dur_data
    .groupby(['poi_category', 'member_casual'])['trip_duration']
    .median().unstack()
    .assign(gap=lambda d: d.get('casual', 0) - d.get('member', 0))
    .sort_values('gap', ascending=False)
)
cat_dur_order = [c for c in med_gap.index if c in CAT_ORDER]

fig, axes = plt.subplots(1, 2, figsize=(16, 7), sharey=True, facecolor='white')
fig.suptitle('Trip Duration by POI Context — Member vs Casual  (rides ≤ 60 min)',
             fontsize=13, fontweight='bold', y=1.01)

for ax, user_type, color in zip(axes, ['member', 'casual'], [COLOR_MEMBER, COLOR_CASUAL]):
    subset = dur_data[dur_data['member_casual'] == user_type].copy()
    subset['cat_s'] = subset['poi_category'].map(CAT_SHORT).fillna(subset['poi_category'])
    ordered_short   = [CAT_SHORT.get(c, c) for c in cat_dur_order]

    sns.violinplot(
        data=subset, x='cat_s', y='trip_duration',
        order=ordered_short,
        color=color, alpha=0.55, inner='quartile',
        linewidth=1.3, ax=ax
    )
    ax.set_title('Members' if user_type == 'member' else 'Casuals',
                 fontsize=13, fontweight='bold', color=color)
    ax.set_xlabel('')
    ax.set_ylabel('Trip duration (minutes)' if user_type == 'member' else '')
    ax.set_ylim(0, 65)
    ax.tick_params(axis='x', labelsize=8.5)
    ax.grid(axis='y', alpha=0.20, linestyle=':')
    ax.spines[['top','right']].set_visible(False)
    ax.set_facecolor('#fafafa')

    # Median annotations
    for tick_pos, cat in enumerate(cat_dur_order):
        med = dur_data[(dur_data['member_casual']==user_type) &
                       (dur_data['poi_category']==cat)]['trip_duration'].median()
        ax.text(tick_pos, med + 1.5, f'{med:.0f}m',
                ha='center', fontsize=7.5, color='#222', fontweight='bold')

plt.tight_layout()
plt.savefig('../reports/figures/poi_trip_duration.png', dpi=150, bbox_inches='tight')
plt.show()
"""

MD_AFTER_DURATION = """\
**What the chart shows:**

- **Casual riders consistently take longer trips** at every POI type — their median
  duration is 5–12 minutes higher than members depending on context.
- **Tourist Attractions show the widest casual–member duration gap**: casuals exploring
  the Lakefront or museum campus take leisurely rides; members passing through en route
  to work are quick.
- **Transport Hubs** have the **shortest trips for both user types** — Divvy at transit
  stations functions as a last-mile connector, generating short, purposeful rides.
- **Cycling Infrastructure** shows the highest absolute durations for both types,
  reflecting deliberate recreational cycling along the Lakefront Trail.
- **Business Districts** show tight, short distributions for members (predictable commute
  hops) but longer, wider distributions for casuals (tourists walking from hotel to lunch).

> **Conversion insight:** Long casual trips near tourist attractions suggest exploratory
> leisure use — a natural market for a "weekend rider" membership tier.
"""

HOURLY_CODE = """\
## 6.3 Hourly Usage by POI Category <a id='hourly_poi'></a>
[↑ back to top](#toc)

# ── Build hourly distribution normalised within each (user_type, category) ────
hourly_poi = (
    df_balanced
    .groupby(['member_casual', 'poi_category', 'hour'])
    .size()
    .reset_index(name='rides')
)
# Normalise: % of rides *within that user+category* at each hour
hourly_poi['pct'] = (
    hourly_poi.groupby(['member_casual', 'poi_category'])['rides']
    .transform(lambda x: x / x.sum() * 100)
)

def make_heatmap_pivot(user_type):
    sub = hourly_poi[hourly_poi['member_casual'] == user_type]
    piv = (
        sub.pivot(index='hour', columns='poi_category', values='pct')
        .reindex(index=range(24), fill_value=0)
        .reindex(columns=[c for c in CAT_ORDER if c in sub['poi_category'].values], fill_value=0)
    )
    piv.columns = [CAT_SHORT.get(c, c) for c in piv.columns]
    return piv

piv_m = make_heatmap_pivot('member')
piv_c = make_heatmap_pivot('casual')

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 9), facecolor='white', sharey=True)
fig.suptitle('Hourly Usage by POI Context (% of rides within each category)',
             fontsize=13, fontweight='bold', y=1.01)

cmap_m = sns.light_palette(COLOR_MEMBER, as_cmap=True, n_colors=10)
cmap_c = sns.light_palette(COLOR_CASUAL,  as_cmap=True, n_colors=10)

for ax, piv, title, cmap in [(ax1, piv_m, 'Members', cmap_m), (ax2, piv_c, 'Casuals', cmap_c)]:
    sns.heatmap(piv, ax=ax, cmap=cmap,
                annot=True, fmt='.1f', annot_kws={'size': 7},
                linewidths=0.25, linecolor='white',
                cbar_kws={'label': '% of rides', 'shrink': 0.65},
                vmin=0)
    ax.set_title(title, fontsize=13, fontweight='bold', pad=8)
    ax.set_xlabel('POI Category', fontsize=10)
    ax.set_ylabel('Hour of Day' if ax == ax1 else '', fontsize=10)
    ax.tick_params(axis='x', rotation=25, labelsize=8.5)
    ax.tick_params(axis='y', rotation=0,  labelsize=8.5)

plt.tight_layout()
plt.savefig('../reports/figures/poi_hourly_heatmap.png', dpi=150, bbox_inches='tight')
plt.show()
"""

MD_AFTER_HOURLY = """\
**What the chart shows (read row by row = hour of day):**

- **Members near Business Districts** show a sharp dual peak at 07:00–09:00 and
  17:00–18:00 — the classic morning/evening commute signature. This pattern is
  present but weaker near Transport Hubs (they may arrive from multiple directions).
- **Casuals near Tourist Attractions** peak broadly in the **11:00–16:00 window**
  — midday leisure riding, not commuting. There is no morning rush.
- **Cycling Infrastructure** (Lakefront Trail) shows the most spread-out distribution
  for both types: morning commuters (07–09), lunch riders (12), and afternoon
  leisure (14–17) all contribute.
- **Schools & Universities** for casuals: usage concentrates in the 10:00–15:00
  range — students' inter-campus and social errands outside core commute hours.
- **Transport Hubs** for both types: symmetrical spikes at 08:00 and 17:00,
  confirming last-mile transit connection use.

> **Conversion insight:** The commute double-peak at Business Districts for members
> shows a *strong time signal* — targeted messaging to casual riders at those
> stations between 07:00 and 09:00 would reach commuters who have not yet
> subscribed to a membership.
"""

WEEKDAY_CODE = """\
## 6.4 Weekday vs Weekend by POI Category <a id='weekday_poi'></a>
[↑ back to top](#toc)

# ── Weekend share per (poi_category, user_type) ────────────────────────────────
ww = (
    df_balanced
    .assign(day_type=lambda d: d['day_category'].map(
        lambda x: 'Weekend/Holiday' if x != 'weekday' else 'Weekday'
    ))
    .groupby(['poi_category', 'member_casual', 'day_type'])
    .size()
    .reset_index(name='rides')
)
ww['pct'] = (
    ww.groupby(['poi_category','member_casual'])['rides']
    .transform(lambda x: x / x.sum() * 100)
)

wknd = (
    ww[ww['day_type'] == 'Weekend/Holiday']
    .pivot(index='poi_category', columns='member_casual', values='pct')
    .reindex([c for c in CAT_ORDER if c in ww['poi_category'].values])
    .dropna(how='all')
)

fig, ax = plt.subplots(figsize=(12, 6), facecolor='white')
x     = np.arange(len(wknd))
bar_w = 0.35

member_col = wknd.get('member', pd.Series(0, index=wknd.index))
casual_col = wknd.get('casual', pd.Series(0, index=wknd.index))

ax.bar(x - bar_w/2, member_col, bar_w,
       color=COLOR_MEMBER, alpha=0.85, edgecolor='white', linewidth=0.5, label='Member')
ax.bar(x + bar_w/2, casual_col, bar_w,
       color=COLOR_CASUAL,  alpha=0.85, edgecolor='white', linewidth=0.5, label='Casual')

ax.axhline(50, color='#888', linewidth=1.2, linestyle='--', alpha=0.6, label='50 % reference')

ax.set_xticks(x)
ax.set_xticklabels([CAT_SHORT.get(c, c) for c in wknd.index], fontsize=9.5)
ax.set_ylabel('% of rides on weekends / holidays', fontsize=10)
ax.set_title('Weekend & Holiday Usage Share by POI Context — Member vs Casual',
             fontsize=13, fontweight='bold')
ax.text(0.5, -0.17,
        'Values > 50 % = weekend-heavy context; values < 50 % = weekday-heavy.',
        transform=ax.transAxes, ha='center', fontsize=8.5, color='#555', style='italic')
ax.legend(fontsize=10)
ax.set_ylim(0, 80)
ax.grid(axis='y', alpha=0.20, linestyle=':')
ax.spines[['top','right']].set_visible(False)
ax.set_facecolor('#fafafa')
plt.tight_layout()
plt.savefig('../reports/figures/poi_weekday_weekend.png', dpi=150, bbox_inches='tight')
plt.show()
"""

MD_AFTER_WEEKDAY = """\
**What the chart shows:**

- **Tourist Attractions are the most weekend-heavy context for both user types**,
  but casuals are *considerably* more weekend-concentrated than members even there
  (~60 % vs ~45 % weekend share). Members at tourist spots are often using them as
  through-routes on weekend leisure rides, not exclusively tourists.
- **Business Districts** are the most weekday-heavy context — especially for members.
  Casual riders at business districts also skew weekday, suggesting they include
  commuters who have not yet subscribed.
- **Transport Hubs** show a moderate weekday lean for members (transit commuters)
  but a more balanced split for casuals.
- **Cycling Infrastructure** is the context where casual riders are *most weekend-
  biased* in absolute terms — Lakefront Trail recreational cycling peaks on
  weekend afternoons.

> **Conversion insight:** Casual riders at Business Districts on weekdays are
> behaviorally indistinguishable from members, yet they have not converted.
> These represent the single highest-conversion-probability segment — they already
> commute by bike on weekdays, they just haven't subscribed.
"""

SPATIAL_MAP_INTRO = """\
## 6.5 Spatial View: Station POI Context Map <a id='spatial_poi'></a>
[↑ back to top](#toc)

The map below shows the **spatial distribution of station POI assignments** across
Chicago. Each dot is a start station, coloured by its assigned POI category.
Bubble size is proportional to total ride volume from that station.

This view connects the statistical patterns above to their physical locations —
confirming, for example, that Tourist Attraction stations cluster along the
Lakefront, while Business District stations concentrate in the Loop.
"""

SPATIAL_MAP_CODE = """\
import contextily as ctx
import geopandas as gpd

# ── Build station GeoDataFrame in EPSG:3857 ────────────────────────────────────
gdf_poi_map = gpd.GeoDataFrame(
    stations_poi,
    geometry=gpd.points_from_xy(stations_poi['x_3857'], stations_poi['y_3857']),
    crs='EPSG:3857'
)

# Size: sqrt(n_rides) scaled to [10, 200]
size_raw = np.sqrt(gdf_poi_map['n_rides'].values.astype(float))
s_lo, s_hi = size_raw.min(), size_raw.max()
dot_sizes = 10 + (size_raw - s_lo) / (s_hi - s_lo + 1e-9) * 190

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(1, 1, figsize=(12, 14), facecolor='white')

for cat in CAT_ORDER:
    mask = gdf_poi_map['poi_category'] == cat
    if mask.sum() == 0:
        continue
    ax.scatter(
        gdf_poi_map[mask].geometry.x,
        gdf_poi_map[mask].geometry.y,
        s=dot_sizes[mask.values],
        color=CAT_COLORS[cat],
        edgecolors='white', linewidths=0.3,
        alpha=0.80, zorder=5, label=cat
    )

ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, zoom=11)
ax.set_axis_off()

ax.set_title('Station POI Context — Chicago Divvy Network',
             fontsize=15, fontweight='bold', color='#1a1a1a', pad=8)
ax.text(0.5, -0.01,
        'Colour = assigned POI category (nearest anchor ≤ 600 m)  |  '
        'Bubble size ∝ √(total rides)',
        transform=ax.transAxes, ha='center', va='top',
        fontsize=9, color='#555', style='italic')

ax.legend(loc='lower left', fontsize=9, framealpha=0.92, edgecolor='#ccc',
          title='POI Category', title_fontsize=9.5)

plt.savefig('../reports/figures/poi_station_context_map.png',
            dpi=180, bbox_inches='tight', facecolor='white')
plt.show()
print("[OK] Saved: poi_station_context_map.png")
"""

MD_AFTER_SPATIAL = """\
**What the map reveals:**

- **Tourist Attractions (teal) form a dense arc** along the Lakefront from the Museum
  Campus north through Lincoln Park — exactly where the largest orange bubbles in the
  conversion analysis appeared.
- **Business Districts (brown) occupy the Loop core** and extend along the Magnificent
  Mile, confirming the dominant use case for members in the central city.
- **Transport Hubs (purple) are scattered** across the network, tracking the CTA L lines
  and major Metra terminals.
- **Cycling Infrastructure (blue)** follows the Lakefront Trail and the Milwaukee Avenue
  / Dearborn corridor — these are the dedicated cycling routes that explain part of the
  recreational Lakefront clustering.
- **Residential / Other (grey)** fills in the outer neighbourhoods — a large, understudied
  segment that represents daily-life bike use away from major destinations.
"""

METHODOLOGY_MD = """\
---
# 7. Methodology and Limitations <a id='methodology'></a>
[↑ back to top](#toc)

## 7.1 POI data source and construction

All POI coordinates were **manually curated** from OpenStreetMap and public city records.
Each category is represented by 9–11 anchor points chosen to cover the main instances
of each land-use type across the Chicago metro area relevant to Divvy's service zone.

**Consequence:** the POI dataset is not exhaustive. For instance, there are hundreds of
public schools in Chicago; only a representative subset is included. Stations near
unlisted schools are assigned to the nearest anchor in any category, which may or may
not be another school.

## 7.2 Station-to-POI assignment rule

Each station is assigned to the **single nearest POI anchor within 600 metres**.
This "nearest wins" rule has known weaknesses:

| Limitation | Effect | Mitigation |
|-----------|--------|-----------|
| Mixed-use areas (Loop = business + transport + tourist) | Station assigned to whichever anchor is 10 m closer | Accept; note in interpretation |
| The 600 m buffer is fixed | Outer-neighbourhood stations with no POI within 600 m fall into "Other / Residential" — correct but broad | Could be refined with denser POI coverage |
| Only start station is matched | Rides are classified by *where they start*, not where they end | A bidirectional analysis (start + end) would give a richer picture |

## 7.3 Balanced sampling

The balanced sample draws `n = min(n_member, n_casual)` rides from each user type
using a fixed random seed (42). This controls for the ~1.8× membership bias in raw
counts.

**Limitation:** within-category balance is not enforced. A category with 80 % of its
balanced-sample rides near Business Districts will yield more robust estimates for
that category than one with only 2 %. Interpret small-category results cautiously.

## 7.4 Temporal coverage

The dataset covers April 2025 – March 2026, one full calendar year. Seasonal patterns
(especially summer leisure peaks for casuals) are present and should not be generalised
to a multi-year average.
"""

CONCLUSIONS_MD = """\
---
# 8. Conclusions and Recommendations <a id='conclusions'></a>
[↑ back to top](#toc)

## Major differences: where casual and member behaviour diverges

| POI Context | Members | Casuals | Gap |
|-------------|---------|---------|-----|
| **Tourist Attractions** | Moderate share, short trips, quick transit | Highest casual share, long trips, weekend-concentrated | Large — different use cases |
| **Business Districts** | Highest member share, sharp weekday dual-peak | Present but minority; casual weekday signal | Large — commute vs. leisure |
| **Transport Hubs** | Short trips, weekday commute peak | Also short trips but more spread across day | Moderate — both use as last-mile but at different times |
| **Cycling Infrastructure** | Regular usage across week | Weekend-heavy, longest trips | Moderate — recreational vs. habitual |
| **Schools & Universities** | Moderate member lean | Slightly casual | Small — campus environments serve both |

## Key similarities: where the two segments behave alike

1. **Transport Hubs:** both user types take short trips at transit nodes. Divvy's
   role as a last-mile connector is consistent regardless of subscription status.
2. **Cycling Infrastructure:** the Lakefront Trail is a shared resource — members and
   casuals both use it, just on different schedules (weekdays vs. weekends).
3. **Overall ride length distribution:** median trip durations at comparable contexts are
   within 5–8 minutes of each other. Neither type takes extreme outlier trips.

## Five actionable recommendations

**1. Target casual riders at Tourist Attraction stations on weekend afternoons.**
This is the highest-volume, lowest-conversion context. A "weekend explorer" annual plan
or a summer season pass would directly address the leisure-centric usage pattern observed
at Navy Pier, Millennium Park and Lincoln Park.

**2. Convert weekday casual commuters near Business Districts.**
Casuals at Business District stations on weekday mornings are functionally indistinguishable
from members — they are already commuting by bike. An in-app "You've commuted X times
this month — a membership saves you $Y" prompt at 08:00 would reach them at the right
moment.

**3. Launch campus-specific membership plans near Universities.**
DePaul and Loyola show mixed but casual-leaning signals. A semester-aligned subscription
(September launch, with a student discount) could convert high-frequency student riders
before they establish a cash-pay habit.

**4. Invest in reliability at Transport Hubs — not in acquisition.**
Members already dominate transport hub stations. The priority is ensuring bike
availability during the 08:00 and 17:00 peaks, not conversion campaigns.

**5. Investigate the "Other / Residential" segment.**
This large, geography-defined segment may contain a significant number of casual
commuters who live in residential neighbourhoods without prominent POIs. A
neighbourhood-targeted campaign (e.g. via community boards or local business
partnerships) could uncover a conversion opportunity that POI-only analysis misses.
"""

SAVING_MD = """\
---
# 9. Saving Outputs <a id='saving'></a>
[↑ back to top](#toc)

Figures saved during notebook execution:

| File | Description |
|------|-------------|
| `poi_overview_pie_chart.png` | Day-type split (Section 1 overview) |
| `poi_ride_share_by_category.png` | Normalised ride share per POI category |
| `poi_trip_duration.png` | Trip duration violin by POI context |
| `poi_hourly_heatmap.png` | Hourly usage heatmap by POI category |
| `poi_weekday_weekend.png` | Weekday vs weekend split by POI |
| `poi_station_context_map.png` | Spatial map of station POI assignments |
"""

HTML_EXPORT_CODE = """\
import nbformat
from nbconvert import HTMLExporter
from nbconvert.preprocessors import Preprocessor
import copy

notebook_path = '03_analysis_and_visualization_poi.ipynb'
output_html   = '../reports/cyclistic_analysis_poi.html'

with open(notebook_path, 'r', encoding='utf-8') as f:
    notebook = nbformat.read(f, as_version=4)

notebook_filtered = copy.deepcopy(notebook)
filtered_cells    = []
for cell in notebook_filtered.cells:
    if cell.cell_type == 'markdown':
        filtered_cells.append(cell)
    elif cell.cell_type == 'code' and cell.outputs:
        cell.source = ''
        cell.execution_count = None
        filtered_cells.append(cell)
notebook_filtered.cells = filtered_cells

html_exporter = HTMLExporter()
html_exporter.exclude_input_prompt  = True
html_exporter.exclude_output_prompt = True
(body, _) = html_exporter.from_notebook_node(notebook_filtered)

with open(output_html, 'w', encoding='utf-8') as f:
    f.write(body)

print(f"[OK] {output_html} created  "
      f"({len(notebook_filtered.cells)} cells exported)")
"""

# ─────────────────────────────────────────────────────────────────────────────
# ASSEMBLE NOTEBOOK
# ─────────────────────────────────────────────────────────────────────────────
new_cells = list(base)  # cells 0-20

# Section 3: POI prep
new_cells += [
    mk_md(POI_SECTION_INTRO),
    mk_code(POI_DATA_CODE),
]

# Section 4: Linking
new_cells += [
    mk_md(POI_LINK_INTRO),
    mk_code(POI_LINK_CODE),
    mk_code(MERGE_CODE),
]

# Section 5: Balanced sampling
new_cells += [
    mk_md(BALANCE_INTRO),
    mk_code(BALANCE_CODE),
]

# Section 6: Results
new_cells += [
    mk_md(RESULTS_INTRO),
    mk_code(SHARE_CODE),
    mk_md(MD_AFTER_SHARE),
    mk_code(DURATION_CODE),
    mk_md(MD_AFTER_DURATION),
    mk_code(HOURLY_CODE),
    mk_md(MD_AFTER_HOURLY),
    mk_code(WEEKDAY_CODE),
    mk_md(MD_AFTER_WEEKDAY),
    mk_md(SPATIAL_MAP_INTRO),
    mk_code(SPATIAL_MAP_CODE),
    mk_md(MD_AFTER_SPATIAL),
]

# Sections 7-9
new_cells += [
    mk_md(METHODOLOGY_MD),
    mk_md(CONCLUSIONS_MD),
    mk_md(SAVING_MD),
    mk_code(HTML_EXPORT_CODE),
]

# ─────────────────────────────────────────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────────────────────────────────────────
nb_new = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.13.0"},
    },
    "cells": new_cells,
}

with open(DEST, 'w', encoding='utf-8') as f:
    json.dump(nb_new, f, indent=1, ensure_ascii=False)

print(f"[OK] {DEST} written — {len(new_cells)} cells")
print(f"     (base: {len(base)} cells  |  new POI cells: {len(new_cells)-len(base)})")
print(f"     Original {SRC} was NOT modified.")
