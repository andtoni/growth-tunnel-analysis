# =============================================================================
# generate_pvsm.py — ParaView State File Generator
# =============================================================================
# Author:      Andrea Tonelli (tnland001@myuct.ac.za)
# ORCID:       https://orcid.org/0000-0002-1601-4103
# Institution: University of Cape Town
# Repository:  https://github.com/andtoni/growth-tunnel-analysis
#
# Description:
#   Reads the reference PVSM template (p16.pvsm) and generates one PVSM file
#   per sample. All pipeline settings are preserved exactly from the template:
#     - Glyph (pore spheres) and Tube (throat tubes) filters + colour maps
#     - Box Clip filter bounds and orientation
#     - CT fibre threshold (Threshold filter, 55–252)
#     - OSPRay lighting, white background, parallel projection
#     - Camera position and focal point
#     - Ruler / scale bar
#
#   Only the file paths are changed: VTP path and all TIFF slice paths.
#   TIFF slices are discovered automatically by scanning each sample's folder.
#
# Usage:
#   python generate_pvsm.py
#   Then in ParaView: File → Load State → select the generated .pvsm file
#
# Requirements:
#   Python 3.x standard library only (no extra packages)
#
# Output:
#   One .pvsm file per sample saved into OUTPUT_DIR
# =============================================================================

import os
import re
import glob

# =============================================================================
# USER SETTINGS
# =============================================================================

# Full path to the reference template PVSM (p16.pvsm)
# Use forward slashes or raw strings for Windows paths
TEMPLATE_PVSM = r"C:\Users\andto\OneDrive\Desktop\University\PhD\DATA\Transmural Space Characterisation\3D Analysis Paper\codeoutput\Full Networks\p16.pvsm"

# Directory containing all VTP files and TIFF subfolders
# This folder should contain:
#   p16.vtp, p18.vtp, p20.vtp ...    ← VTP pore network files
#   SR-p16-REV\, SR-p18-REV\, ...   ← TIFF series subfolders (one per sample)
BASE_DIR = r"C:\Users\andto\OneDrive\Desktop\University\PhD\DATA\Transmural Space Characterisation\3D Analysis Paper\codeoutput\Full Networks"

# Output directory for generated PVSM files (can be same as BASE_DIR)
OUTPUT_DIR = BASE_DIR

# Samples to process — each entry is:
#   (sample_label, vtp_filename, tiff_subfolder_name)
#
# sample_label    : used in the output PVSM filename (e.g. "p16" → "p16.pvsm")
# vtp_filename    : VTP file name inside BASE_DIR (e.g. "p16.vtp")
# tiff_subfolder  : subfolder inside BASE_DIR containing the TIFF slices
#
# Example with three samples:
SAMPLES = [
    ("p16", "16.vtp", "SR-p16-REV"),
    ("p18", "18.vtp", "SR-p18-REV"),
    ("p20", "20.vtp", "SR-p20-REV"),
]

# TIFF file extension to search for (case-insensitive)
TIFF_EXTENSION = ".tiff"   # change to ".tif" if your files use that extension

# =============================================================================
# DO NOT EDIT BELOW THIS LINE
# =============================================================================

def discover_tiff_files(folder_path, extension=".tiff"):
    """
    Scan a folder for TIFF files and return them sorted by filename.
    Returns a list of full absolute paths.
    """
    pattern = os.path.join(folder_path, f"*{extension}")
    files = sorted(glob.glob(pattern, recursive=False))
    # Also try uppercase extension
    if not files:
        pattern_upper = os.path.join(folder_path, f"*{extension.upper()}")
        files = sorted(glob.glob(pattern_upper, recursive=False))
    return files


def build_filenames_xml(file_list, property_id):
    """
    Build the XML <Property name="FileNames"> block for a TIFFSeriesReader.
    property_id: the proxy id string, e.g. "15579"
    """
    n = len(file_list)
    lines = []
    lines.append(
        f'      <Property name="FileNames" id="{property_id}.FileNames"'
        f' number_of_elements="{n}">'
    )
    for i, fpath in enumerate(file_list):
        lines.append(f'        <Element index="{i}" value="{fpath}"/>')
    lines.append(f'        <Domain name="files" id="{property_id}.FileNames.files"/>')
    lines.append(f'      </Property>')
    return "\n".join(lines)


def replace_tiff_filenames(content, tiff_reader_id, new_file_list):
    """
    Replace the FileNames property block for the TIFFSeriesReader proxy.
    Handles any number of TIFF files in the template.
    """
    # Match the FileNames property block for this specific proxy id
    pattern = (
        r'(<Property name="FileNames" id="' + re.escape(tiff_reader_id) + r'\.FileNames"'
        r'[^>]+>)'
        r'(.*?)'
        r'(</Property>)'
    )
    new_block = build_filenames_xml(new_file_list, tiff_reader_id)

    repl = lambda m, b=new_block: b
    result = re.sub(pattern, repl, content, count=1, flags=re.DOTALL)
    if result == content:
        print(f"  WARNING: Could not find FileNames property for id={tiff_reader_id}")
    return result


