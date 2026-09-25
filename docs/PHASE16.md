# Phase 16 — Static x86_64 Gate Mapping

Phase 16 examines the exact installed Chrome Framework.

It locates relevant ANGLE/EGL strings and maps them to x86_64 RIP-relative code references. When LLDB is available, small disassembly windows are saved around those references.

Output:

    ~/Desktop/chrome-patcher-baseline/phase16/static_gate.txt

This phase is read-only and never modifies Chrome.
