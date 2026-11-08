# Harald developer notes

Architecture, test layers, build internals and the working conventions. These
pages are for changing Harald; the user guide is under `docs/`.

This site is built and read locally only. It is not built in CI and not
published. Serve it from the repository root with

```sh
uv run --with-requirements docs/requirements.txt mkdocs serve -f dev/docs/mkdocs.yml
```

or render it once into `site-dev/` with `mkdocs build --strict` in place of
`serve`.
