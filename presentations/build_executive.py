"""Executive deck (9 slides) — white background, strict group color assignment."""
from deck_common import *
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.chart.data import CategoryChartData
import os

prs   = new_deck("Cyclistic — Casual-to-Member Conversion (Executive)")
TOTAL = 9
LX, RW = Inches(0.6), Inches(12.13)


def title_block(slide, kick, kick_num, kick_color, title_text, sub=None, tsize=30):
    kicker(slide, LX, Inches(0.55), kick, kick_color, kick_num)
    text(slide, LX, Inches(0.92), RW, Inches(1.0),
         [[(title_text, {'size': tsize, 'color': INK, 'bold': True, 'font': HEAD})]],
         anchor=MSO_ANCHOR.TOP)
    if sub:
        text(slide, LX, Inches(1.78), Inches(11.2), Inches(0.5),
             [[(sub, {'size': 14, 'color': MUTED})]])


# ── 1 · Title ────────────────────────────────────────────────────────────────
s = blank(prs); bg(s, WHITE)
rect(s, LX, Inches(2.35), Inches(0.55), Inches(0.07), fill=CASUAL)
text(s, LX, Inches(2.55), Inches(12.5), Inches(2.1), [
    [("Turning ", {'size': 44, 'color': INK, 'bold': True, 'font': HEAD}),
     ("casual riders", {'size': 44, 'color': CASUAL, 'bold': True, 'font': HEAD})],
    [("into ", {'size': 44, 'color': INK, 'bold': True, 'font': HEAD}),
     ("annual members", {'size': 44, 'color': MEMBER, 'bold': True, 'font': HEAD})],
], line_spacing=1.08)
text(s, LX, Inches(4.75), Inches(11.5), Inches(0.5),
     [[("A behavioural segmentation · who to convert, and how",
        {'size': 16, 'color': MUTED})]])
text(s, LX, Inches(5.55), Inches(11.5), Inches(0.35),
     [[("Chicago bike-share  ·  5.84 M rides  ·  Jun 2025 – May 2026  ·  Executive summary",
        {'size': 11, 'color': MUTED, 'font': HEAD, 'spacing': 1})]])
chip(s, LX, Inches(6.38), CASUAL)
text(s, Inches(0.92), Inches(6.31), Inches(2.2), Inches(0.35),
     [[("Casual riders", {'size': 12, 'color': CASUAL})]], anchor=MSO_ANCHOR.MIDDLE)
chip(s, Inches(2.6), Inches(6.38), MEMBER)
text(s, Inches(2.92), Inches(6.31), Inches(2.8), Inches(0.35),
     [[("Annual members", {'size': 12, 'color': MEMBER})]], anchor=MSO_ANCHOR.MIDDLE)

# ── 2 · Business question ─────────────────────────────────────────────────────
s = blank(prs); bg(s, WHITE)
title_block(s, "The question", "01", CASUAL,
            "Which casual riders are worth converting?")
text(s, LX, Inches(1.95), Inches(11.7), Inches(0.85),
     [[("Cyclistic has two user types — ", {'size': 15.5, 'color': INK}),
       ("casual riders", {'size': 15.5, 'color': CASUAL, 'bold': True}),
       (" (single / day pass) and ", {'size': 15.5, 'color': INK}),
       ("annual members", {'size': 15.5, 'color': MEMBER, 'bold': True}),
       (". Converting the right casual riders is the cheapest growth lever.",
        {'size': 15.5, 'color': INK})]], line_spacing=1.2)
qs = [("01", "Do casual riders behave differently from members?"),
      ("02", "Are casual riders one group — or several distinct profiles?"),
      ("03", "Which profiles look most like members, and are big enough to target?")]
y = 3.1
for num, q in qs:
    rect(s, LX, Inches(y), Inches(0.07), Inches(0.78), fill=CASUAL)
    text(s, Inches(0.9), Inches(y), Inches(1.1), Inches(0.78),
         [[(num, {'size': 22, 'color': CASUAL, 'bold': True, 'font': HEAD})]],
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, Inches(1.95), Inches(y), Inches(10.3), Inches(0.78),
         [[(q, {'size': 16, 'color': INK})]], anchor=MSO_ANCHOR.MIDDLE)
    rect(s, Inches(1.95), Inches(y + 0.82), Inches(10.3), Pt(0.75), fill=HAIRLINE)
    y += 1.0
