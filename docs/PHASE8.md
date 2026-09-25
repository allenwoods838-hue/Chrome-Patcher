# Phase 8 — Safe Full Restore System

## Goal

Phase 8 provides a controlled rollback path for any future Chrome Framework modification.

The restore tool:

- uses only backups created under the patcher backup directory;
- verifies the selected backup exists and is non-empty;
- refuses to restore while Chrome is running;
- shows current and backup SHA-256 hashes;
- defaults to dry-run;
- verifies a temporary copy before replacing the Framework;
- verifies the final Framework hash after replacement;
- records successful restores in a manifest.

## Files

- `restore.py` — guarded restore/rollback tool.
- `backups/` — runtime backup location on the user's Desktop, not a repository payload.

## Dry-run

List available backups:

```bash
ls -lh ~/Desktop/chrome-patcher-baseline/backups/
```

Preview the most recent backup:

```python3 restore.py
```

Preview a specific backup:

```python3 restore.py --backup Chrome-Framework-154-XXXXXXXXXXXXXXX.bak
```

No files are changed without `--apply`.

## Apply

First quit Chrome completely:

```bash
osascript -e 'tell application "Google Chrome" to quit'
pkill -f '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' 2>/dev/null || true
```

Then perform the restore:

```bash
python3 restore.py --apply
```

Or select a specific backup:

```bash
python3 restore.py --backup <backup-file> --apply
```

## Safety boundaries

Phase 8 does **not**:

- patch Chrome;
- generate patch bytes;
- modify Apple graphics kexts;
- modify OCLP;
- install or remove LaunchAgents;
- change system settings;
- restore arbitrary files outside the patcher backup directory.

The target is only the current Google Chrome Framework binary.

## Important signing note

A restored Framework should match the selected backup byte-for-byte, but modifying/restoring a Framework can affect its code-signing state. If Chrome refuses to launch afterward, reinstalling the same Chrome build is the cleanest way to restore the vendor-signed application bundle.

## Success criteria

A restore is successful only when the final Framework SHA-256 exactly equals the selected backup SHA-256.
