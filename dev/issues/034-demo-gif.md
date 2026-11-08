# [feat] Add a demo GIF of the README taste

Give the README a recording of the taste block, kept honest by a test.

Depends on 033. Spec: `dev/specs/structured-documentation.md`

## Acceptance Criteria

- A VHS tape records the README taste at 80 columns. The tape and the GIF are checked in, and the README embeds the GIF.
- A test fails if the tape's commands differ from the README block in text or order.
- The steps to regenerate the GIF by hand are in `dev/docs/`.
- The GIF is not regenerated in CI or in the test suite.
