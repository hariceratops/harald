# [chore] Record the documentation rules in AGENTS.md

`AGENTS.md` says nothing about documentation, so the rules this sweep sets up are not stated where agents read them.

Depends on 028 to 035, since the section describes what they built. Spec: `dev/specs/structured-documentation.md`

## Acceptance Criteria

- `AGENTS.md` has a `## Documentation` section that says:
  - `docs/` is the user-facing description of behaviour, and the README is only a pitch that points to it
  - the build commands for the user guide and for `dev/docs/`
  - the checker's docstring defines the example syntax
  - a slice that changes user-visible behaviour updates the matching page in the same PR
  - when an example's output changes, the page is fixed and the example is never loosened
  - the README roadmap follows the briefs in `dev/inbox/`
  - the personal-data rule
- The section matches what issues 028–035 built.
