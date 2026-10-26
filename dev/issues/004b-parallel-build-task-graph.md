# [feat] Parallel build task graph

Populate `lexicon.db` through a task graph, with unrelated tasks run in worker processes, to cut build time (design estimate: about 2.5× on 4 cores; this issue measures it). The guarantees from 004a must hold at any worker count. Depends on 004a and 001.

Spec: `dev/specs/harald-v1.md`
Design: `dev/design/harald-v1.md` §3.7

## Acceptance Criteria

- Output is byte-identical for any `build_workers` value, including `0` (everything inline).
- A failing task cancels the remaining tasks and nothing is published; the previous `lexicon.db` is untouched.
- No shard or staging file survives a failure or Ctrl-C.
- The build prints per-step timings, and the measured speedup over `build_workers = 0` on the real English dump is recorded in the design.

## Review 2026-10-20
Findings are cross-cutting, from the review of the range 001–004b. They are filed here because 004b is the latest slice. Both are to be fixed together with the remaining review points at the end, not now.
- Use `click` instead of `argparse` for the CLI (`src/harald/cli.py`).
- Introduce a use-case/service abstraction: the CLI and other entry points call use-case services rather than the lower-level modules directly. The user found this more readable, and it is the structure used in the kohle project. Look at kohle for the shape before designing it. Likely needs a design note in `dev/design/harald-v1.md`.

## Update 2026-10-24
Both cross-cutting points above landed in `7e5c00e` and `fbe6864`: the CLI uses `click`, and front-ends call `use_cases/` classes (design §11). The "remaining review points" are now only the 005 findings and the 006 note.
