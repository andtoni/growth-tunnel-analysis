from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATERIAL = Path("/home/andto/Nextcloud/Work/PhD/Projects/growth-tunnel-analysis")

REQUIRED_REPO_PATHS = [
    "AGENTS.md",
    "README.md",
    "REBUILD.md",
    "RUNS.jsonl",
    "STATE.md",
    "project.yml",
    "pyproject.toml",
    "Makefile",
    "docs/START_HERE.md",
    "docs/DATA_LEDGER.md",
    "docs/SCRIPT_INVENTORY.md",
    "01_run_snow2.py",
    "02_run_network_analysis.py",
    "03_run_paraview_batch.py",
    "04_quantification_export.py",
    "05_pnm_data_export.py",
    "verify_environment.py",
    "scripts/legacy/confocal-porosity/confocal_porosity.py",
    "scripts/legacy/imagej/image_process.ijm",
    "scripts/legacy/imagej/3D Paper-SEM.ijm",
    "scripts/legacy/mechanical/InstronAnalysis.bas",
    "scripts/legacy/stablePNM/04_quantification_export.py",
    "figures/source/paraview/p16SR.legacy-system.pvsm",
]

REQUIRED_MATERIAL_PATHS = [
    "Original/transmural-space-characterisation-3d-analysis-paper",
    "Original/paper-2-manuscript-and-extra-analysis",
    "Original/paper-2-manuscript-and-extra-analysis/Extra Analysis/Mechanical Data Summary.xlsx",
    "Original/paper-2-manuscript-and-extra-analysis/Extra Analysis/Mechanical",
    "Original/paper-2-manuscript-and-extra-analysis/Extra Analysis/Table for Mechanical Properties.docx",
    "Original/paper-2-manuscript-and-extra-analysis/Extra Analysis/mechanical_anisotropy_svg_table.svg",
    "Original/transmural-space-characterisation-3d-analysis-paper/codeoutput/Pore_Network_Quantification.xlsx",
    "Original/transmural-space-characterisation-3d-analysis-paper/codeoutput/PNM_Prism_Grouped.xlsx",
    "Original/transmural-space-characterisation-3d-analysis-paper/Porosity/Confocal/porosity_output/porosity_results.xlsx",
    "Manuscript/README.md",
    "Manuscript/mtbio-d-26-02595-revision-package-2026-06",
    "Manuscript/mtbio-d-26-02595-revision-package-2026-06/paper2_v3_clean.docx",
    "Manuscript/mtbio-d-26-02595-revision-package-2026-06/paper2_v3_tracked.docx",
    "Manuscript/mtbio-d-26-02595-revision-package-2026-06/detailedreviewerresponses_v3.docx",
    "Manuscript/mtbio-d-26-02595-revision-package-2026-06/coverletter_v3.docx",
    "Manuscript/mtbio-d-26-02595-revision-package-2026-06/Reviewer Comments Original.docx",
    "Manuscript/mtbio-d-26-02595-revision-package-2026-06/Final Figure Outputs/Fig1.pdf",
    "Manuscript/mtbio-d-26-02595-revision-package-2026-06/RAW Data/Fig1data_mechanical.xlsx",
    "Manuscript/mtbio-d-26-02595-revision-package-2026-06/Project2.prism",
    "Manuscript/manifests/mtbio-d-26-02595-revision-package-2026-06.sha256",
    "_legacy/system-coding-mirror/stablePNM",
    "_legacy/system-coding-mirror/confocalPorosity",
    "_legacy/system-coding-mirror/Great Scripts",
]

FORBIDDEN_TRACKED_SUFFIXES = {
    ".czi",
    ".docx",
    ".emf",
    ".lif",
    ".mp4",
    ".npy",
    ".pdf",
    ".pkl",
    ".prism",
    ".raw",
    ".tif",
    ".tiff",
    ".vtp",
    ".vti",
    ".xlsx",
}

ALLOWED_TRACKED_SUFFIXES = {
    "pore_data_example.csv",
    "throat_data_example.csv",
    "figures/source/paraview/p16SR.legacy-system.pvsm",
}


def ok_path(path: Path, label: str) -> bool:
    exists = path.exists()
    print(f"{'ok' if exists else 'missing'} {label}: {path}")
    return exists


def check_runs() -> bool:
    path = ROOT / "RUNS.jsonl"
    ok = True
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError as exc:
            print(f"bad RUNS.jsonl line {line_no}: {exc}")
            ok = False
    if ok:
        print("ok RUNS.jsonl")
    return ok


def git_lines(args: list[str]) -> list[str]:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        print(result.stderr.strip())
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def check_remote() -> bool:
    remotes = git_lines(["git", "remote", "-v"])
    bad = [line for line in remotes if "github.com" in line.lower()]
    for line in remotes:
        print(f"remote {line}")
    if bad:
        print("forbidden GitHub remote detected")
        return False
    expected = "https://git.stilltarn.com/admin1/growth-tunnel-analysis.git"
    ok = any(expected in line for line in remotes)
    print(f"{'ok' if ok else 'missing'} Forgejo origin")
    return ok


def check_tracked_data() -> bool:
    tracked = git_lines(["git", "ls-files"])
    bad: list[str] = []
    for path in tracked:
        if path in ALLOWED_TRACKED_SUFFIXES:
            continue
        suffix = Path(path).suffix.lower()
        if suffix in FORBIDDEN_TRACKED_SUFFIXES:
            bad.append(path)
    if bad:
        print("forbidden generated/raw artefacts tracked by Git:")
        for path in bad:
            print(f"  {path}")
        return False
    print("ok no forbidden generated/raw artefacts tracked")
    return True


def main() -> int:
    checks: list[bool] = []
    checks.extend(ok_path(ROOT / path, "repo") for path in REQUIRED_REPO_PATHS)
    checks.extend(ok_path(MATERIAL / path, "material") for path in REQUIRED_MATERIAL_PATHS)
    checks.append(check_runs())
    checks.append(check_remote())
    checks.append(check_tracked_data())
    return 0 if all(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
