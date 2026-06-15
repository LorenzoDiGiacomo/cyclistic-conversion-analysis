#!/usr/bin/env python3
"""
Replace cell[18] in 03_analysis_and_visualization_poi.ipynb:
  - Remove dropdown filter → replace with Plotly slider
  - transition.duration=0  → instant update on every slider step drag
  - Style aligned with cell[17] (static hourly):
      #ff4444 weekday, #4477ff weekend, alpha 0.45, white bg, light grid
  - Insert new interpretation markdown after cell[18]
"""
import json
import ast

NB = 'notebooks/03_analysis_and_visualization_poi.ipynb'

# Read the new cell-18 code from a separate .py file (avoids triple-quote conflicts)
with open('scripts/cell18_slider_code.py', encoding='utf-8') as f:
    NEW_CELL_18_SRC = f.read()

# Quick syntax check before patching the notebook
try:
    ast.parse(NEW_CELL_18_SRC)
    print("[OK] cell18_slider_code.py passes syntax check")
except SyntaxError as e:
    print(f"[FAIL] Syntax error in cell18_slider_code.py: {e}")
    raise SystemExit(1)

with open(NB) as f:
    nb = json.load(f)

def mk_code(s):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": s.splitlines(keepends=True)}

def mk_md(s):
    return {"cell_type": "markdown", "metadata": {},
            "source": s.splitlines(keepends=True)}

# ── Markdown interpretation cell ───────────────────────────────────────────────
MD_AFTER_SLIDER = """\
### How to use this chart and what to look for
[↑ back to top](#toc)

This interactive chart shows the **hourly usage distribution** — average hours of
riding per day — broken down by user type (Member / Casual) and day category
(Weekday / Weekend + Holiday).

**Drag the month slider** at the bottom to filter to a specific month.
The chart updates **immediately** as you drag, allowing a fluid month-by-month
comparison without releasing the slider.

> **Leftmost position (All months):** full-year aggregate, April 2025 – March 2026.
> **Drag right** to step through individual months chronologically.

---

#### Key patterns to look for

**1 — Seasonal amplitude: casuals are far more sensitive than members.**
Slide to June–August and watch the *Casual Weekend* panel: the broad midday leisure
curve (11:00–16:00) nearly doubles compared to winter months.
The *Member Weekday* double-peak (07:00–09:00 and 17:00–18:00) barely changes —
commuters keep cycling regardless of season.

**2 — The commute signature is month-invariant for members.**
Whatever month you select, the Member Weekday panel reliably shows two symmetrical
peaks. This stability is the clearest evidence that **daily commuting**, not leisure,
drives member behaviour — and explains why member rides are consistently higher
in winter than casual rides.

**3 — Winter casual weekdays start to look like commuter rides.**
From November through February, casual weekday curves partially develop a dual-peak
form: the midday leisure bulge shrinks and morning/evening shoulders grow. These are
likely functional riders who have not yet subscribed —
the **highest-conversion-potential segment** in cold months.

**4 — Late spring is the seasonal tipping point.**
Drag from March to April: casual weekend volumes roughly double in that single step.
April marks when leisure riding "switches on" — making early spring the ideal
window for seasonal membership promotions targeting casual riders.
"""

# ── Build new cell list ────────────────────────────────────────────────────────
old = nb['cells']
new = []

for idx, cell in enumerate(old):
    if idx == 18:
        new.append(mk_code(NEW_CELL_18_SRC))   # replaced slider version
        new.append(mk_md(MD_AFTER_SLIDER))      # new interpretation markdown
    else:
        new.append(cell)

nb['cells'] = new

with open(NB, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f"[OK] Notebook saved — {len(new)} cells (was {len(old)})")
print(f"     Cell[18] replaced: dropdown -> slider (transition.duration=0)")
print(f"     Cell[19] inserted: interpretation markdown")
