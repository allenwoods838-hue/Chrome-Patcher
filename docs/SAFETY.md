# Safety model

Chrome-Patcher is fail-closed.

A profile must be explicitly approved before any byte write is possible. An approved profile must identify an exact Framework build and exact equal-length replacement.

Before mutation, the engine checks the Chrome/Framework milestone match, hardware profile, Chrome process state, optional Framework hash, exact unique byte signature, verified backup hash, atomic write, and final hash. A manifest records the operation.

No Intel byte patch is currently approved.

Do not copy AMD-specific or IOSurface substitutions into an Intel profile without separate Intel evidence.
