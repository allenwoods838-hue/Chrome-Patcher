#!/usr/bin/env python3
"""Chromium milestone parsing for Phase 3. Metadata only; never changes Chrome."""
import re
import subprocess
from typing import Optional

def parse_milestone(version: str) -> Optional[int]:
    m = re.search(r"\b(\d+)\.\d+\.\d+\.\d+\b", version)
    return int(m.group(1)) if m else None

def installed_chrome_version() -> str:
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    try:
        p = subprocess.run([chrome, "--version"], text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, check=False)
        return p.stdout.strip()
    except OSError:
        return ""

def installed_milestone() -> Optional[int]:
    return parse_milestone(installed_chrome_version())

if __name__ == "__main__":
    version = installed_chrome_version()
    print(f"Chrome: {version or 'not found'}")
    print(f"Milestone: {installed_milestone() or 'unknown'}")
