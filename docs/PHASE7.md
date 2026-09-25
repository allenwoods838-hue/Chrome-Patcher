# Phase 7 — Automated GPU Validation

## Goal

Phase 7 changes validation from "Chrome launched" to evidence about the GPU process and GPU feature state.

It records Chrome executable version, current Framework SHA-256, GPU launch-matrix results, known GPU-process failure markers, and optional chrome://gpu feature-state evidence.

## Files

- phase7_validate.py — captures environment metadata and runs the diagnostic matrix.
- tests/gpu_validation.py — classifies evidence as FAIL, HARDWARE_EVIDENCE, SOFTWARE_OR_DISABLED, or UNKNOWN.

## Run

    python3 phase7_validate.py
    python3 tests/gpu_validation.py

To include a saved text dump of chrome://gpu:

    python3 tests/gpu_validation.py --gpu-report ~/Desktop/chrome-patcher-baseline/gpu-report.txt

## Interpretation

- FAIL: GPU-process crash/boot failure evidence was found.
- HARDWARE_EVIDENCE: supplied evidence contains multiple hardware-acceleration indicators.
- SOFTWARE_OR_DISABLED: multiple software/disabled indicators were found.
- UNKNOWN: evidence is insufficient.

A running Chrome process, successful window launch, or absence of a simple error string is not considered GPU acceleration.

## Safety

Phase 7 is read-only with respect to Chrome and system graphics. It does not patch binaries, change kexts, alter OCLP, install LaunchAgents, or modify code signatures.

No Intel patch bytes are introduced by Phase 7.
