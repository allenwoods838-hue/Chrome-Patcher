#!/usr/bin/env python3
"""Phase 13: compact Chromium 154 ANGLE/GL candidate scan.

Read-only. Prints only a short list of relevant strings from the exact
installed Chrome Framework. It does not patch, sign, launch, or replace Chrome.
"""
from __future__ import annotations
import argparse, hashlib, re, subprocess
from pathlib import Path

FRAMEWORK = Path("/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Versions/Current/Google Chrome Framework")
PATTERNS = (
    r"egl-angle", r"angle=metal", r"use-angle", r"use-gl",
    r"Requested GL implementation", r"AllowedGL", r"ANGLE",
    r"OpenGL", r"Metal", r"SharedImage", r"CompoundImageBacking",
)
def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--framework",type=Path,default=FRAMEWORK)
    ap.add_argument("--limit",type=int,default=20)
    a=ap.parse_args()
    if not a.framework.exists():
        print("REFUSED: Framework not found"); return 2
    try:
        raw=subprocess.run(["/usr/bin/strings","-a",str(a.framework)],text=True,
                           stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,check=False).stdout
    except OSError:
        print("REFUSED: strings unavailable"); return 2
    hits=[]; seen=set()
    for line in raw.splitlines():
        s=line.strip()
        if not s or len(s)>180: continue
        if any(re.search(p,s,re.I) for p in PATTERNS) and s not in seen:
            seen.add(s); hits.append(s)
    print("=== Phase 13 ===")
    print("Mode: READ_ONLY")
    print("Framework SHA256:",sha256(a.framework))
    print("Candidates:")
    for s in hits[:a.limit]: print("-",s)
    print("Candidate count:",len(hits))
    print("RESULT: READ_ONLY_CANDIDATE_SCAN")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
