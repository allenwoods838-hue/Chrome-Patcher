#!/usr/bin/env python3
"""Guarded Intel Chromium Framework patch engine.

Patch data is intentionally empty until an exact Intel-specific gate is
verified on the target Framework build. The engine is fail-closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
FRAMEWORK = Path("/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Versions/Current/Google Chrome Framework")
ROOT = Path(__file__).resolve().parent
PROFILE_DB = ROOT / "patchdb" / "profiles.json"
BACKUP_ROOT = Path.home() / "Desktop/chrome-patcher-baseline" / "backups"
MANIFEST = BACKUP_ROOT / "patch-manifest.json"

def run(*cmd: str) -> str:
    p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return p.stdout.strip()

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def chrome_version() -> str:
    return run(str(CHROME), "--version")

def parse_milestone(value: str) -> int | None:
    m = re.search(r"\b(\d+)\.\d+\.\d+\.\d+\b", value)
    return int(m.group(1)) if m else None

def detect_device() -> int | None:
    text = run("system_profiler", "SPDisplaysDataType")
    m = re.search(r"\bdevice\s*(?:id)?\s*[:=]?\s*0x([0-9a-fA-F]{4})\b", text, re.I)
    return int(m.group(1), 16) if m else None

def chrome_running() -> bool:
    return subprocess.run(
        ["/usr/bin/pgrep", "-f", str(CHROME)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0

def signature(path: Path) -> str:
    return run("/usr/bin/codesign", "-dv", "--verbose=4", str(path)) if path.exists() else "missing"

def load_profiles() -> dict:
    return json.loads(PROFILE_DB.read_text(encoding="utf-8"))["profiles"]

def select_profile(device: int | None, milestone: int | None) -> tuple[str | None, dict | None]:
    if device is None or milestone is None:
        return None, None
    needle = f"0x{device:04x}"
    for name, profile in load_profiles().items():
        if profile["milestone"] == milestone and needle in [x.lower() for x in profile["device_ids"]]:
            return name, profile
    return None, None

def atomic_replace(path: Path, data: bytes) -> str:
    fd, name = tempfile.mkstemp(prefix=".chrome-framework.", dir=str(path.parent))
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp, path.stat().st_mode)
        os.replace(tmp, path)
        dfd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
        return sha256(path)
    finally:
        if tmp.exists():
            tmp.unlink()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Apply only an approved profile.")
    args = ap.parse_args()

    print("=== Guarded Intel Patch Engine ===")
    if not CHROME.exists() or not FRAMEWORK.exists():
        print("REFUSED: Chrome or Framework not found.")
        return 2

    app_v = chrome_version()
    app_ms = parse_milestone(app_v)
    fw_ms = parse_milestone(FRAMEWORK.parent.name)
    print("Chrome:", app_v)
    print("Chrome milestone:", app_ms or "unknown")
    print("Framework milestone:", fw_ms or "unknown")
    print("Framework SHA256:", sha256(FRAMEWORK))

    if app_ms is None or fw_ms is None or app_ms != fw_ms:
        print("REFUSED: Chrome application and Framework milestones do not match.")
        return 2

    device = detect_device()
    profile_name, profile = select_profile(device, app_ms)
    print("GPU device:", f"0x{device:04x}" if device is not None else "unknown")
    print("Profile:", profile_name or "none")

    if profile is None:
        print("REFUSED: no Intel profile for this hardware/milestone.")
        return 2
    if not profile["patch_approved"]:
        print("REFUSED: this profile has no approved Intel patch bytes.")
        print("Status: diagnostic-only")
        return 3
    if chrome_running():
        print("REFUSED: Chrome is currently running.")
        return 2

    patch = profile.get("patch") or {}
    find_hex = patch.get("find_hex")
    replace_hex = patch.get("replace_hex")
    expected_sha = patch.get("framework_sha256")
    patched_sha = patch.get("patched_sha256")
    if not find_hex or not replace_hex:
        print("REFUSED: approved profile has no byte sequence.")
        return 3
    if expected_sha and sha256(FRAMEWORK) != expected_sha:
        print("REFUSED: Framework SHA256 does not match the approved build.")
        return 2

    old = bytes.fromhex(find_hex)
    new = bytes.fromhex(replace_hex)
    if not old or len(old) != len(new):
        print("REFUSED: invalid patch lengths.")
        return 2

    data = FRAMEWORK.read_bytes()
    count = data.count(old)
    print("Exact signature matches:", count)
    if count != 1:
        print("REFUSED: expected exactly one unique byte signature.")
        return 2

    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    original_sha = sha256(FRAMEWORK)
    backup = BACKUP_ROOT / f"Chrome-Framework-{app_ms}-{original_sha[:16]}.bak"
    if not backup.exists():
        shutil.copy2(FRAMEWORK, backup)
    if sha256(backup) != original_sha:
        print("REFUSED: backup verification failed.")
        return 2

    if not args.apply:
        print("DRY RUN: signature and backup checks passed. No Chrome files modified.")
        return 0

    patched = data[:data.index(old)] + new + data[data.index(old) + len(old):]
    final_sha = atomic_replace(FRAMEWORK, patched)
    if patched_sha and final_sha != patched_sha:
        print("CRITICAL: post-patch SHA256 mismatch.")
        return 4

    manifest = {}
    if MANIFEST.exists():
        try:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            manifest = {}
    manifest.setdefault("patches", []).append({
        "profile": profile_name,
        "chrome_version": app_v,
        "original_sha256": original_sha,
        "patched_sha256": final_sha,
        "backup": str(backup),
        "signature_before": signature(backup),
        "signature_after": signature(FRAMEWORK),
    })
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Applied patch.")
    print("Backup:", backup)
    print("Patched Framework SHA256:", final_sha)
    print("Code signing was not performed by this engine.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
