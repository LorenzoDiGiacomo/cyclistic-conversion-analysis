# Cyclistic - Bike Sharing - Chicago - Analysis

[![View on Kaggle — Analysis](https://img.shields.io/badge/Kaggle-Analysis_notebook-20BEFF?logo=kaggle&logoColor=white)](https://www.kaggle.com/code/lorenzodigiacomo13/cyclistic-bike-sharing-chicago-analysis)
[![View on Kaggle — Data Cleaning](https://img.shields.io/badge/Kaggle-Data_cleaning_notebook-20BEFF?logo=kaggle&logoColor=white)](https://www.kaggle.com/code/lorenzodigiacomo13/cyclistic-bike-sharing-chicago-data-cleaning)
[![Kaggle Dataset](https://img.shields.io/badge/Kaggle-Dataset-20BEFF?logo=kaggle&logoColor=white)](https://www.kaggle.com/datasets/lorenzodigiacomo13/cyclistic-chicago-clean)

> **Live, fully-executed notebooks (with all charts and output) are on Kaggle** — click the badges above.
> This repository holds the reproducible source.

Casual-to-member conversion strategy for a Chicago bike-share service (Divvy data, **Jun 2025 – May 2026**,
**5.8 million rides**), built to answer one business question:

> *Which casual riders behave most like annual members — and are therefore the most
> realistic targets for a conversion campaign?*

This is a personal data-analytics portfolio project: full pipeline from raw trip
data to a segmentation model and a marketing-ready recommendation.

---

## Key results

- Casual riders are **not one group**. K-Means segmentation surfaces three distinct
  behavioural profiles:
  | Subgroup | Share of casual rides | Similarity to members | Priority |
  |---|---:|---:|---|
  | **E-Bike Riders** | 52.1% | 0.65 | **High** |
  | Commute E-Bike Riders | 17.2% | 0.49 | Medium |
  | Classic Leisure Riders | 30.8% | 0.00 | Low |
- The **E-Bike Riders** subgroup is both the largest *and* the closest to member
  behaviour — short rides, predominantly weekday-adjacent — making it the strongest
  structural conversion target.
- A secondary signal: the **Commute E-Bike Riders** subgroup has 100% commute-window
  rides and ~1 in 4 end outside a docking station, pointing to a possible infrastructure
  lever beyond marketing alone.

Full write-up with charts: [`reports/cyclistic_conversion_strategy.html`](reports/cyclistic_conversion_strategy.html)
(open locally, or view the notebook directly on GitHub).

---

## Repository structure

```
Ciclistic_analisi/
├── notebooks/                  # analysis pipeline, run in order
│   ├── 01_data_cleaning.ipynb              # 12 raw CSVs → df_clean.csv
│   └── 04_conversion_strategy_casual_to_member.ipynb  # segmentation + strategy
├── scripts/                    # helper scripts (incl. data download)
│   └── download_data.py        # fetches the raw Divvy trip data
├── src/                        # reusable helpers (utils, viz)
├── reports/                    # rendered HTML reports + figures (versioned)
│   └── figures/
├── data/                       # NOT versioned — see "Getting the data" below
│   ├── raw/                    # raw Divvy CSVs + Chicago city files
│   ├── interim/                # intermediate datasets
│   └── processed/              # df_clean.csv and aggregates
└── requirements.txt
```

> The `data/` folder is intentionally excluded from Git (the cleaned dataset alone
> is ~1 GB). The structure is preserved with `.gitkeep` files and the data is
> regenerated with the steps below.

---

## Getting the data

The raw Divvy trip files are public. From the project root:

```bash
pip install -r requirements.txt
python scripts/download_data.py        # → data/raw/trips/*.csv
```

Two auxiliary files come from the [Chicago Data Portal](https://data.cityofchicago.org)
and are only needed for notebooks 02–03 (the script prints the exact links if they
are missing):

- `data/raw/Chicago_Zoning_Districts.csv`
- `data/raw/Divvy_Bicycle_Stations.csv`

Then run the notebooks **in order** — `01` produces `data/processed/df_clean.csv`,
which the later notebooks consume.

---

## Running on Kaggle

Each notebook starts with a small **portable bootstrap cell**: it does nothing on a
local machine, and on Kaggle it links the attached dataset so the same `../data`
paths keep working. To reproduce on Kaggle:

1. Upload `df_clean.csv` (and the `interim/` files for notebook 03) as a Kaggle Dataset.
2. Attach it to a new notebook and paste in `04_conversion_strategy_casual_to_member.ipynb`.
3. Run — the bootstrap cell auto-detects Kaggle and wires up the paths.

See [`PUBLISHING.md`](PUBLISHING.md) for the full GitHub + Kaggle publishing walkthrough.

---

## Method (notebook 04)

1. **Feature engineering** — per ride: duration, haversine distance, speed, weekend
   flag, commute-window flag, time-of-day slot, season, e-bike flag.
2. **Segmentation** — MiniBatch K-Means on 8 standardised features; `K=3` chosen via
   inertia elbow + silhouette, calibrated for business interpretability.
3. **Member benchmark** — members clustered the same way to confirm the reference
   point is meaningful, then each casual subgroup scored by Euclidean distance to the
   member profile in standardised space.
4. **Prioritisation** — `combined score = similarity × ride share`, balancing
   behavioural fit against audience size.

The notebook is explicit about its limitations: segmentation is at **ride level**
(no persistent user ID), commute windows are a **proxy** for intent, and similarity
is a **structural** indicator, not a guarantee of conversion.

---

## Tech stack

Python · pandas · NumPy · scikit-learn · matplotlib · seaborn · GeoPandas · `holidays`
· JupyterLab. Full list in [`requirements.txt`](requirements.txt).

---

*Data: [Divvy / Lyft public trip data](https://divvybikes.com/system-data) ·
[Chicago Data Portal](https://data.cityofchicago.org). Used here for educational,
non-commercial portfolio purposes.*
