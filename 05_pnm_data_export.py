# =============================================================================
# Script 05 — PNM Pore & Throat Data Export (Universal Format)
# =============================================================================
# Author:      Andrea Tonelli (tnland001@myuct.ac.za)
# ORCID:       https://orcid.org/0000-0002-1601-4103
# Institution: University of Cape Town
# Repository:  https://github.com/andtoni/growth-tunnel-analysis
# Preprint:    https://dx.doi.org/10.2139/ssrn.6664677
# Zenodo:      https://doi.org/10.5281/zenodo.20308262
#
# Description:
#   Reads pore and throat Excel files from INPUT_DIR, takes the first N_ROWS
#   measurements per variable, and exports three universally compatible output
#   formats suitable for any statistical software.
#
# Output files (all saved to OUTPUT_DIR):
#
#   1. PNM_data_long.csv         — LONG FORMAT
#      Columns: data_type | variable | sample | value
#      Use with: R (tidyverse/ggplot2), Stata, SPSS, Python (pandas)
#      Example R:    df <- read.csv("PNM_data_long.csv")
#      Example Stata: import delimited "PNM_data_long.csv"
#
#   2. wide/<type>_<variable>_wide.csv — WIDE FORMAT (one file per variable)
#      Columns: one per sample | Rows: individual measurements
#      Use with: GraphPad Prism (import as Grouped/Column table),
#                Excel, SPSS, JMP
#
#   3. PNM_summary_statistics.csv — SUMMARY STATISTICS
#      Columns: data_type | variable | sample | n | mean | sd | median |
#               min | max | p25 | p75 | sem | cv_pct
#      Use with: any software for table reporting
#
#   4. PNM_data_README.txt        — plain-text guide for all output files
#
# File naming convention for input files:
#   pores<sample>.xlsx    e.g. pores16SR.xlsx
#   throats<sample>.xlsx  e.g. throats16SR.xlsx
#
# Converting Script 02 CSV outputs to input format:
#   import pandas as pd
#   pd.read_csv("pore_data.csv").to_excel("poresSR-Pel16.xlsx", index=False)
#
# Usage:
#   python 05_pnm_data_export.py
#
# Requires:
#   pandas  — already in requirements.txt
#   openpyxl — pip install openpyxl  (for reading xlsx input files)
#   scipy   — already in requirements.txt (for percentile statistics)
# =============================================================================

import os
import re
import glob
import pandas as pd
import numpy as np
from scipy import stats as scipy_stats
from datetime import datetime

# =============================================================================
# USER SETTINGS
# =============================================================================

# Directory containing all pores*.xlsx and throats*.xlsx input files
INPUT_DIR = r"C:\path\to\your\Pore_Throats_Summary"

# Output directory — all CSVs and the README are saved here
# Set to the same as INPUT_DIR to keep everything together,
# or specify a separate folder
OUTPUT_DIR = r"C:\path\to\your\Pore_Throats_Summary"

# Number of measurements to take from the top of each input file
# All samples should have at least this many rows for a balanced comparison
N_ROWS = 512

# Columns to treat as metadata — excluded from measurement outputs
EXCLUDE_COLS = {"group", "weight", "sample", "id", "index"}

# =============================================================================
# DO NOT EDIT BELOW THIS LINE
# =============================================================================

def parse_filename(fname):
    """
    Extract data type and sample name from filename.
    pores16SR.xlsx   → ('pore',   '16SR')
    throatsSR-Pel16.xlsx → ('throat', 'SR-Pel16')
    Returns (None, None) if filename does not match expected pattern.
    """
    base = os.path.splitext(os.path.basename(fname))[0]
    m = re.match(r'^pores?(.+)$', base, re.IGNORECASE)
    if m:
        return 'pore', m.group(1)
    m = re.match(r'^throats?(.+)$', base, re.IGNORECASE)
    if m:
        return 'throat', m.group(1)
    return None, None


