#!/usr/bin/env python3
"""
Download the raw Divvy trip data used by this project.

The 12 monthly CSV files (Apr 2025 – Mar 2026) are published by Lyft/Divvy as
public ZIP archives. They are too large to keep in the Git repository, so this
script fetches them on demand into ``data/raw/trips/``.

Usage
-----
    python scripts/download_data.py            # download everything that's missing
    python scripts/download_data.py --force    # re-download even if present

After this runs, execute the notebooks in order (01 → 02 → 03 → 04) to rebuild
the processed datasets (``data/processed/df_clean.csv`` etc.).

Note
----
The two auxiliary files are NOT on the Divvy bucket and must be obtained from the
Chicago Data Portal (links printed at the end if they are missing):
    data/raw/Chicago_Zoning_Districts.csv
    data/raw/Divvy_Bicycle_Stations.csv
"""
from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path
from urllib.request import urlopen, Request

# Project root = parent of this script's folder
ROOT      = Path(__file__).resolve().parents[1]
TRIPS_DIR = ROOT / "data" / "raw" / "trips"
RAW_DIR   = ROOT / "data" / "raw"

# Public Divvy bucket. Each month is "<YYYYMM>-divvy-tripdata.zip".
BASE_URL = "https://divvy-tripdata.s3.amazonaws.com"
MONTHS   = [
    "202504", "202505", "202506", "202507", "202508", "202509",
    "202510", "202511", "202512", "202601", "202602", "202603",
]

AUX_FILES = {
    "Chicago_Zoning_Districts.csv":
        "https://data.cityofchicago.org/  (search: 'Zoning Districts' → export CSV)",
    "Divvy_Bicycle_Stations.csv":
        "https://data.cityofchicago.org/  (search: 'Divvy Bicycle Stations' → export CSV)",
}


def download_month(month: str, force: bool = False) -> str:
    """Fetch and unzip one month of trip data. Returns a short status string."""
    out_csv = TRIPS_DIR / f"{month}-divvy-tripdata.csv"
    if out_csv.exists() and not force:
        return f"  = {out_csv.name} already present — skipped"

    url = f"{BASE_URL}/{month}-divvy-tripdata.zip"
    try:
        req = Request(url, headers={"User-Agent": "cyclistic-portfolio/1.0"})
        with urlopen(req, timeout=120) as resp:
            blob = resp.read()
    except Exception as exc:  # network, 404, etc. — report and continue
        return f"  ✗ {month}: download failed ({exc})"

    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            # the archive contains a single CSV (sometimes inside a subfolder)
            csv_names = [n for n in zf.namelist()
                         if n.lower().endswith(".csv") and "__macosx" not in n.lower()]
            if not csv_names:
                return f"  ✗ {month}: no CSV inside the archive"
            with zf.open(csv_names[0]) as fsrc:
                out_csv.write_bytes(fsrc.read())
    except zipfile.BadZipFile:
        return f"  ✗ {month}: downloaded file is not a valid ZIP"

    size_mb = out_csv.stat().st_size / 1e6
    return f"  ✓ {out_csv.name}  ({size_mb:,.0f} MB)"


def main() -> int:
    parser = argparse.ArgumentParser(description="Download raw Divvy trip data.")
    parser.add_argument("--force", action="store_true",
                        help="re-download files that already exist")
    args = parser.parse_args()

    TRIPS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {len(MONTHS)} months of Divvy data → {TRIPS_DIR}\n")

    failures = 0
    for month in MONTHS:
        line = download_month(month, force=args.force)
        print(line)
        if line.lstrip().startswith("✗"):
            failures += 1

    # Remind about the auxiliary city files if absent
    missing_aux = [name for name in AUX_FILES if not (RAW_DIR / name).exists()]
    if missing_aux:
        print("\nAuxiliary files still missing (needed for notebook 02 / 03):")
        for name in missing_aux:
            print(f"  • {name}\n      → {AUX_FILES[name]}")

    print("\nDone." if not failures else f"\nDone with {failures} failed month(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
