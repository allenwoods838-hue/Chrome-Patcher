#!/usr/bin/env python3
"""Phase 8: safe Chrome Framework restore.

Restore only from backups created by the patch engine. Default is a dry-run.
The command refuses to overwrite Chrome unless the selected backup exists,
the target is present, and the backup is a valid file. It records hashes before
and after the operation. It never changes system graphics, OCLP, or LaunchAgents.
"""
from __future__ import annotations
import argparse, hashlib, shutil, subprocess, sys
from pathlib import Path

FRAMEWORK=Path("/Applications/Google Chrome.app/Contents/Frameworks/Google Chrome Framework.framework/Versions/Current/Google Chrome Framework")
BACKUP_ROOT=Path.home()/"Desktop"/"chrome-patcher-baseline"/"backups"
MANIFEST=BACKUP_ROOT/"restore-manifest.txt"

def sha256(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def chrome_running()->bool:
    p=subprocess.run(["pgrep","-f","/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    return p.returncode==0

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--backup",help="Backup filename under the patcher backup directory.")
    ap.add_argument("--apply",action="store_true",help="Perform the restore after all checks pass.")
    args=ap.parse_args()

    if not BACKUP_ROOT.exists():
        print(f"REFUSED: backup directory not found: {BACKUP_ROOT}")
        return 2
    if not FRAMEWORK.exists():
        print(f"REFUSED: Chrome Framework not found: {FRAMEWORK}")
        return 2

    backups=sorted(p for p in BACKUP_ROOT.glob("Chrome-Framework-*.bak") if p.is_file())
    if args.backup:
        candidate=BACKUP_ROOT/args.backup
        if candidate not in backups:
            print("REFUSED: requested backup is not a patcher backup.")
            return 2
    else:
        if not backups:
            print("REFUSED: no patcher backups found.")
            return 2
        candidate=backups[-1]

    current_hash=sha256(FRAMEWORK)
    backup_hash=sha256(candidate)
    print("=== Phase 8 Restore Gate ===")
    print(f"Target: {FRAMEWORK}")
    print(f"Backup: {candidate}")
    print(f"Current SHA256: {current_hash}")
    print(f"Backup SHA256: {backup_hash}")
    print(f"Chrome running: {'yes' if chrome_running() else 'no'}")

    if chrome_running():
        print("REFUSED: Chrome is running. Quit Chrome before restoring.")
        return 2
    if candidate.stat().st_size==0:
        print("REFUSED: backup is empty.")
        return 2
    if current_hash==backup_hash:
        print("ALREADY_RESTORED: target already matches selected backup.")
        return 0
    if not args.apply:
        print("DRY RUN: no files modified. Use --apply after reviewing the backup/hash.")
        return 0

    tmp=FRAMEWORK.with_name(FRAMEWORK.name+".restore.tmp")
    shutil.copy2(candidate,tmp)
    if sha256(tmp)!=backup_hash:
        tmp.unlink(missing_ok=True)
        print("REFUSED: temporary restore failed hash verification.")
        return 2
    shutil.copystat(candidate,tmp,follow_symlinks=True)
    tmp.replace(FRAMEWORK)
    final_hash=sha256(FRAMEWORK)
    if final_hash!=backup_hash:
        print("ERROR: final hash does not match backup.")
        return 3
    MANIFEST.parent.mkdir(parents=True,exist_ok=True)
    with MANIFEST.open("a",encoding="utf-8") as f:
        f.write(f"RESTORED backup={candidate.name} sha256={final_hash}\n")
    print(f"RESTORED: {FRAMEWORK}")
    print(f"Restored SHA256: {final_hash}")
    print("NOTE: macOS code-signing state may need to be re-established by the Chrome installer/update process.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
