# Phase 3 — Intel Generation Detection

Phase 3 is detection-only. It does not modify Chrome, re-sign applications, install LaunchAgents, or change macOS graphics files.

## Scope

Initial generation profiles:
- Ivy Bridge
- Haswell
- Broadwell
- Skylake

The first compatibility target is Broadwell, especially Intel HD Graphics 6000 (PCI device 0x1626).

## Detection

The detector prefers the PCI device ID reported by macOS. Human-readable GPU names are supporting evidence, not the primary selector. Unknown Intel devices remain `generic` rather than being guessed into a generation.

For the current target, 0x1626 maps to Broadwell / HD Graphics 6000 / broadwell.

## Chromium milestone

`chromium/milestone.py` parses the installed Chrome version into its major milestone. Hardware generation and Chromium milestone remain separate so later compatibility profiles can combine both.

## Safety

- No binary patching.
- No code-signing changes.
- No LaunchAgent installation.
- No system graphics changes.
- No AMD-specific offsets or IOSurface substitutions.
- Hardware profiles stay independent from Chromium milestone profiles.

## Exit criteria

The tool can identify Intel generation and Chrome milestone, while unknown hardware receives a conservative generic profile.

## Next phase

Phase 4 adds diagnostic-only launch profiles and validation helpers.
