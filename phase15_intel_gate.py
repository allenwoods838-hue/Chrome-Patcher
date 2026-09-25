#!/usr/bin/env python3
"""Phase 15: compact Intel ANGLE/EGL gate capture.

Runs a focused, read-only GPU diagnostic on the exact installed Chrome build.
It captures deeper EGL/ANGLE initialization lines than Phase 14, but prints
only the small set of lines needed to decide what code path to investigate.

No Chrome file is patched, signed, replaced, or modified.
"""
from __future__ import annotations

import os
import re
import signal
import subprocess
import time
from pathlib import Path

CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
OUT = Path.home() / "Desktop/chrome-patcher-baseline/phase15"
PROFILES = {
    "angle-gl": ["--use-gl=angle", "--use-angle=gl"],
    "angle-metal": ["--use-gl=angle", "--use-angle=metal"],
}

NOISE = re.compile(
    r"(file_util_posix|Import Map|segmentation_platform|scheduler_loop_quarantine|"
    r"net/cert|new_tab_ui|mach_port_rendezvous|usb_context|No entry found)",
    re.I,
)
SIGNAL = re.compile(
    r"(requested gl implementation|allowed implementations|eglInitialize|EGL Driver message|"
    r"EGL_BAD_|EGL_NOT_|ANGLE.*(Display|initialize|error)|Metal|gl_display|"
    r"gl_initializer_mac|gpu_init|GPU process|initialization failed|context was lost)",
    re.I,
)

def run(*cmd: str) -> str:
    p = subprocess.run(
        cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False
    )
    return p.stdout.strip()

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

def compact(log_path: Path, limit: int = 12) -> list[str]:
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    result: list[str] = []
    seen: set[str] = set()
    for line in lines:
        s = line.strip()
        if not s or NOISE.search(s) or not SIGNAL.search(s):
            continue
        if s not in seen:
            seen.add(s)
            result.append(s)
            if len(result) >= limit:
                break
    return result

def run_profile(name: str, flags: list[str], duration: float) -> list[str]:
    profile = OUT / "profiles" / name
    profile.mkdir(parents=True, exist_ok=True)
    log_path = OUT / f"{name}.log"

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
        "--vmodule=gpu*=2,gl*=3,angle*=3,egl_util*=3,angle_platform_impl*=3,"
        "gl_display*=3,gl_initializer_mac*=3,command_buffer*=2",
        "chrome://gpu",
    ]
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write("$ " + " ".join(cmd) + "\n\n")
        proc = subprocess.Popen(
            cmd, stdout=log, stderr=subprocess.STDOUT, start_new_session=True
        )
        try:
            time.sleep(duration)
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
    return compact(log_path)

def summarize(hits: dict[str, list[str]]) -> str:
    gl_text = "\n".join(hits.get("angle-gl", []))
    metal_text = "\n".join(hits.get("angle-metal", []))
    lines = ["Phase 15 result", "Mode: READ_ONLY", ""]
    if "not found in allowed implementations" in gl_text and "angle=opengl" in gl_text:
        lines.append("OpenGL ANGLE: REJECTED by Chromium's allowed-implementation list.")
    else:
        lines.append("OpenGL ANGLE: no explicit allowed-list rejection captured.")
    if re.search(
        r"(eglInitialize|GLDisplayEGL::Initialize failed|Initialization of all \(1\) EGL display types failed)",
        metal_text, re.I
    ):
        lines.append("Metal ANGLE: selected/allowed, but EGL initialization failed.")
    else:
        lines.append("Metal ANGLE: no EGL initialization failure captured.")
    if "GPU process" in metal_text and "Exiting GPU process" in metal_text:
        lines.append("GPU process: initialization failure confirmed.")
    lines.append("")
    lines.append("Conclusion: investigate Chromium's removed/restricted OpenGL path and the Intel/OCLP Metal/EGL initialization path separately.")
    lines.append("Patch status: NOT APPROVED. No Chrome files were modified.")
    return "\n".join(lines) + "\n"

def main() -> int:
    if not CHROME.exists():
        print("REFUSED: Chrome executable not found")
        return 2

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.txt").write_text("", encoding="utf-8")

    version = run(str(CHROME), "--version")
    framework = Path(
        "/Applications/Google Chrome.app/Contents/Frameworks/"
        "Google Chrome Framework.framework/Versions/Current/Google Chrome Framework"
    )
    framework_sha = "missing"
    if framework.exists():
        import hashlib
        h = hashlib.sha256()
        with framework.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        framework_sha = h.hexdigest()

    hits: dict[str, list[str]] = {}
    print("=== Phase 15 ===")
    print("Mode: READ_ONLY")
    print("Chrome:", version)
    print("Framework SHA256:", framework_sha)
    print("")
    for name, flags in PROFILES.items():
        hits[name] = run_profile(name, flags, duration=10)
        print(f"[{name}]")
        for line in hits[name]:
            print("-", line)
        if not hits[name]:
            print("- no relevant ANGLE/EGL lines captured")
        print("")

    report = summarize(hits)
    (OUT / "report.txt").write_text(
        report + "\n" + "Full logs: " + str(OUT) + "\n",
        encoding="utf-8",
    )
    print(report)
    print("Saved:", OUT / "report.txt")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
