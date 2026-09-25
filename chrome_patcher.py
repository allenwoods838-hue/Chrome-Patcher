#!/usr/bin/env python3
"""Unified Chrome-Patcher controller for legacy Intel Macs.

Safe by default. Diagnostics are read-only; patching remains fail-closed.
"""
from __future__ import annotations

import argparse
import hashlib
import platform
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DESKTOP = Path.home() / "Desktop" / "chrome-patcher-baseline"
OUT = DESKTOP / "project"
CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
FRAMEWORK = Path("/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Versions/Current/Google Chrome Framework")

GPU_MAP = {
    "0x1626": ("Broadwell", "HD Graphics 6000"),
    "0x1616": ("Broadwell", "Broadwell graphics"),
    "0x161e": ("Broadwell", "Broadwell graphics"),
    "0x1627": ("Broadwell", "Broadwell graphics"),
    "0x0412": ("Haswell", "Haswell graphics"),
    "0x0416": ("Haswell", "Haswell graphics"),
    "0x0a16": ("Haswell", "Haswell graphics"),
    "0x0a26": ("Haswell", "Haswell graphics"),
    "0x0162": ("Ivy Bridge", "HD Graphics 4000"),
    "0x0152": ("Ivy Bridge", "Ivy Bridge graphics"),
    "0x0166": ("Ivy Bridge", "Ivy Bridge graphics"),
    "0x1912": ("Skylake", "HD Graphics 530"),
    "0x1906": ("Skylake", "Skylake graphics"),
    "0x1916": ("Skylake", "Skylake graphics"),
    "0x1926": ("Skylake", "Skylake graphics"),
    "0x1927": ("Skylake", "Skylake graphics"),
}

def run(*cmd: str, timeout: int = 120) -> str:
    p = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=timeout,
    )
    return p.stdout.strip()

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def chrome_version() -> str:
    return run(str(CHROME), "--version") if CHROME.exists() else "missing"

def milestone(value: str) -> int | None:
    m = re.search(r"\b(\d+)\.\d+\.\d+\.\d+\b", value)
    return int(m.group(1)) if m else None

def framework_version() -> str:
    return FRAMEWORK.parent.name if FRAMEWORK.exists() else "missing"

def detect_gpu() -> tuple[str, str, str, str]:
    text = run("system_profiler", "SPDisplaysDataType")
    m = re.search(r"\bdevice\s*(?:id)?\s*[:=]?\s*0x([0-9a-fA-F]{4})\b", text, re.I)
    device = f"0x{int(m.group(1), 16):04x}" if m else "unknown"
    generation, model = GPU_MAP.get(device, ("unknown", "Unknown Intel GPU"))
    vendor = "Intel" if "Intel" in text else "unknown"
    return vendor, device, model, generation

def signature(path: Path) -> str:
    if not path.exists():
        return "missing"
    return run("/usr/bin/codesign", "-dv", "--verbose=4", str(path))

def find_python() -> str | None:
    return shutil.which("python3") or ("/usr/bin/python3" if Path("/usr/bin/python3").exists() else None)

def status_report() -> str:
    vendor, device, model, generation = detect_gpu()
    chrome_v = chrome_version()
    app_ms = milestone(chrome_v)
    fw_name = framework_version()
    fw_ms = milestone(fw_name)
    lines = [
        "Chrome-Patcher status",
        "",
        f"OS: {platform.system()} {platform.mac_ver()[0] or 'unknown'}",
        f"Chrome: {chrome_v}",
        f"Chrome milestone: {app_ms or 'unknown'}",
        f"Framework version: {fw_name}",
        f"Framework milestone: {fw_ms or 'unknown'}",
        f"Application/Framework match: {'yes' if app_ms and fw_ms and app_ms == fw_ms else 'no'}",
        f"Framework SHA256: {sha256(FRAMEWORK) if FRAMEWORK.exists() else 'missing'}",
        f"GPU: {vendor} / {device} / {model} / {generation}",
        f"Framework signature: {signature(FRAMEWORK).splitlines()[0] if FRAMEWORK.exists() else 'missing'}",
        "",
        "Patch mode: FAIL-CLOSED",
        "Published Intel byte patches: NONE",
    ]
    return "\n".join(lines)

def run_component(name: str) -> str:
    script = ROOT / name
    py = find_python()
    if not script.exists():
        return f"Missing component: {name}"
    if not py:
        return "REFUSED: Python 3 was not found."
    return run(py, str(script), timeout=240)

def full_diagnostic() -> str:
    OUT.mkdir(parents=True, exist_ok=True)
    report = "\n".join([
        status_report(),
        "",
        "=== Phase 15 Runtime ANGLE/EGL ===",
        run_component("phase15_intel_gate.py"),
        "",
        "=== Phase 16 Static x86_64 Gate Mapping ===",
        run_component("phase16_static_gate.py"),
        "",
    ])
    path = OUT / "full-report.txt"
    path.write_text(report, encoding="utf-8")
    return report + f"Saved: {path}"

def gui_show(title: str, message: str) -> None:
    safe = message.replace("\\", "/").replace('"', '\"')
    subprocess.run(
        ["/usr/bin/osascript", "-e", f'display dialog "{safe[-9000:]}" buttons {{"Close"}} default button "Close" with title "{title}"'],
        check=False,
    )

def menu() -> int:
    choices = ["Full Diagnostic", "Status Only", "Guarded Patch Check", "Restore", "Open Report", "Quit"]
    while True:
        script = 'choose from list {"' + '","'.join(choices) + '"} with prompt "Chrome-Patcher"'
        out = run("/usr/bin/osascript", "-e", script)
        if not out or out in {"false", "Quit"}:
            return 0
        if out == "Full Diagnostic":
            gui_show("Chrome-Patcher", full_diagnostic())
        elif out == "Status Only":
            gui_show("Chrome-Patcher", status_report())
        elif out == "Guarded Patch Check":
            gui_show("Chrome-Patcher", run_component("phase5_patch.py"))
        elif out == "Restore":
            confirm = run("/usr/bin/osascript", "-e", 'display dialog "Restore Chrome from the latest verified patch backup?" buttons {"Cancel","Restore"} default button "Cancel" with title "Chrome-Patcher"')
            if "Restore" in confirm:
                gui_show("Chrome-Patcher", run_component("restore.py"))
        elif out == "Open Report":
            path = OUT / "full-report.txt"
            if path.exists():
                run("/usr/bin/open", str(path))
            else:
                gui_show("Chrome-Patcher", "No report exists yet. Run Full Diagnostic first.")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", nargs="?", choices=["menu", "status", "diagnostic", "patch", "restore", "report"], default="menu")
    args = ap.parse_args()
    if args.command == "menu":
        return menu()
    if args.command == "status":
        print(status_report())
    elif args.command == "diagnostic":
        print(full_diagnostic())
    elif args.command == "patch":
        print(run_component("phase5_patch.py"))
    elif args.command == "restore":
        print(run_component("restore.py"))
    elif args.command == "report":
        path = OUT / "full-report.txt"
        print(path.read_text(encoding="utf-8") if path.exists() else "No report exists yet.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
