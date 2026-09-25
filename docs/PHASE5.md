# Phase 5 — Intel Chromium Patch Framework

## Target

First Intel target: Broadwell graphics, including HD Graphics 6000 (device 0x1626), on macOS Sequoia.

## What this phase does

Phase 5 adds the **guarded patch engine** needed for an Intel Chromium patch:

- identifies the Intel device and generation;
- verifies the installed Chrome milestone;
- identifies the current Chrome Framework;
- supports exact byte-signature matching;
- requires exactly one match before a patch can be applied;
- creates a backup before modification;
- defaults to dry-run;
- refuses to patch when no Intel-specific patch bytes have been validated.

## What it deliberately does not do

There is currently **no Intel Broadwell byte patch embedded in the repository**.

This is intentional. The earlier Chromium evidence showed that Chrome can reduce the allowed GL implementations to a Metal-only configuration and that desktop GL can become:

`gl=none,angle=none`

That behavior identifies a gate, but it does not by itself establish the correct Intel byte substitution.

An AMD patch must not be copied into this profile. In particular, IOSurface or SharedImage substitutions require Intel-specific evidence.

## Run

From the repository:

```bash
python3 phase5_patch.py
```

For the current Broadwell/Chrome 154 target:

```bash
python3 phase5_patch.py --profile broadwell-m154
```

Expected current result:

```
REFUSED: no Intel patch bytes are approved yet.
```

That refusal is a safety check, not a failure.

## Apply mode

`--apply` is intentionally ineffective until an exact Intel profile is populated and validated. When eventually enabled, the engine will require:

1. Broadwell hardware;
2. matching Chrome milestone;
3. non-empty exact find/replace bytes;
4. exactly one signature match;
5. a backup before writing.

The script does not perform code signing. Signing and launch validation remain separate steps.

## Phase 5 evidence gate

Before adding real bytes, we need to capture:

- exact Chrome Framework version/hash;
- exact Chromium milestone;
- the active GL implementation selection path;
- the Intel-specific function/instruction sequence responsible for excluding the required backend;
- a unique byte signature;
- an independently checked replacement of equal length;
- post-patch hardware acceleration results.

Only then should `find_hex` / `replace_hex` be populated.

## Success criteria

A patch is not considered successful merely because the framework changes or Chrome starts.

Success requires actual GPU initialization and hardware-backed operation, including stable GPU process behavior and the relevant Chromium GPU feature status.
