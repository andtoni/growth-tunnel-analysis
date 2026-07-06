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
import glob
import shutil
import imageio.v2 as imageio
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# CHANGE THESE FOR EACH RUN
# ═══════════════════════════════════════════════════════════════════════════════
sample_name      = "SR-Pel20"
pore_threshold   = 5        # um
throat_threshold = 5      # um
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

def save_vtk_with_name(project, output_dir, target_name):
    """
    Saves OpenPNM project to VTK and renames the first generated VTP file
    to target_name. Returns True if successful, False otherwise.

    project_to_vtk generates filenames based on internal project object names
    which are unpredictable — this function handles the renaming reliably.
    """
    # Use a dedicated temp folder so we only catch VTPs from this save call
    temp_dir = os.path.join(output_dir, f"_vtk_temp_{target_name.replace('.', '_')}")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Save to temp dir using a neutral filename
        temp_base = os.path.join(temp_dir, "network")
        op.io.project_to_vtk(project=project, filename=temp_base)

        # Find all generated VTP files
        generated = sorted(glob.glob(os.path.join(temp_dir, "*.vtp")))
        log(f"  VTP files generated: {[os.path.basename(f) for f in generated]}")

        if not generated:
            log(f"  ERROR: No VTP files were generated for {target_name}")
            return False

        # Copy the first (primary) VTP to the output directory with the target name
        target_path = os.path.join(output_dir, target_name)
        shutil.copy(generated[0], target_path)
        size_mb = os.path.getsize(target_path) / 1e6
        log(f"  Saved: {target_name} ({size_mb:.1f} MB)")

        # If a second VTP was generated (geometry object), save it too with _b suffix
        if len(generated) >= 2:
            b_name   = target_name.replace('.vtp', '_b.vtp')
            b_path   = os.path.join(output_dir, b_name)
            shutil.copy(generated[1], b_path)
            log(f"  Saved: {b_name} (secondary geometry file)")

        return True

    except Exception as e:
        log(f"  ERROR saving {target_name}: {e}")
        return False

    finally:
        # Always clean up temp folder
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            log(f"  Cleaned up temp folder")

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
# SAVE FULL UNTHRESHOLDED NETWORK → proj_02.vtp
# Must be saved BEFORE any trimming
# ═══════════════════════════════════════════════════════════════════════════════
log("Saving full unthresholded network as proj_02.vtp...")
save_vtk_with_name(pn.project, output_dir, "proj_02.vtp")


# - Remove Restrictive Throats ────────────────────────────────────────────────
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

def extract_largest_cluster(pn, log):
    """
    Uses scipy graph analysis to find and keep only the largest
    connected cluster. Completely bypasses OpenPNM cluster models
    which can be unreliable across versions.
    """
    n_pores = pn.num_pores()
    if n_pores == 0:
        log("  Network is empty — nothing to extract")
        return

    # Build sparse adjacency matrix from throat connections
    conns   = pn['throat.conns']
    row     = conns[:, 0]
    col     = conns[:, 1]
    data    = np.ones(len(conns))
    adj     = csr_matrix(
                (data, (row, col)),
                shape=(n_pores, n_pores)
              )

    # Find all connected components
    n_components, labels = connected_components(
        adj, directed=False, connection='weak'
    )

    if n_components == 1:
        log("  Network is already a single connected cluster")
        return

    # Find the largest component
    component_sizes = np.bincount(labels)
    largest_label   = int(np.argmax(component_sizes))
    largest_size    = int(component_sizes[largest_label])

    log(f"  Found {n_components} clusters")
    log(f"  Largest cluster: {largest_size} pores "
        f"({largest_size/n_pores*100:.1f}% of network)")
    log(f"  Removing {n_pores - largest_size} pores in "
        f"{n_components - 1} smaller cluster(s)")

    # Remove all pores not in the largest cluster
    pores_to_remove = np.where(labels != largest_label)[0]
    op.topotools.trim(network=pn, pores=pores_to_remove)
    log(f"  After cluster trim: {pn.num_pores()} pores, "
        f"{pn.num_throats()} throats")

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

# ── Extract Largest Connected Cluster (Pass 1) ────────────────────────────────
log("Extracting largest connected cluster (Pass 1)...")
extract_largest_cluster(pn, log)

