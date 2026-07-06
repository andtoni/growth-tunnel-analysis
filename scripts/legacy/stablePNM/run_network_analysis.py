import matplotlib
matplotlib.use('Agg')

import porespy as ps
import openpnm as op
import numpy as np
import matplotlib.pyplot as plt
import pickle
import pandas as pd
import os
import sys
import imageio.v2 as imageio
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# CHANGE THESE FOR EACH RUN
# ═══════════════════════════════════════════════════════════════════════════════
sample_name      = "SR-Pel20"
pore_threshold   = 15       # um
throat_threshold = 15       # um
base_data_dir    = r"C:\Users\andto\OneDrive\Desktop\University\PhD\DATA\Transmural Space Characterisation\3D Analysis Paper\codeoutput"

# ═══════════════════════════════════════════════════════════════════════════════

# ── Paths ─────────────────────────────────────────────────────────────────────
sample_dir = os.path.join(base_data_dir, sample_name)
run_label  = f"pore{pore_threshold}um_throat{throat_threshold}um"
output_dir = os.path.join(sample_dir, "outputs", run_label)
os.makedirs(output_dir, exist_ok=True)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

log(f"Sample:           {sample_name}")
log(f"Pore threshold:   {pore_threshold} um")
log(f"Throat threshold: {throat_threshold} um")
log(f"Run label:        {run_label}")
log(f"Output dir:       {output_dir}")
log("=" * 60)

# ── Load SNOW2 Output ─────────────────────────────────────────────────────────
pkl_path = os.path.join(sample_dir, "snow2_output.pkl")
if not os.path.exists(pkl_path):
    raise FileNotFoundError(
        f"SNOW2 output not found at:\n{pkl_path}\n"
        f"Please run run_snow2_only.py first for sample: {sample_name}"
    )

log("Loading saved SNOW2 output...")
with open(pkl_path, "rb") as f:
    snow_output = pickle.load(f)
log("SNOW2 output loaded successfully!")

# ── Load Binarised Images ─────────────────────────────────────────────────────
log("Loading binarised image arrays...")
im  = np.load(os.path.join(sample_dir, "im_pores.npy"))
im2 = np.load(os.path.join(sample_dir, "im_fibres.npy"))
log(f"Image shape: {im.shape}")

# ── Build Pore Network ────────────────────────────────────────────────────────
log("Building pore network model...")
pn = op.io.network_from_porespy(snow_output.network)
geo = op.models.collections.geometry.spheres_and_cylinders
pn.add_model_collection(geo, domain='all')
pn.regenerate_models()
log(f"Initial network: {pn.num_pores()} pores, {pn.num_throats()} throats")

# ── Label Boundaries ──────────────────────────────────────────────────────────
net = ps.networks.label_boundaries(network=pn)
net = pn

# ── Plot Raw Histograms ───────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=[12, 4])
ax1.hist(pn['pore.inscribed_diameter'], bins=25, edgecolor='k')
ax1.set_xlabel('Diameter (um)')
ax1.set_title(f'{sample_name} — Pore Diameter (raw)')
ax2.hist(pn['throat.inscribed_diameter'], bins=25, edgecolor='k')
ax2.set_xlabel('Diameter (um)')
ax2.set_title(f'{sample_name} — Throat Diameter (raw)')
fig.savefig(os.path.join(output_dir, "01_histograms_raw.png"), dpi=150)
plt.close()
log("Saved: 01_histograms_raw.png")

# ═══════════════════════════════════════════════════════════════════════════════
# SAVE FULL UNTHRESHOLDED NETWORK — matches original proj_02.vtp in ParaView
# ═══════════════════════════════════════════════════════════════════════════════
log("Saving full unthresholded network (proj_02.vtp)...")

# Save to a temporary name then rename to proj_02.vtp
# project_to_vtk saves as {filename}.vtp — we use a temp name to isolate it
pre_threshold_dir = os.path.join(output_dir, "_pre_threshold_temp")
os.makedirs(pre_threshold_dir, exist_ok=True)

op.io.project_to_vtk(
    project=pn.project,
    filename=os.path.join(pre_threshold_dir, "pre_threshold")
)

# Find and move the generated VTP to output_dir as proj_02.vtp
import glob
import shutil

pre_vtps = sorted(glob.glob(os.path.join(pre_threshold_dir, "*.vtp")))
log(f"Pre-threshold VTP files generated: {[os.path.basename(f) for f in pre_vtps]}")

if len(pre_vtps) >= 1:
    shutil.copy(pre_vtps[0], os.path.join(output_dir, "proj_02.vtp"))
    log("Saved: proj_02.vtp (full unthresholded network)")
if len(pre_vtps) >= 2:
    shutil.copy(pre_vtps[1], os.path.join(output_dir, "proj_02b.vtp"))
    log("Saved: proj_02b.vtp (additional pre-threshold file)")

shutil.rmtree(pre_threshold_dir)
log("Cleaned up temporary folder")

# ── Remove Restrictive Throats ────────────────────────────────────────────────
log(f"Trimming throats < {throat_threshold} um...")
mask = net["throat.inscribed_diameter"] < throat_threshold
op.topotools.trim(pn, throats=mask)
log(f"After throat trim: {pn.num_pores()} pores, {pn.num_throats()} throats")

# ── Remove Restrictive Pores ──────────────────────────────────────────────────
log(f"Trimming pores < {pore_threshold} um...")
mask = net["pore.inscribed_diameter"] < pore_threshold
op.topotools.trim(pn, pores=mask)
log(f"After pore trim: {pn.num_pores()} pores, {pn.num_throats()} throats")

