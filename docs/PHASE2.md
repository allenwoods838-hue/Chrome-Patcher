# Phase 2 — Chromium GPU Pipeline Mapping

## Goal

Identify the exact Chromium/ANGLE gates that prevent Intel Broadwell from reaching a working OpenGL or ANGLE backend, without modifying Chrome.

## Evidence carried forward from Phase 1

- MacBookAir7,2 with Intel HD Graphics 6000, device 0x1626
- Metal 2 support
- Working native CGL/OpenGL: Intel Inc. / Intel(R) HD Graphics 6000 / 4.1 INTEL-18.8.4
- OCLP-loaded Broadwell graphics kexts
- Chrome GPU process currently launches with --use-gl=disabled
- Chrome 153/154 testing showed GPU initialization failure
- Desktop-GL testing produced: Requested GL implementation (gl=none,angle=none) not found in allowed implementations: [(gl=egl-angle,angle=metal)]

## Phase 2 questions

1. Where does this Chrome build construct its allowed GL implementation list?
2. What converts --use-gl=desktop into gl=none,angle=none?
3. Which ANGLE backend is selected on macOS?
4. Is the Metal backend failing because of Intel/OCLP compatibility, or is an OpenGL backend excluded before initialization?
5. Which SharedImage/GPU-memory-buffer paths are reached after backend selection?
6. What changes between Chrome 153 and later milestones?

## Method

1. Record Chrome version and framework Mach-O layout.
2. Search framework strings for GL/ANGLE selection and GPU initialization markers.
3. Inspect the actual GPU-process command line.
4. Compare chrome://gpu output using isolated user profiles.
5. Capture GPU-process stderr for each experiment.
6. Propose a binary patch only after the exact gate is identified.

## Critical Intel rule

Do not copy the AMD Mac Pro patch set into the Intel profile. In particular, do not copy IOSurface target substitutions or SharedImage patches without Intel-specific evidence.

## Experiment matrix

| Test | Purpose | Modifies Chrome? |
|---|---|---|
| Normal Chrome | Establish current behavior | No |
| --use-gl=desktop | Test desktop-GL request handling | No |
| --use-angle=gl | Test whether GL backend can be selected | No |
| --use-gl=angle --use-angle=metal | Test ANGLE Metal path | No |
| --disable-gpu-sandbox | Separate sandbox startup from backend selection | No |
| Isolated --user-data-dir | Remove profile state/flags | No |

## Success evidence

Phase 2 requires a stable GPU process plus actual hardware-backed compositing/rasterization and a validated GL/WebGL or equivalent hardware path. Process startup alone is not success.

## Next phase

Phase 3 will implement Intel-generation detection and profiles, beginning with Broadwell/HD 6000.