footer(s, 2, TOTAL)

# ── 3 · Headline finding ──────────────────────────────────────────────────────
s = blank(prs); bg(s, WHITE)
title_block(s, "The finding", "02", CASUAL,
            "Casual riders are not one audience")
text(s, LX, Inches(2.0), Inches(11.8), Inches(0.5),
     [[("Of every ride taken, ", {'size': 15.5, 'color': INK}),
       ("36% are casual", {'size': 15.5, 'color': CASUAL, 'bold': True}),
       (" — 2.09 M rides in play for conversion.", {'size': 15.5, 'color': INK})]])
hsplit_bar(s, LX, Inches(2.65), RW, Inches(0.78),
           [(64.1, MEMBER, "Members  64.1%", WHITE),
            (35.9, CASUAL, "Casual  35.9%", WHITE)])
text(s, LX, Inches(3.9), Inches(11.8), Inches(0.5),
     [[("Inside that casual third sit ", {'size': 15.5, 'color': INK}),
       ("three behavioural profiles", {'size': 15.5, 'color': INK, 'bold': True}),
       (" — differing in ride length, timing, and how closely they resemble members:",
        {'size': 15.5, 'color': INK})]])
rows = [("E-Bike Riders",           "Short, purposeful, weekday-concentrated — most member-like"),
        ("Commute E-Bike Riders",    "Rush-hour trips, often ending outside a dock"),
        ("Classic Leisure Riders",   "Long weekend rides — furthest from member behaviour")]
y = 4.65
for name, desc in rows:
    chip(s, LX, Inches(y + 0.07), CASUAL, size=0.22)
    text(s, Inches(1.0), Inches(y), Inches(4.8), Inches(0.5),
         [[(name, {'size': 15.5, 'color': CASUAL, 'bold': True})]], anchor=MSO_ANCHOR.MIDDLE)
    text(s, Inches(5.6), Inches(y), Inches(7.1), Inches(0.5),
         [[(desc, {'size': 14, 'color': MUTED})]], anchor=MSO_ANCHOR.MIDDLE)
    y += 0.65
footer(s, 3, TOTAL)

# ── 4 · Three segments ───────────────────────────────────────────────────────
s = blank(prs); bg(s, WHITE)
title_block(s, "The segments", "03", CASUAL,
            "Three profiles, ranked by member similarity")
cards = [
    ("E-Bike Riders",        "52.1%", "0.65", "HIGH",
     "Short, purposeful trips on weekdays. Already ride like members."),
    ("Commute E-Bike Riders","17.2%", "0.49", "MEDIUM",
     "100% rush-hour rides; ~1 in 4 ends outside a dock. Infrastructure angle."),
    ("Classic Leisure Riders","30.8%", "0.00", "LOW",
     "Longer recreational rides, weekend-skewed. A different product fits better."),
]
cw, gap, x = 3.95, 0.14, 0.6
for name, share, sim, pri, desc in cards:
    rect(s, Inches(x), Inches(2.2), Inches(cw), Inches(4.35),
         fill=None, line=HAIRLINE, line_w=0.75, rounded=True, radius=0.05)
    rect(s, Inches(x), Inches(2.2), Inches(cw), Inches(0.1), fill=CASUAL)
    text(s, Inches(x + 0.3), Inches(2.5), Inches(cw - 0.5), Inches(0.75),
         [[(name, {'size': 17, 'color': INK, 'bold': True, 'font': HEAD})]], line_spacing=1.0)
    rect(s, Inches(x + 0.3), Inches(3.3), Inches(1.65), Inches(0.4),
         fill=CASUAL, rounded=True, radius=0.5)
    text(s, Inches(x + 0.3), Inches(3.3), Inches(1.65), Inches(0.4),
         [[(pri + " PRIORITY", {'size': 10, 'color': WHITE, 'bold': True,
                                'font': HEAD, 'spacing': 1})]],
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, Inches(x + 0.3), Inches(3.95), Inches(1.7), Inches(0.95),
         [[(share, {'size': 26, 'color': CASUAL, 'bold': True, 'font': HEAD})],
          [("of casual rides", {'size': 11, 'color': MUTED})]])
    text(s, Inches(x + 2.2), Inches(3.95), Inches(1.6), Inches(0.95),
         [[(sim, {'size': 26, 'color': MEMBER, 'bold': True, 'font': HEAD})],
          [("member similarity", {'size': 11, 'color': MUTED})]])
    text(s, Inches(x + 0.3), Inches(5.05), Inches(cw - 0.55), Inches(1.25),
         [[(desc, {'size': 13, 'color': INK})]], line_spacing=1.15)
    x += cw + gap
