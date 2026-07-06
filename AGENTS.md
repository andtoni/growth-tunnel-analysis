# AGENTS.md - Growth Tunnel Analysis

Purpose: reproducible paper/code project for the pore-network, confocal porosity, mechanical testing, and multimodality scaffold-characterisation workflow associated with the Paper 2 / growth-tunnel-analysis manuscript.

Hard rules:
- Use `uv` for Python. Never use pip, conda, poetry, pipenv, virtualenv, or `python -m venv`.
- Forgejo is canonical: `https://git.stilltarn.com/admin1/growth-tunnel-analysis.git`.
- Do not add GitHub remotes.
- Do not commit raw micro-CT stacks, CZI files, `.raw` Instron exports, generated SNOW2 `.pkl`, VTK/VTP/VTI volumes, Prism files, DOCX/PDF exports, or secrets.
- Project material lives at `/home/andto/Nextcloud/Work/PhD/Projects/growth-tunnel-analysis`.
- Treat root scripts `01_*` to `05_*`, legacy scripts under `scripts/legacy/`, editable SVG/PVSM sources, and documentation as source.
- Treat Excel/DOCX/Prism/EMF/PNG/TIFF outputs in the material folder as artefacts unless explicitly promoted to source.
- Record material changes in `RUNS.jsonl`.

Standard re-entry:

```bash
cd /home/andto/coding/papers/growth-tunnel-analysis
make status
make check
sed -n '1,220p' docs/START_HERE.md
```
