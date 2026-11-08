# [chore] Split the developer docs from the user guide

The user guide and the developer notes share one site, and nothing validates the nav. Separate them so the guide can be published and checked on its own.

Spec: `dev/specs/structured-documentation.md`

## Acceptance Criteria

- `docs/developer/*` lives in `dev/docs/`, with its own strict `mkdocs.yml`. It builds locally and is never built in CI or published.
- The guide's index and nav no longer link to the developer pages, and no page in `docs/` links to them.
- `docs/roadmap.md` is removed and nothing links to it. The README roadmap stays as it is until issue 033.
- `docs/mkdocs.yml` fails the strict build on a page that exists on disk but is missing from the nav, and on a broken anchor.
- `mkdocs build --strict` passes for both sites.
