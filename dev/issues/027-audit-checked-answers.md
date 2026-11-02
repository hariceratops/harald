# [chore] Audit the checked answers

Depends on 026, so the notes are in the data the audit reads. Brief: `dev/inbox/change3-typed-meaning-check.md`, decision D26.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- An audit script lists the failed checked reviews of English → German and German → German cards, one at a time, with the typed answer and the expected one. The user presses y when they were right.
- It runs after 200 checked reviews or two weeks of use, whichever comes first, and says how many reviews it covered.
- It reports the share of failed answers the user marked y, out of the checked reviews it covered. If more than 5% were, the output says a way to claim a right answer should be reconsidered.
- It only reads: it writes nothing to `learning.db`, and it stores no marks.

## Status

Built: `dev/audit/checked_answers.py`, a stdlib `sqlite3` script. Run `python dev/audit/checked_answers.py PATH_TO_COPY_OF_LEARNING_DB` on a copy of the newest phone backup. It opens the file with `mode=ro`, so a missing file is reported and not created, and it stores nothing.

- Checked reviews are `review` rows of `meaning_en_de` and `meaning_de_de` cards whose `answer` is not NULL. Self-graded `meaning_de_en` and old reviews with NULL answers are ignored.
- It lists the Again reviews one at a time with the typed answer (both tries as stored `first | second`) and the expected article and lemma. `y` marks "I was right"; Enter or `n` means no; `q` stops asking. EOF counts as `q`. Empty answers are counted, not asked.
- It prints the checked reviews covered, the failed and empty counts, and whether the 200-review or 14-day threshold is reached (it says "neither" and still runs). The 14 days run from the first checked review to the script's run time.
- The share is `y` marks over all checked reviews covered (so quitting early lowers it). Above 5% it says a way to claim a right answer should be reconsidered.
- Pure parts are `checked`, `to_ask`, `share`; tests in `tests/component/test_audit_checked_answers.py` check the counts, share, message, thresholds and that the database file is byte-identical after a run.
- Not done, as the design leaves it: recomputing verdicts with `check_meaning`/`known_words` and recording the lexicon's sha256 (the design says the audit "can" and "records" it, but the issue's criteria and the stdlib-only script do not need it).
