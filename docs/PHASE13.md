# Phase 13 — Compact ANGLE/GL Candidate Scan

Phase 13 is a small, read-only follow-up to Phase 12.

It scans the exact installed Chrome Framework and prints only a limited set of relevant ANGLE/GL/SharedImage strings, avoiding a full strings dump while preserving the Framework SHA-256.

Run:

    cd ~/Chrome-Patcher
    python3 phase13_candidate_scan.py

Optional:

    python3 phase13_candidate_scan.py --limit 10

This is reconnaissance only. A string is not proof of an active control-flow gate. No patch bytes are generated, and nothing under /Applications is modified.

The next evidence step is to connect a useful candidate string or symbol to x86_64 disassembly on the same Framework build.