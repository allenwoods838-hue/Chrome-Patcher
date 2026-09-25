# Phase 11 — Immutable Preflight & Evidence Bundle

## Goal

Establish a final read-only evidence gate before any Intel byte patch is considered. Phase 11 does not patch Chrome.

## What it records

- Chrome application version and code-signing metadata.
- Chrome Framework SHA-256 and code-signing metadata.
- Intel hardware profile.
- Chrome application milestone versus Framework milestone.
- Compatibility resolver status.
- Current patch-profile state and whether bytes are present.

Output:

    ~/Desktop/chrome-patcher-baseline/phase11/preflight.txt

## Run

    python3 phase11_preflight.py

## Interpretation

App/framework milestone match is required before milestone-specific patching. A mismatch or unknown milestone is a hard blocker.

RESULT: READ_ONLY_PREFLIGHT means evidence was collected. It is not authorization to patch.

The repository intentionally has no approved Intel patch bytes, so Phase 11 cannot modify the Framework.

## Patch approval gate

Before bytes are added to any profile, document all of the following for the exact Framework build:

1. Exact Intel-specific Chromium/ANGLE gate and active control flow.
2. Exact Framework SHA-256.
3. Unique byte signature with exactly one match.
4. Equal-length replacement with instruction-level justification.
5. Evidence that the change targets the Intel failure path rather than AMD or another backend.
6. Pre-patch and post-patch GPU evidence showing the intended hardware-backed path.
7. Verified backup and restore using Phase 8.
8. Code-signing implications understood and tested.
9. A clean refusal path for every mismatch.

## Safety

Phase 11 does not write to /Applications, modify Apple graphics components, modify OCLP, install LaunchAgents, alter Chrome signing, add patch bytes, or reuse AMD/IOSurface substitutions.

## Next phase

Only after the evidence gate is satisfied should an Intel-specific patch profile be authored. The first candidate remains Broadwell HD Graphics 6000 (0x1626), but no patch is approved by this phase.