# ── Iterative Health Check ────────────────────────────────────────────────────
# Each trim can create new isolated pores — run until network is stable
log("Running iterative health check...")
for pass_num in range(1, 11):
    h = op.utils.check_network_health(pn)
    pores_to_trim = np.union1d(h['isolated_pores'], h['disconnected_pores'])

    if len(pores_to_trim) == 0:
        log(f"Health check passed after {pass_num} pass(es)")
        break

    log(f"Pass {pass_num}: trimming {len(pores_to_trim)} pores...")
    op.topotools.trim(network=pn, pores=pores_to_trim)
    log(f"  Remaining: {pn.num_pores()} pores, {pn.num_throats()} throats")

# ── Extract Largest Cluster Again (Pass 2) ────────────────────────────────────
# Health check trimming can re-create small disconnected clusters
log("Final cluster extraction (Pass 2)...")
extract_largest_cluster(pn, log)

# ── Final Verification ────────────────────────────────────────────────────────
conns_final         = pn['throat.conns']
n_final             = pn.num_pores()
adj_final           = csr_matrix(
                        (np.ones(len(conns_final)),
                         (conns_final[:, 0], conns_final[:, 1])),
                        shape=(n_final, n_final)
                      )
n_final_components, _ = connected_components(
    adj_final, directed=False, connection='weak'
)

if n_final_components == 1:
    log(f"Verified: single connected network — "
        f"{pn.num_pores()} pores, {pn.num_throats()} throats")
else:
    log(f"WARNING: {n_final_components} clusters remain after cleaning")
    log(f"  This may indicate disconnected boundary pores — "
        f"check network visually in ParaView")


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

# ═══════════════════════════════════════════════════════════════════════════════
# SAVE THRESHOLDED NETWORK → growthtunnel.vtp
# Saved AFTER all trimming and cluster extraction
# ═══════════════════════════════════════════════════════════════════════════════
log("Saving thresholded network as growthtunnel.vtp...")
save_vtk_with_name(pn.project, output_dir, "growthtunnel.vtp")

# ── Verify Both VTP Files Exist ───────────────────────────────────────────────
log("Verifying VTP output files...")
for fname in ["proj_02.vtp", "growthtunnel.vtp"]:
    fpath = os.path.join(output_dir, fname)
    if os.path.exists(fpath):
        log(f"  ✓ {fname} ({os.path.getsize(fpath) / 1e6:.1f} MB)")
    else:
        log(f"  ✗ {fname} — MISSING, VTP save may have failed")

# ── Save Image Volumes ────────────────────────────────────────────────────────
# image.tif  = fibres (im2) — matches ParaView batch script expectation
# image2.tif = pores  (im)  — matches ParaView batch script expectation
log("Saving aligned image volumes...")
im_aligned  = ps.tools.align_image_with_openpnm(im)
im2_aligned = ps.tools.align_image_with_openpnm(im2)

imageio.volsave(
    os.path.join(output_dir, "image.tif"),
    np.array(im2_aligned, dtype=np.int8)
)
log("Saved: image.tif (fibres)")

imageio.volsave(
    os.path.join(output_dir, "image2.tif"),
    np.array(im_aligned, dtype=np.int8)
)
log("Saved: image2.tif (pores)")

# ── Verify All Four ParaView Files Exist ─────────────────────────────────────
log("Verifying all ParaView-required output files...")
paraview_files = ["growthtunnel.vtp", "proj_02.vtp", "image.tif", "image2.tif"]
all_present = True
for fname in paraview_files:
    fpath = os.path.join(output_dir, fname)
    if os.path.exists(fpath):
        log(f"  ✓ {fname}")
    else:
        log(f"  ✗ {fname} — MISSING")
        all_present = False

if all_present:
    log("All ParaView files present — batch script will run without skipping")
else:
    log("WARNING: Some files missing — ParaView batch script will skip this run")

# ── Summary ───────────────────────────────────────────────────────────────────
porosity = ps.metrics.porosity(im_aligned) * 100
log("=" * 60)
log(f"Analysis complete for sample: {sample_name}")
log(f"Run label:  {run_label}")
log(f"Porosity:   {porosity:.2f}%")
log(f"Pores:      {pn.num_pores()}")
log(f"Throats:    {pn.num_throats()}")
log("─" * 60)
log("Output files (ParaView batch compatible):")
log(f"  proj_02.vtp      — full unthresholded network")
log(f"  growthtunnel.vtp — thresholded + cleaned network")
log(f"  image.tif        — fibres volume")
log(f"  image2.tif       — pores volume")
log(f"  pore_data.csv    — pore data for GraphPad Prism")
log(f"  throat_data.csv  — throat data for GraphPad Prism")
log("=" * 60)