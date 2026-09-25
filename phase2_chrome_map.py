#!/usr/bin/env python3
"""Phase 2 read-only Chromium GPU/ANGLE mapping tool for macOS."""
from pathlib import Path
import subprocess

CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
FRAMEWORK = Path("/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Versions/Current/Google Chrome Framework")
OUT = Path.home() / "Desktop" / "chrome-patcher-baseline"
OUT.mkdir(parents=True, exist_ok=True)
REPORT = OUT / "phase2_chrome_map.txt"

def run(*args):
    p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return p.stdout

lines = ["=== Phase 2 Chromium GPU/ANGLE Map ===", ""]
if CHROME.exists():
    lines += ["=== Chrome ===", run(str(CHROME), "--version").strip(), ""]
else:
    lines += ["Chrome not found.", ""]

if FRAMEWORK.exists():
    lines += ["=== Framework ===", str(FRAMEWORK), run("file", str(FRAMEWORK)).strip(), ""]
    lines += ["=== Relevant ANGLE / GL strings ==="]
    strings = run("strings", "-a", str(FRAMEWORK))
    needles = ("GetAllowedGLImplementation","GetDisplayInitializationParams","egl-angle","angle=metal","use-angle","use-gl","Requested GL implementation","AllowedGL","InitializeGLOneOffscreen","InitializeStaticGLBindings","IOSurface","SharedImage","CompoundImageBacking")
    seen = set()
    for line in strings.splitlines():
        if any(n.lower() in line.lower() for n in needles) and line not in seen:
            lines.append(line); seen.add(line)
    lines.append("")
else:
    lines += ["Framework not found.", ""]

lines += ["=== GPU Helper Paths ==="]
if CHROME.exists():
    helper_root = CHROME.parent.parent / "Frameworks" / "Google Chrome Framework.framework" / "Versions" / "Current" / "Helpers"
    if helper_root.exists():
        for p in sorted(helper_root.rglob("*")):
            if p.name.startswith("Google Chrome Helper"): lines.append(str(p))
lines += ["", "=== Notes ===", "This tool is read-only. It does not patch or re-sign Chrome.", "String presence is evidence for investigation, not proof that a code path is active.", ""]
REPORT.write_text("\n".join(lines), encoding="utf-8")
print(REPORT)