# Spec revision: mobile first, no Syncthing

Raised 2026-11-04. A Pixel 9 builds the lexicon in Termux in about 11 minutes (fetch about 200 s, build about 460 s), so the lexicon is built where Harald runs and Syncthing leaves the spec. The desktop keeps working. The app is mobile first, not mobile only. The code, AGENTS.md, README and user docs already say this (change/build-local). Line numbers refer to `dev/specs/harald-v1.md` as it is on main.

The user applies this after moving the spec out of `dev/specs/`, together with `spec-revision-typed-check-gaps.md`.

## Lines to replace

**Lines 9-10**
- "commands for one-shot lookups and the scriptable desktop build." becomes "commands for one-shot lookups and the scriptable build."

**Lines 16-19**
- "The dictionary is built on a desktop from Wiktionary (kaikki.org wiktextract) and Tatoeba data, then pushed one way to a phone. Studying happens on the phone in Termux, in spare moments." becomes "The dictionary is built from Wiktionary (kaikki.org wiktextract) and Tatoeba data with one command, on the device the learner uses. The app is mobile first: studying happens on the phone in Termux, in spare moments, and the desktop works the same way."

**Line 34**
- "the desktop `build` (with `--fetch`), which must stay scriptable;" becomes "`build` (with `--fetch`), which must stay scriptable;".

**Line 188**
- "**Data build (desktop)**" becomes "**Data build**".

**Lines 206-207**
- "`lexicon.db` byte-for-byte untouched, so Syncthing has nothing to resend." becomes "`lexicon.db` byte-for-byte untouched."

**Line 258, heading**
- "**Two databases, two machines.**" becomes "**Two databases.**"

**Lines 261-263 (the `lexicon.db` bullets)**
- Replace "Built on the desktop." and "Pushed one way to the phone by Syncthing, which is send-only on the desktop." with "Built where Harald runs, with `harald-cli build --fetch`."
- Add: "The downloaded sources (about 3.4 GB) can be deleted with `harald-cli prune`; a rebuild then downloads them again."
- "About 1 GB is acceptable." stays (the real file is 468 MB).

**Line 298**
- "`lexicon.db` intact, and a partial file never reaches the phone." becomes "`lexicon.db` intact, and a partial file is never published."

**Lines 268-271 (the `learning.db` bullets): needs a decision**
- "Lives on the phone, which is its only writer." and "Is never synced two ways." can stay if the phone is where Harald runs.
- "A consistent copy goes one way from the phone to the desktop as a backup, and is never read back automatically." depended on Syncthing. Without it the backup needs another way off the device. This is issue 022 and the design's §10. Options:
  - a copy written to a configurable folder (the user's own sync tool or cloud app picks it up);
  - an explicit `harald-cli backup --to PATH`;
  - drop the backup from v1.
- Until the user decides, leave the bullet as it is and say so in the PR.

## Also decided or derived

- The 40-column minimum and the 80-or-more desktop wording already match mobile first. They need no change.
- Open question 2 (does kaikki keep older dumps) is easier now: the local copy of the sources can be deleted, so pinning a dump is the user's choice. Leave it open.
- The desktop is not removed anywhere. "SSH" and "desktop" stay as secondary targets.

## What follows the spec

- Design: the 16 Syncthing mentions and §10 (backup), for the architect.
- Issues: 004a (wording), 009 (the timed build numbers), 022 (the backup).
