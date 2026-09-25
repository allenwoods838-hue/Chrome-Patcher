#!/usr/bin/env python3
"""Milestone profile registry for Intel Chromium diagnostics."""
from .m152 import PROFILE as M152
from .m153 import PROFILE as M153
from .m154 import PROFILE as M154
from .m155 import PROFILE as M155
PROFILES={p["milestone"]:p for p in (M152,M153,M154,M155)}
def get(milestone:int):
    return PROFILES.get(milestone)
if __name__=="__main__":
    for milestone, profile in sorted(PROFILES.items()):
        print(f"M{milestone}: {profile['status']} / patch={profile['patch_status']}")
