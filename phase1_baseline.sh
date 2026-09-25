#!/bin/bash
set -u
OUT="$HOME/Desktop/chrome-patcher-baseline"
mkdir -p "$OUT"
REPORT="$OUT/baseline.txt"
exec > >(tee "$REPORT") 2>&1

echo "=== Chrome-Patcher Phase 1 Baseline ==="
date
echo
echo "=== macOS ==="
sw_vers 2>/dev/null || true
echo
echo "=== Hardware ==="
system_profiler SPHardwareDataType 2>/dev/null || true
echo
echo "=== Graphics ==="
system_profiler SPDisplaysDataType 2>/dev/null || true
echo
echo "=== Native OpenGL Test ==="
if [ -x "$HOME/Desktop/test_opengl" ]; then
  "$HOME/Desktop/test_opengl" || true
else
  echo "No ~/Desktop/test_opengl binary found."
fi
echo
echo "=== Loaded Graphics Components ==="
kmutil showloaded 2>/dev/null | grep -Ei 'AppleIntel|IOGraphics|AppleGraphics' || true
echo
echo "=== Broadwell Graphics Files ==="
for p in \
  /Library/Extensions/AppleIntelBDWGraphics.kext \
  /Library/Extensions/AppleIntelBDWGraphicsFramebuffer.kext \
  /System/Library/Extensions/AppleIntelBDWGraphicsGLDriver.bundle \
  /System/Library/Extensions/AppleIntelBDWGraphicsMTLDriver.bundle \
  /System/Library/Extensions/AppleIntelBDWGraphicsVADriver.bundle \
  /System/Library/Extensions/AppleIntelBDWGraphicsVAME.bundle \
  /System/Library/Extensions/AppleIntelGraphicsShared.bundle
do
  if [ -e "$p" ]; then echo "PRESENT  $p"; else echo "MISSING  $p"; fi
done
echo
echo "=== IOGraphicsAccelerator ==="
kmutil showloaded 2>/dev/null | grep -i IOGraphicsAccelerator || true
echo
echo "=== Chrome ==="
if [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version || true
  codesign -dv --verbose=4 "/Applications/Google Chrome.app" 2>&1 | grep -E '^(Identifier|Authority|TeamIdentifier|Sealed Resources)' || true
  for p in \
    "/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Versions/Current/Libraries/libEGL.dylib" \
    "/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Versions/Current/Libraries/libGLESv2.dylib"
  do
    if [ -e "$p" ]; then
      echo "--- $p"; file "$p"; shasum -a 256 "$p" 2>/dev/null || true
    fi
  done
else
  echo "Google Chrome not found at /Applications/Google Chrome.app"
fi
echo
echo "=== Chrome Patcher Processes ==="
ps aux | grep -Ei '[c]hrome.*patch|[p]atch.py' || true
echo
echo "=== LaunchAgents ==="
launchctl list 2>/dev/null | grep -Ei 'chrome|patch' || true
find "$HOME/Library/LaunchAgents" -maxdepth 1 -type f \( -iname '*chrome*' -o -iname '*patch*' \) 2>/dev/null || true
echo
echo "=== Chrome Processes ==="
ps aux | grep -E '[G]oogle Chrome' || true
echo
echo "Report: $REPORT"
