import matplotlib
matplotlib.use('Agg')

import porespy as ps
import numpy as np
import pickle
import os
import sys
from datetime import datetime
from skimage.io import imread_collection

# ═══════════════════════════════════════════════════════════════════════════════
# CHANGE THESE PER SAMPLE ONLY
# ═══════════════════════════════════════════════════════════════════════════════
sample_name   = "SR-Pel20"
voxel_size    = 0.54
threshold     = 50
image_path    = rf"C:\Users\andto\OneDrive\Desktop\University\PhD\DATA\Transmural Space Characterisation\3D Analysis Paper\{sample_name}\SR-p20-REV\*.tiff"
base_data_dir = r"C:\Users\andto\OneDrive\Desktop\University\PhD\DATA\Transmural Space Characterisation\3D Analysis Paper\codeoutput"
# ═══════════════════════════════════════════════════════════════════════════════
#ENSURE SAMPLE NAME SAME FOR SNOW AND NETWORK SCRIPTS, ensure directories are correct

# Output goes to sample folder — NOT threshold subfolder
sample_dir = os.path.join(base_data_dir, sample_name)
os.makedirs(sample_dir, exist_ok=True)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

log(f"Sample:      {sample_name}")
log(f"Voxel size:  {voxel_size} um")
log(f"Threshold:   {threshold}")
log(f"Image path:  {image_path}")
log(f"Sample dir:  {sample_dir}")
log("=" * 60)

# ── Check if SNOW2 already run for this sample ────────────────────────────────
pkl_path = os.path.join(sample_dir, "snow2_output.pkl")
if os.path.exists(pkl_path):
    size_mb = os.path.getsize(pkl_path) / 1e6
    log(f"WARNING: snow2_output.pkl already exists ({size_mb:.1f} MB)")
    log("Delete it manually if you want to rerun SNOW2 for this sample")
    log("Exiting to avoid overwriting existing data")
    sys.exit(0)

# ── Load Images ───────────────────────────────────────────────────────────────
log("Loading images...")
seq = imread_collection(image_path)
log(f"Loaded {len(seq)} slices")

# ── Convert to 3D ─────────────────────────────────────────────────────────────
log("Converting to 3D stack...")
im3d = np.zeros([*seq[0].shape, len(seq)])
for i, im in enumerate(seq):
    im3d[..., i] = im
log(f"Stack shape:     {im3d.shape}")
log(f"Stack RAM usage: {im3d.nbytes / 1e9:.2f} GB")

# ── Binarise ──────────────────────────────────────────────────────────────────
log("Binarising...")
im  = im3d < threshold
im2 = im3d > threshold
porosity = ps.metrics.porosity(im) * 100
log(f"Porosity: {porosity:.2f}%")

# ── Run SNOW2 ─────────────────────────────────────────────────────────────────
log("Running SNOW2 — this is the slowest step, please wait...")
ps.settings.verbosity = 1
snow_output = ps.networks.snow2(im, voxel_size=voxel_size)
log("SNOW2 complete!")

# ── Save Outputs to Sample Root ───────────────────────────────────────────────
log(f"Saving SNOW2 output to: {pkl_path}")
with open(pkl_path, "wb") as f:
    pickle.dump(snow_output, f)

file_size = os.path.getsize(pkl_path)
if file_size < 1000:
    log(f"WARNING: pkl file suspiciously small ({file_size} bytes) — may be corrupt")
else:
    log(f"pkl saved successfully ({file_size / 1e6:.1f} MB)")

log("Verifying pkl can be reloaded...")
with open(pkl_path, "rb") as f:
    test = pickle.load(f)
log(f"Verification passed! Network has {len(test.network['pore.coords'])} pores")

log("Saving binarised image arrays...")
np.save(os.path.join(sample_dir, "im_pores.npy"),  im)
np.save(os.path.join(sample_dir, "im_fibres.npy"), im2)
log("Saved: im_pores.npy and im_fibres.npy")

log("=" * 60)
log(f"SNOW2 complete for sample: {sample_name}")
log(f"Porosity: {porosity:.2f}%")
log(f"All outputs saved to: {sample_dir}")
log("Now run run_network_analysis.py with your chosen thresholds")
log("=" * 60)