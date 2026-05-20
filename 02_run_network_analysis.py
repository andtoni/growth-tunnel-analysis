# =============================================================================
# Script 02 — Pore Network Analysis and Threshold Sensitivity
# =============================================================================
# Author:      Andrea Tonelli (tnland001@myuct.ac.za)
# ORCID:       https://orcid.org/0000-0002-1601-4103
# Institution: University of Cape Town
# Repository:  https://github.com/andtoni/pore-network-analysis
# Preprint:    https://dx.doi.org/10.2139/ssrn.6664677
#
# Description:
#   Loads the SNOW2 output from Script 01, builds the pore network model using
#   OpenPNM, applies minimum inscribed diameter thresholds, extracts the
#   largest connected cluster (isolating the main percolating network), and
#   exports all results for GraphPad Prism and ParaView visualisation.
#
#   Run freely with different threshold values — each unique combination saves
#   to its own subfolder so no data is ever overwritten.
#
# Third-party dependencies (MIT Licence):
#   PoreSpy  — Gostick et al. (2019) doi:10.21105/joss.01296
#   OpenPNM  — Gostick et al. (2016) doi:10.1109/MCSE.2016.49
#
# Usage:
#   python scripts/02_run_network_analysis.py
#
# Outputs (data_dir / sample_name / outputs / poreXum_throatYum /):
#   growthtunnel.vtp            — thresholded network (ParaView / Script 03)
#   proj_02.vtp                 — full unthresholded network (ParaView)
#   image.tif                   — fibre volume (ParaView)
#   image2.tif                  — pore volume (ParaView)
#   pore_data.csv               — pore diameters and volumes (GraphPad Prism)
#   throat_data.csv             — throat diameters and lengths (GraphPad Prism)
#   01_histograms_raw.png       — size distributions before filtering
#   02_histograms_filtered.png  — size distributions after filtering
# =============================================================================

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
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

# =============================================================================
# USER SETTINGS — edit these before running
# =============================================================================

# Must match sample_name used in Script 01
sample_name = "Sample_01"

# Minimum inscribed diameter threshold in micrometres.
# Pores and throats smaller than these values are removed from the network.
# Re-run with different values to perform threshold sensitivity analysis.
# Each run saves to its own subfolder — no data is overwritten.
pore_threshold   = 10  # um
throat_threshold = 10  # um

# Must match data_dir used in Script 01
data_dir = r"C:\path\to\your\output\directory"

# =============================================================================
# DO NOT EDIT BELOW THIS LINE
# =============================================================================

sample_dir = os.path.join(data_dir, sample_name)
run_label  = f"pore{pore_threshold}um_throat{throat_threshold}um"
output_dir = os.path.join(sample_dir, "outputs", run_label)
os.makedirs(output_dir, exist_ok=True)

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

def save_vtk_with_name(project, output_dir, target_name):
    """
    Saves an OpenPNM project to VTK format with a guaranteed output filename.

    OpenPNM's project_to_vtk() names output files based on internal project
    object names which are unpredictable. This function saves to an isolated
    temporary folder, captures the generated filenames, and copies the primary
    VTP file to target_name.

    Parameters
    ----------
    project    : OpenPNM project
    output_dir : str — destination directory
    target_name: str — desired filename (e.g. 'growthtunnel.vtp')

    Returns
    -------
    bool — True on success, False on failure
    """
    temp_dir = os.path.join(
        output_dir,
        f"_vtk_temp_{target_name.replace('.', '_')}"
    )
    os.makedirs(temp_dir, exist_ok=True)
    try:
        op.io.project_to_vtk(
            project=project,
            filename=os.path.join(temp_dir, "network")
        )
        generated = sorted(glob.glob(os.path.join(temp_dir, "*.vtp")))
        log(f"  Generated VTPs: {[os.path.basename(f) for f in generated]}")

        if not generated:
            log(f"  ERROR: No VTP files generated for {target_name}")
            return False

        shutil.copy(generated[0], os.path.join(output_dir, target_name))
        log(f"  Saved: {target_name} "
            f"({os.path.getsize(os.path.join(output_dir, target_name))/1e6:.1f} MB)")

        if len(generated) >= 2:
            b_name = target_name.replace('.vtp', '_b.vtp')
            shutil.copy(generated[1], os.path.join(output_dir, b_name))
            log(f"  Saved: {b_name} (secondary geometry)")

        return True

    except Exception as e:
        log(f"  ERROR saving {target_name}: {e}")
        return False
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def extract_largest_cluster(pn, log):
    """
    Retains only the largest connected pore cluster using scipy graph analysis.

    Bypasses OpenPNM's cluster models (which vary across package versions) and
    works directly on the raw throat connectivity array via scipy's
    connected_components algorithm.

    Scientific rationale: isolated pore clusters that are not connected to the
    main percolating network cannot support cell migration and are not
    functionally relevant to transmural scaffold growth. Their removal is
    consistent with biological interpretations of angio-permissive porosity.

    Reference: Tonelli A. et al. (2025) doi:10.2139/ssrn.6664677

    Parameters
    ----------
    pn  : OpenPNM network object (modified in place)
    log : logging function
    """
    n_pores = pn.num_pores()
    if n_pores == 0:
        log("  Network is empty — nothing to extract")
        return

    conns = pn['throat.conns']
    adj   = csr_matrix(
        (np.ones(len(conns)), (conns[:, 0], conns[:, 1])),
        shape=(n_pores, n_pores)
    )
    n_components, labels = connected_components(
        adj, directed=False, connection='weak'
    )

    if n_components == 1:
        log("  Single connected cluster — no trimming required")
        return

    sizes         = np.bincount(labels)
    largest_label = int(np.argmax(sizes))
    largest_size  = int(sizes[largest_label])

    log(f"  {n_components} clusters found | "
        f"Largest: {largest_size} pores "
        f"({largest_size / n_pores * 100:.1f}% of network)")
    log(f"  Removing {n_pores - largest_size} pores "
        f"across {n_components - 1} smaller cluster(s)")

    op.topotools.trim(
        network=pn,
        pores=np.where(labels != largest_label)[0]
    )
    log(f"  After trim: {pn.num_pores()} pores, {pn.num_throats()} throats")

