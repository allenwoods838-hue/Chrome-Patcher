# Phase 1 — Baseline and Diagnostics

## Objective

Establish whether the legacy Intel GPU is functioning natively and separate macOS/OCLP graphics problems from Chromium/ANGLE initialization problems.

Phase 1 is diagnostics-only. It does not modify Chrome, install a LaunchAgent, or apply GPU patches.

## Initial target

- MacBookAir7,2
- Intel Core i7-5650U
- Intel HD Graphics 6000 / Broadwell
- macOS Sequoia 15.7.5
- OCLP 2.5.1 root patch
- Chrome 153.0.8010.53

## Required evidence

1. macOS version/build
2. Mac model and GPU
3. OCLP/root-patched Intel graphics components
4. Native OpenGL renderer
5. Chrome version/signature
6. Chrome ANGLE/GL initialization behavior
7. Relevant Chromium GPU libraries
8. Existing patcher/LaunchAgent state

## Initial findings

The native CGL/OpenGL test succeeded independently of Chromium:

- GL_VENDOR: Intel Inc.
- GL_RENDERER: Intel(R) HD Graphics 6000
- GL_VERSION: 4.1 INTEL-18.8.4

This establishes that native macOS OpenGL is functional on the Broadwell GPU.

Chrome 153 failed during GPU-process initialization. A desktop-GL test reported that the requested implementation was unavailable and showed an allowed implementation of:

(gl=egl-angle,angle=metal)

The observed error was:

Requested GL implementation (gl=none,angle=none) not found in allowed implementations: [(gl=egl-angle,angle=metal)]

Chrome then exited the GPU process during initialization.

## Interpretation

The evidence points to a Chromium/ANGLE/GL implementation-selection problem rather than a completely non-functional Intel GPU or native OpenGL stack.

This is a working hypothesis, not a final patch specification.

## Safety rules

- Do not port AMD Mac Pro patches directly to Intel.
- Do not force GL_TEXTURE_RECTANGLE or IOSurface target substitutions without Intel-specific evidence.
- Do not automatically modify Chrome in Phase 1.
- Do not install a LaunchAgent in Phase 1.
- Back up every binary before any later modification.
- Validate actual GPU initialization, not merely a patch count.
- Treat each Chromium milestone as a separate compatibility target.

## Exit criteria

Phase 1 is complete when the native GPU stack, OCLP state, Chrome version, and Chromium failure mode are documented well enough to begin Chromium GPU pipeline analysis without guessing.

## Next phase

Phase 2 will map Chromium's macOS GPU path and identify the exact implementation-selection and ANGLE/EGL gates that must be changed for Intel Broadwell.
