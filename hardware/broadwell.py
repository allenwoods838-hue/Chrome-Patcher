"""Broadwell detection profile. Detection metadata only; no Chrome or system modification."""
BROADWELL_DEVICE_IDS = {0x1616, 0x161E, 0x1626, 0x1627}
SUPPORTED_PROFILE = {"generation": "Broadwell", "macos_scope": "Sequoia", "chromium_scope": "153", "status": "diagnostic-only"}
def matches(device_id: int) -> bool:
    return device_id in BROADWELL_DEVICE_IDS
