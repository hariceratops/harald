# [feat] Check German → German answers

Depends on 023 and 014. Brief: `dev/inbox/change3-typed-meaning-check.md`, decisions D17–D24, D37 and D20.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- On a German → German card, Enter checks the typed answer with the same rules as 023, and with 024's slip and retry rules once that has landed.
- The card shows the German definition and the part of speech; the card stores the sense's labels.
- Gender comes from the entry the card's own sense came from: a German definition takes the German entry's gender, even when English senses of a homograph are picked in the same add.
- A German → German card created before this change keeps studying: it reads as having no stored labels and still works.
- The checked card fits at 40x30, 40x12 and 100x30, with no vertical scrolling at 40x12 for the test fixtures.
- Before this issue is built, the brief's measurement of German definitions that contain their own lemma (F4) is recorded here.
