# =============================================================================
# Script 01 — SNOW2 Pore Network Extraction
# =============================================================================
# Author:      Andrea Tonelli (tnland001@myuct.ac.za)
# ORCID:       https://orcid.org/0000-0002-1601-4103
# Institution: University of Cape Town
# Repository:  https://github.com/andtoni/pore-network-analysis
# Preprint:    https://dx.doi.org/10.2139/ssrn.6664677
#
# Description:
#   Loads a pre-processed µCT TIFF image stack, binarises it, and runs the
#   SNOW2 pore network extraction algorithm (PoreSpy). The result is saved to
#   disk so that Script 02 can load it in seconds without re-running the
#   computationally expensive extraction step.
#
#   Run this script ONCE per sample.
#
# Third-party dependencies (MIT Licence):
#   PoreSpy  — Gostick et al. (2019) doi:10.21105/joss.01296
#   OpenPNM  — Gostick et al. (2016) doi:10.1109/MCSE.2016.49
#
# Usage:
#   python scripts/01_run_snow2.py
#
# Output (saved to data_dir / sample_name /):
#   snow2_output.pkl  — serialised SNOW2 result (required by Script 02)
#   im_pores.npy      — binarised pore array
#   im_fibres.npy     — binarised fibre array
# =============================================================================

import matplotlib
matplotlib.use('Agg')

import porespy as ps
import numpy as np
import pickle
import os
import sys
from datetime import datetime
from skimage.io import imread_collection

# =============================================================================
# USER SETTINGS — edit these before running
# =============================================================================

# Unique name for this sample — used as folder name (no spaces recommended)
sample_name = "Sample_01"

# Physical voxel size in micrometres — from your scan acquisition parameters
voxel_size = 0.54  # um/voxel

# Greyscale binarisation threshold (0–255 for 8-bit images)
# Pores are assigned where pixel intensity < threshold (dark = pore space)
# Check 01_histograms_raw.png after running Script 02 to verify this is correct
threshold = 50

# Full path to your pre-processed 8-bit TIFF image stack
# Use *.tiff or *.tif to match your file extension
image_path = r"C:\path\to\your\tiff_stack\*.tiff"

# Root output directory — all results save under: data_dir / sample_name /
data_dir = r"C:\path\to\your\output\directory"

# =============================================================================
# DO NOT EDIT BELOW THIS LINE
# =============================================================================

sample_dir = os.path.join(data_dir, sample_name)
os.makedirs(sample_dir, exist_ok=True)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

log("=" * 60)
log("SNOW2 Pore Network Extraction")
log("Tonelli A. — University of Cape Town — 2025")
log("=" * 60)
log(f"Sample:     {sample_name}")
log(f"Voxel size: {voxel_size} um/voxel")
log(f"Threshold:  {threshold} (pores = intensity < {threshold})")
log(f"Images:     {image_path}")
log(f"Output:     {sample_dir}")
log("=" * 60)

# ── Prevent accidental overwrite ──────────────────────────────────────────────
pkl_path = os.path.join(sample_dir, "snow2_output.pkl")
if os.path.exists(pkl_path):
    size_mb = os.path.getsize(pkl_path) / 1e6
    log(f"WARNING: snow2_output.pkl already exists ({size_mb:.1f} MB)")
    log("Delete it manually if you need to re-run SNOW2 for this sample")
    log("Exiting to protect existing data")
    sys.exit(0)

# ── Load TIFF stack ───────────────────────────────────────────────────────────
log("Loading TIFF stack...")
seq = imread_collection(image_path)
if len(seq) == 0:
    raise FileNotFoundError(
        f"No TIFF files found at:\n  {image_path}\n"
        "Check image_path and file extension (.tiff vs .tif)"
    )
log(f"Loaded {len(seq)} slices | Slice shape: {seq[0].shape}")

# ── Build 3D volume ───────────────────────────────────────────────────────────
log("Building 3D volume array...")
im3d = np.zeros([*seq[0].shape, len(seq)])
for i, im in enumerate(seq):
    im3d[..., i] = im
log(f"Volume shape:    {im3d.shape}")
log(f"RAM usage:       {im3d.nbytes / 1e9:.2f} GB")

# ── Binarise ──────────────────────────────────────────────────────────────────
log("Binarising...")
im  = im3d < threshold   # pore space (low intensity = dark)
im2 = im3d > threshold   # fibre/solid space (high intensity = bright)
porosity = ps.metrics.porosity(im) * 100
log(f"Porosity: {porosity:.2f}%")
if porosity < 1 or porosity > 99:
    log("WARNING: Porosity is unusually high or low.")
    log("  Verify your threshold value is correct.")
    log("  If pores are bright and fibres dark, add: im = ~im")

# ── Run SNOW2 algorithm ───────────────────────────────────────────────────────
# SNOW2 is implemented in PoreSpy (Gostick et al., 2019, doi:10.21105/joss.01296)
# Uses marker-based watershed segmentation with distance transform peak finding
log("Running SNOW2 algorithm (PoreSpy) — may take 10–60 min...")
ps.settings.verbosity = 1
snow_output = ps.networks.snow2(im, voxel_size=voxel_size)
log("SNOW2 complete!")

# ── Save SNOW2 output ─────────────────────────────────────────────────────────
log("Saving SNOW2 output...")
with open(pkl_path, "wb") as f:
    pickle.dump(snow_output, f)

file_size = os.path.getsize(pkl_path)
if file_size < 1000:
    log(f"WARNING: pkl file is very small ({file_size} bytes) — may be corrupt")
    log("Try deleting and re-running this script")
else:
    log(f"Saved: snow2_output.pkl ({file_size / 1e6:.1f} MB)")

# ── Verify the pkl reloads correctly ─────────────────────────────────────────
log("Verifying pkl integrity...")
with open(pkl_path, "rb") as f:
    test = pickle.load(f)
log(f"Verified — raw network contains {len(test.network['pore.coords'])} pores")

# ── Save binarised arrays ─────────────────────────────────────────────────────
log("Saving binarised image arrays...")
np.save(os.path.join(sample_dir, "im_pores.npy"),  im)
np.save(os.path.join(sample_dir, "im_fibres.npy"), im2)
log("Saved: im_pores.npy and im_fibres.npy")

# ── Summary ───────────────────────────────────────────────────────────────────
log("=" * 60)
log(f"SNOW2 complete for: {sample_name}")
log(f"Porosity:           {porosity:.2f}%")
log(f"Raw pore count:     {len(test.network['pore.coords'])}")
log(f"Output folder:      {sample_dir}")
log("")
log("Next step: edit and run  02_run_network_analysis.py")
log("=" * 60)
