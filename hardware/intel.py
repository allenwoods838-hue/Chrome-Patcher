#!/usr/bin/env python3
"""Read-only Intel GPU identification for Chrome-Patcher Phase 3."""
from dataclasses import dataclass
import re, subprocess
from typing import Optional
@dataclass(frozen=True)
class IntelGPU:
 vendor:str; device_id:Optional[int]; model:str; generation:str; profile:str
DEVICE_GENERATIONS={0x0152:("Ivy Bridge","HD Graphics 4000","ivy_bridge"),0x0166:("Ivy Bridge","HD Graphics 4000","ivy_bridge"),0x0402:("Haswell","HD Graphics","haswell"),0x0412:("Haswell","HD Graphics 4400/4600","haswell"),0x0416:("Haswell","HD Graphics 4400/4600","haswell"),0x0D22:("Haswell","Iris Pro","haswell"),0x1616:("Broadwell","HD Graphics 5500","broadwell"),0x161E:("Broadwell","Iris Pro 6100","broadwell"),0x1626:("Broadwell","HD Graphics 6000","broadwell"),0x1627:("Broadwell","Iris Pro 6200","broadwell"),0x1912:("Skylake","HD Graphics 530","skylake"),0x1916:("Skylake","HD Graphics 520","skylake"),0x1926:("Skylake","Iris Graphics 550","skylake")}
def _run(*args):
 try:
  p=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=False); return p.stdout
 except OSError:return ""
def _first_hex_device(text):
 for pat in [r"\bdevice\s*(?:id)?\s*[:=]?\s*0x([0-9a-fA-F]{4})\b",r"\bDevice\s+ID\s*[:=]\s*0x([0-9a-fA-F]{4})\b"]:
  m=re.search(pat,text,re.I)
  if m:return int(m.group(1),16)
 return None
def detect():
 g=_run("system_profiler","SPDisplaysDataType"); d=_first_hex_device(g)
 if d in DEVICE_GENERATIONS:
  gen,model,profile=DEVICE_GENERATIONS[d]; return IntelGPU("Intel",d,model,gen,profile)
 if "Intel" in g:return IntelGPU("Intel",d,"Unknown Intel GPU","unknown","generic")
 return IntelGPU("Unknown",d,"Unknown GPU","unknown","generic")
if __name__=="__main__":
 g=detect(); d=f"0x{g.device_id:04x}" if g.device_id is not None else "unknown"
 print(f"Vendor: {g.vendor}"); print(f"Device ID: {d}"); print(f"Model: {g.model}"); print(f"Generation: {g.generation}"); print(f"Profile: {g.profile}")
