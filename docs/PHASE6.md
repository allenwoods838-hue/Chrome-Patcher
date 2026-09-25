# Phase 6 — Chromium Milestone Profiles

## Scope

Phase 6 separates Chromium behavior by milestone so a byte sequence or diagnostic result from one Chrome build is never silently reused on another.

Profiles are provided for M152, M153, M154, and M155. Each profile currently remains diagnostic-only. No patch bytes are approved for any milestone.

## Broadwell target

M154 contains the first explicit target metadata: Intel Broadwell, device 0x1626, HD Graphics 6000. This does not authorize a patch; it identifies the hardware/milestone combination for validation.

## Safety gate

Chromium GPU/ANGLE behavior can change between milestones. A patch signature, replacement, framework hash, and GPU result must therefore be validated against the exact milestone. No cross-milestone byte copying is permitted.

## Matrix

| Milestone | Profile | Patch bytes | Status |
|---|---|---|---|
| M152 | chromium/m152.py | none | diagnostic-only |
| M153 | chromium/m153.py | none | diagnostic-only |
| M154 | chromium/m154.py | none | diagnostic-only |
| M155 | chromium/m155.py | none | diagnostic-only |

## Run

    python3 -m chromium.profiles
    python3 chromium/milestone.py

The first command lists the available milestone profiles. The second reports the installed Chrome milestone.

## Before any real patch

1. Identify the active Chromium/ANGLE gate for the exact build.
2. Identify the exact framework binary and hash.
3. Confirm a unique byte signature.
4. Validate equal-length replacement bytes.
5. Understand code-signing implications.
6. Verify hardware-backed GPU feature status after testing.

The repository is currently at the profile/validation stage; the M154 Broadwell target is defined, but the Intel patch remains unapproved.
