#!/usr/bin/env python3
"""Read-only Phase 4 result checker."""
from pathlib import Path
OUT=Path.home()/"Desktop"/"chrome-patcher-baseline"/"phase4"
def main():
 for name in ["normal","desktop","angle-gl","angle-metal","disable-gpu-sandbox"]:
  p=OUT/f"{name}.log"
  if not p.exists(): print(f"{name}: no result"); continue
  t=p.read_text(encoding="utf-8",errors="replace").lower()
  markers=["gpu process exited unexpectedly","gpu process unable to boot","use-gl=disabled","disable-gpu-compositing"]
  print(f"{name}: failure markers present" if any(x in t for x in markers) else f"{name}: no failure marker in captured snapshot")
if __name__=="__main__": main()
