#!/usr/bin/env python3
"""Phase 7: evidence-based GPU validation.

Reads Phase 4 launch logs plus an optional chrome://gpu text report.
It does not patch Chrome. A process that merely starts is never treated as
hardware acceleration.
"""
from __future__ import annotations
import argparse
from pathlib import Path

OUT=Path.home()/"Desktop"/"chrome-patcher-baseline"/"phase4"
PROFILES=("normal","desktop","angle-gl","angle-metal","disable-gpu-sandbox")
ERRORS=("gpu process exited unexpectedly","gpu process unable to boot","context was lost","restarting gpu process")
SOFTWARE=("canvas: software only","compositing: software only","rasterization: software only","opengl: disabled","webgl: disabled","webgpu: disabled")
HARDWARE=("compositing: hardware accelerated","rasterization: hardware accelerated","opengl: enabled","webgl: hardware accelerated")

def classify(text:str)->tuple[str,list[str]]:
    t=text.lower()
    errors=[x for x in ERRORS if x in t]
    if errors: return "FAIL",errors
    hw=sum(x in t for x in HARDWARE)
    sw=sum(x in t for x in SOFTWARE)
    if hw>=2: return "HARDWARE_EVIDENCE",[x for x in HARDWARE if x in t]
    if sw>=2: return "SOFTWARE_OR_DISABLED",[x for x in SOFTWARE if x in t]
    return "UNKNOWN",[]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--gpu-report",type=Path,help="Text captured from chrome://gpu")
    args=ap.parse_args()
    report=""
    if args.gpu_report and args.gpu_report.exists():
        report=args.gpu_report.read_text(encoding="utf-8",errors="replace")
    print("=== Phase 7 GPU Validation ===")
    for name in PROFILES:
        p=OUT/f"{name}.log"
        if not p.exists():
            print(f"{name}: NO_DATA")
            continue
        text=p.read_text(encoding="utf-8",errors="replace")
        status,evidence=classify(text+"\n"+report)
        gpu_process=("gpu-process" in text.lower() or " gpu " in text.lower())
        print(f"{name}: {status}; gpu_process_snapshot={'yes' if gpu_process else 'no'}")
        if evidence: print("  evidence: "+", ".join(evidence))
    if not report:
        print("NOTE: no chrome://gpu report supplied; launch success alone is not acceleration evidence.")
    print(f"Logs: {OUT}")

if __name__=="__main__":
    main()
