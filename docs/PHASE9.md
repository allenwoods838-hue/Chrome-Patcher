# Phase 9 — Intel Architecture Expansion

## Goal
Expand the hardware model to four independently gated generations: Ivy Bridge, Haswell, Broadwell, and Skylake.

## Current status
All four profiles are detection-only. No binary patch bytes are included and no generation inherits another generation's patch.

| Generation | Example device IDs | Profile |
|---|---|---|
| Ivy Bridge | 0x0152, 0x0166 | ivy_bridge |
| Haswell | 0x0402, 0x0412, 0x0416, 0x0D22 | haswell |
| Broadwell | 0x1616, 0x161E, 0x1626, 0x1627 | broadwell |
| Skylake | 0x1912, 0x1916, 0x1926 | skylake |

Unknown Intel devices remain generic rather than being assigned to a nearby generation.

## Evidence gate
Before any generation receives patch bytes, require the exact Chromium/ANGLE gate, exact Framework version/hash, Intel-specific instruction sequence, unique signature, equal-length replacement, GPU validation, and verified rollback.

## Run
```bash
python3 hardware/intel.py
python3 -m chromium.profiles
```

Phase 9 does not modify Chrome, Framework binaries, Apple graphics components, OCLP, LaunchAgents, or system settings.
