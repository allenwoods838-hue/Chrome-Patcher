# Architecture

Chrome-Patcher separates evidence collection from mutation.

1. Hardware detection identifies Intel generation and PCI device ID.
2. Chrome/Framework compatibility blocks cross-build patching.
3. Runtime diagnostics capture the actual ANGLE/EGL path.
4. Static analysis maps relevant strings to x86_64 code references on the exact Framework.
5. patchdb/profiles.json describes hardware/milestone compatibility and approval status.
6. Phase 5 requires explicit approval, exact build identity, unique bytes, a verified backup, closed Chrome, atomic replacement, and post-write hashing.
7. Restore independently verifies and restores a previously patched Framework.
8. CI validates pure-Python logic.

Fail-closed is the project rule: a diagnostic result never grants permission to mutate Chrome.
