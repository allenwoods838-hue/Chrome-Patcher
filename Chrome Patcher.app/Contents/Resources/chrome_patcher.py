#!/usr/bin/env python3
"""Unified Chrome-Patcher controller for legacy Intel Macs."""
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
    p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False, timeout=timeout)
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
    return run("/usr/bin/codesign", "-dv", "--verbose=4", str(path)) if path.exists() else "missing"

def find_python() -> str | None:
    return shutil.which("python3") or ("/usr/bin/python3" if Path("/usr/bin/python3").exists() else None)

def run_component(name: str, *args: str) -> str:
    script = ROOT / name
    py = find_python()
    if not script.exists():
        return f"Missing component: {name}"
    if not py:
        return "REFUSED: Python 3 was not found."
    return run(py, str(script), *args, timeout=300)

def status_report() -> str:
    vendor, device, model, generation = detect_gpu()
    app_v = chrome_version()
    app_ms = milestone(app_v)
    fw_v = framework_version()
    fw_ms = milestone(fw_v)
    return "\n".join([
        "Chrome-Patcher",
        "",
        f"macOS: {platform.mac_ver()[0] or 'unknown'}",
        f"Chrome: {app_v}",
        f"Chrome milestone: {app_ms or 'unknown'}",
        f"Framework: {fw_v}",
        f"Framework milestone: {fw_ms or 'unknown'}",
        f"Application/Framework match: {'YES' if app_ms and fw_ms and app_ms == fw_ms else 'NO'}",
        f"GPU: {vendor} / {device} / {model} / {generation}",
        f"Framework SHA256: {sha256(FRAMEWORK) if FRAMEWORK.exists() else 'missing'}",
        "",
        "PATCH STATUS: NO INTEL BYTE PATCHES APPROVED",
        "MODE: FAIL-CLOSED",
    ])

def full_diagnostic() -> str:
    OUT.mkdir(parents=True, exist_ok=True)
    runtime = run_component("phase15_intel_gate.py")
    static = run_component("phase16_static_gate.py", "--no-disassembly")
    report = "\n".join([
        status_report(),
        "",
        "=== Runtime ANGLE/EGL ===",
        runtime,
        "",
        "=== Static x86_64 Gate Mapping ===",
        static,
        "",
    ])
    path = OUT / "full-report.txt"
    path.write_text(report, encoding="utf-8")
    summary = "\n".join([
        "Full Diagnostic complete.",
        "",
        "The detailed evidence was saved to:",
        str(path),
        "",
        "No Chrome files were modified.",
    ])
    return summary

def show(title: str, message: str) -> None:
    safe = message.replace("\\", "/").replace('"', '\"')
    subprocess.run([
        "/usr/bin/osascript", "-e",
        f'display dialog "{safe[-7000:]}" buttons {{"Close"}} default button "Close" with title "{title}"'
    ], check=False)

def choose() -> str:
    items = [
        "Full Diagnostic",
        "Status Only",
        "Guarded Patch Check",
        "Apply Approved Patch",
        "Restore",
        "Open Report",
        "Quit",
    ]
    joined = '","'.join(items)
    script = f'choose from list {{"{joined}"}} with prompt "Chrome-Patcher"'
    return run("/usr/bin/osascript", "-e", script)

def menu() -> int:
    while True:
        choice = choose()
        if choice in {"", "false", "Quit"}:
            return 0
        if choice == "Full Diagnostic":
            show("Chrome-Patcher", full_diagnostic())
        elif choice == "Status Only":
            show("Chrome-Patcher", status_report())
        elif choice == "Guarded Patch Check":
            show("Chrome-Patcher", run_component("phase5_patch.py"))
        elif choice == "Apply Approved Patch":
            confirm = run(
                "/usr/bin/osascript", "-e",
                'display dialog "Apply the approved Intel patch? The patch engine will refuse unless every safety gate passes." buttons {"Cancel","Apply"} default button "Cancel" with title "Chrome-Patcher"'
            )
            if "Apply" in confirm:
                show("Chrome-Patcher", run_component("phase5_patch.py", "--apply"))
        elif choice == "Restore":
            confirm = run(
                "/usr/bin/osascript", "-e",
                'display dialog "Restore Chrome from a verified patch backup?" buttons {"Cancel","Restore"} default button "Cancel" with title "Chrome-Patcher"'
            )
            if "Restore" in confirm:
                show("Chrome-Patcher", run_component("restore.py", "--apply"))
        elif choice == "Open Report":
            path = OUT / "full-report.txt"
            if path.exists():
                run("/usr/bin/open", str(path))
            else:
                show("Chrome-Patcher", "No report exists yet. Run Full Diagnostic first.")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", nargs="?", choices=["menu","status","diagnostic","patch","restore","report"], default="menu")
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
        print(run_component("restore.py", "--apply"))
    elif args.command == "report":
        path = OUT / "full-report.txt"
        print(path.read_text(encoding="utf-8") if path.exists() else "No report exists yet.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
