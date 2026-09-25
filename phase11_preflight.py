#!/usr/bin/env python3
"""Phase 11: immutable preflight and evidence bundle for Intel patch approval.

Read-only. This phase does not patch, sign, replace, or launch Chrome.
"""
from __future__ import annotations
import hashlib
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
FRAMEWORK = Path("/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Versions/Current/Google Chrome Framework")
OUT = Path.home() / "Desktop" / "chrome-patcher-baseline" / "phase11"

def run(*cmd: str) -> str:
    try:
        p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        return p.stdout.strip()
    except OSError:
        return ""

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def signature(path: Path) -> str:
    return run("/usr/bin/codesign", "-dv", "--verbose=4", str(path))

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    lines = [
        "=== Chrome-Patcher Phase 11 Preflight ===",
        f"Chrome exists: {CHROME.exists()}",
        f"Framework exists: {FRAMEWORK.exists()}",
    ]
    if CHROME.exists():
        lines.append("Chrome version: " + run(str(CHROME), "--version"))
        lines.append("Chrome signature:")
        lines.append(signature(CHROME))
    if FRAMEWORK.exists():
        lines.append("Framework SHA256: " + sha256(FRAMEWORK))
        lines.append("Framework signature:")
        lines.append(signature(FRAMEWORK))

    sys.path.insert(0, str(ROOT))
    try:
        from chromium.compatibility import snapshot
        s = snapshot()
        v = s["versions"]
        lines.extend([
            f"Hardware profile: {s['hardware_profile']}",
            f"Chrome milestone: {v['chrome_milestone'] or 'unknown'}",
            f"Framework milestone: {v['framework_milestone'] or 'unknown'}",
            f"App/framework match: {'yes' if v['match'] else 'NO'}",
            f"Compatibility status: {s['compatibility'].get('status', 'unknown')}",
            f"Patch status: {s['compatibility'].get('patch_status', 'unknown')}",
        ])
    except Exception as exc:
        lines.append(f"Compatibility check error: {type(exc).__name__}: {exc}")

    try:
        from phase5_patch import PROFILES
        lines.append("Patch profiles:")
        for name, profile in PROFILES.items():
            present = bool(profile["find_hex"] and profile["replace_hex"])
            lines.append(
                f"{name}: milestone={profile['milestone']} status={profile['status']} "
                f"bytes={'present' if present else 'none'}"
            )
    except Exception as exc:
        lines.append(f"Patch-profile read error: {type(exc).__name__}: {exc}")

    report = "\n".join(lines) + "\n"
    path = OUT / "preflight.txt"
    path.write_text(report, encoding="utf-8")
    print(report, end="")
    print(f"Saved: {path}")
    print("RESULT: READ_ONLY_PREFLIGHT")
    print("No Intel patch bytes are approved by Phase 11.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