# ── Log run parameters ────────────────────────────────────────────────────────
log("=" * 60)
log("Pore Network Analysis — Threshold Sensitivity")
log("Tonelli A. — University of Cape Town — 2025")
log("=" * 60)
log(f"Sample:           {sample_name}")
log(f"Pore threshold:   {pore_threshold} um")
log(f"Throat threshold: {throat_threshold} um")
log(f"Run label:        {run_label}")
log(f"Output:           {output_dir}")
log("=" * 60)

# ── Load SNOW2 output (from Script 01) ───────────────────────────────────────
pkl_path = os.path.join(sample_dir, "snow2_output.pkl")
if not os.path.exists(pkl_path):
    raise FileNotFoundError(
        f"SNOW2 output not found:\n  {pkl_path}\n\n"
        f"Run Script 01 first for sample: {sample_name}"
    )
log("Loading SNOW2 output...")
with open(pkl_path, "rb") as f:
    snow_output = pickle.load(f)
log("Loaded successfully")

# ── Load binarised images ─────────────────────────────────────────────────────
log("Loading binarised image arrays...")
im  = np.load(os.path.join(sample_dir, "im_pores.npy"))
im2 = np.load(os.path.join(sample_dir, "im_fibres.npy"))
log(f"Image shape: {im.shape}")

# ── Build pore network model using OpenPNM ────────────────────────────────────
# OpenPNM reference: Gostick et al. (2016) doi:10.1109/MCSE.2016.49
log("Building pore network model (OpenPNM)...")
pn = op.io.network_from_porespy(snow_output.network)
geo = op.models.collections.geometry.spheres_and_cylinders
pn.add_model_collection(geo, domain='all')
pn.regenerate_models()
log(f"Initial network: {pn.num_pores()} pores, {pn.num_throats()} throats")

# ── Label boundaries ──────────────────────────────────────────────────────────
net = ps.networks.label_boundaries(network=pn)
net = pn

# ── Plot raw size distributions ───────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=[12, 4])
ax1.hist(pn['pore.inscribed_diameter'], bins=25, edgecolor='k')
ax1.set_xlabel('Inscribed Diameter (µm)')
ax1.set_ylabel('Count')
ax1.set_title(f'{sample_name} — Pore Diameter (unfiltered)')
ax2.hist(pn['throat.inscribed_diameter'], bins=25, edgecolor='k')
ax2.set_xlabel('Inscribed Diameter (µm)')
ax2.set_ylabel('Count')
ax2.set_title(f'{sample_name} — Throat Diameter (unfiltered)')
fig.tight_layout()
fig.savefig(os.path.join(output_dir, "01_histograms_raw.png"), dpi=150)
plt.close()
log("Saved: 01_histograms_raw.png")

# ── Save unthresholded network → proj_02.vtp ─────────────────────────────────
# Saved BEFORE any trimming — represents the full extracted network
log("Saving unthresholded network → proj_02.vtp")
save_vtk_with_name(pn.project, output_dir, "proj_02.vtp")

# ── Apply minimum throat diameter threshold ───────────────────────────────────
log(f"Trimming throats with inscribed diameter < {throat_threshold} µm...")
mask = net["throat.inscribed_diameter"] < throat_threshold
op.topotools.trim(pn, throats=mask)
log(f"After throat trim: {pn.num_pores()} pores, {pn.num_throats()} throats")

# ── Apply minimum pore diameter threshold ─────────────────────────────────────
log(f"Trimming pores with inscribed diameter < {pore_threshold} µm...")
mask = net["pore.inscribed_diameter"] < pore_threshold
op.topotools.trim(pn, pores=mask)
log(f"After pore trim: {pn.num_pores()} pores, {pn.num_throats()} throats")

# ── Extract largest connected cluster (Pass 1) ────────────────────────────────
# Removes isolated pore islands not connected to the main percolating network
log("Extracting largest connected cluster (Pass 1)...")
extract_largest_cluster(pn, log)

