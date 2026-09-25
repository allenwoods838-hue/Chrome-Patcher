#!/usr/bin/env python3
"""Intel GPU generation registry and conservative profile selection."""
from dataclasses import dataclass
import re, subprocess
from typing import Optional
@dataclass(frozen=True)
class IntelGPU:
    vendor: str
    device_id: Optional[int]
    model: str
    generation: str
    profile: str
DEVICE_GENERATIONS = {
    0x0152: ("Ivy Bridge", "HD Graphics 4000", "ivy_bridge"),
    0x0166: ("Ivy Bridge", "HD Graphics 4000", "ivy_bridge"),
    0x0402: ("Haswell", "HD Graphics", "haswell"),
    0x0412: ("Haswell", "HD Graphics 4400/4600", "haswell"),
    0x0416: ("Haswell", "HD Graphics 4400/4600", "haswell"),
    0x0D22: ("Haswell", "Iris Pro", "haswell"),
    0x1616: ("Broadwell", "HD Graphics 5500", "broadwell"),
    0x161E: ("Broadwell", "Iris Pro 6100", "broadwell"),
    0x1626: ("Broadwell", "HD Graphics 6000", "broadwell"),
    0x1627: ("Broadwell", "Iris Pro 6200", "broadwell"),
    0x1912: ("Skylake", "HD Graphics 530", "skylake"),
    0x1916: ("Skylake", "HD Graphics 520", "skylake"),
    0x1926: ("Skylake", "Iris Graphics 550", "skylake"),
}
def _run(*args: str) -> str:
    try:
        p = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        return p.stdout
    except OSError:
        return ""
def _first_hex_device(text: str) -> Optional[int]:
    patterns = (r"\bdevice\s*(?:id)?\s*[:=]?\s*0x([0-9a-fA-F]{4})\b", r"\bDevice\s+ID\s*[:=]\s*0x([0-9a-fA-F]{4})\b")
    for pattern in patterns:
        m = re.search(pattern, text, re.I)
        if m: return int(m.group(1), 16)
    return None
def detect() -> IntelGPU:
    text = _run("system_profiler", "SPDisplaysDataType")
    device_id = _first_hex_device(text)
    if device_id in DEVICE_GENERATIONS:
        generation, model, profile = DEVICE_GENERATIONS[device_id]
        return IntelGPU("Intel", device_id, model, generation, profile)
    if "Intel" in text: return IntelGPU("Intel", device_id, "Unknown Intel GPU", "unknown", "generic")
    return IntelGPU("Unknown", device_id, "Unknown GPU", "unknown", "generic")
if __name__ == "__main__":
    gpu = detect()
    device = f"0x{gpu.device_id:04x}" if gpu.device_id is not None else "unknown"
    print(f"Vendor: {gpu.vendor}")
    print(f"Device ID: {device}")
    print(f"Model: {gpu.model}")
    print(f"Generation: {gpu.generation}")
    print(f"Profile: {gpu.profile}")
