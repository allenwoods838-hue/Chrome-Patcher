# Phase 10 — Chromium Milestone Expansion

## Goal
Make Chromium milestone handling explicit and conservative across M152, M153, M154, and M155, while refusing unsupported or mismatched builds.

## What changed
- chromium/milestone.py reports both the Chrome application version and resolved Framework version directory.
- App/framework milestone mismatch is a patching blocker.
- chromium/profiles.py resolves known milestones and refuses unknown milestones or unsupported hardware/milestone combinations.
- M152–M155 remain independent diagnostic-only profiles.
- chromium/compatibility.py combines detected Intel hardware with the detected Chromium milestone.
- No milestone inherits patch bytes from another milestone.

## Current policy

| Milestone | Intel profiles | Patch status |
|---|---|---|
| M152 | Ivy Bridge, Haswell, Broadwell, Skylake | Not approved |
| M153 | Ivy Bridge, Haswell, Broadwell, Skylake | Not approved |
| M154 | Ivy Bridge, Haswell, Broadwell, Skylake | Not approved |
| M155 | Ivy Bridge, Haswell, Broadwell, Skylake | Not approved |
| Unknown | None | Refused |

M154 retains Broadwell HD Graphics 6000 (0x1626) as the primary diagnostic target.

## Commands
Run from the repository root:

    python3 chromium/milestone.py
    python3 -m chromium.profiles
    python3 -m chromium.compatibility

The milestone command should show whether the Chrome application and its Framework agree. If they do not, do not interpret a milestone-specific patch result.

## Safety
Phase 10 does not patch, sign, replace, or modify Chrome. It does not modify Apple graphics components, OCLP, LaunchAgents, or system settings.

## Exit criteria
- Known M152–M155 builds resolve to their own profile.
- Unknown milestones refuse patch compatibility.
- Chrome app/framework mismatch is visible and treated as unsafe for milestone-specific patching.
- Hardware generation remains independently selected from Chromium milestone.
