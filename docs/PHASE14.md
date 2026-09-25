# Phase 14 — Runtime ANGLE/GL Decision Capture

Phase 14 moves from static string reconnaissance to runtime evidence on the exact installed Chrome build.

It launches Chrome with isolated temporary profiles and captures stderr with verbose GPU/GL/ANGLE logging. It also records a GPU-process command-line snapshot and prints only lines mentioning ANGLE, EGL, OpenGL, Metal, GPU-process startup, SharedImage, or related failures.

Profiles:

- `normal`
- `angle-gl` — `--use-gl=angle --use-angle=gl`
- `angle-metal` — `--use-gl=angle --use-angle=metal`

Run:

    cd ~/Chrome-Patcher
    python3 phase14_runtime_gl.py

Optional:

    python3 phase14_runtime_gl.py --profiles normal angle-gl --duration 10 --limit 40

Results are written to:

    ~/Desktop/chrome-patcher-baseline/phase14/

This phase is diagnostic-only. It does not patch, sign, replace, or modify Chrome. The isolated profiles are created under the Phase 14 evidence directory.

Important: successful process launch is not proof of acceleration. The useful evidence is the backend selected, GPU-process initialization result, context-loss/error path, and any explicit ANGLE/GL implementation decision.

The next step is to use the captured runtime evidence to identify one concrete Intel-relevant gate. No patch bytes should be added until that gate is tied to a verified x86_64 code path on the exact Framework SHA-256.
