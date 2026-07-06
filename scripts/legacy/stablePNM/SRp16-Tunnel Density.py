import matplotlib
matplotlib.use('Agg')  # Prevents plot windows blocking execution

import porespy as ps
import openpnm as op
import numpy as np
import matplotlib.pyplot as plt
import sys
import skimage as ski
import imageio.v2 as imageio
import scipy.ndimage as spim

from skimage.io import imread_collection
from matplotlib.pyplot import subplots
from porespy.filters import find_peaks, trim_saddle_points, trim_nearby_peaks
from porespy.tools import randomize_colors
from skimage.segmentation import watershed
from datetime import datetime

np.set_printoptions(threshold=sys.maxsize)
ps.settings.verbosity = 1  # Show porespy progress

# ── Helper: timestamped logging ──────────────────────────────────────────────
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    sys.stdout.flush()

# ── Output folder ─────────────────────────────────────────────────────────────
import os
output_dir = "outputs"
os.makedirs(output_dir, exist_ok=True)

# ── Load Images ───────────────────────────────────────────────────────────────
log("Loading images...")
seq = imread_collection("C:\\Users\\andto\\OneDrive\\Desktop\\University\\PhD\\DATA\\Transmural Space Characterisation\\3D Analysis Paper\\SR-Pel16\\SR-p16-REV\\*.tiff")
log(f"Loaded {len(seq)} slices")

fig, ax = subplots(figsize=[5, 5])
ax.imshow(seq[0])
fig.savefig(f"{output_dir}/01_first_slice.png", dpi=150)
plt.close()
log("Saved: 01_first_slice.png")

# ── Convert to 3D ─────────────────────────────────────────────────────────────
log("Converting to 3D stack...")
im3d = np.zeros([*seq[0].shape, len(seq)])
for i, im in enumerate(seq):
    im3d[..., i] = im
log(f"Stack shape: {im3d.shape}")
log(f"Stack RAM usage: {im3d.nbytes / 1e9:.2f} GB")

fig, ax = subplots(figsize=[5, 5])
ax.imshow(ps.visualization.show_planes(im3d))
fig.savefig(f"{output_dir}/02_show_planes.png", dpi=150)
plt.close()
log("Saved: 02_show_planes.png")

# ── Binarise ──────────────────────────────────────────────────────────────────
log("Binarising...")

fig, ax = subplots(figsize=[5, 5])
ax.hist(im3d.flatten(), bins=25, edgecolor='k')
ax.set_title('Intensity Histogram')
fig.savefig(f"{output_dir}/03_histogram.png", dpi=150)
plt.close()
log("Saved: 03_histogram.png")

im  = im3d < 50   # pores
im2 = im3d > 50   # fibres

fig, ax = subplots(figsize=[5, 5])
ax.imshow(ps.visualization.sem(im, axis=2))
fig.savefig(f"{output_dir}/04_sem_view.png", dpi=150)
plt.close()
log("Saved: 04_sem_view.png")

porosity = ps.metrics.porosity(im) * 100
log(f"Porosity: {porosity:.2f}%")

# ── SNOW2 Algorithm ───────────────────────────────────────────────────────────
voxel = 0.54
log("Running SNOW2 algorithm — this is the slowest step, please wait...")
snow_output = ps.networks.snow2(im, voxel_size=voxel)
log("SNOW2 complete!")

import pickle
log("Saving SNOW2 output to disk...")
with open(r"C:\Users\andto\OneDrive\Desktop\University\Coding\stablePNM\outputs\snow2_output.pkl", "wb") as f:
    pickle.dump(snow_output, f)
log("Saved: snow2_output.pkl")
