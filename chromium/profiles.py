#!/usr/bin/env python3
"""Chromium milestone compatibility registry; no patch bytes."""
from __future__ import annotations
from .m152 import PROFILE as M152
from .m153 import PROFILE as M153
from .m154 import PROFILE as M154
from .m155 import PROFILE as M155

PROFILES = {p["milestone"]: p for p in (M152, M153, M154, M155)}

def get(milestone: int):
    return PROFILES.get(milestone)

def resolve(milestone: int | None, hardware_profile: str | None = None) -> dict:
    if milestone is None:
        return {"status": "unsupported", "patch_status": "refused", "reason": "unknown milestone"}
    profile = get(milestone)
    if profile is None:
        return {"status": "unsupported", "patch_status": "refused", "milestone": milestone,
                "reason": "milestone profile not defined"}
    if hardware_profile and hardware_profile not in profile.get("intel_profiles", set()):
        return {**profile, "status": "unsupported-combination", "patch_status": "refused",
                "reason": f"hardware profile {hardware_profile} is not enabled for this milestone"}
    return dict(profile)

if __name__ == "__main__":
    for milestone, profile in sorted(PROFILES.items()):
        print(f"M{milestone}: {profile['status']} / patch={profile['patch_status']}")
    print("Unknown milestones: unsupported / patch=refused")
