#!/usr/bin/env python3
"""Read-only Phase 1 diagnostics for legacy Intel Chromium GPU work."""
from pathlib import Path
import platform
import subprocess
import sys

OUT = Path.home() / "Desktop" / "chrome-patcher-baseline"
OUT.mkdir(parents=True, exist_ok=True)
REPORT = OUT / "diagnose.txt"

def run(*args):
    try:
        p = subprocess.run(args, text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, check=False)
        return p.stdout.strip()
    except Exception as exc:
        return f"<error: {exc}>"

def section(name, value):
    return f"=== {name} ===\n{value}\n"

parts = [
    section("Python / Platform",
            f"Python: {sys.version}\nPlatform: {platform.platform()}\nMachine: {platform.machine()}"),
    section("macOS", run("sw_vers")),
    section("Hardware", run("system_profiler", "SPHardwareDataType")),
    section("Graphics", run("system_profiler", "SPDisplaysDataType")),
]

loaded = run("kmutil", "showloaded")
parts.append(section("Loaded Graphics Components", "\n".join(
    line for line in loaded.splitlines()
    if any(x.lower() in line.lower() for x in
           ("AppleIntel", "IOGraphics", "AppleGraphics")))))

chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
parts.append(section("Chrome Version",
                    run(chrome, "--version") if Path(chrome).exists()
                    else "Google Chrome not found."))

parts.append(section("Chrome Signature",
                    run("codesign", "-dv", "--verbose=4",
                        "/Applications/Google Chrome.app")
                    if Path("/Applications/Google Chrome.app").exists()
                    else "Google Chrome not found."))

for lib in (
    Path("/Applications/Google Chrome.app/Contents/Frameworks/"
         "Google Chrome Framework.framework/Versions/Current/Libraries/libEGL.dylib"),
    Path("/Applications/Google Chrome.app/Contents/Frameworks/"
         "Google Chrome Framework.framework/Versions/Current/Libraries/libGLESv2.dylib"),
):
    if lib.exists():
        parts.append(section(str(lib),
                             run("file", str(lib)) + "\n" +
                             run("shasum", "-a", "256", str(lib))))

REPORT.write_text("\n".join(parts) + "\n", encoding="utf-8")
print(REPORT)