text(s, LX, Inches(6.65), RW, Inches(0.3),
     [[("Member similarity: 1.00 = most member-like. Shown in blue because it measures distance to the member profile.",
        {'size': 10, 'color': MUTED, 'italic': True})]])
footer(s, 4, TOTAL)

# ── 5 · Priority ─────────────────────────────────────────────────────────────
s = blank(prs); bg(s, WHITE)
title_block(s, "Where to focus", "04", CASUAL,
            "One segment leads on both size and fit")
text(s, LX, Inches(1.95), Inches(11.8), Inches(0.55),
     [[("Priority = member similarity × share of casual rides. ",
        {'size': 15, 'color': INK}),
       ("E-Bike Riders win on both dimensions.", {'size': 15, 'color': INK, 'bold': True})]],
     line_spacing=1.2)
vbars_custom(s, Inches(0.7), Inches(3.0), Inches(7.2), Inches(2.95),
             [("E-Bike\nRiders",         0.339, CASUAL),
              ("Commute\nE-Bike Riders",  0.084, CASUAL),
              ("Classic\nLeisure Riders", 0.0,   CASUAL)],
             maxval=0.40, fmt=lambda v: f"{v:.2f}", val_size=16)
# Callout: amber left accent bar
rect(s, Inches(8.35), Inches(2.85), Inches(0.08), Inches(3.55), fill=CASUAL)
text(s, Inches(8.6), Inches(2.95), Inches(4.5), Inches(0.38),
     [[("THE TARGET", {'size': 11, 'color': CASUAL, 'bold': True, 'font': HEAD, 'spacing': 2})]])
text(s, Inches(8.6), Inches(3.38), Inches(4.5), Inches(0.75),
     [[("E-Bike Riders", {'size': 26, 'color': INK, 'bold': True, 'font': HEAD})]])
text(s, Inches(8.6), Inches(4.2), Inches(4.45), Inches(2.1),
     [[("Largest casual segment ", {'size': 14, 'color': INK}),
       ("(52%)", {'size': 14, 'color': CASUAL, 'bold': True}),
       (" and closest to member behaviour ", {'size': 14, 'color': INK}),
       ("(0.65 similarity)", {'size': 14, 'color': MEMBER, 'bold': True}),
       (". Size and fit point the same way — a rare, clean targeting call.",
        {'size': 14, 'color': INK})]], line_spacing=1.25)
text(s, LX, Inches(6.78), RW, Inches(0.3),
     [[("Priority score = member similarity × share of casual rides.",
        {'size': 10, 'color': MUTED, 'italic': True})]])
footer(s, 5, TOTAL)

# ── 6 · Recommendations ──────────────────────────────────────────────────────
s = blank(prs); bg(s, WHITE)
title_block(s, "Recommendations", "05", CASUAL,
            "Four moves, matched to behaviour")
