# =============================================================================
# verify_environment.py — Confirm all dependencies are installed correctly
# =============================================================================
# Author:      Andrea Tonelli (tnland001@myuct.ac.za)
# ORCID:       https://orcid.org/0000-0002-1601-4103
# Repository:  https://github.com/andtoni/pore-network-analysis
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
print("https://github.com/andtoni/pore-network-analysis")
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
    # (import_name, display_name, licence)
    ("numpy",      "numpy",        "BSD-3-Clause"),
    ("scipy",      "scipy",        "BSD-3-Clause"),
    ("skimage",    "scikit-image", "BSD-3-Clause"),
    ("matplotlib", "matplotlib",   "PSF"),
    ("porespy",    "porespy",      "MIT — Gostick et al. 2019 doi:10.21105/joss.01296"),
    ("openpnm",    "openpnm",      "MIT — Gostick et al. 2016 doi:10.1109/MCSE.2016.49"),
    ("imageio",    "imageio",      "BSD-2-Clause"),
    ("pandas",     "pandas",       "BSD-3-Clause"),
    ("tqdm",       "tqdm",         "MIT/MPLv2"),
]

print()
print(f"  {'Package':<16} {'Version':<12} {'Licence'}")
print(f"  {'-'*16} {'-'*12} {'-'*45}")

for import_name, display_name, licence in packages:
    try:
        mod = __import__(import_name)
        ver = getattr(mod, "__version__", "stdlib")
        print(f"  {display_name:<16} {ver:<12} {licence}")
    except ImportError:
        print(f"  {display_name:<16} {'MISSING':<12} {licence}")
        errors.append(display_name)

# Optional — pypardiso (speeds up OpenPNM)
print()
try:
    import pypardiso
    ver = getattr(pypardiso, "__version__", "installed")
    print(f"  {'pypardiso':<16} {ver:<12} MIT  (optional — solver acceleration active)")
except ImportError:
    print(f"  {'pypardiso':<16} {'not installed':<12} optional")
    print(f"  {'':16} Install with: pip install pypardiso")

print()
print("=" * 60)

if errors:
    print(f"FAILED — {len(errors)} missing package(s): {', '.join(errors)}")
    print()
    print("To install all dependencies:")
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
    print("  1.  python scripts/01_run_snow2.py")
    print("  2.  python scripts/02_run_network_analysis.py")
    print("  3.  pvpython scripts/03_run_paraview_batch.py")

print("=" * 60)
print()
print("Third-party attributions:")
print("  PoreSpy  — Gostick et al. (2019) doi:10.21105/joss.01296  [MIT]")
print("  OpenPNM  — Gostick et al. (2016) doi:10.1109/MCSE.2016.49 [MIT]")
print("  ParaView — Kitware Inc. https://www.paraview.org           [BSD-3]")
print("=" * 60)
