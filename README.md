# Chrome-Patcher

Intel-focused Chromium GPU diagnostics and a guarded patch framework for legacy Macs.

## One-click macOS app

Download the repository ZIP, unzip it, and double-click Chrome-Patcher.app.

The app provides diagnostics, compatibility status, guarded patch checking, restore, and report viewing.

No terminal commands are required for the normal workflow.

## Primary target

The main validation target is Intel Broadwell, including HD Graphics 6000 device 0x1626, on macOS Sequoia with Chromium milestone 154.

A current Chromium report documents a Broadwell GPU regression in Chrome 152, including GPU-process initialization failure:
https://issues.chromium.org/issues/554386283

Chromium's GL factory rejects a requested implementation when it is not in the allowed implementation list:
https://chromium.googlesource.com/chromium/src/+/HEAD/ui/gl/init/gl_factory.cc

## Safety status

The project is fail-closed.

The current profile database contains no approved Intel byte patches. Diagnostics never automatically enable patching.

The pipeline includes hardware detection, Chrome/Framework milestone checks, runtime ANGLE/EGL capture, static x86_64 mapping, centralized profiles, guarded patching, verified backup/restore, tests, and a one-click macOS app.

AMD-specific byte substitutions and IOSurface modifications are not copied into the Intel path without separate Intel evidence.

## Output

Reports are stored under:

    ~/Desktop/chrome-patcher-baseline/

See docs/BUILD.md, docs/ARCHITECTURE.md, and docs/SAFETY.md.
