# State - Growth Tunnel Analysis

Last updated: 2026-07-06

## Current State

The Forgejo repository has been restored locally at `/home/andto/coding/papers/growth-tunnel-analysis`.

The complete associated material has been moved into `/home/andto/Nextcloud/Work/PhD/Projects/growth-tunnel-analysis`:

- `Original/transmural-space-characterisation-3d-analysis-paper`
- `Original/paper-2-manuscript-and-extra-analysis`
- `Manuscript/mtbio-d-26-02595-revision-package-2026-06`
- `_legacy/system-coding-mirror`

The active published pipeline remains at the repository root:

- `01_run_snow2.py`
- `02_run_network_analysis.py`
- `03_run_paraview_batch.py`
- `04_quantification_export.py`
- `05_pnm_data_export.py`
- `verify_environment.py`

Legacy paper-specific code has been filed into Git under `scripts/legacy/`, including the confocal porosity workflow, ImageJ macros, stablePNM variants, and `InstronAnalysis.bas`.

## Critical Material Confirmed

- Mechanical raw Instron files: `Original/paper-2-manuscript-and-extra-analysis/Extra Analysis/Mechanical`
- Mechanical summary workbook: `Original/paper-2-manuscript-and-extra-analysis/Extra Analysis/Mechanical Data Summary.xlsx`
- Mechanical table: `Original/paper-2-manuscript-and-extra-analysis/Extra Analysis/Table for Mechanical Properties.docx`
- Mechanical figure source: `Original/paper-2-manuscript-and-extra-analysis/Extra Analysis/mechanical_anisotropy_svg_table.svg`
- Prism project: `Original/paper-2-manuscript-and-extra-analysis/Extra Analysis/Project2.prism`
- Confocal porosity output: `Original/transmural-space-characterisation-3d-analysis-paper/Porosity/Confocal/porosity_output`
- PNM summary workbooks: `Original/transmural-space-characterisation-3d-analysis-paper/codeoutput`
- Latest clean manuscript: `Manuscript/mtbio-d-26-02595-revision-package-2026-06/paper2_v3_clean.docx`
- Latest tracked manuscript: `Manuscript/mtbio-d-26-02595-revision-package-2026-06/paper2_v3_tracked.docx`
- Latest response to reviewers: `Manuscript/mtbio-d-26-02595-revision-package-2026-06/detailedreviewerresponses_v3.docx`
- Latest cover letter: `Manuscript/mtbio-d-26-02595-revision-package-2026-06/coverletter_v3.docx`
- Original reviewer comments: `Manuscript/mtbio-d-26-02595-revision-package-2026-06/Reviewer Comments Original.docx`
- Manuscript package checksum manifest: `Manuscript/manifests/mtbio-d-26-02595-revision-package-2026-06.sha256`

## Resume Procedure

```bash
cd /home/andto/coding/papers/growth-tunnel-analysis
make status
make check
sed -n '1,260p' docs/SCRIPT_INVENTORY.md
```

## Open Decisions

- Confirm whether the public README should remain broad/public-facing or be split into public pipeline docs plus private paper reproducibility docs.
- Decide whether to port the hard-coded Windows paths inside legacy scripts into parameterised configs.
- Decide whether to produce a checksum manifest for the full material directory; this may be expensive because the project contains large microscopy and generated modelling artefacts.
