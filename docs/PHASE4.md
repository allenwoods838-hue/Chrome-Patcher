# Phase 4 — Diagnostic-Only Chrome GPU Launch Matrix

Phase 4 only collects evidence. It does not patch, re-sign, install LaunchAgents, or modify system graphics.

Profiles:
- normal: baseline
- desktop: --use-gl=desktop
- angle-gl: --use-gl=angle --use-angle=gl
- angle-metal: --use-gl=angle --use-angle=metal
- disable-gpu-sandbox: sandbox diagnostic only

Each run uses an isolated temporary Chrome profile and opens chrome://gpu. Existing Chrome processes are asked to quit before each run.

Run from the repository root:
    python3 phase4_diagnostic.py
    python3 tests/gpu_status.py

Single profile:
    python3 phase4_diagnostic.py --profiles angle-gl

Results: ~/Desktop/chrome-patcher-baseline/phase4/

A successful process launch is not proof of GPU acceleration. Later phases require a stable GPU process plus hardware-backed compositing/rasterization and working GL/WebGL or an equivalent validated Chromium path.

If Phase 3 reports unknown device while macOS reports 0x1626, the detector must be fixed before interpreting Phase 4.
