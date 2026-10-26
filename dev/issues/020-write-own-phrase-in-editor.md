# [feat] Write your own phrase in $EDITOR

Like `git commit`. Depends on 019.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- `$EDITOR` opens a template with English, German and an optional note field.
- Saving the template empty or unchanged cancels.
- Saving with the English or German side missing reopens the editor with the error at the top and the user's text kept.
- In the TUI, the app suspends while the editor runs and resumes afterwards; the saved pair becomes a phrase card.
