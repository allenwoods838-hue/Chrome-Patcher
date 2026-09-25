#!/usr/bin/env python3
"""Phase 4: diagnostic-only Chrome GPU launch matrix."""
from __future__ import annotations
import argparse, os, shutil, signal, subprocess, tempfile, time
from pathlib import Path

CHROME=Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
OUT=Path.home()/"Desktop"/"chrome-patcher-baseline"/"phase4"
PROFILES={
 "normal":[],
 "desktop":["--use-gl=desktop"],
 "angle-gl":["--use-gl=angle","--use-angle=gl"],
 "angle-metal":["--use-gl=angle","--use-angle=metal"],
 "disable-gpu-sandbox":["--disable-gpu-sandbox"],
}
def run(cmd,timeout=8):
 try:
  p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout,check=False)
  return p.returncode,p.stdout
 except Exception as e: return -1,f"{type(e).__name__}: {e}\n"
def quit_existing():
 subprocess.run(["osascript","-e",'tell application "Google Chrome" to quit'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
 time.sleep(2)
 subprocess.run(["pkill","-f","/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
 time.sleep(1)
def snapshot():
 rc,out=run(["pgrep","-af","Google Chrome"],5)
 return out if rc==0 else ""
def launch(name,flags,duration):
 profile=Path(tempfile.mkdtemp(prefix=f"chrome-patcher-{name}-"))
 log=OUT/f"{name}.log"
 cmd=[str(CHROME),f"--user-data-dir={profile}","--no-first-run","--no-default-browser-check",
      "--disable-background-networking","--disable-features=OptimizationGuideModelDownloading",*flags,"chrome://gpu"]
 proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True)
 try:
  time.sleep(duration); proc.poll()
  live=proc.returncode is None
  body=[f"PROFILE={name}",f"COMMAND={' '.join(cmd)}",
        f"RETURN_CODE={proc.returncode if proc.returncode is not None else 'running'}",
        f"GPU_PAGE_LAUNCHED={live or proc.returncode==0}","","PROCESS_SNAPSHOT",snapshot()]
  log.write_text("\n".join(body),encoding="utf-8")
  if live:
   os.killpg(proc.pid,signal.SIGTERM)
   try: proc.wait(timeout=3)
   except subprocess.TimeoutExpired: os.killpg(proc.pid,signal.SIGKILL)
 finally: shutil.rmtree(profile,ignore_errors=True)
 return log
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--profiles",nargs="*",choices=list(PROFILES),default=list(PROFILES))
 ap.add_argument("--duration",type=float,default=6.0)
 args=ap.parse_args()
 if not CHROME.exists(): raise SystemExit(f"Chrome not found: {CHROME}")
 OUT.mkdir(parents=True,exist_ok=True); quit_existing()
 summary=[]
 for name in args.profiles:
  log=launch(name,PROFILES[name],args.duration); summary.append(f"{name}: {log}"); quit_existing()
 (OUT/"summary.txt").write_text("\n".join(summary)+"\n",encoding="utf-8")
 print(f"Results: {OUT}"); print("\n".join(summary))
if __name__=="__main__": main()
