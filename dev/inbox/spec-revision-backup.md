# Spec revision: backup is an explicit command

Raised 2026-11-05. Syncthing left the spec in `change/spec-mobile-first`, which left the `learning.db` backup bullet with no way off the device. The user chose an explicit `harald-cli backup --to PATH`. Line numbers refer to `dev/specs/harald-v1.md` as it is on main.

The user applies this after moving the spec out of `dev/specs/`.

## Lines to replace

**Lines 279-280 (the `learning.db` backup bullet)**
- "A consistent copy goes one way from the phone to the desktop as a backup, and is never read back automatically." becomes:
  - "`harald-cli backup --to PATH` writes a consistent copy of it into the folder PATH. It is the only way a copy leaves the device."
  - "Harald never makes a copy on its own and never reads one back."

**Lines 340-342 (open question 1)**
- "an escape route beyond the one-way backup" becomes "an escape route beyond the backup command".

**Lines 355-356 (open question 6)**
- "Resolved: after each session and on exit, plus `harald backup`, keeping 10 copies; see design §10." becomes "Resolved: only the explicit `harald-cli backup --to PATH`, with no automatic copies; see design §10."

## What this replaces

Question 6's old answer made a copy after each session and on exit, kept 10, and wrote to a configured `backup_dir`. The design's §10 describes that. This revision drops the automatic copies, the `backup_dir` setting and `backup_keep`. The user decides where the copy goes, each time, and the user's own sync or cloud app can watch that folder.

## What follows the spec

- Design §10 and everything that cites it (the 16 Syncthing mentions, the `backup.py` module, config, the migration section's use of the backup folder, the `prune` line in §16). Points for the architect:
  - PATH is a folder, and the file is named with a timestamp, so a second run never overwrites the first. No pruning.
  - A consistent copy means `VACUUM INTO` a partial file, then a rename, as §10 has it now.
  - It works while the TUI is open (WAL lets a reader copy).
  - Whether the TUI gets a backup entry or only the CLI does. This is not decided here.
  - Restoring is by hand (copy the file back). No restore feature.
- Issue 022: rewrite for the explicit command.
- Issues 004a and 009: Syncthing wording.
