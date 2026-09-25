#!/usr/bin/env python3
"""Phase 16: static x86_64 mapping of the Chromium ANGLE/EGL gate.

Read-only. Maps relevant strings into the x86_64 __TEXT,__text section and
finds RIP-relative code references. Optionally asks LLDB for a small
disassembly window around each reference. No bytes are modified.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import subprocess
from pathlib import Path

FRAMEWORK = Path("/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Versions/Current/Google Chrome Framework")
OUT = Path.home() / "Desktop/chrome-patcher-baseline/phase16"

TARGETS = (
    "Requested GL implementation",
    "not found in allowed implementations",
    "angle=metal",
    "angle=opengl",
    "GetAllowedGLImplementation",
    "GetDisplayInitializationParams",
)

def run(*cmd: str, timeout: int = 30) -> str:
    p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       check=False, timeout=timeout)
    return p.stdout

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def parse_section_table(text: str) -> dict[str, tuple[int, int, int]]:
    sections: dict[str, tuple[int, int, int]] = {}
    seg = None
    current = None
    pending = {}
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"segname\s+(__\S+)", s)
        if m:
            seg = m.group(1)
            current = None
            pending = {}
            continue
        m = re.match(r"sectname\s+(__\S+)", s)
        if m and seg == "__TEXT":
            current = m.group(1)
            pending = {}
            continue
        if current is None or seg != "__TEXT":
            continue
        for key in ("addr", "size", "offset"):
            m = re.match(rf"{key}\s+(0x[0-9a-fA-F]+|\d+)", s)
            if m:
                pending[key] = int(m.group(1), 0)
        if {"addr", "size", "offset"} <= pending.keys():
            sections[current] = (pending["addr"], pending["size"], pending["offset"])
    return sections

def string_offsets() -> dict[str, list[int]]:
    text = run("/usr/bin/strings", "-a", "-t", "x", str(FRAMEWORK))
    found = {t: [] for t in TARGETS}
    for line in text.splitlines():
        m = re.match(r"^\s*([0-9a-fA-F]+)\s+(.*)$", line)
        if not m:
            continue
        off = int(m.group(1), 16)
        value = m.group(2)
        for target in TARGETS:
            if target in value:
                found[target].append(off)
    return found

def rip_refs(text_bytes: bytes, text_vmaddr: int, target_vmaddr: set[int]) -> list[tuple[int, int]]:
    refs: list[tuple[int, int]] = []
    n = len(text_bytes)

    for i in range(max(0, n - 6)):
        b0 = text_bytes[i]
        b1 = text_bytes[i + 1]
        if not 0x40 <= b0 <= 0x4f or b1 not in (0x8b, 0x8d, 0x89, 0x8a, 0x3b, 0x39, 0x81, 0x83):
            continue
        modrm = text_bytes[i + 2]
        if ((modrm >> 6) & 3) != 0 or (modrm & 7) != 5:
            continue
        disp = int.from_bytes(text_bytes[i + 3:i + 7], "little", signed=True)
        target = text_vmaddr + i + 7 + disp
        if target in target_vmaddr:
            refs.append((i, target))

    for i in range(max(0, n - 5)):
        if text_bytes[i] not in (0x8b, 0x8d, 0x89, 0x8a, 0x3b, 0x39):
            continue
        modrm = text_bytes[i + 1]
        if ((modrm >> 6) & 3) != 0 or (modrm & 7) != 5:
            continue
        disp = int.from_bytes(text_bytes[i + 2:i + 6], "little", signed=True)
        target = text_vmaddr + i + 6 + disp
        if target in target_vmaddr:
            refs.append((i, target))
    return refs

def disassemble(addr: int, count: int) -> str:
    lldb = shutil.which("lldb")
    if not lldb:
        return ""
    try:
        return run(
            lldb, "-b",
            "-o", f'target create --arch x86_64 "{FRAMEWORK}"',
            "-o", f"disassemble --start-address 0x{addr:x} --count {count}",
            "-o", "quit",
            timeout=45,
        )
    except subprocess.TimeoutExpired:
        return ""

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=24)
    ap.add_argument("--no-disassembly", action="store_true")
    args = ap.parse_args()

    print("=== Phase 16 ===")
    print("Mode: READ_ONLY")
    if not FRAMEWORK.exists():
        print("REFUSED: Chrome Framework not found")
        return 2

    OUT.mkdir(parents=True, exist_ok=True)
    framework_hash = sha256(FRAMEWORK)
    print("Framework SHA256:", framework_hash)
    print("Framework:", FRAMEWORK)
    print("file:", run("/usr/bin/file", str(FRAMEWORK)).strip())

    sections = parse_section_table(run("/usr/bin/otool", "-arch", "x86_64", "-l", str(FRAMEWORK)))
    if "__text" not in sections or "__cstring" not in sections:
        print("RESULT: READ_ONLY_STATIC_SCAN_INCOMPLETE")
        print("Reason: x86_64 __text/__cstring sections were not located.")
        return 0

    text_addr, text_size, text_off = sections["__text"]
    cstr_addr, cstr_size, cstr_off = sections["__cstring"]
    data = FRAMEWORK.read_bytes()
    text_bytes = data[text_off:text_off + text_size]

    found = []
    target_vms = set()
    for target, offsets in string_offsets().items():
        for off in offsets:
            if cstr_off <= off < cstr_off + cstr_size:
                vm = cstr_addr + off - cstr_off
                found.append((target, off, vm))
                target_vms.add(vm)

    print("Relevant strings:")
    if not found:
        print("- none found")
    else:
        for target, off, vm in found:
            print(f"- {target} file=0x{off:x} vm=0x{vm:x}")

    refs = rip_refs(text_bytes, text_addr, target_vms)
    print("RIP-relative references:", len(refs))
    full = [
        f"Framework SHA256: {framework_hash}",
        f"__text addr=0x{text_addr:x} size=0x{text_size:x} offset=0x{text_off:x}",
        f"__cstring addr=0x{cstr_addr:x} size=0x{cstr_size:x} offset=0x{cstr_off:x}",
        "",
        "Relevant strings:",
    ]
    for target, off, vm in found:
        full.append(f"{target} file=0x{off:x} vm=0x{vm:x}")

    for code_off, target in refs[:20]:
        addr = text_addr + code_off
        print(f"- code file=0x{text_off + code_off:x} vm=0x{addr:x} -> string=0x{target:x}")
        full.append(f"code file=0x{text_off + code_off:x} vm=0x{addr:x} -> string=0x{target:x}")
        if not args.no_disassembly:
            asm = disassemble(addr, args.count)
            if asm:
                path = OUT / f"disasm-0x{addr:x}.txt"
                path.write_text(asm, encoding="utf-8")
                print("  disassembly:", path)

    full.append("")
    full.append(f"RIP-relative references: {len(refs)}")
    (OUT / "static_gate.txt").write_text("\n".join(full) + "\n", encoding="utf-8")

    print("")
    print("RESULT: READ_ONLY_STATIC_GATE_MAPPING")
    print("Saved:", OUT / "static_gate.txt")
    print("No Chrome files were modified.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