def load_file(fpath, n_rows):
    """
    Load an Excel file, coerce data columns to numeric, and return
    the first n_rows rows. Metadata columns are excluded.
    """
    df = pd.read_excel(fpath)
    data_cols = [c for c in df.columns if c.lower() not in EXCLUDE_COLS]
    df = df[data_cols].copy()
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(how='all', inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df.head(n_rows)


def compute_summary(series, sample, variable, data_type):
    """Return a summary statistics dict for one group × variable."""
    s = series.dropna()
    if len(s) == 0:
        return None
    p25, p75 = np.percentile(s, [25, 75])
    return {
        'data_type': data_type,
        'variable':  variable,
        'sample':    sample,
        'n':         int(len(s)),
        'mean':      round(float(s.mean()),   4),
        'sd':        round(float(s.std()),    4),
        'sem':       round(float(scipy_stats.sem(s)), 4),
        'median':    round(float(s.median()), 4),
        'min':       round(float(s.min()),    4),
        'max':       round(float(s.max()),    4),
        'p25':       round(float(p25),        4),
        'p75':       round(float(p75),        4),
        'cv_pct':    round(float(s.std() / s.mean() * 100), 2) if s.mean() != 0 else None,
    }


# =============================================================================
# DISCOVER AND LOAD FILES
# =============================================================================

print("=" * 65)
print("Script 05 — PNM Data Export (Universal Format)")
print("Tonelli A. — University of Cape Town — 2025")
print("=" * 65)
print(f"Input directory  : {INPUT_DIR}")
print(f"Output directory : {OUTPUT_DIR}")
print(f"Rows per sample  : {N_ROWS}")
print()

os.makedirs(OUTPUT_DIR, exist_ok=True)
wide_dir = os.path.join(OUTPUT_DIR, "wide")
os.makedirs(wide_dir, exist_ok=True)

all_xlsx = sorted(glob.glob(os.path.join(INPUT_DIR, "*.xlsx")))
# Exclude any previously generated output files
all_xlsx = [f for f in all_xlsx
            if not os.path.basename(f).startswith("PNM_")]

pore_files   = {}
throat_files = {}

for fpath in all_xlsx:
    dtype, sample = parse_filename(fpath)
    if dtype == 'pore':
        pore_files[sample] = fpath
        print(f"  Pore   [{sample}] : {os.path.basename(fpath)}")
    elif dtype == 'throat':
        throat_files[sample] = fpath
        print(f"  Throat [{sample}] : {os.path.basename(fpath)}")
    else:
        print(f"  Skipped          : {os.path.basename(fpath)}")

if not pore_files and not throat_files:
    raise FileNotFoundError(
        f"No pore or throat files found in:\n  {INPUT_DIR}\n\n"
        "Files must be named:\n"
        "  pores<sample>.xlsx    e.g. pores16SR.xlsx\n"
        "  throats<sample>.xlsx  e.g. throats16SR.xlsx"
    )

# Load all data
pore_data   = {}
throat_data = {}

for sample, fpath in sorted(pore_files.items()):
    pore_data[sample] = load_file(fpath, N_ROWS)
    print(f"  Loaded pore [{sample}] : "
          f"{len(pore_data[sample])} rows | "
          f"cols: {pore_data[sample].columns.tolist()}")

for sample, fpath in sorted(throat_files.items()):
    throat_data[sample] = load_file(fpath, N_ROWS)
    print(f"  Loaded throat [{sample}] : "
          f"{len(throat_data[sample])} rows | "
          f"cols: {throat_data[sample].columns.tolist()}")

# Collect unique variable names per type
pore_vars   = []
throat_vars = []
for df in pore_data.values():
    for c in df.columns:
        if c not in pore_vars:
            pore_vars.append(c)
for df in throat_data.values():
    for c in df.columns:
        if c not in throat_vars:
            throat_vars.append(c)

pore_samples   = sorted(pore_data.keys())
throat_samples = sorted(throat_data.keys())

print()
print(f"Pore variables   : {pore_vars}")
print(f"Throat variables : {throat_vars}")
print(f"Pore samples     : {pore_samples}")
print(f"Throat samples   : {throat_samples}")

# =============================================================================
# OUTPUT 1 — LONG FORMAT CSV
# Columns: data_type | variable | sample | value
# Compatible with: R, Stata, SPSS, Python pandas, JMP
# =============================================================================

print("\nBuilding long-format CSV...")

long_rows = []

for sample, df in sorted(pore_data.items()):
    for var in pore_vars:
        if var in df.columns:
            for val in df[var].dropna():
                long_rows.append({
                    'data_type': 'pore',
                    'variable':  var,
                    'sample':    sample,
                    'value':     round(float(val), 6),
                })

for sample, df in sorted(throat_data.items()):
    for var in throat_vars:
        if var in df.columns:
            for val in df[var].dropna():
                long_rows.append({
                    'data_type': 'throat',
                    'variable':  var,
                    'sample':    sample,
                    'value':     round(float(val), 6),
                })

df_long = pd.DataFrame(long_rows,
                        columns=['data_type', 'variable', 'sample', 'value'])
long_path = os.path.join(OUTPUT_DIR, "PNM_data_long.csv")
df_long.to_csv(long_path, index=False)
print(f"  Saved: PNM_data_long.csv  ({len(df_long):,} rows)")

# =============================================================================
# OUTPUT 2 — WIDE FORMAT CSVs (one per variable)
# Columns: one per sample | Rows: individual measurements
# Compatible with: GraphPad Prism (Grouped/Column table), Excel, SPSS, JMP
# =============================================================================

print("\nBuilding wide-format CSVs...")

wide_files = []

def build_wide(variables, samples, data_dict, dtype_label):
    for var in variables:
        cols = {}
        for sample in samples:
            df = data_dict.get(sample)
            if df is not None and var in df.columns:
                series = df[var].dropna().reset_index(drop=True)
                cols[sample] = series
        if not cols:
            continue
        df_wide = pd.DataFrame(cols)
        fname   = f"{dtype_label}_{var}_wide.csv"
        fpath   = os.path.join(wide_dir, fname)
        df_wide.to_csv(fpath, index=False)
        wide_files.append(fname)
        print(f"  Saved: wide/{fname}  "
              f"({len(df_wide)} rows × {len(df_wide.columns)} samples)")

build_wide(pore_vars,   pore_samples,   pore_data,   "pore")
build_wide(throat_vars, throat_samples, throat_data, "throat")

# =============================================================================
# OUTPUT 3 — SUMMARY STATISTICS CSV
# Columns: data_type | variable | sample | n | mean | sd | sem |
#           median | min | max | p25 | p75 | cv_pct
# Compatible with: all statistical software for table reporting
# =============================================================================

print("\nBuilding summary statistics CSV...")

summary_rows = []

for sample, df in sorted(pore_data.items()):
    for var in pore_vars:
        if var in df.columns:
            row = compute_summary(df[var], sample, var, 'pore')
            if row:
                summary_rows.append(row)

for sample, df in sorted(throat_data.items()):
    for var in throat_vars:
        if var in df.columns:
            row = compute_summary(df[var], sample, var, 'throat')
            if row:
                summary_rows.append(row)

df_summary = pd.DataFrame(summary_rows)
summary_path = os.path.join(OUTPUT_DIR, "PNM_summary_statistics.csv")
df_summary.to_csv(summary_path, index=False)
print(f"  Saved: PNM_summary_statistics.csv  ({len(df_summary)} rows)")

# =============================================================================
# OUTPUT 4 — README TEXT FILE
# Plain-text import guide for all output files
# =============================================================================

readme_text = f"""PNM Data Export — Import Guide
================================================================================
Author      : Andrea Tonelli — University of Cape Town
ORCID       : https://orcid.org/0000-0002-1601-4103
Repository  : https://github.com/andtoni/growth-tunnel-analysis
Zenodo DOI  : https://doi.org/10.5281/zenodo.20308262
Preprint    : https://dx.doi.org/10.2139/ssrn.6664677
Generated   : {datetime.now().strftime("%Y-%m-%d %H:%M")}
Rows/sample : {N_ROWS}

================================================================================
FILES IN THIS EXPORT
================================================================================

1. PNM_data_long.csv               ← LONG FORMAT (recommended for R / Stata)
   Columns : data_type | variable | sample | value
   Rows    : {len(df_long):,} (all samples × variables × measurements combined)
   Use for : ANOVA, mixed models, ggplot2, any long-format workflow

2. wide/<type>_<variable>_wide.csv ← WIDE FORMAT (one file per variable)
   Columns : one column per sample
   Rows    : individual measurements (up to {N_ROWS})
   Use for : GraphPad Prism Grouped/Column table, JMP, Excel
   Files   :
{chr(10).join(f"     wide/{f}" for f in wide_files)}

3. PNM_summary_statistics.csv      ← SUMMARY STATISTICS
   Columns : data_type | variable | sample | n | mean | sd | sem |
             median | min | max | p25 | p75 | cv_pct
   Use for : reporting tables, quick comparison across groups

================================================================================
HOW TO IMPORT — SOFTWARE-SPECIFIC INSTRUCTIONS
================================================================================

── R (tidyverse) ─────────────────────────────────────────────────────────────

  # Long format — best for full analysis
  library(tidyverse)
  df <- read_csv("PNM_data_long.csv")

  # Filter by type and variable
  pore_diam <- df |> filter(data_type == "pore", variable == "ediameter")

  # Box plot
  ggplot(pore_diam, aes(x = sample, y = value, fill = sample)) +
    geom_boxplot() + labs(y = "Pore diameter (µm)") + theme_bw()

  # One-way ANOVA
  aov(value ~ sample, data = pore_diam) |> summary()

  # Kruskal-Wallis (non-parametric)
  kruskal.test(value ~ sample, data = pore_diam)

── Stata ──────────────────────────────────────────────────────────────────────

  import delimited "PNM_data_long.csv", clear
  keep if data_type == "pore" & variable == "ediameter"
  encode sample, gen(group)
  oneway value group, tabulate
  kwallis value, by(group)

── GraphPad Prism ─────────────────────────────────────────────────────────────

  Option A (wide format — recommended):
    New → Grouped Table → File → Import → From File
    Select wide/pore_ediameter_wide.csv
    Each column = one sample, each row = one measurement

  Option B (from summary statistics):
    New → Grouped Table → enter mean, SD, n from PNM_summary_statistics.csv

── SPSS ───────────────────────────────────────────────────────────────────────

  File → Import Data → CSV
  Select PNM_data_long.csv
  Analyze → Compare Means → One-Way ANOVA
  Factor: sample | Dependent: value

── Python (pandas / pingouin) ────────────────────────────────────────────────

  import pandas as pd
  import pingouin as pg

  df = pd.read_csv("PNM_data_long.csv")
  pore = df.query("data_type == 'pore' and variable == 'ediameter'")

  # Descriptive statistics
  pore.groupby("sample")["value"].describe()

  # One-way ANOVA
  pg.anova(data=pore, dv="value", between="sample")

  # Kruskal-Wallis
  pg.kruskal(data=pore, dv="value", between="sample")

── Excel ──────────────────────────────────────────────────────────────────────

  Open any wide/pore_*_wide.csv directly in Excel.
  Each column is one sample — create box plots using Insert → Chart.

================================================================================
VARIABLE DESCRIPTIONS
================================================================================

Pore variables
  ediameter  — equivalent sphere diameter (µm) — diameter of sphere with same volume
  idiameter  — inscribed diameter (µm) — largest sphere fitting inside the pore
  volume     — pore volume (µm³)

Throat variables (if present)
  diameter   — throat inscribed diameter (µm)
  length     — throat centre-to-centre length (µm)

Note: For topology metrics (coordination number, connectivity density, etc.)
see the output of Script 04: Pore_Network_Quantification.xlsx

================================================================================
"""

readme_path = os.path.join(OUTPUT_DIR, "PNM_data_README.txt")
with open(readme_path, 'w', encoding='utf-8') as f:
    f.write(readme_text)
print(f"  Saved: PNM_data_README.txt")

# =============================================================================
# SUMMARY
# =============================================================================

print()
print("=" * 65)
print("COMPLETE")
print("=" * 65)
print(f"Output directory  : {OUTPUT_DIR}")
print()
print("  PNM_data_long.csv           — long format (R, Stata, SPSS, Python)")
print("  PNM_summary_statistics.csv  — summary stats table")
print("  PNM_data_README.txt         — software-specific import guide")
for f in wide_files:
    print(f"  wide/{f:<40} — wide format (Prism, Excel, JMP)")
print()
print("For topology metrics see Script 04: Pore_Network_Quantification.xlsx")
print("=" * 65)
