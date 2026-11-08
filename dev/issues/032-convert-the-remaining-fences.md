# [chore] Convert the remaining fences and apply the personal-data rule

Only `lookup.md` is checked after 029. Bring every other page under the checker and the key-table test, with no page exempt.

Depends on 029 and 031. Spec: `dev/specs/structured-documentation.md`

## Acceptance Criteria

- Every `harald-cli` line in `docs/` is in a checked `console` block or marked `illustration`. The commands that cannot run in a test (`build --fetch`, `prune`, the Termux install) are marked `illustration`. The lint passes with no exemption.
- Examples show bare `harald-cli`. `docs/user/getting-started.md` explains `uv run` once, for the desktop.
- On `docs/user/getting-started.md` and `docs/user/study.md` only fences and key-table markup change. Their prose waits for the content pass.
- Examples use the sample lexicon's words and invented notes. The user's own cards, notes, words and setup appear nowhere.
- The Termux timing reads "about 11 minutes on a recent phone".
- The unused `admonition` extension is removed, or no checked fence sits inside any construct the checker cannot see.
- `uv run pytest` and the strict build pass.
