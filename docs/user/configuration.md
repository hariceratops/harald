# Configuration

Harald runs with no configuration. To override, create
`~/.config/harald/config.toml` (or `$XDG_CONFIG_HOME/harald/config.toml`), or
pass `--config PATH` / set `HARALD_CONFIG`.

```toml
lexicon = "~/.local/share/harald/lexicon.db"
sources_dir = "~/.local/share/harald/sources"
staging_dir = "~/.cache/harald/staging"
build_min_entries = 50000
build_workers = 3
```

| Key | Default | Meaning |
|---|---|---|
| `lexicon` | `$XDG_DATA_HOME/harald/lexicon.db` | the built dictionary |
| `sources_dir` | `$XDG_DATA_HOME/harald/sources` | downloaded source files |
| `staging_dir` | `$XDG_CACHE_HOME/harald/staging` | build scratch space |
| `build_min_entries` | `50000` | a build with fewer entries is rejected |
| `build_workers` | CPU count − 1 (at least 1) | build worker processes |

Unknown keys are an error (exit 2), not ignored. The config is read by each
command, so a broken one does not break `--help`.
