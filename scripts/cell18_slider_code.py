import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
import datetime
import time

t0 = time.time()

# ── Visual constants — match static hourly chart (cell 17) exactly ────────────
# Colors: #ff4444 = weekday (red), #4477ff = weekend (blue)  — same as cell 17
# Fill alpha 0.45 — same as cell 17 fill_between alpha
FONT_FAMILY = 'Arial, sans-serif'

COLOR_LINE = {
    'weekday_member': '#ff4444',
    'weekday_casual': '#ff4444',
    'weekend_member': '#4477ff',
    'weekend_casual': '#4477ff',
}
COLOR_FILL = {
    'weekday_member': 'rgba(255, 68,  68, 0.45)',
    'weekday_casual': 'rgba(255, 68,  68, 0.45)',
    'weekend_member': 'rgba( 68,119, 255, 0.45)',
    'weekend_casual': 'rgba( 68,119, 255, 0.45)',
}
SUBPLOT_LABELS = {
    'weekday_member': 'Member — Weekday',
    'weekday_casual': 'Casual — Weekday',
    'weekend_member': 'Member — Weekend + Holiday',
    'weekend_casual': 'Casual — Weekend + Holiday',
}
GROUP_NAMES = ['weekday_member', 'weekday_casual', 'weekend_member', 'weekend_casual']
SUBPLOT_POS = {
    'weekday_member': (1, 1), 'weekday_casual': (1, 2),
    'weekend_member': (2, 1), 'weekend_casual': (2, 2),
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def ensure_group_id(df):
    # Rebuild group_id if it was dropped by cell 17 cleanup
    if 'group_id' not in df.columns:
        if 'day_cat_simple' not in df.columns:
            df = df.copy()
            df['day_cat_simple'] = np.where(
                df['day_category'] == 'weekday', 'weekday', 'weekend'
            )
        df['group_id'] = (
            df['day_cat_simple'].map({'weekday': 0, 'weekend': 2}) +
            df['member_casual'].map({'member': 0, 'casual': 1})
        ).astype(np.int32)
    return df


def compute_hourly_profile(df_subset):
    # Return {group_name: array(24) h/day} for a dataframe subset.
    # Reuses sum_minutes_all_groups (Numba JIT) defined in cell 17.
    if df_subset.empty:
        return {name: np.zeros(24) for name in GROUP_NAMES}
    start_min = (
        df_subset['started_at'].dt.hour * 60 +
        df_subset['started_at'].dt.minute
    ).values.astype(np.int32)
    durations = df_subset['trip_duration'].values.astype(np.float64)
    group_ids = df_subset['group_id'].values.astype(np.int32)
    days_pg = (
        df_subset.groupby('group_id')['ride_date']
        .nunique().reindex(range(4), fill_value=0).values
    )
    totals = sum_minutes_all_groups(start_min, durations, group_ids, 4)
    return {
        name: (totals[g] / days_pg[g] / 60) if days_pg[g] > 0 else np.zeros(24)
        for g, name in enumerate(GROUP_NAMES)
    }


# ── Pre-compute hourly profiles for every month + "All" ──────────────────────
df_work = ensure_group_id(df_clean)

months_sorted = sorted(df_work['started_at'].dt.to_period('M').unique().astype(str))
month_options = ['All'] + months_sorted   # "All" = full-year aggregate

print(f"  Months available : {len(months_sorted)}  "
      f"({months_sorted[0]} -> {months_sorted[-1]})")

profiles = {'All': compute_hourly_profile(df_work)}
for month in months_sorted:
    mask = df_work['started_at'].dt.to_period('M').astype(str) == month
    profiles[month] = compute_hourly_profile(df_work[mask])

# Consistent y-axis ceiling across all months and groups
y_max = max(
    v.max()
    for month_profiles in profiles.values()
    for v in month_profiles.values()
) * 1.12

print(f"  Profiles computed: {len(profiles)}  |  y_max = {y_max:.3f} h/day")


# ── Build Plotly figure ────────────────────────────────────────────────────────
HOURS = list(range(24))
N_OPTS = len(month_options)     # All + 12 months = 13
N_GROUPS = len(GROUP_NAMES)     # 4
N_TRACES = N_OPTS * N_GROUPS * 2  # fill + line per group per option

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=list(SUBPLOT_LABELS.values()),
    shared_xaxes=True,
    shared_yaxes=True,
    vertical_spacing=0.13,
    horizontal_spacing=0.06,
)

trace_idx = 0
month_trace_map = {}   # month key -> [indices of its data traces]

