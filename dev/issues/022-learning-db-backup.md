# [feat] One-way backup of learning.db

Open question 6 (spec): how often the backup is written and how many copies are kept. Depends on 010.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- Harald writes a consistent copy of `learning.db` to a configurable backup folder (intended to be a send-only Syncthing folder to the desktop).
- The backup is never read back automatically.