recs = [
    (CASUAL, "01", "Lead with E-Bike Riders",
     "Push the annual membership to this segment first. Message the commute-cost saving "
     "vs. pay-per-ride on short weekday e-bike trips."),
    (CASUAL, "02", "Sell leisure riders a different product",
     "Don't pitch annual membership to Classic Leisure Riders. Offer a weekend or seasonal "
     "pass — it matches their long, recreational weekend rides."),
    (CASUAL, "03", "Test the infrastructure lever",
     "~25% of PM commute e-bike rides end outside docks. Pilot added docking in the "
     "residential areas where they end — it may remove a real conversion barrier."),
    (MUTED,  "04", "Prove it before scaling",
     "Similarity is a structural signal, not a guarantee. Run a controlled A/B campaign "
     "on E-Bike Riders and measure real conversion before committing full budget."),
]
y = 2.1
for c, num, head, body in recs:
    rect(s, LX, Inches(y), Inches(0.08), Inches(1.0), fill=c)
    text(s, Inches(0.9), Inches(y + 0.12), Inches(0.95), Inches(0.78),
         [[(num, {'size': 22, 'color': c, 'bold': True, 'font': HEAD})]],
         anchor=MSO_ANCHOR.MIDDLE)
    text(s, Inches(1.95), Inches(y + 0.12), Inches(10.7), Inches(0.38),
         [[(head, {'size': 16, 'color': INK, 'bold': True})]])
    text(s, Inches(1.95), Inches(y + 0.5), Inches(10.7), Inches(0.5),
         [[(body, {'size': 12.5, 'color': MUTED})]], line_spacing=1.1)
    rect(s, Inches(1.95), Inches(y + 1.02), Inches(10.7), Pt(0.5), fill=HAIRLINE)
    y += 1.14
footer(s, 6, TOTAL)

# ── 7 · Action map ───────────────────────────────────────────────────────────
s = blank(prs); bg(s, WHITE)
title_block(s, "Action map", "06", CASUAL,
            "The right offer for each segment")
colx = [0.6,  3.7,  6.55, 9.95]
colw = [3.0,  2.75, 3.3,  2.78]
ytab = 2.3
for j, h in enumerate(["Segment", "Offer", "Channel signal", "Expectation"]):
    text(s, Inches(colx[j]), Inches(ytab), Inches(colw[j]), Inches(0.35),
         [[(h.upper(), {'size': 11, 'color': MUTED, 'bold': True,
                        'font': HEAD, 'spacing': 1})]])
rect(s, LX, Inches(ytab + 0.42), RW, Pt(1.2), fill=HAIRLINE)
rowdata = [
    ("E-Bike Riders",         "Annual membership",        "Short weekday e-bike trips",     "Lead target — scale after test"),
    ("Commute E-Bike Riders", "Membership + docking pilot","Rush-hour, free-floating ends",  "Watch — infra may unlock"),
    ("Classic Leisure Riders","Weekend / seasonal pass",   "Long weekend recreational rides","Don't push annual"),
]
y = ytab + 0.62
for cells in rowdata:
    chip(s, Inches(colx[0] + 0.18), Inches(y + 0.47), CASUAL, size=0.18)
    text(s, Inches(colx[0] + 0.5), Inches(y), Inches(colw[0] - 0.5), Inches(1.12),
         [[(cells[0], {'size': 14, 'color': INK, 'bold': True})]], anchor=MSO_ANCHOR.MIDDLE)
    for j in range(1, 4):
        text(s, Inches(colx[j]), Inches(y), Inches(colw[j] - 0.15), Inches(1.12),
             [[(cells[j], {'size': 12.5, 'color': INK if j == 1 else MUTED})]],
             anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.1)
    rect(s, LX, Inches(y + 1.14), RW, Pt(0.5), fill=HAIRLINE)
    y += 1.28
footer(s, 7, TOTAL)

# ── 8 · Limitations ──────────────────────────────────────────────────────────
s = blank(prs); bg(s, WHITE)
title_block(s, "Read with care", "07", CASUAL,
            "What this analysis can and cannot say")
# Left: limitations
text(s, LX, Inches(2.05), Inches(6.0), Inches(0.38),
     [[("LIMITATIONS", {'size': 11, 'color': CASUAL, 'bold': True, 'font': HEAD, 'spacing': 2})]])
lims = ["Ride-level, not person-level — no user IDs; segments describe behaviour, not individuals.",
        "Similarity is structural, not a conversion guarantee — price and habit aren't in this data.",
        "Volume counts rides — frequent riders are over-represented in segment sizes.",
        "Segments are soft regions, not sharp groups; 'commute' is a proxy for intent."]