# ── Iterative network health check ───────────────────────────────────────────
# Each trimming step can create new isolated pores — iterate until stable
log("Running iterative health check...")
for pass_num in range(1, 11):
    h             = op.utils.check_network_health(pn)
    pores_to_trim = np.union1d(h['isolated_pores'], h['disconnected_pores'])
    if len(pores_to_trim) == 0:
        log(f"Network healthy after {pass_num} pass(es)")
        break
    log(f"Pass {pass_num}: trimming {len(pores_to_trim)} pores...")
    op.topotools.trim(network=pn, pores=pores_to_trim)
    log(f"  Remaining: {pn.num_pores()} pores, {pn.num_throats()} throats")

# ── Extract largest cluster again (Pass 2) ────────────────────────────────────
# Health check trimming can re-fragment the network
log("Final cluster extraction (Pass 2)...")
extract_largest_cluster(pn, log)

# ── Verify single connected network ──────────────────────────────────────────
conns_f = pn['throat.conns']
n_f     = pn.num_pores()
adj_f   = csr_matrix(
    (np.ones(len(conns_f)), (conns_f[:, 0], conns_f[:, 1])),
    shape=(n_f, n_f)
)
n_comps_f, _ = connected_components(adj_f, directed=False, connection='weak')
if n_comps_f == 1:
    log(f"Verified: single connected network — "
        f"{pn.num_pores()} pores, {pn.num_throats()} throats")
else:
    log(f"WARNING: {n_comps_f} clusters remain — inspect visually in ParaView")

# ── Plot filtered size distributions ─────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=[12, 4])
ax1.hist(pn['pore.inscribed_diameter'], bins=25, edgecolor='k')
ax1.set_xlabel('Inscribed Diameter (µm)')
ax1.set_ylabel('Count')
ax1.set_title(f'{sample_name} — Pore Diameter ({run_label})')
ax2.hist(pn['throat.inscribed_diameter'], bins=25, edgecolor='k')
ax2.set_xlabel('Inscribed Diameter (µm)')
ax2.set_ylabel('Count')
ax2.set_title(f'{sample_name} — Throat Diameter ({run_label})')
fig.tight_layout()
fig.savefig(os.path.join(output_dir, "02_histograms_filtered.png"), dpi=150)
plt.close()
log("Saved: 02_histograms_filtered.png")

# ── Export CSVs for GraphPad Prism ────────────────────────────────────────────
log("Exporting CSVs for GraphPad Prism...")
pd.DataFrame({
    'pore_diameter_um': pn['pore.inscribed_diameter'],
    'pore_volume':      pn['pore.volume'],
}).to_csv(os.path.join(output_dir, "pore_data.csv"), index=False)

pd.DataFrame({
    'throat_diameter_um': pn['throat.inscribed_diameter'],
    'throat_length_um':   pn['throat.length'],
}).to_csv(os.path.join(output_dir, "throat_data.csv"), index=False)
log("Saved: pore_data.csv and throat_data.csv")

# ── Save thresholded network → growthtunnel.vtp ───────────────────────────────
# Saved AFTER all trimming and cluster extraction
log("Saving thresholded network → growthtunnel.vtp")
save_vtk_with_name(pn.project, output_dir, "growthtunnel.vtp")

# ── Save aligned image volumes for ParaView ───────────────────────────────────
# NOTE: image.tif = fibres | image2.tif = pores
# These exact filenames are required by Script 03 (ParaView batch)
log("Saving aligned image volumes for ParaView...")
im_aligned  = ps.tools.align_image_with_openpnm(im)
im2_aligned = ps.tools.align_image_with_openpnm(im2)
imageio.volsave(
    os.path.join(output_dir, "image.tif"),
    np.array(im2_aligned, dtype=np.int8)   # fibres
)
imageio.volsave(
    os.path.join(output_dir, "image2.tif"),
    np.array(im_aligned, dtype=np.int8)    # pores
)
log("Saved: image.tif (fibres) and image2.tif (pores)")

# ── Verify all ParaView-required files are present ───────────────────────────
log("Verifying ParaView output files...")
required = ["growthtunnel.vtp", "proj_02.vtp", "image.tif", "image2.tif"]
all_ok   = True
for fname in required:
    fpath = os.path.join(output_dir, fname)
    if os.path.exists(fpath):
        log(f"  OK  {fname}")
    else:
        log(f"  MISSING  {fname}")
        all_ok = False

if all_ok:
    log("All files present — Script 03 will process this run without skipping")
else:
    log("WARNING: Missing files — Script 03 will skip this run")

# ── Summary ───────────────────────────────────────────────────────────────────
porosity = ps.metrics.porosity(im_aligned) * 100
log("=" * 60)
log(f"Analysis complete:  {sample_name} / {run_label}")
log(f"Porosity:           {porosity:.2f}%")
log(f"Pores retained:     {pn.num_pores()}")
log(f"Throats retained:   {pn.num_throats()}")
log(f"Output:             {output_dir}")
log("")
log("Next step: run  03_run_paraview_batch.py  via pvpython")
log("=" * 60)
