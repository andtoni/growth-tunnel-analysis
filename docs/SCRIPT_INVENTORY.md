# Script Inventory

## Active Pipeline

These are the canonical pipeline scripts already present in the Forgejo repository. The archived `Paper 2/Git` copies were byte-identical during the 2026-07-06 migration.

| Script | Role |
|---|---|
| `01_run_snow2.py` | SNOW2 pore-network extraction from preprocessed micro-CT TIFF stacks. |
| `02_run_network_analysis.py` | Thresholded network analysis, CSV/VTK export. |
| `03_run_paraview_batch.py` | ParaView screenshot/state generation. |
| `04_quantification_export.py` | PNM topology/density metrics and Prism-ready Excel workbook. |
| `05_pnm_data_export.py` | Universal long/wide pore-throat data export. |
| `verify_environment.py` | Pipeline dependency/environment verification. |

## Filed Legacy Scripts

| Location | Source | Notes |
|---|---|---|
| `scripts/legacy/stablePNM/` | `_System/Coding-mirror/stablePNM` | Earlier variants and utilities: `run_snow2_only.py`, `run_network_analysis*.py`, `run_paraview_batch.py`, `reference_pipeline.py`, `pnm_prism_export.py`, `fullPNM.py`, `SnowtoVTK`, and related small config/source files. |
| `scripts/legacy/confocal-porosity/confocal_porosity.py` | `_System/Coding-mirror/confocalPorosity/scripts/confocal_porosity.py` | CZI z-stack porosity workflow with Prism-ready CSV/XLSX output. Contains old Windows paths and should be parameterised before reuse. |
| `scripts/legacy/imagej/image_process.ijm` | `_System/Coding-mirror/Great Scripts/image_process.ijm` | Fiji/ImageJ image-processing macro referenced by the growth-tunnel workflow. |
| `scripts/legacy/imagej/3D Paper-SEM.ijm` | `Original/transmural-space-characterisation-3d-analysis-paper/3D Paper-SEM.ijm` | SEM/ImageJ macro from the paper material folder. |
| `scripts/legacy/mechanical/InstronAnalysis.bas` | `Original/paper-2-manuscript-and-extra-analysis/Extra Analysis/InstronAnalysis.bas` | VBA macro for the mechanical testing workbook. |
| `figures/source/paraview/p16SR.legacy-system.pvsm` | `_System/Coding-mirror/stablePNM/p16SR.pvsm` | Legacy ParaView state template retained as editable figure/source state. |

## Critical Non-Git Artefacts

These are intentionally external to Git:

| Artefact | Location |
|---|---|
| Mechanical Data Summary workbook | `/home/andto/Nextcloud/Work/PhD/Projects/growth-tunnel-analysis/Original/paper-2-manuscript-and-extra-analysis/Extra Analysis/Mechanical Data Summary.xlsx` |
| Mechanical raw exports | `/home/andto/Nextcloud/Work/PhD/Projects/growth-tunnel-analysis/Original/paper-2-manuscript-and-extra-analysis/Extra Analysis/Mechanical` |
| Mechanical table DOCX | `/home/andto/Nextcloud/Work/PhD/Projects/growth-tunnel-analysis/Original/paper-2-manuscript-and-extra-analysis/Extra Analysis/Table for Mechanical Properties.docx` |
| Mechanical anisotropy SVG table | `/home/andto/Nextcloud/Work/PhD/Projects/growth-tunnel-analysis/Original/paper-2-manuscript-and-extra-analysis/Extra Analysis/mechanical_anisotropy_svg_table.svg` |
| Prism project | `/home/andto/Nextcloud/Work/PhD/Projects/growth-tunnel-analysis/Original/paper-2-manuscript-and-extra-analysis/Extra Analysis/Project2.prism` |
| PNM quantification workbook | `/home/andto/Nextcloud/Work/PhD/Projects/growth-tunnel-analysis/Original/transmural-space-characterisation-3d-analysis-paper/codeoutput/Pore_Network_Quantification.xlsx` |
| PNM Prism grouped workbook | `/home/andto/Nextcloud/Work/PhD/Projects/growth-tunnel-analysis/Original/transmural-space-characterisation-3d-analysis-paper/codeoutput/PNM_Prism_Grouped.xlsx` |
| Confocal porosity output workbook | `/home/andto/Nextcloud/Work/PhD/Projects/growth-tunnel-analysis/Original/transmural-space-characterisation-3d-analysis-paper/Porosity/Confocal/porosity_output/porosity_results.xlsx` |

## Remaining Porting Work

- Parameterise hard-coded Windows paths in legacy scripts before running them on Linux.
- Convert the mechanical VBA workflow into a scripted Python/R workflow only after preserving original workbook behaviour.
- Build a checksum manifest for material directories when ready; skip during routine checks because the archive is large.