y = 2.58
for lim in lims:
    chip(s, LX, Inches(y + 0.04), CASUAL, size=0.14)
    text(s, Inches(0.92), Inches(y), Inches(5.8), Inches(0.55),
         [[(lim, {'size': 13, 'color': INK})]], line_spacing=1.12)
    y += 0.88
# Right: what's needed next (hairline-bordered box)
rect(s, Inches(7.0), Inches(2.05), Inches(5.73), Inches(4.45),
     fill=None, line=HAIRLINE, line_w=1, rounded=True, radius=0.04)
text(s, Inches(7.35), Inches(2.35), Inches(5.1), Inches(0.38),
     [[("TO SHARPEN THE NEXT ROUND", {'size': 11, 'color': MEMBER, 'bold': True,
                                      'font': HEAD, 'spacing': 1})]])
nexts = [("User IDs",          "Segment by person, not by ride"),
         ("Survey data",       "Validate intent behind the behaviour"),
         ("Conversion history","Calibrate similarity against real outcomes")]
yy = 3.05
for h, d in nexts:
    chip(s, Inches(7.35), Inches(yy + 0.06), MEMBER, size=0.16)
    text(s, Inches(7.67), Inches(yy - 0.02), Inches(4.8), Inches(0.4),
         [[(h, {'size': 16, 'color': INK, 'bold': True})]])
    text(s, Inches(7.67), Inches(yy + 0.35), Inches(4.8), Inches(0.4),
         [[(d, {'size': 13, 'color': MUTED})]])
    yy += 1.05
footer(s, 8, TOTAL)

# ── 9 · Closing ───────────────────────────────────────────────────────────────
s = blank(prs); bg(s, WHITE)
rect(s, LX, Inches(2.35), Inches(0.55), Inches(0.07), fill=CASUAL)
text(s, LX, Inches(2.55), Inches(12), Inches(0.5),
     [[("THE DECISION", {'size': 14, 'color': CASUAL, 'bold': True, 'font': HEAD, 'spacing': 2})]])
text(s, LX, Inches(3.1), Inches(12), Inches(2.1), [
    [("Run a controlled membership campaign",
      {'size': 34, 'color': INK, 'bold': True, 'font': HEAD})],
    [("on ", {'size': 34, 'color': INK, 'bold': True, 'font': HEAD}),
     ("E-Bike Riders", {'size': 34, 'color': CASUAL, 'bold': True, 'font': HEAD}),
     (" — then scale on results.", {'size': 34, 'color': INK, 'bold': True, 'font': HEAD})],
], line_spacing=1.1)
text(s, LX, Inches(5.35), Inches(11.5), Inches(0.85),
     [[("Largest, most member-like casual segment. Pair the test with a weekend-pass offer "
        "for ", {'size': 15, 'color': MUTED}),
       ("Classic Leisure Riders", {'size': 15, 'color': CASUAL}),
       (" and a docking pilot for ", {'size': 15, 'color': MUTED}),
       ("Commute E-Bike Riders", {'size': 15, 'color': CASUAL}),
       (".", {'size': 15, 'color': MUTED})]],
     line_spacing=1.3)
chip(s, LX, Inches(6.42), CASUAL)
text(s, Inches(0.92), Inches(6.35), Inches(2.2), Inches(0.35),
     [[("Casual riders", {'size': 12, 'color': CASUAL})]], anchor=MSO_ANCHOR.MIDDLE)
chip(s, Inches(2.6), Inches(6.42), MEMBER)
text(s, Inches(2.92), Inches(6.35), Inches(2.8), Inches(0.35),
     [[("Annual members", {'size': 12, 'color': MEMBER})]], anchor=MSO_ANCHOR.MIDDLE)
text(s, Inches(8.0), Inches(6.82), Inches(5.1), Inches(0.35),
     [[("Cyclistic Analytics  ·  Divvy public data  ·  Jun 2025 – May 2026",
        {'size': 10, 'color': MUTED, 'font': HEAD, 'spacing': 1})]],
     align=PP_ALIGN.RIGHT)

out = os.path.join(os.path.dirname(__file__), "Cyclistic_Conversion_Executive.pptx")
prs.save(out)
print("Saved:", out, "·", TOTAL, "slides")