# ── Check Network Health ──────────────────────────────────────────────────────
log("Checking network health...")
h = op.utils.check_network_health(pn)
print(h)
pores_to_trim = np.union1d(h['isolated_pores'], h['disconnected_pores'])
if len(pores_to_trim) > 0:
    log(f"Trimming {len(pores_to_trim)} problematic pores...")
    op.topotools.trim(network=pn, pores=pores_to_trim)
else:
    log("Network is healthy — no pores to trim")
log(f"Final network: {pn.num_pores()} pores, {pn.num_throats()} throats")

# ── Plot Filtered Histograms ──────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=[12, 4])
ax1.hist(pn['pore.inscribed_diameter'], bins=25, edgecolor='k')
ax1.set_xlabel('Diameter (um)')
ax1.set_title(f'{sample_name} — Pore Diameter ({run_label})')
ax2.hist(pn['throat.inscribed_diameter'], bins=25, edgecolor='k')
ax2.set_xlabel('Diameter (um)')
ax2.set_title(f'{sample_name} — Throat Diameter ({run_label})')
fig.savefig(os.path.join(output_dir, "02_histograms_filtered.png"), dpi=150)
plt.close()
log("Saved: 02_histograms_filtered.png")

# ── Export CSVs for Prism ─────────────────────────────────────────────────────
log("Exporting CSVs for GraphPad Prism...")
df_pores = pd.DataFrame({
    'pore_diameter_um': pn['pore.inscribed_diameter'],
    'pore_volume':      pn['pore.volume'],
})
df_throats = pd.DataFrame({
    'throat_diameter_um': pn['throat.inscribed_diameter'],
    'throat_length_um':   pn['throat.length'],
})
df_pores.to_csv(os.path.join(output_dir, "pore_data.csv"), index=False)
df_throats.to_csv(os.path.join(output_dir, "throat_data.csv"), index=False)
log("Saved: pore_data.csv and throat_data.csv")

# ── Save Thresholded Network as growthtunnel.vtp ──────────────────────────────
log("Saving thresholded network (growthtunnel.vtp)...")

post_threshold_dir = os.path.join(output_dir, "_post_threshold_temp")
os.makedirs(post_threshold_dir, exist_ok=True)

op.io.project_to_vtk(
    project=pn.project,
    filename=os.path.join(post_threshold_dir, "growthtunnel")
)

post_vtps = sorted(glob.glob(os.path.join(post_threshold_dir, "*.vtp")))
log(f"Post-threshold VTP files generated: {[os.path.basename(f) for f in post_vtps]}")

if len(post_vtps) >= 1:
    shutil.copy(post_vtps[0], os.path.join(output_dir, "growthtunnel.vtp"))
    log("Saved: growthtunnel.vtp (thresholded network)")
if len(post_vtps) >= 2:
    shutil.copy(post_vtps[1], os.path.join(output_dir, "growthtunnel_b.vtp"))
    log("Saved: growthtunnel_b.vtp (additional post-threshold file)")

shutil.rmtree(post_threshold_dir)
log("Cleaned up temporary folder")

# ── Save Image Volumes ────────────────────────────────────────────────────────
log("Saving aligned image volumes...")
im_aligned  = ps.tools.align_image_with_openpnm(im)
im2_aligned = ps.tools.align_image_with_openpnm(im2)

imageio.volsave(os.path.join(output_dir, "image.tif"),
                np.array(im2_aligned, dtype=np.int8))
imageio.volsave(os.path.join(output_dir, "image2.tif"),
                np.array(im_aligned,  dtype=np.int8))
log("Saved: image.tif (fibres) and image2.tif (pores)")

# ── Update pvsm for this run ──────────────────────────────────────────────────
pvsm_template = r"C:\Users\andto\OneDrive\Desktop\University\PhD\DATA\Transmural Space Characterisation\3D Analysis Paper\SR-Pel16\p16SR.pvsm"

if os.path.exists(pvsm_template):
    log("Generating updated pvsm for ParaView...")

    with open(pvsm_template, 'r') as f:
        content = f.read()

    # Find the original directory from the template pvsm
    original_dir = os.path.dirname(
        [l for l in content.split('\n')
         if 'growthtunnel.vtp' in l][0]
        .split('value="')[1]
        .split('"')[0]
    ).replace('/', '\\')

    # Replace with this run's output directory
    updated_content = content.replace(
        original_dir,
        output_dir
    )

    pvsm_out = os.path.join(output_dir, f"{sample_name}_{run_label}.pvsm")
    with open(pvsm_out, 'w') as f:
        f.write(updated_content)
    log(f"Saved: {sample_name}_{run_label}.pvsm")
else:
    log("WARNING: pvsm template not found — skipping pvsm generation")
    log(f"Expected at: {pvsm_template}")

# ── Summary ───────────────────────────────────────────────────────────────────
porosity = ps.metrics.porosity(im_aligned) * 100
log("=" * 60)
log(f"Analysis complete for sample: {sample_name}")
log(f"Run label:  {run_label}")
log(f"Porosity:   {porosity:.2f}%")
log(f"Pores:      {pn.num_pores()}")
log(f"Throats:    {pn.num_throats()}")
log("─" * 60)
log("Output files:")
log(f"  proj_02.vtp      — full unthresholded network")
log(f"  growthtunnel.vtp — thresholded network")
log(f"  image.tif        — fibres volume")
log(f"  image2.tif       — pores volume")
log(f"  pore_data.csv    — pore data for Prism")
log(f"  throat_data.csv  — throat data for Prism")
log(f"  {sample_name}_{run_label}.pvsm — open in ParaView")
log("=" * 60)
