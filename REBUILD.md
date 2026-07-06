# Rebuild - Growth Tunnel Analysis

From this workstation:

```bash
cd /home/andto/coding/papers/growth-tunnel-analysis
uv sync
make check
```

Install the full pore-network pipeline dependencies only when you need to run the modelling scripts:

```bash
uv sync --extra pipeline
uv run --extra pipeline python verify_environment.py
```

The raw data and generated paper artefacts are external to Git:

```bash
ls "/home/andto/Nextcloud/Work/PhD/Projects/growth-tunnel-analysis"
```

Do not restore from the old `Archive/OneDrive` paths. They were moved into the clean project directory on 2026-07-06.
