# Phase 15 — Compact Intel ANGLE/EGL Gate Capture

Phase 15 is a user-friendly follow-up to Phase 14. It runs only the two useful ANGLE tests, increases logging specifically around EGL/ANGLE initialization, filters the common profile noise, and prints a compact result.

Profiles:
- angle-gl
- angle-metal

The script records the exact installed Chrome version and Framework SHA-256, then saves full logs under:

    ~/Desktop/chrome-patcher-baseline/phase15/

The concise report is:

    ~/Desktop/chrome-patcher-baseline/phase15/report.txt

### What the current evidence already shows

On the tested Chrome 154 build, --use-gl=angle --use-angle=gl is rejected because Chromium reports that (gl=egl-angle,angle=opengl) is not in its allowed implementations; only (gl=egl-angle,angle=metal) is allowed in that run.

The angle-metal test reaches the allowed backend but fails during EGL initialization and the GPU process exits.

A current Chromium report describes Broadwell Intel graphics losing GPU acceleration on Chrome 152, with the GPU process unable to boot. That report is tracked as a duplicate of Chromium issue 553120490. Other current reports show the same EGL initialization failure on OCLP legacy Intel Macs.

### Safety

Phase 15 is diagnostic-only. It does not:
- patch Chrome
- replace libraries
- modify the Framework
- codesign or resign Chrome
- alter macOS graphics components

No Intel byte sequence is approved by this phase.

### Exit condition

Phase 15 is complete when the focused runtime evidence is captured. The next engineering step is static x86_64 analysis of the exact Framework build to identify the concrete gate and determine whether a safe Intel-specific patch exists. The project must not copy AMD or IOSurface substitutions merely because similar OCLP patchers use them.
