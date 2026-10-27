# [feat] Per-(tense, person) conjugation cards on request

Depends on 012. Open question 5 is resolved in design §7.12. This slice also removes the TRENNBAR badge from the Stammformen card.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- For a verb, the user can choose from the 14 tenses and get one card per (tense, person) for those tenses. The six persons are ich, du, er/sie/es, wir, ihr and sie/Sie; formal Sie is not a separate person and there is no imperative. Conjugation cards can be requested on a later add without picking a sense.
- The answer is the verb form without the pronoun, as the data gives it; any form listed for that slot is accepted. Answers are typed and checked exactly, with ae/oe/ue/ss accepted for ä/ö/ü/ß.
- Missing forms are refused per (tense, person), with the missing forms named; the chosen tense's other persons are still created.
- Neither the conjugation card nor the Stammformen card shows a TRENNBAR badge or a split-form hint.

## Status

Built in seven commits. All four criteria are met in unit, component and
pilot tests at 40x30, 40x12 and 100x30. Smoke-tested by hand on `anrufen`
as far as the Add word steps; the conjugation study card and typing on the
Termux soft keyboard are not yet checked by hand. Decisions and
departures are in design §7.12.

## Review 2026-10-27
- `learning/content.py`: `_conjugation_cards` returned `Refusal | None`;
  AGENTS.md wants `Option` for an expected no-value. Fixed by returning a
  list.
- Found in the smoke run, not fixed here: the Add word steps give no hint
  that a row must be ticked with `space`, so Next with nothing ticked ends
  on "nothing new". A separate change.
