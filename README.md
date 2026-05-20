# Pore Network Analysis Pipeline for Electrospun Scaffolds

[![Preprint](https://img.shields.io/badge/Preprint-SSRN-orange)](https://dx.doi.org/10.2139/ssrn.6664677)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![ORCID](https://img.shields.io/badge/ORCID-0000--0002--1601--4103-green)](https://orcid.org/0000-0002-1601-4103)

A Python pipeline for extracting and quantifying pore networks from micro-CT scans of electrospun scaffolds, developed at the **University of Cape Town**. Uses [PoreSpy](https://github.com/PMEAL/porespy) and [OpenPNM](https://github.com/PMEAL/OpenPNM) for SNOW2-based network extraction and analysis. Outputs are compatible with GraphPad Prism (statistics) and ParaView (3D visualisation).

---

## Associated Publication

> **Tonelli, A.** et al. (2025). *In vivo validation of multimodality pore-network modelling to identify angio-permissive scaffold porosity.* Preprint available at SSRN: [https://dx.doi.org/10.2139/ssrn.6664677](https://dx.doi.org/10.2139/ssrn.6664677)

If you use this pipeline in your research, please cite the above paper and the code repository (see [CITATION.cff](CITATION.cff) and the **Cite this repository** button on GitHub).

---

## Table of Contents

1. [Pipeline Overview](#1-pipeline-overview)
2. [Raw µCT Data — Pre-Processing](#2-raw-µct-data--pre-processing)
3. [Installation](#3-installation)
4. [Directory Setup](#4-directory-setup)
5. [Script 01 — SNOW2 Extraction](#5-script-01--snow2-extraction)
6. [Script 02 — Network Analysis](#6-script-02--network-analysis-and-threshold-sensitivity)
7. [Script 03 — ParaView Visualisation](#7-script-03--paraview-batch-visualisation)
8. [Outputs and GraphPad Prism](#8-outputs-and-graphpad-prism)
9. [Troubleshooting](#9-troubleshooting)
10. [Dependencies and Licences](#10-dependencies-and-licences)
11. [Contact](#11-contact)

---

## 1. Pipeline Overview

```
Raw µCT projections
       ↓
Reconstruction + Pre-processing
(Dragonfly ORS / Fiji/ImageJ)
       ↓  8-bit TIFF stack
01_run_snow2.py            ← run ONCE per sample (~10–60 min)
       ↓  snow2_output.pkl + im_pores.npy + im_fibres.npy
02_run_network_analysis.py ← run freely, adjust thresholds
       ↓  growthtunnel.vtp | proj_02.vtp | image.tif | image2.tif | *.csv
03_run_paraview_batch.py   ← run via pvpython (no virtual env needed)
       ↓  3840×3840 PNG screenshots + .pvsm state files
GraphPad Prism             ← import pore_data.csv / throat_data.csv
```

**Key design:** Script 01 (SNOW2) saves its result to disk. Scripts 02 and 03 reload that result in seconds, so threshold sensitivity analysis requires no re-extraction. Each threshold run saves to its own subfolder — no data is ever overwritten.

---

## 2. Raw µCT Data — Pre-Processing

Before running the pipeline your µCT data must be reconstructed and exported as a clean 8-bit TIFF stack. This section covers the full process from raw scan to pipeline-ready images.

### 2.1 Scan Acquisition Parameters

Record and report these in your methods section:

| Parameter | Description | Example |
|---|---|---|
| Voxel size | Physical voxel size (µm) | 0.54 µm |
| Voltage | X-ray tube voltage (kV) | 60 kV |
| Current | X-ray tube current (µA) | 200 µA |
| Exposure | Per-frame exposure (ms) | 500 ms |
| Projections | Total angular projections | 1001 |
| Filter | Hardware beam filter | Al 0.5 mm |

> **Note your voxel size carefully** — it is a required input in Script 01 (`voxel_size` parameter).

### 2.2 Reconstruction

Reconstruct raw projections using your scanner's software (e.g. NRecon for Bruker/SkyScan, CT-Pro for Nikon):

1. Open raw projections in reconstruction software
2. Apply beam hardening correction (typically 20–40% for polymer scaffolds)
3. Apply ring artefact reduction if needed
4. Set output format to **8-bit TIFF slices**
5. Export as sequentially numbered TIFFs: `slice_0001.tiff`, `slice_0002.tiff`, ...

### 2.3 Pre-Processing in Dragonfly ORS (Recommended)

[Dragonfly ORS](https://theobjects.com/dragonfly/index.html) is **free for academic use** and provides GPU-accelerated image processing:

1. **File → Import** your reconstructed TIFF stack
2. **Image → Filters → Gaussian** — sigma 0.5–1.0 to reduce noise
3. **ROI Tools → Crop** — select your Representative Elementary Volume (REV):
   - Exclude boundary artefacts and beam hardening at sample edges
   - Minimum 200×200×200 voxels recommended for electrospun scaffolds
4. **Image → Type → 8-bit** if not already 8-bit
5. **File → Export → Image Stack** — save as sequential TIFF

### 2.4 Pre-Processing in Fiji/ImageJ (Free Alternative)

1. **File → Import → Image Sequence** — select first slice
2. **Analyze → Histogram** — verify two peaks are visible (pores = dark, fibres = bright)
3. **Process → Filters → Gaussian Blur 3D** — sigma 0.5–1.0
4. Select REV region → **Image → Crop** — apply to all slices
5. **Image → Type → 8-bit**
6. **File → Save As → Image Sequence** — export as TIFF, start number 0001

### 2.5 Verify Your Stack Is Ready

Organise files before running:

```
your_data/
└── Sample_01/
    └── tiff_stack/
        ├── slice_0001.tiff
        ├── slice_0002.tiff
        └── ...
```

Checklist:

- [ ] All slices present with sequential numbering and no gaps
- [ ] All slices are the same width × height
- [ ] Images are **8-bit grayscale TIFF** format
- [ ] **Pores are dark (low intensity) | Fibres are bright (high intensity)**
- [ ] No visible edge artefacts or beam hardening rings in the REV

> If your images are inverted (pores bright, fibres dark), add `im = ~im` after binarisation in Script 01.

---

## 3. Installation

### 3.1 Install uv

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal, then verify: `uv --version`

### 3.2 Clone the Repository

```bash
git clone https://github.com/andtoni/pore-network-analysis
cd pore-network-analysis
```

### 3.3 Create Environment and Install Packages

**Windows:**
```powershell
uv venv --python 3.12
.venv\Scripts\activate
uv pip install -r requirements.txt
```

**macOS / Linux:**
```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 3.4 Verify Installation

```bash
python verify_environment.py
```

Expected output:
```
ALL CHECKS PASSED — environment is ready
```

### 3.5 Install ParaView (Script 03 only)

Download ParaView 5.13+ from: https://www.paraview.org/download/

Script 03 uses ParaView's bundled `pvpython` interpreter — **your virtual environment does not need to be active** when running Script 03.

---

## 4. Directory Setup

All three scripts share a single `data_dir`. The pipeline creates all required subfolders automatically:

```
data_dir/                              ← set in all three scripts
└── Sample_01/                         ← sample_name
    ├── snow2_output.pkl               ← Script 01 output (never overwritten)
    ├── im_pores.npy                   ← Script 01 output
    ├── im_fibres.npy                  ← Script 01 output
    └── outputs/
        ├── pore10um_throat10um/       ← one folder per threshold run
        │   ├── growthtunnel.vtp       ← thresholded network (ParaView)
        │   ├── proj_02.vtp            ← unthresholded network (ParaView)
        │   ├── image.tif              ← fibre volume (ParaView)
        │   ├── image2.tif             ← pore volume (ParaView)
        │   ├── pore_data.csv          ← GraphPad Prism
        │   ├── throat_data.csv        ← GraphPad Prism
        │   ├── 01_histograms_raw.png
        │   ├── 02_histograms_filtered.png
        │   ├── Sample_01_pore10um_throat10um_visualization.png
        │   └── Sample_01_pore10um_throat10um.pvsm
        └── pore15um_throat15um/
            └── ...
```

### Settings to Change in Each Script

**Script 01** — change once per sample:
```python
sample_name = "Sample_01"         # unique name, no spaces
voxel_size  = 0.54                # µm/voxel — from your scan parameters
threshold   = 50                  # binarisation threshold (0–255)
image_path  = r"C:\...\*.tiff"    # path to your TIFF stack
data_dir    = r"C:\...\outputs"   # root output directory
```

**Script 02** — change per threshold run:
```python
sample_name      = "Sample_01"    # must match Script 01
pore_threshold   = 10             # µm — minimum pore diameter to retain
throat_threshold = 10             # µm — minimum throat diameter to retain
data_dir         = r"C:\...\outputs"
```

**Script 03** — change when adding samples or thresholds:
```python
data_dir              = r"C:\...\outputs"
samples               = ["Sample_01", "Sample_02"]
threshold_combinations = [(5, 5), (10, 10), (15, 15)]
```

---

## 5. Script 01 — SNOW2 Extraction

```bash
python scripts/01_run_snow2.py
```

Runs the SNOW2 pore network extraction algorithm (PoreSpy, Gostick et al. 2019) on your TIFF stack. Saves the result to disk so it never needs to be re-run.

**Runtime:** 10–60 minutes depending on volume size and CPU. Script 01 will not overwrite an existing `snow2_output.pkl` — delete it manually if you need to re-run for a sample.

**Check your threshold:** Run Script 02 and inspect `01_histograms_raw.png`. The histogram should show a clear bimodal distribution. If porosity is <1% or >99%, adjust the threshold.

---

## 6. Script 02 — Network Analysis and Threshold Sensitivity

```bash
python scripts/02_run_network_analysis.py
```

Loads the saved SNOW2 output (seconds), builds the network model, applies filters, and exports all results. Run freely with different thresholds.

**Network cleaning procedure:**
1. Remove throats below `throat_threshold`
2. Remove pores below `pore_threshold`
3. **Extract largest connected cluster** (scipy graph analysis) — removes isolated pore islands not connected to the main percolating network
4. Iterative health check — runs until the network is stable

**Scientific justification for cluster removal:**
Isolated pore clusters cannot support cell migration and are not functionally relevant to transmural scaffold growth. Their removal is consistent with biological interpretations of angio-permissive porosity as described in the associated publication.

Include in your methods:
> *"Following network extraction, only the largest percolating pore cluster was retained, as isolated clusters do not contribute to transmural cell migration pathways [Tonelli et al., 2025, doi:10.2139/ssrn.6664677]."*

---

## 7. Script 03 — ParaView Batch Visualisation

**Windows PowerShell:**
```powershell
& "C:\Program Files\ParaView 5.13.3\bin\pvpython.exe" "scripts\03_run_paraview_batch.py"
```

**macOS:**
```bash
/Applications/ParaView-5.13.3.app/Contents/bin/pvpython scripts/03_run_paraview_batch.py
```

Generates publication-quality 3840×3840 PNG screenshots and `.pvsm` state files for every sample × threshold combination. If any required file is missing, that run is skipped with a clear message.

---

## 8. Outputs and GraphPad Prism

### CSV Format

| File | Columns | Import into Prism as |
|---|---|---|
| `pore_data.csv` | `pore_diameter_um`, `pore_volume` | Column table → Y column |
| `throat_data.csv` | `throat_diameter_um`, `throat_length_um` | Column table → Y column |

See `examples/` for example output files.

**In GraphPad Prism:**
1. **File → New → Column Table**
2. **File → Import → From File** → select CSV
3. Assign `pore_diameter_um` or `throat_diameter_um` to Y
4. Use **Analyze → Column Statistics** for descriptive statistics
5. Use **Graphs → Box and Whisker** or **Frequency Distribution** for figures

---

## 9. Troubleshooting

| Error | Likely cause | Fix |
|---|---|---|
| `FileNotFoundError: snow2_output.pkl` | Script 01 not run | Run `01_run_snow2.py` first |
| `No TIFF files found` | Wrong path or extension | Check `image_path`; use `*.tiff` or `*.tif` |
| Porosity 0% or 100% | Threshold wrong or image inverted | Adjust `threshold`; add `im = ~im` if inverted |
| Script appears frozen | SNOW2 running normally | Check CPU in Task Manager — it should be active |
| VTP files not generated | OpenPNM naming issue | `save_vtk_with_name()` handles this — check log |
| Script 03 skips all runs | Missing Script 02 outputs | Run `02_run_network_analysis.py` first |
| Isolated pores in ParaView | High threshold fragments network | Check cluster extraction log — lower threshold if needed |
| `pvpython` not found | Wrong ParaView install path | Run `Get-Item "C:\Program Files\ParaView*"` to find path |
| Memory error | Image stack too large | Crop to a smaller REV in Fiji/Dragonfly |

---

## 10. Dependencies and Licences

This pipeline is released under the **MIT Licence** (see [LICENSE](LICENSE)). All third-party dependencies are used as external libraries via `pip install` and retain their own licences. See [LICENSE](LICENSE) for full third-party notices.

| Package | Version | Licence | Citation |
|---|---|---|---|
| **PoreSpy** | 2.2.0 | MIT | Gostick et al. (2019). *JOSS*. [doi:10.21105/joss.01296](https://doi.org/10.21105/joss.01296) |
| **OpenPNM** | 3.3.0 | MIT | Gostick et al. (2016). *Comput. Sci. Eng.* [doi:10.1109/MCSE.2016.49](https://doi.org/10.1109/MCSE.2016.49) |
| NumPy | 1.26.4 | BSD-3-Clause | — |
| SciPy | 1.13.1 | BSD-3-Clause | — |
| scikit-image | 0.22.0 | BSD-3-Clause | — |
| Matplotlib | 3.9.0 | PSF | — |
| imageio | 2.34.0 | BSD-2-Clause | — |
| pandas | 2.2.0 | BSD-3-Clause | — |
| pypardiso | 0.4.6 | MIT | optional |
| **ParaView** | 5.13+ | BSD-3-Clause | Kitware Inc. https://www.paraview.org |

**PoreSpy and OpenPNM are both MIT licensed.** MIT licence compliance requires citing their authors in publications — the table above provides the required citations. No licence text inclusion is required for end-user software that uses these packages as dependencies (only for redistribution of modified source code).

If you use this pipeline in a publication, please also cite PoreSpy and OpenPNM directly:

```
Gostick J, Khan ZA, Tranter TG, et al. PoreSpy: A Python Toolkit for
Quantitative Analysis of Porous Media Images. Journal of Open Source
Software. 2019;4(37):1296. doi:10.21105/joss.01296

Gostick JT, Aghighi M, Hinebaugh J, et al. OpenPNM: A Pore Network
Modeling Package. Computing in Science & Engineering. 2016;18(4):60–74.
doi:10.1109/MCSE.2016.49
```

---

## 11. Contact

**Andrea Tonelli**
University of Cape Town, South Africa
tnland001@myuct.ac.za
ORCID: [0000-0002-1601-4103](https://orcid.org/0000-0002-1601-4103)
GitHub: [@andtoni](https://github.com/andtoni)

For questions about adapting this pipeline to other porous materials or imaging modalities, please open a [GitHub issue](https://github.com/andtoni/pore-network-analysis/issues).

---

*Developed for the analysis of electrospun scaffold architecture using nano-CT imaging, University of Cape Town, 2025.*
