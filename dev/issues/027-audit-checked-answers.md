# [chore] Audit the checked answers

Depends on 026, so the notes are in the data the audit reads. Brief: `dev/inbox/change3-typed-meaning-check.md`, decision D26.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- An audit script lists the failed checked reviews of English → German and German → German cards, one at a time, with the typed answer and the expected one. The user presses y when they were right.
- It runs after 200 checked reviews or two weeks of use, whichever comes first, and says how many reviews it covered.
- It reports the share of failed answers the user marked y, out of the checked reviews it covered. If more than 5% were, the output says a way to claim a right answer should be reconsidered.
- It only reads: it writes nothing to `learning.db`, and it stores no marks.
