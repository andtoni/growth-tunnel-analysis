# Pore Network Analysis Pipeline for Porous Biomaterials

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20308262.svg)](https://doi.org/10.5281/zenodo.20308262)
[![Preprint](https://img.shields.io/badge/Preprint-SSRN-orange)](https://dx.doi.org/10.2139/ssrn.6664677)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![ORCID](https://img.shields.io/badge/ORCID-0000--0002--1601--4103-green)](https://orcid.org/0000-0002-1601-4103)

A Python pipeline for extracting, quantifying and visualising pore networks from micro-CT scans of porous biomaterials. Originally developed for electrospun scaffolds at the **University of Cape Town**, this pipeline is applicable to **any porous material** used in biomedical research — including hydrogels, freeze-dried scaffolds, decellularised tissue, trabecular bone, sintered ceramics, and 3D-printed constructs.

Uses [PoreSpy](https://github.com/PMEAL/porespy) and [OpenPNM](https://github.com/PMEAL/OpenPNM) for SNOW2-based pore network extraction. Statistical outputs are exported in formats compatible with **R, Stata, GraphPad Prism, SPSS, Python and Excel**.

---

## Associated Publication

> **Tonelli, A.** et al. (2025). *In vivo validation of multimodality pore-network modelling to identify angio-permissive scaffold porosity.* Preprint: [https://dx.doi.org/10.2139/ssrn.6664677](https://dx.doi.org/10.2139/ssrn.6664677)

Please cite this paper and the code repository if you use the pipeline (see [CITATION.cff](CITATION.cff)).

---

## Table of Contents

1. [Pipeline Overview](#1-pipeline-overview)
2. [Raw µCT Data — Pre-Processing](#2-raw-µct-data--pre-processing)
3. [Installation](#3-installation)
4. [Directory Setup](#4-directory-setup)
5. [Script 01 — SNOW2 Extraction](#5-script-01--snow2-extraction)
6. [Script 02 — Network Analysis](#6-script-02--network-analysis-and-threshold-sensitivity)
7. [Script 03 — ParaView Visualisation](#7-script-03--paraview-batch-visualisation)
8. [Script 04 — Network Quantification Export](#8-script-04--network-quantification-export)
9. [Script 05 — Universal Data Export](#9-script-05--universal-data-export)
10. [Statistical Analysis Guide](#10-statistical-analysis-guide)
11. [Troubleshooting](#11-troubleshooting)
12. [Dependencies and Licences](#12-dependencies-and-licences)
13. [Contact](#13-contact)

---

## 1. Pipeline Overview

```
Raw µCT projections
       ↓
Reconstruction + Pre-processing (Dragonfly ORS / Fiji/ImageJ)
       ↓  8-bit TIFF stack
01_run_snow2.py               ← run ONCE per sample (~10–60 min)
       ↓  snow2_output.pkl + im_pores.npy + im_fibres.npy
02_run_network_analysis.py    ← run freely, adjust thresholds
       ↓  growthtunnel.vtp | proj_02.vtp | pore_data.csv | throat_data.csv
03_run_paraview_batch.py      ← run via pvpython (no virtual env needed)
       ↓  3840×3840 PNG screenshots + .pvsm state files
04_quantification_export.py   ← topology & density metrics → Excel workbook
       ↓  Pore_Network_Quantification.xlsx
05_pnm_data_export.py         ← raw pore/throat data → universal CSV format
       ↓  PNM_data_long.csv | PNM_summary_statistics.csv | wide/*.csv
R / Stata / SPSS / GraphPad Prism / Python / Excel
```

**Key design:** Script 01 saves its result once. All other scripts reload in seconds. Scripts 04 and 05 are independent — run either or both after Script 02.

---

## 2. Raw µCT Data — Pre-Processing

### 2.1 Supported Material Types

The pipeline accepts any porous material that can be imaged by µCT and binarised:

| Material | Examples |
|---|---|
| Electrospun fibres | PCL, PLGA, PLA scaffolds |
| Freeze-dried hydrogels | Collagen, gelatin, chitosan |
| Decellularised tissue | ECM scaffolds |
| 3D-printed constructs | FDM, SLA porous structures |
| Trabecular bone | Native or scaffold-seeded |
| Sintered ceramics | HA, TCP, bioglass |
| Polymer foams | Melt-derived porous scaffolds |

The only requirement is that the µCT image can be binarised into **pore space (dark)** and **solid phase (bright)**.

### 2.2 Scan Acquisition Parameters

| Parameter | Description | Example |
|---|---|---|
| Voxel size | Physical voxel size (µm) | 0.54 µm |
| Voltage | X-ray tube voltage (kV) | 60 kV |
| Current | X-ray tube current (µA) | 200 µA |
| Exposure | Per-frame exposure (ms) | 500 ms |
| Projections | Total angular projections | 1001 |

> **Note your voxel size carefully** — required in Scripts 01 and 04.

### 2.3 Reconstruction

1. Apply beam hardening correction (20–40% for polymer scaffolds)
2. Apply ring artefact reduction if needed
3. Export as **8-bit TIFF slices**: `slice_0001.tiff`, `slice_0002.tiff`, ...

### 2.4 Pre-Processing in Dragonfly ORS (Recommended)

[Dragonfly ORS](https://theobjects.com/dragonfly/index.html) — free for academic use:

1. **File → Import** TIFF stack → **Filters → Gaussian** (sigma 0.5–1.0)
2. **ROI Tools → Crop** — select Representative Elementary Volume (REV)
3. **Image → Type → 8-bit** → **File → Export → Image Stack**

### 2.5 Pre-Processing in Fiji/ImageJ

1. **File → Import → Image Sequence** → **Gaussian Blur 3D** (sigma 0.5–1.0)
2. Crop to REV → **Image → Type → 8-bit** → **Save As → Image Sequence**

### 2.6 Checklist

- [ ] 8-bit grayscale TIFF, sequential numbering, no gaps
- [ ] **Pore space = dark | Solid phase = bright**
- [ ] No edge artefacts or beam hardening in the REV

> If inverted (pores bright), add `im = ~im` after binarisation in Script 01.

---

## 3. Installation

### 3.1 Install uv

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3.2 Clone and Install

```bash
git clone https://github.com/andtoni/growth-tunnel-analysis
cd growth-tunnel-analysis
uv venv --python 3.12
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 3.3 Verify

```bash
python verify_environment.py
```

### 3.4 Install ParaView (Script 03 only)

Download ParaView 5.13+ from https://www.paraview.org/download/ — Script 03 uses its bundled `pvpython`, no virtual environment needed.

---

## 4. Directory Setup

```
base_data_dir/
└── Sample_01/
    ├── snow2_output.pkl               ← Script 01
    ├── im_pores.npy / im_fibres.npy   ← Script 01
    └── outputs/
        └── pore10um_throat10um/
            ├── pore_data.csv          ← Script 02 → convert for Script 05
            └── throat_data.csv        ← Script 02 → convert for Script 05
Pore_Network_Quantification.xlsx       ← Script 04 output
Pore_Throats_Summary/                  ← Script 05 input/output folder
  poresSample_01.xlsx  throatsSample_01.xlsx
  PNM_data_long.csv    PNM_summary_statistics.csv
  wide/pore_ediameter_wide.csv  ...
```

---

## 5. Script 01 — SNOW2 Extraction

```bash
python 01_run_snow2.py
```

Run once per sample. Settings: `sample_name`, `voxel_size`, `threshold`, `image_path`, `base_data_dir`. Runtime: 10–60 min.

---

## 6. Script 02 — Network Analysis and Threshold Sensitivity

```bash
python 02_run_network_analysis.py
```

Loads saved pkl (seconds), applies size thresholds, extracts the largest connected cluster, exports CSV and VTK outputs. Run freely — each threshold saves to its own subfolder.

Settings: `sample_name`, `pore_threshold` (µm), `throat_threshold` (µm), `base_data_dir`.

> *"Only the largest percolating pore cluster was retained, as isolated clusters do not contribute to transmural migration pathways [Tonelli et al., 2025, doi:10.2139/ssrn.6664677]."*

---

## 7. Script 03 — ParaView Batch Visualisation

**Windows:**
```powershell
& "C:\Program Files\ParaView 5.13.3\bin\pvpython.exe" "03_run_paraview_batch.py"
```

**macOS:**
```bash
/Applications/ParaView-5.13.3.app/Contents/bin/pvpython 03_run_paraview_batch.py
```

Generates 3840×3840 screenshots and `.pvsm` state files for every sample × threshold.

---

## 8. Script 04 — Network Quantification Export

```bash
python 04_quantification_export.py
```

Rebuilds the cleaned network from each pkl (seconds), computes topology and density metrics, and writes a comprehensive Excel workbook. Mean pore/throat diameter is intentionally excluded as a primary metric — it is trivially bounded by the threshold. The metrics below are meaningful independent of threshold choice.

**Settings:** `base_data_dir`, `samples`, `threshold_combinations`, `voxel_size_um`, `excel_filename`.

**Primary metrics:**

| Metric | Unit | Significance |
|---|---|---|
| Porosity | % | Volume-based, threshold-independent |
| Pore density | pores/mm³ | Normalised — comparable across sample sizes |
| Throat density | throats/mm³ | Normalised interconnection measure |
| Connectivity density | mm⁻³ | Euler-based, comparable to bone literature |
| Coordination number | connections/pore | **Key topology metric** |
| Dead-end pore fraction | % | Topologically non-permissive pores |
| Well-connected fraction | % | Pores with ≥3 connections |
| Throat length | µm | Transport/migration distance |
| Throat aspect ratio | L/D | Transport difficulty index |
| Constriction ratio | pore D / throat D | Bottleneck metric |

**Output — `Pore_Network_Quantification.xlsx`** (9 sheets): Primary Metrics Summary, Threshold Sensitivity, Coordination Numbers, Throat Lengths, Throat Aspect Ratios, Constriction Ratios, Full Data Archive, Metric Descriptions.

---

## 9. Script 05 — Universal Data Export

```bash
python 05_pnm_data_export.py
```

Exports raw pore and throat measurements in three universal formats — no software-specific formatting applied.

### 9.1 Prepare Input Files

Convert Script 02 CSV outputs to named xlsx files:

```python
import pandas as pd
pd.read_csv(r"C:\...\pore_data.csv").to_excel(
    r"C:\...\Pore_Throats_Summary\poresSample_01.xlsx", index=False)
pd.read_csv(r"C:\...\throat_data.csv").to_excel(
    r"C:\...\Pore_Throats_Summary\throatsSample_01.xlsx", index=False)
```

Name files as `pores<sample>.xlsx` and `throats<sample>.xlsx`.

### 9.2 Settings

```python
INPUT_DIR  = r"C:\...\Pore_Throats_Summary"
OUTPUT_DIR = r"C:\...\Pore_Throats_Summary"
N_ROWS     = 512
```

### 9.3 Output Files

| File | Format | Compatible with |
|---|---|---|
| `PNM_data_long.csv` | Long: data_type, variable, sample, value | R, Stata, SPSS, Python |
| `PNM_summary_statistics.csv` | mean, SD, SEM, median, IQR, CV | All software |
| `wide/<type>_<var>_wide.csv` | One column per sample | GraphPad Prism, Excel, JMP |
| `PNM_data_README.txt` | Software-specific import guide | Reference |

---

## 10. Statistical Analysis Guide

### R
```r
library(tidyverse)
df <- read_csv("PNM_data_long.csv")
df |> filter(data_type=="pore", variable=="ediameter") |>
  ggplot(aes(x=sample, y=value, fill=sample)) + geom_boxplot() + theme_bw()
aov(value ~ sample, data = df |> filter(data_type=="pore", variable=="ediameter")) |> summary()
```

### Stata
```stata
import delimited "PNM_data_long.csv", clear
keep if data_type == "pore" & variable == "ediameter"
encode sample, gen(group)
oneway value group, tabulate
```

### GraphPad Prism
Open `wide/pore_ediameter_wide.csv` as a Grouped Table (File → Import → From File). Each column = one sample. Use Analyze → One-way ANOVA or Column Statistics. If no graph appeared: click **New → New Graph of Existing Data**, select table, choose Box-and-Whiskers.

### Python
```python
import pandas as pd, pingouin as pg
df = pd.read_csv("PNM_data_long.csv")
pore = df.query("data_type=='pore' and variable=='ediameter'")
pg.anova(data=pore, dv="value", between="sample")
```

---

## 11. Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `FileNotFoundError: snow2_output.pkl` | Script 01 not run | Run `01_run_snow2.py` first |
| `No TIFF files found` | Wrong path/extension | Check `image_path`; use `*.tiff` or `*.tif` |
| Porosity 0% or 100% | Wrong threshold or inverted image | Adjust `threshold`; add `im = ~im` |
| Script 04 finds no data | pkl/npy files missing | Run Scripts 01 and 02 first |
| Script 05 finds no files | Wrong naming | Files must be `pores<sample>.xlsx` |
| `openpyxl` not found | Not installed | `uv pip install openpyxl` |
| `networkx` not found | Optional, not installed | Set `compute_path_length = False` |
| `pvpython` not found | Wrong ParaView path | `Get-Item "C:\Program Files\ParaView*"` |

---

## 12. Dependencies and Licences

Released under the **MIT Licence** (see [LICENSE](LICENSE)).

| Package | Version | Licence | Used by |
|---|---|---|---|
| **PoreSpy** | 2.2.0 | MIT | Scripts 01–02 · [doi:10.21105/joss.01296](https://doi.org/10.21105/joss.01296) |
| **OpenPNM** | 3.3.0 | MIT | Scripts 02–04 · [doi:10.1109/MCSE.2016.49](https://doi.org/10.1109/MCSE.2016.49) |
| NumPy | 1.26.4 | BSD-3 | Scripts 01–04 |
| SciPy | 1.13.1 | BSD-3 | Scripts 01–05 |
| scikit-image | 0.22.0 | BSD-3 | Scripts 01–02 |
| Matplotlib | 3.9.0 | PSF | Scripts 01–02 |
| imageio | 2.34.0 | BSD-2 | Script 02 |
| pandas | 2.2.0 | BSD-3 | Scripts 02, 05 |
| openpyxl | 3.1.2 | MIT | Scripts 04–05 |
| pypardiso | 0.4.6 | MIT | Scripts 01–02 (optional) |
| networkx | ≥3.0 | BSD-3 | Script 04 (optional) |
| **ParaView** | 5.13+ | BSD-3 | Script 03 |

---

## 13. Contact

**Andrea Tonelli** · University of Cape Town
tnland001@myuct.ac.za · ORCID: [0000-0002-1601-4103](https://orcid.org/0000-0002-1601-4103) · [@andtoni](https://github.com/andtoni)

For questions about adapting this pipeline to other porous materials, open a [GitHub issue](https://github.com/andtoni/growth-tunnel-analysis/issues).

---

*Developed at the University of Cape Town, 2025. Originally applied to electrospun scaffold characterisation — designed to be applicable to any porous biomaterial that can be imaged by micro-CT.*
