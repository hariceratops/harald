# [feat] TUI dictionary browsing, verified in Termux

Textual TUI for lookup and browsing. This slice also retires the spec's early risks before anything else builds on the TUI. Depends on 002.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- A Textual app offers German lookup and browsing of an entry in portrait, down to 40 columns.
- On the phone in Termux, the app suspends for `$EDITOR` and resumes cleanly. Verified by hand, with the result recorded in this issue.
- TUI startup time in Termux is measured and recorded in this issue.

## Status

Built and covered headlessly (pilot at 40x30, 40x12, 100x30; `harald` and
`harald tui` start the TUI). The 2nd and 3rd criteria are **not met** and need
a by-hand run in Termux; record the results here:

- [ ] Suspend for `$EDITOR` and resume cleanly. No screen calls an editor yet
  (`harald.editor` does not exist), so this needs a probe or a later slice.
- [ ] TUI startup time.
- [ ] Real row count in portrait with the keyboard up (§12.7 q4).
- [ ] Taps arrive as clicks, swipes as scroll.

## Review notes

- No `~N` fuzzy-distance marker or entry count on result rows: the model does
  not expose them.
- `tab` is not rebound; "tab or up from the first row returns to the Input"
  is not implemented.
- Use cases take `Config` and open the lexicon per call (design §11.2 says
  handles); one open per search and per "Also" row.
- `tests/unit/test_layering.py` now allows `harald.tui` as a front-end.

## Desktop observations on the real lexicon (2026-10-25)

Built with `harald-cli build --fetch`: 7 m 14 s, 468.2 MB, 102,897 entries.
`harald-cli lookup Hund` took 5.4 s (single core) because of a bad query plan
in the fuzzy candidate query, now fixed (about 1.1 s cold); the TUI's German
lookup runs the same query. Output wraps
correctly at 40 and 80 columns. Details in design §14.9.
- Search runs on Enter only, not as you type. Accepted by the user for now (2026-10-25).
