"""Chrome 154 milestone profile. First Broadwell diagnostic target."""
PROFILE = {
    "milestone": 154, "name": "M154", "status": "diagnostic-only",
    "intel_profiles": {"ivy_bridge","haswell","broadwell","skylake"},
    "patch_status": "not-approved",
    "primary_target": {"generation":"Broadwell","device_id":0x1626,"model":"HD Graphics 6000"},
}
