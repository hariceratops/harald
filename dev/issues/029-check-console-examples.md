# [feat] Check the console examples in the docs

Nothing in the docs is checked, so a renamed command or changed output goes unnoticed. Run every `console` fence in the normal test suite against a sample lexicon.

Depends on 028. Spec: `dev/specs/structured-documentation.md`

## Acceptance Criteria

- Every ` ```console ` fence in `docs/**/*.md` and `README.md` is a checked example. `$ ` lines are commands and the lines under each are the expected output. A module docstring in the checker defines the syntax.
- An optional `<!-- docs: ... -->` comment above a fence carries options from a closed vocabulary that includes `illustration`. An unknown option word is reported as a problem.
- The checker also reports a non-`harald-cli` command in a console block, a shell operator, a command that would prompt, and any `harald-cli` invocation outside a console fence that is not marked `illustration`.
- Examples run in `uv run pytest`, offline, against a small sample lexicon built from shipped sample sources, a scratch `learning.db` and a scratch config. The user's real files are never touched.
- Output is pinned to 80 columns, and any date or clock shown is pinned.
- Output must match exactly, line by line, ignoring trailing whitespace. An example whose output changes fails the suite.
- `docs/user/lookup.md` is converted as the first checked page.
- Every other `harald-cli` fence in `docs/` and the README's Quick start is marked `illustration`, so the suite stays green. Issue 032 converts them.