for month in month_options:
    indices = []
    visible = (month == 'All')   # only "All" visible at start

    for g_name in GROUP_NAMES:
        row, col = SUBPLOT_POS[g_name]
        y_data = profiles[month][g_name]

        # Fill area below curve — matches cell 17 fill_between style
        fig.add_trace(go.Scatter(
            x=HOURS, y=y_data,
            mode='none', fill='tozeroy',
            fillcolor=COLOR_FILL[g_name],
            showlegend=False, visible=visible,
            hoverinfo='skip',
        ), row=row, col=col)
        indices.append(trace_idx); trace_idx += 1

        # Curve line on top
        fig.add_trace(go.Scatter(
            x=HOURS, y=y_data,
            mode='lines',
            line=dict(color=COLOR_LINE[g_name], width=2.2),
            showlegend=False, visible=visible,
            hovertemplate='<b>%{x:02d}:00</b>  %{y:.3f} h/day<extra></extra>',
        ), row=row, col=col)
        indices.append(trace_idx); trace_idx += 1

    month_trace_map[month] = indices

# Legend proxy traces — invisible data, appear in legend only
for label, line_col, fill_col in [
    ('Weekday',           '#ff4444', 'rgba(255, 68,  68, 0.45)'),
    ('Weekend / Holiday', '#4477ff', 'rgba( 68,119, 255, 0.45)'),
]:
    fig.add_trace(go.Scatter(
        x=[None], y=[None], mode='lines',
        line=dict(color=line_col, width=2.2),
        fillcolor=fill_col, fill='tozeroy',
        name=label, showlegend=True, visible=True,
    ))


# ── Slider steps ───────────────────────────────────────────────────────────────
# transition.duration = 0 -> each step updates IMMEDIATELY while dragging.
# For monthly data (13 discrete steps) this gives the real-time response
# requested: the chart changes at every step boundary as the slider is dragged.
def fmt_label(month_str):
    if month_str == 'All':
        return 'All months'
    dt = datetime.datetime.strptime(month_str, '%Y-%m')
    return dt.strftime('%b %Y')

slider_steps = []
for month in month_options:
    # Toggle data traces; legend proxies (last 2) remain always visible
    vis = [i in month_trace_map[month] for i in range(N_TRACES)] + [True, True]
    slider_steps.append(dict(
        label=fmt_label(month),
        method='update',
        args=[{'visible': vis}],
    ))


# ── Layout ────────────────────────────────────────────────────────────────────
fig.update_layout(
    title=dict(
        text='Hourly Usage Distribution — Normalized by Number of Days',
        font=dict(family=FONT_FAMILY, size=16, color='#1a1a1a'),
        x=0.5, xanchor='center',
    ),
    height=710,
    plot_bgcolor='white',
    paper_bgcolor='white',
    font=dict(family=FONT_FAMILY, size=11, color='#333333'),
    # Horizontal legend — mirrors cell 17 fig.legend(loc='upper center')
    legend=dict(
        orientation='h',
        x=0.5, xanchor='center',
        y=1.045, yanchor='bottom',
        font=dict(size=12, family=FONT_FAMILY),
        bgcolor='rgba(0,0,0,0)',
        borderwidth=0,
    ),
    # Slider — replaces dropdown; transition.duration=0 gives instant drag-updates
    sliders=[dict(
        active=0,
        currentvalue=dict(
            font=dict(size=12, color='#333333', family=FONT_FAMILY),
            prefix='',
            visible=True,
            xanchor='center',
        ),
        transition=dict(duration=0),
        pad=dict(b=10, t=50),
        len=0.95,
        x=0.025, xanchor='left',
        y=0,     yanchor='top',
        bgcolor='#f8f8f8',
        bordercolor='#cccccc',
        borderwidth=1,
        font=dict(size=9, color='#444444', family=FONT_FAMILY),
        steps=slider_steps,
    )],
    margin=dict(t=110, b=135, l=70, r=35),
)

# Axes — aligned with cell 17 (light grid alpha 0.3, clean hour labels)
tick_h = list(range(0, 24, 2))
for row in [1, 2]:
    for col in [1, 2]:
        fig.update_xaxes(
            title_text='Hour of day' if row == 2 else '',
            title_font=dict(size=11, color='#555555'),
            tickvals=tick_h,
            ticktext=[f'{h:02d}:00' for h in tick_h],
            tickangle=45,
            gridcolor='rgba(0,0,0,0.12)',
            showline=True, linecolor='#dddddd', mirror=False,
            zeroline=False,
            row=row, col=col,
        )
        fig.update_yaxes(
            title_text='Hours per day' if col == 1 else '',
            title_font=dict(size=11, color='#555555'),
            range=[0, y_max],
            gridcolor='rgba(0,0,0,0.12)',
            showline=True, linecolor='#dddddd', mirror=False,
            zeroline=False,
            row=row, col=col,
        )

# Subplot title style: size 12, bold, matches cell 17 subplot titles
for ann in fig.layout.annotations[:4]:
    ann.update(font=dict(size=12, color='#333333', family=FONT_FAMILY))

fig.write_html('../reports/cyclistic_hourly_interactive.html')
fig.show()

print(f"[OK] Saved: ../reports/cyclistic_hourly_interactive.html")
print(f"     Slider: {len(slider_steps)} steps  |  "
      f"Traces: {N_TRACES} data + 2 legend = {N_TRACES + 2}")
print(f"     [{time.time()-t0:.1f}s]")
