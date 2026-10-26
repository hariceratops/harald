# [feat] `harald check` after a rebuild

Repairs for cards whose lexicon entry changed, disappeared or became ambiguous. Depends on 004a and 010. Design: `dev/design/harald-v1.md` §8.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- After a rebuild, each card's link to `lexicon.db` is re-resolved without touching the card's own copy.
- Cards whose entry changed, disappeared or became ambiguous are listed only by `harald check`; nothing is shown automatically at startup.
- If an entry that cards were built from disappears or splits, those cards still study correctly from their own content.
- Upstream content is never taken over silently; changes apply only through a repair action the user chooses in `check`.
- `check` is reachable from the CLI and from the TUI (Home → Check); nothing is shown at startup.
- Each flagged card offers the actions its flag allows: relink, accept upstream, keep own copy.
- Accept shows a per-field diff and requires confirmation. By default, cards with a typed or keypress answer reset their schedule when that answer changes, and self-graded cards keep theirs; both are overridable. Review history is never modified.
- Keep on an ambiguous or disappeared card marks it unlinked. Unlinked cards are re-listed only when their candidate set changes; kept changed cards are re-listed only when upstream changes again.
- Every repair is recorded in the audit trail as one operation group.
- The CLI has a listing mode (exit 1 when anything is flagged), an interactive mode and per-card subcommands. All output fits 40 columns.
