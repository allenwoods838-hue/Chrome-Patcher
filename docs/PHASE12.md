# Phase 12 — Intel/ANGLE Gate Reconnaissance

## Goal

Identify the exact Chromium/ANGLE control-flow gate that prevents the Intel Broadwell GPU path from reaching a usable backend. This phase is static analysis only.

## What it does

phase12_gate_recon.py:
- hashes the exact Chrome Framework being inspected;
- searches for known Chromium/ANGLE gate strings;
- records every occurrence and nearby printable context;
- saves the complete strings -a output;
- prints manual otool and nm commands for disassembly validation.

Output:
    ~/Desktop/chrome-patcher-baseline/phase12/gate_recon.txt
    ~/Desktop/chrome-patcher-baseline/phase12/strings.txt

## Run

    python3 phase12_gate_recon.py
    python3 phase12_gate_recon.py --radius 192

## Required evidence before patch bytes

1. Framework SHA-256 recorded.
2. Relevant function/symbol identified.
3. x86_64 disassembly showing the active decision/control flow.
4. Evidence that the decision affects the Intel Broadwell path.
5. A unique byte sequence at a single offset.
6. Equal-length replacement with instruction-level justification.
7. Pre/post GPU evidence demonstrating the intended hardware-backed path.
8. Verified restore path.

## Intel-specific safety rule

Do not copy an AMD patch, an IOSurface substitution, or an offset from another milestone merely because the same strings occur. Chromium/ANGLE layout can change between builds.

Phase 12 generates no patch bytes and modifies nothing under /Applications.

## Next step

Run the reconnaissance on the exact installed Framework, then use the resulting offsets with otool/nm to identify the candidate control-flow sequence. Only after that can an Intel-specific patch profile be evaluated.
