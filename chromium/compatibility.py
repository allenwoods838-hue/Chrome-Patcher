#!/usr/bin/env python3
"""Resolve hardware + Chromium milestone without modifying Chrome."""
from __future__ import annotations
import subprocess
from .milestone import compatibility_snapshot
from .profiles import resolve
from hardware.intel import _first_hex_device
from hardware.profiles import profile_for_device, PROFILES as HARDWARE_PROFILES

def detect_device_id():
    try:
        p = subprocess.run(["system_profiler", "SPDisplaysDataType"], text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        return _first_hex_device(p.stdout)
    except OSError:
        return None

def hardware_profile_name(device_id):
    selected = profile_for_device(device_id)
    for name, profile in HARDWARE_PROFILES.items():
        if profile is selected:
            return name
    return "generic"

def snapshot():
    versions = compatibility_snapshot()
    device_id = detect_device_id()
    hw_name = hardware_profile_name(device_id)
    compatibility = resolve(versions["chrome_milestone"], hw_name)
    if not versions["match"]:
        compatibility = {**compatibility, "status": "version-mismatch", "patch_status": "refused",
                         "reason": "Chrome application and Framework milestones do not match"}
    return {"versions": versions, "hardware_profile": hw_name, "compatibility": compatibility}

if __name__ == "__main__":
    s = snapshot()
    print(f"Hardware profile: {s['hardware_profile']}")
    print(f"Chrome milestone: {s['versions']['chrome_milestone'] or 'unknown'}")
    print(f"Framework milestone: {s['versions']['framework_milestone'] or 'unknown'}")
    print(f"App/framework match: {'yes' if s['versions']['match'] else 'NO'}")
    print(f"Compatibility: {s['compatibility']['status']} / patch={s['compatibility']['patch_status']}")
