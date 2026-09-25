#!/usr/bin/env python3
"""Phase 7 runner: diagnostic matrix + evidence-based validation."""
from __future__ import annotations
import argparse, hashlib, subprocess
from pathlib import Path
CHROME=Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
FRAMEWORK=Path("/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Versions/Current/Google Chrome Framework")
OUT=Path.home()/"Desktop"/"chrome-patcher-baseline"/"phase7"
def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b): h.update(b)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--duration",type=float,default=8.0)
    args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    meta=[f"CHROME_EXISTS={CHROME.exists()}",f"FRAMEWORK_EXISTS={FRAMEWORK.exists()}"]
    if CHROME.exists(): meta.append("CHROME_VERSION="+subprocess.run([str(CHROME),"--version"],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT).stdout.strip())
    if FRAMEWORK.exists(): meta.append("FRAMEWORK_SHA256="+sha256(FRAMEWORK))
    (OUT/"environment.txt").write_text("\n".join(meta)+"\n",encoding="utf-8")
    cmd=["python3","phase4_diagnostic.py","--duration",str(args.duration)]
    print("Running Phase 4 diagnostic matrix...")
    raise SystemExit(subprocess.run(cmd,check=False).returncode)
if __name__=="__main__": main()
