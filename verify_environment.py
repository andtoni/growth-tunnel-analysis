# =============================================================================
# verify_environment.py — Confirm all dependencies are installed correctly
# =============================================================================
# Author:      Andrea Tonelli (tnland001@myuct.ac.za)
# ORCID:       https://orcid.org/0000-0002-1601-4103
# Repository:  https://github.com/andtoni/growth-tunnel-analysis
#
# Run this before any pipeline script to verify your Python environment.
#
# Usage:
#   python verify_environment.py
# =============================================================================

import sys

print("=" * 60)
print("Pore Network Analysis Pipeline — Environment Verification")
print("Tonelli A. — University of Cape Town — 2025")
print("https://github.com/andtoni/growth-tunnel-analysis")
print("=" * 60)

errors   = []
warnings = []

# Python version check
major, minor = sys.version_info[:2]
ver_str = f"Python {major}.{minor}"
if major == 3 and minor >= 11:
    print(f"{ver_str:<20} OK")
else:
    print(f"{ver_str:<20} WARNING — Python 3.11+ recommended")
    warnings.append(f"{ver_str} detected; Python 3.11+ is recommended")

# Required packages with licence info
packages = [
    # (import_name, display_name, required_by, licence)
    ("numpy",      "numpy",        "Scripts 01-04", "BSD-3-Clause"),
    ("scipy",      "scipy",        "Scripts 01-04", "BSD-3-Clause"),
    ("skimage",    "scikit-image", "Scripts 01-02", "BSD-3-Clause"),
    ("matplotlib", "matplotlib",   "Scripts 01-02", "PSF"),
    ("porespy",    "porespy",      "Script 01",
     "MIT — Gostick et al. 2019 doi:10.21105/joss.01296"),
    ("openpnm",    "openpnm",      "Scripts 02-04",
     "MIT — Gostick et al. 2016 doi:10.1109/MCSE.2016.49"),
    ("imageio",    "imageio",      "Script 02",     "BSD-2-Clause"),
    ("pandas",     "pandas",       "Scripts 02-05", "BSD-3-Clause"),
    ("tqdm",       "tqdm",         "Scripts 01-02", "MIT/MPLv2"),
    ("openpyxl",   "openpyxl",     "Scripts 04-05", "MIT"),
]

print()
print(f"  {'Package':<16} {'Version':<12} {'Required by':<16} {'Licence'}")
print(f"  {'-'*16} {'-'*12} {'-'*16} {'-'*40}")

for import_name, display_name, required_by, licence in packages:
    try:
        mod = __import__(import_name)
        ver = getattr(mod, "__version__", "installed")
        print(f"  {display_name:<16} {ver:<12} {required_by:<16} {licence}")
    except ImportError:
        print(f"  {display_name:<16} {'MISSING':<12} {required_by:<16} {licence}")
        errors.append(display_name)

# Optional packages
print()
optional = [
    ("pypardiso", "pypardiso", "optional", "MIT",
     "speeds up OpenPNM solver"),
    ("networkx",  "networkx",  "Script 04 (optional)", "BSD-3-Clause",
     "mean shortest path length computation"),
]

for import_name, display_name, required_by, licence, note in optional:
    try:
        mod = __import__(import_name)
        ver = getattr(mod, "__version__", "installed")
        print(f"  {display_name:<16} {ver:<12} {required_by:<16} {note}")
    except ImportError:
        print(f"  {display_name:<16} {'not installed':<12} {required_by:<16} {note}")
        print(f"  {'':16} Install: uv pip install {import_name}")

print()
print("=" * 60)

if errors:
    print(f"FAILED — {len(errors)} missing package(s): {', '.join(errors)}")
    print()
    print("Install all dependencies:")
    print("  uv pip install -r requirements.txt")
    sys.exit(1)
elif warnings:
    print(f"PASSED with {len(warnings)} warning(s):")
    for w in warnings:
        print(f"  - {w}")
    print()
    print("Scripts can still run — see README for details")
else:
    print("ALL CHECKS PASSED — environment is ready")
    print()
    print("Run scripts in this order:")
    print("  1.  python 01_run_snow2.py")
    print("  2.  python 02_run_network_analysis.py")
    print("  3.  pvpython 03_run_paraview_batch.py")
    print("  4.  python 04_quantification_export.py")
    print("  5.  python 05_pnm_data_export.py")

print()
print("Third-party attributions:")
print("  PoreSpy  — Gostick et al. (2019) doi:10.21105/joss.01296  [MIT]")
print("  OpenPNM  — Gostick et al. (2016) doi:10.1109/MCSE.2016.49 [MIT]")
print("  ParaView — Kitware Inc. https://www.paraview.org           [BSD-3]")
print("=" * 60)
