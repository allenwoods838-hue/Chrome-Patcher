#!/usr/bin/env python3
"""Phase 5: Intel Chromium patch engine (guarded; no unvalidated patch bytes).

This phase deliberately ships the patching machinery before shipping an Intel
Broadwell byte patch. A profile must provide an exact expected byte sequence
and replacement sequence. The engine refuses to modify Chrome unless:
  1. the detected GPU is Broadwell,
  2. the installed Chrome milestone matches the profile,
  3. the framework contains exactly the expected bytes at the expected count,
  4. a backup can be created before modification.

Default mode is --dry-run.
"""
from __future__ import annotations
import argparse, hashlib, shutil, subprocess, sys
from pathlib import Path

CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
FRAMEWORK = Path("/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Versions/Current/Google Chrome Framework")
BACKUP_ROOT = Path.home() / "Desktop" / "chrome-patcher-baseline" / "backups"

# Intentionally empty until Phase 2/4 evidence identifies an Intel-specific
# gate. Never populate this with an AMD patch or an IOSurface substitution.
PROFILES = {
    "broadwell-m154": {
        "generation": "Broadwell",
        "device_ids": {0x1616, 0x161E, 0x1626, 0x1627},
        "milestone": 154,
        "status": "awaiting-validated-intel-gate",
        "find_hex": None,
        "replace_hex": None,
        "description": "Broadwell/Chrome 154 guarded profile; no patch bytes are approved yet.",
    },
}

def run(*cmd: str) -> str:
    p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return p.stdout.strip()

def chrome_version() -> str:
    return run(str(CHROME), "--version")

def milestone(version: str) -> int | None:
    import re
    m = re.search(r"\b(\d+)\.\d+\.\d+\.\d+\b", version)
    return int(m.group(1)) if m else None

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def detect_gpu() -> tuple[str, int | None, str]:
    text = run("system_profiler", "SPDisplaysDataType")
    import re
    m = re.search(r"\bdevice\s*(?:id)?\s*[:=]?\s*0x([0-9a-fA-F]{4})\b", text, re.I)
    device = int(m.group(1), 16) if m else None
    generation = "Broadwell" if device in PROFILES["broadwell-m154"]["device_ids"] else "unknown"
    return "Intel" if "Intel" in text else "unknown", device, generation

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=PROFILES, default="broadwell-m154")
    ap.add_argument("--apply", action="store_true", help="Apply only a fully validated profile.")
    args = ap.parse_args()
    profile = PROFILES[args.profile]

    print("=== Phase 5 Intel Patch Gate ===")
    print(f"Chrome: {chrome_version()}")
    vendor, device, generation = detect_gpu()
    print(f"GPU: {vendor} device={f'0x{device:04x}' if device is not None else 'unknown'} generation={generation}")
    print(f"Framework: {FRAMEWORK}")
    if not FRAMEWORK.exists():
        print("REFUSED: Chrome Framework not found.")
        return 2

    ms = milestone(chrome_version())
    if ms != profile["milestone"]:
        print(f"REFUSED: profile expects Chrome milestone {profile['milestone']}, detected {ms}.")
        return 2

    # Phase 11 hard gate: application and Framework must be the same milestone.
    try:
        from chromium.milestone import compatibility_snapshot
        versions = compatibility_snapshot()
    except Exception as exc:
        print(f"REFUSED: compatibility preflight failed: {type(exc).__name__}: {exc}")
        return 2
    if not versions["match"]:
        print("REFUSED: Chrome application and Framework milestones do not match.")
        print(f"Chrome milestone: {versions['chrome_milestone'] or 'unknown'}")
        print(f"Framework milestone: {versions['framework_milestone'] or 'unknown'}")
        return 2
    if generation != profile["generation"]:
        print("REFUSED: this profile is Broadwell-only.")
        return 2
    if profile["find_hex"] is None or profile["replace_hex"] is None:
        print("REFUSED: no Intel patch bytes are approved yet.")
        print("Next evidence required: exact Intel-specific Chromium gate and byte-level validation.")
        print(f"Framework SHA256: {sha256(FRAMEWORK)}")
        return 3

    old = bytes.fromhex(profile["find_hex"])
    new = bytes.fromhex(profile["replace_hex"])
    if len(old) != len(new) or not old:
        print("REFUSED: invalid patch lengths.")
        return 2
    data = FRAMEWORK.read_bytes()
    count = data.count(old)
    print(f"Exact signature matches: {count}")
    if count != 1:
        print("REFUSED: expected exactly one signature match.")
        return 2
    offset = data.index(old)
    print(f"Patch offset: 0x{offset:x}")

    if not args.apply:
        print("DRY RUN: no Chrome files modified.")
        return 0

    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_ROOT / f"Chrome-Framework-{profile['milestone']}-{sha256(FRAMEWORK)[:16]}.bak"
    shutil.copy2(FRAMEWORK, backup)
    patched = data[:offset] + new + data[offset + len(old):]
    FRAMEWORK.write_bytes(patched)
    print(f"Backup: {backup}")
    print(f"Patched framework SHA256: {sha256(FRAMEWORK)}")
    print("IMPORTANT: code signing/notarization is not performed by this script.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