def replace_vtp_path(content, vtp_reader_id, new_vtp_path):
    """
    Replace the FileName and FileNameInfo values for the XMLPolyDataReader proxy.
    """
    # Replace both FileName and FileNameInfo properties
    for prop_name in ["FileName", "FileNameInfo"]:
        pattern = (
            r'(<Property name="' + re.escape(prop_name) + r'" id="'
            + re.escape(vtp_reader_id) + r'\.' + re.escape(prop_name) + r'"[^>]+>'
            r'\s*<Element index="0" value=")[^"]+(")'
        )
        repl = lambda m, p=new_vtp_path: m.group(1) + p + m.group(2)
        result = re.sub(pattern, repl, content, count=1, flags=re.DOTALL)
        if result != content:
            content = result
        else:
            print(f"  WARNING: Could not replace {prop_name} for id={vtp_reader_id}")
    return content


def find_proxy_id(content, group, proxy_type):
    """Find the first proxy id matching the given group and type."""
    m = re.search(
        r'<Proxy group="' + re.escape(group) + r'" type="' + re.escape(proxy_type) + r'" id="(\d+)"',
        content
    )
    return m.group(1) if m else None


# =============================================================================
# MAIN
# =============================================================================

print("=" * 60)
print("generate_pvsm.py — ParaView State File Generator")
print("Tonelli A. — University of Cape Town — 2025")
print("=" * 60)

# Load template
if not os.path.exists(TEMPLATE_PVSM):
    raise FileNotFoundError(
        f"Template PVSM not found:\n  {TEMPLATE_PVSM}\n"
        "Check TEMPLATE_PVSM path in user settings."
    )

with open(TEMPLATE_PVSM, 'r', encoding='utf-8', errors='replace') as f:
    template = f.read()

print(f"Template: {TEMPLATE_PVSM}")
print(f"Base dir: {BASE_DIR}")
print()

# Auto-detect proxy IDs from template
vtp_reader_id  = find_proxy_id(template, "sources", "XMLPolyDataReader")
tiff_reader_id = find_proxy_id(template, "sources", "TIFFSeriesReader")

if not vtp_reader_id:
    raise ValueError("Could not find XMLPolyDataReader proxy in template PVSM")
if not tiff_reader_id:
    raise ValueError("Could not find TIFFSeriesReader proxy in template PVSM")

print(f"Detected VTP  reader proxy id : {vtp_reader_id}")
print(f"Detected TIFF reader proxy id : {tiff_reader_id}")
print()

# ── List what is actually in BASE_DIR to help diagnose name mismatches ────────
print("Files found in BASE_DIR:")
if os.path.isdir(BASE_DIR):
    vtp_found  = sorted([f for f in os.listdir(BASE_DIR) if f.lower().endswith(".vtp")])
    tiff_dirs  = sorted([f for f in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, f))])
    if vtp_found:
        print("  VTP files  :", vtp_found)
    else:
        print("  VTP files  : (none found — check BASE_DIR)")
    if tiff_dirs:
        print("  Subfolders :", tiff_dirs)
    else:
        print("  Subfolders : (none found)")
else:
    print(f"  WARNING: BASE_DIR does not exist: {BASE_DIR}")
print()

# Process each sample
n_ok   = 0
n_fail = 0

for sample_label, vtp_filename, tiff_subfolder in SAMPLES:

    print(f"--- Sample: {sample_label} ---")

    # Build absolute paths
    vtp_path  = os.path.join(BASE_DIR, vtp_filename)
    tiff_dir  = os.path.join(BASE_DIR, tiff_subfolder)
    out_pvsm  = os.path.join(OUTPUT_DIR, f"{sample_label}.pvsm")

    # Validate VTP file exists
    if not os.path.exists(vtp_path):
        print(f"  SKIP — VTP not found: {vtp_path}")
        n_fail += 1
        continue

    # Validate TIFF directory exists
    if not os.path.isdir(tiff_dir):
        print(f"  SKIP — TIFF folder not found: {tiff_dir}")
        n_fail += 1
        continue

    # Discover TIFF files
    tiff_files = discover_tiff_files(tiff_dir, TIFF_EXTENSION)

    if not tiff_files:
        print(f"  SKIP — No *{TIFF_EXTENSION} files found in: {tiff_dir}")
        n_fail += 1
        continue

    print(f"  VTP:  {vtp_path}")
    print(f"  TIFF: {tiff_dir}  ({len(tiff_files)} slices)")

    # Start from the template and apply replacements
    out = template

    # 1. Replace VTP path
    out = replace_vtp_path(out, vtp_reader_id, vtp_path)

    # 2. Replace TIFF FileNames
    out = replace_tiff_filenames(out, tiff_reader_id, tiff_files)

    # 3. Save output PVSM
    with open(out_pvsm, 'w', encoding='utf-8', errors='replace') as f:
        f.write(out)

    print(f"  Saved: {out_pvsm}")
    n_ok += 1

# Summary
print()
print("=" * 60)
print("COMPLETE")
print(f"  Generated : {n_ok}")
print(f"  Skipped   : {n_fail}")
print()
print("To open in ParaView:")
print("  File → Load State → select the generated .pvsm file")
print("=" * 60)
