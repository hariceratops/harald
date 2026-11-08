# [chore] Cut the README to the pitch

The README repeats the feature list and carries a second roadmap. Reduce it to a pitch that points to the guide.

Depends on 029 and 030. Spec: `dev/specs/structured-documentation.md`

## Acceptance Criteria

- The README holds only:
  - the pitch (the existing "reading, TV and conversation" line stays)
  - a short taste, as a checked `console` block (for example `lookup lief` and `lookup --en use`)
  - a link to the guide
  - how to read the guide locally, using the `uv run --with-requirements` command
  - the licence and data note
  - the one roadmap, which follows the briefs in `dev/inbox/`
- The feature list moves into the guide, and nothing it said is lost.
- The README links to the published guide and to no removed page.
- `uv run pytest` and the strict build pass.
