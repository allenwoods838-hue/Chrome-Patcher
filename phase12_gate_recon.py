#!/usr/bin/env python3
"""Phase 12: Intel-specific Chromium/ANGLE gate reconnaissance.

Read-only static analysis. It does not patch, sign, launch, or replace Chrome.
"""
from __future__ import annotations
import argparse, hashlib, subprocess
from pathlib import Path

DEFAULT_FRAMEWORK = Path("/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Versions/Current/Google Chrome Framework")
OUT = Path.home() / "Desktop" / "chrome-patcher-baseline" / "phase12"
TERMS = ("GetAllowedGLImplementation", "GetDisplayInitializationParams", "InitializeGLOneOffscreen", "InitializeStaticGLBindings", "egl-angle", "angle=metal", "use-angle", "use-gl", "Requested GL implementation", "AllowedGL", "IOSurface", "SharedImage", "CompoundImageBacking")

def run(*cmd: str) -> str:
    try:
        p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        return p.stdout
    except OSError:
        return ""

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def string_offsets(data: bytes, needle: bytes) -> list[int]:
    out=[]; start=0
    while True:
        i=data.find(needle,start)
        if i<0: return out
        out.append(i); start=i+1

def context(data: bytes, offset: int, radius: int) -> str:
    chunk=data[max(0,offset-radius):offset+len(data[offset:offset+1])+radius]
    return "".join(chr(b) if 32<=b<127 else "." for b in chunk)

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--framework",type=Path,default=DEFAULT_FRAMEWORK)
    ap.add_argument("--radius",type=int,default=96)
    args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if not args.framework.exists():
        print(f"REFUSED: Framework not found: {args.framework}"); return 2
    data=args.framework.read_bytes()
    lines=["=== Chrome-Patcher Phase 12 Gate Reconnaissance ===",f"Framework: {args.framework}",f"Framework SHA256: {sha256(args.framework)}",f"Framework size: {len(data)} bytes","Mode: READ_ONLY","","Candidate term occurrences:"]
    total=0
    for term in TERMS:
        hits=string_offsets(data,term.encode())
        total+=len(hits); lines.append(f"- {term}: {len(hits)}")
        for off in hits:
            lines.append(f"  offset=0x{off:x} ({off})")
            lines.append(f"  context={context(data,off,args.radius)}")
    strings_out=OUT/"strings.txt"
    strings_out.write_text(run("/usr/bin/strings","-a",str(args.framework)),encoding="utf-8",errors="replace")
    lines += ["",f"Full strings output: {strings_out}",f"Total candidate occurrences: {total}","","Control-flow validation commands:","  otool -arch x86_64 -tvV '<Framework>'","  nm -arch x86_64 -nm '<Framework>'","  strings -a '<Framework>' | grep -E 'GetAllowedGLImplementation|GetDisplayInitializationParams|InitializeGL|SharedImage|CompoundImageBacking'","","Interpretation:","String proximity is not proof of the active code path.","An approved patch requires disassembly-level evidence tying the Intel failure path","to a unique instruction sequence and showing the replacement does not affect","unrelated GPU backends.","No patch bytes were generated or modified by Phase 12."]
    path=OUT/"gate_recon.txt"; path.write_text("\n".join(lines)+"\n",encoding="utf-8"); print("\n".join(lines)); print(f"Saved: {path}"); print("RESULT: READ_ONLY_GATE_RECON"); return 0

if __name__=="__main__": raise SystemExit(main())
