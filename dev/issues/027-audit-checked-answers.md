# [chore] Audit the checked answers

Depends on 026, so the notes are in the data the audit reads. Brief: `dev/inbox/change3-typed-meaning-check.md`, decision D26.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- A script reads `learning.db` and lists the checked reviews of English → German and German → German cards with their typed answers, the stored answer and the grade given.
- It runs after 200 checked reviews or two weeks of use, whichever comes first, and says how many reviews it covered.
- It reports the share of answers the user marks as failed wrongly. If more than 5% were, the output says a way to claim a right answer should be reconsidered.
- It only reads: it writes nothing to `learning.db`.
