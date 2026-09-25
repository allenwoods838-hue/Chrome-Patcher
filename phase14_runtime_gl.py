#!/usr/bin/env python3
"""Phase 14: runtime ANGLE/GL decision capture.

Read-only diagnostics. Launches isolated Chrome profiles, captures stderr and
GPU-process command lines, and extracts a compact set of ANGLE/GL/Metal lines.
It does not patch, sign, or replace Chrome.
"""
from __future__ import annotations

import argparse
import os
import re
import signal
import subprocess
import time
from pathlib import Path

CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
OUT = Path.home() / "Desktop/chrome-patcher-baseline/phase14"
PROFILES = {
    "normal": [],
    "angle-gl": ["--use-gl=angle", "--use-angle=gl"],
    "angle-metal": ["--use-gl=angle", "--use-angle=metal"],
}

PATTERNS = (
    re.compile(r"(egl|angle|opengl|metal|gl implementation|gpu process|context was lost|sharedimage|compoundimage)", re.I),
)

def quit_chrome() -> None:
    subprocess.run(
        ["/usr/bin/osascript", "-e", 'tell application "Google Chrome" to quit'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )
    time.sleep(1)
    subprocess.run(
        ["/usr/bin/pkill", "-f", str(CHROME)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )

def snapshot() -> str:
    p = subprocess.run(
        ["/usr/bin/pgrep", "-af", "Google Chrome"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
    )
    return p.stdout.strip()

def compact(lines: list[str], limit: int) -> list[str]:
    out, seen = [], set()
    for line in lines:
        s = line.strip()
        if not s or s in seen:
            continue
        if any(p.search(s) for p in PATTERNS):
            seen.add(s)
            out.append(s)
            if len(out) >= limit:
                break
    return out

def run_profile(name: str, flags: list[str], duration: float, limit: int) -> None:
    profile = OUT / "profiles" / name
    profile.mkdir(parents=True, exist_ok=True)
    log_path = OUT / f"{name}.log"
    snap_path = OUT / f"{name}.processes.txt"

    quit_chrome()
    cmd = [
        str(CHROME), *flags,
        "--user-data-dir=" + str(profile),
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-features=OptimizationGuideModelDownloading",
        "--enable-logging=stderr",
        "--v=1",
        "--vmodule=gpu*=2,gl*=2,angle*=2,command_buffer*=2",
        "chrome://gpu",
    ]
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write("$ " + " ".join(cmd) + "\n\n")
        proc = subprocess.Popen(
            cmd, stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            time.sleep(duration)
            snap = snapshot()
            snap_path.write_text(snap + "\n", encoding="utf-8")
        finally:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    hits = compact(lines, limit)
    print(f"\\n[{name}]")
    if hits:
        for line in hits:
            print("-", line)
    else:
        print("- no matching runtime lines captured")
    print("process snapshot:", snap_path)
    print("full log:", log_path)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--duration", type=float, default=8.0)
    ap.add_argument("--limit", type=int, default=25)
    ap.add_argument("--profiles", nargs="+", choices=sorted(PROFILES), default=list(PROFILES))
    a = ap.parse_args()

    if not CHROME.exists():
        print("REFUSED: Chrome executable not found")
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    print("=== Phase 14 ===")
    print("Mode: READ_ONLY")
    print("Runtime ANGLE/GL capture; no Chrome files are modified.")
    for name in a.profiles:
        run_profile(name, PROFILES[name], a.duration, a.limit)
    print("\nRESULT: READ_ONLY_RUNTIME_GL_CAPTURE")
    print("Use the extracted lines to identify the actual backend/gate before any patch work.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
