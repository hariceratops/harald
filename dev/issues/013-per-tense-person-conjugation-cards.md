# [feat] Per-(tense, person) conjugation cards on request

Depends on 012. Open question 5 is resolved in design §7.12. This slice also removes the TRENNBAR badge from the Stammformen card.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- For a verb, the user can choose from the 14 tenses and get one card per (tense, person) for those tenses. The six persons are ich, du, er/sie/es, wir, ihr and sie/Sie; formal Sie is not a separate person and there is no imperative. Conjugation cards can be requested on a later add without picking a sense.
- The answer is the verb form without the pronoun, as the data gives it; any form listed for that slot is accepted. Answers are typed and checked exactly, with ae/oe/ue/ss accepted for ä/ö/ü/ß.
- Missing forms are refused per (tense, person), with the missing forms named; the chosen tense's other persons are still created.
- Neither the conjugation card nor the Stammformen card shows a TRENNBAR badge or a split-form hint.

## Status

Built in seven commits, plus docs, review fixes and the Add word hint. All four criteria are met in unit, component and
pilot tests at 40x30, 40x12 and 100x30. Smoke-tested by hand on `anrufen`
as far as the Add word steps; the conjugation study card and typing on the
Termux soft keyboard are not yet checked by hand. Decisions and
departures are in design §7.12.

After review: the study card now redraws on resize, both typed cards show
the digraph hint under the fields, and the footers in the wireframes match
the built screens (see issue 014). Accepted 2026-10-30 and not built yet:
the conjugation check will accept the reflexive pronoun (design §16).

## Review 2026-10-27
- `learning/content.py`: `_conjugation_cards` returned `Refusal | None`;
  AGENTS.md wants `Option` for an expected no-value. Fixed by returning a
  list.
- Found in the smoke run: the Add word steps gave no hint that a row must
  be ticked with `space`, so Next with nothing ticked ended on "nothing
  new". Fixed in 3c55951.

## Review 2026-10-27 (range dbab7cb..HEAD)
- `tui/addword.py`: the "Nothing was ticked" line on Confirm tested the
  forms found, not the picks, so ticking a tense whose forms are all missing
  said nothing was ticked above the refusal. It now tests the picks.
- Two comments explained WHAT: the `check_conjugation` docstring and the
  slot-format comment in `lexicon/model.py`. Removed.
- Stale artifacts: the note above saying the hint was unfixed, and the
  commit count in Status.
- Design §7.12 and §12 Add word wireframes and the user guide did not show
  the picker hint or the "Nothing was ticked" line.
