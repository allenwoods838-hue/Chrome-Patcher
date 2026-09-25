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
    if not FRAMEWORK.exists():
        return "missing"
    try:
        return FRAMEWORK.parent.resolve().name
    except OSError:
        return FRAMEWORK.parent.name

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

def component_path(name: str) -> Path:
    candidates = [ROOT / name]
    if ROOT.name == "Resources":
        candidates.append(ROOT.parent.parent.parent / name)
    candidates.append(Path.cwd() / name)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]

def run_component(name: str, *args: str) -> str:
    script = component_path(name)
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

def phase16_static_gate() -> str:
    framework = FRAMEWORK
    out_dir = DESKTOP / "phase16"
    if not framework.exists():
        return "Phase 16: Chrome Framework not found."
    out_dir.mkdir(parents=True, exist_ok=True)

    data = framework.read_bytes()
    framework_hash = sha256(framework)
    file_info = run("/usr/bin/file", str(framework)).strip()
    load_info = run("/usr/bin/otool", "-arch", "x86_64", "-l", str(framework))

    def sections(text: str) -> dict[str, tuple[int, int, int]]:
        result = {}
        seg = None
        current = None
        pending = {}
        for line in text.splitlines():
            s = line.strip()
            m = re.match(r"segname\s+(__\S+)", s)
            if m:
                seg = m.group(1)
                current = None
                pending = {}
                continue
            m = re.match(r"sectname\s+(__\S+)", s)
            if m and seg == "__TEXT":
                current = m.group(1)
                pending = {}
                continue
            if seg != "__TEXT" or current is None:
                continue
            for key in ("addr", "size", "offset"):
                m = re.match(rf"{key}\s+(0x[0-9a-fA-F]+|\d+)", s)
                if m:
                    pending[key] = int(m.group(1), 0)
            if {"addr", "size", "offset"} <= pending.keys():
                result[current] = (pending["addr"], pending["size"], pending["offset"])
        return result

    sec = sections(load_info)
    if "__text" not in sec or "__cstring" not in sec:
        return "Phase 16: x86_64 __text/__cstring sections not found.\nNo Chrome files were modified."

    text_addr, text_size, text_off = sec["__text"]
    cstr_addr, cstr_size, cstr_off = sec["__cstring"]
    cstr = data[cstr_off:cstr_off + cstr_size]

    targets = (
        b"Requested GL implementation",
        b"not found in allowed implementations",
        b"angle=metal",
        b"angle=opengl",
        b"GetAllowedGLImplementation",
        b"GetDisplayInitializationParams",
    )
    found = []
    target_vms = set()
    for target in targets:
        start = 0
        while True:
            idx = cstr.find(target, start)
            if idx < 0:
                break
            vm = cstr_addr + idx
            label = target.decode("ascii", errors="replace")
            found.append((label, cstr_off + idx, vm))
            target_vms.add(vm)
            start = idx + 1

    text_bytes = data[text_off:text_off + text_size]
    refs = []
    for i in range(max(0, len(text_bytes) - 7)):
        if i + 7 <= len(text_bytes) and 0x40 <= text_bytes[i] <= 0x4f:
            op = text_bytes[i + 1]
            if op in (0x8b, 0x8d, 0x89, 0x8a, 0x3b, 0x39, 0x81, 0x83):
                modrm = text_bytes[i + 2]
                if ((modrm >> 6) & 3) == 0 and (modrm & 7) == 5:
                    disp = int.from_bytes(text_bytes[i + 3:i + 7], "little", signed=True)
                    target = text_addr + i + 7 + disp
                    if target in target_vms:
                        refs.append((text_off + i, text_addr + i, target))
    report_lines = [
        "Phase 16",
        "Mode: READ_ONLY",
        f"Framework SHA256: {framework_hash}",
        f"file: {file_info}",
        f"__text addr=0x{text_addr:x} size=0x{text_size:x} offset=0x{text_off:x}",
        f"__cstring addr=0x{cstr_addr:x} size=0x{cstr_size:x} offset=0x{cstr_off:x}",
        "",
        "Relevant strings:",
    ]
    if found:
        for label, off, vm in found:
            report_lines.append(f"- {label} file=0x{off:x} vm=0x{vm:x}")
    else:
        report_lines.append("- none")
    report_lines.extend(["", f"RIP-relative references: {len(refs)}"])
    for file_off, vm, target in refs[:20]:
        report_lines.append(f"- code file=0x{file_off:x} vm=0x{vm:x} -> string=0x{target:x}")
    report_lines.append("")
    report_lines.append("No Chrome files were modified.")
    path = out_dir / "static_gate.txt"
    path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    return "\n".join(report_lines)

def full_diagnostic() -> str:
    OUT.mkdir(parents=True, exist_ok=True)
    runtime = run_component("phase15_intel_gate.py")
    static = phase16_static_gate()
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
