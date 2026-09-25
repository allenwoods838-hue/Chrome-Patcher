#!/usr/bin/env python3
"""Chromium milestone detection with app/framework consistency checks."""
from __future__ import annotations
import re
import subprocess
from pathlib import Path
from typing import Optional

CHROME = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
FRAMEWORK_CURRENT = Path("/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Versions/Current")

def parse_milestone(version: str) -> Optional[int]:
    m = re.search(r"\b(\d+)\.\d+\.\d+\.\d+\b", version)
    return int(m.group(1)) if m else None

def _run(*cmd: str) -> str:
    try:
        p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        return p.stdout.strip()
    except OSError:
        return ""

def installed_chrome_version() -> str:
    return _run(str(CHROME), "--version") if CHROME.exists() else ""

def framework_path() -> Path:
    return FRAMEWORK_CURRENT / "Google Chrome Framework"

def framework_version_label() -> str:
    try:
        return FRAMEWORK_CURRENT.resolve().name
    except OSError:
        return ""

def installed_framework_milestone() -> Optional[int]:
    return parse_milestone(framework_version_label())

def installed_milestone() -> Optional[int]:
    return parse_milestone(installed_chrome_version())

def compatibility_snapshot() -> dict:
    chrome_version = installed_chrome_version()
    chrome_milestone = parse_milestone(chrome_version)
    framework_label = framework_version_label()
    framework_milestone = parse_milestone(framework_label)
    return {
        "chrome_version": chrome_version,
        "chrome_milestone": chrome_milestone,
        "framework_label": framework_label,
        "framework_milestone": framework_milestone,
        "match": chrome_milestone is not None and framework_milestone is not None
        and chrome_milestone == framework_milestone,
    }

if __name__ == "__main__":
    s = compatibility_snapshot()
    print(f"Chrome: {s['chrome_version'] or 'not found'}")
    print(f"Chrome milestone: {s['chrome_milestone'] or 'unknown'}")
    print(f"Framework version: {s['framework_label'] or 'unknown'}")
    print(f"Framework milestone: {s['framework_milestone'] or 'unknown'}")
    print(f"Version match: {'yes' if s['match'] else 'NO — refuse milestone-specific patching'}")
