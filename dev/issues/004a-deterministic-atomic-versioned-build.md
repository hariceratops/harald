# [feat] Deterministic, atomic, versioned build

Lock in the rebuild guarantees from the spec early, so every later slice that touches the build has to preserve them. Runs in a single process (`build_workers = 0`); the parallel task graph is 004b. Depends on 001.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- Rebuilding from the same local files leaves the existing `lexicon.db` byte-for-byte untouched (same mtime and hash), so Syncthing has nothing to resend.
- Killing the build mid-run (Ctrl-C or crash) leaves the previous `lexicon.db` intact; no partial file appears at the final path.
- If the Harald version and the `lexicon.db` schema version don't match, Harald refuses to start and names both versions.
