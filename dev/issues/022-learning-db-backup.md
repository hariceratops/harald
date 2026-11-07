# [feat] Back up learning.db with an explicit command

Open question 6 (spec) is resolved: only `harald-cli backup --to PATH`, no automatic copies. Depends on 010. Design: §10.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- `harald-cli backup --to PATH` writes a consistent copy of `learning.db` into the existing folder PATH, named `learning-<UTC stamp>.db`, and prints the path.
- It works while the TUI is grading in another session.
- A failed or interrupted backup leaves nothing under a `learning-*.db` name.
- A missing PATH, a PATH that is not a folder, or no `learning.db` exits 2 and writes nothing.
- It never overwrites or deletes a copy. Harald never makes a copy on its own and never reads one back.
- The user docs explain restoring by hand (design §10).
- Termux check (add to issue 009): a backup into `~/storage/shared/...` while the TUI is open.
