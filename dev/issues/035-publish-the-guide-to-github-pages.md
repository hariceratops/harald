# [chore] Publish the user guide to GitHub Pages

CI builds the docs but nothing is published. Deploy the guide from `main`, only after a strict build succeeds.

Depends on 028 and 030. Spec: `dev/specs/structured-documentation.md`

## Acceptance Criteria

- `.github/workflows/docs.yml` deploys the guide to GitHub Pages on a push to `main`, after the strict build succeeds. A failed build publishes nothing.
- The workflow also runs `uv run --frozen pytest tests/docs`, and the deploy is gated on it as well as on the strict build. This goes beyond the spec's strict-build gate, by the user's decision.
- Pull requests build the guide strictly and do not publish.
- CI uses the `uv run --with-requirements docs/requirements.txt` build command.
- `dev/docs/` is not built or published by the workflow.
- The README guide link points to the published URL.
- The one-time GitHub setting (Pages source set to GitHub Actions) is noted in `dev/docs/`.
