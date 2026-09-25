"""Phase 9 Intel architecture registry. Detection/compatibility metadata only; no binary patch bytes."""
PROFILES = {
    "ivy_bridge": {"generation":"Ivy Bridge","device_ids":{0x0152,0x0166},"status":"diagnostic-only","patch_status":"not-approved"},
    "haswell": {"generation":"Haswell","device_ids":{0x0402,0x0412,0x0416,0x0D22},"status":"diagnostic-only","patch_status":"not-approved"},
    "broadwell": {"generation":"Broadwell","device_ids":{0x1616,0x161E,0x1626,0x1627},"status":"diagnostic-only","patch_status":"not-approved"},
    "skylake": {"generation":"Skylake","device_ids":{0x1912,0x1916,0x1926},"status":"diagnostic-only","patch_status":"not-approved"},
    "generic": {"generation":"unknown","device_ids":set(),"status":"diagnostic-only","patch_status":"not-approved"},
}
def profile_for_device(device_id: int | None):
    for name, profile in PROFILES.items():
        if device_id is not None and device_id in profile["device_ids"]: return profile
    return PROFILES["generic"]
if __name__ == "__main__":
    for name, profile in PROFILES.items(): print(f"{name}: {profile['status']} / patch={profile['patch_status']} / devices={len(profile['device_ids'])}")
