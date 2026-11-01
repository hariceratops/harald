# Change 3: typed checking of meaning cards

Status: settled 2026-11-01. Every question put to the user is answered
(D1-D44). What remains is follow-up work (F1-F14), the measurements named
there, and one reading of D42 that the pilot test settles (P64). None of
it waits on the user before F1.

## Decision log and open points (updated 2026-11-01, Round 10)

This section is the running record. The rounds below it are kept as
written, except the paste-ready spec wording in Rounds 7 and 9, which is
kept in line with the decisions. Status is one of three: decided (date, by
whom), open (owner), or superseded (by what). "User" means the learner and
owner of Harald. Recommendations in the rounds are the thinking partner's;
only what the Decided table lists is decided.

### Waiting on the user

Nothing. The eight questions from Rounds 7 and 9 were answered yes on
2026-11-01 (D37-D44).

### Decided

| # | Point | Status |
|---|-------|--------|
| D1 | The meaning check matches with `answer_matches`: exact, case-sensitive, whitespace collapsed, ae/oe/ue/ss accepted | decided 2026-10-30, user. Widened by D22 and D23 |
| D2 | An optional leading `sich` is accepted on any lemma in the meaning check (design §16) | decided 2026-10-30, user |
| D3 | The conjugation check accepts the reflexive pronoun after the first word. This is a separate change, not part of change 3 | decided 2026-10-30, user; not built |
| D4 | Suspect auxiliaries in the data (`bin beeilt`) are accepted as they are | decided 2026-10-30, user |
| D5 | Change 1 (typed attempt before the reveal, stored in `review.answer`) and change 2 (self-graded cards get Again/Good only) | shipped on feature/014, 2026-10-28; local, not merged or pushed |
| D6 | Plural-only nouns (Leute, Eltern): the article that counts is the plural article, `die` | decided 2026-10-30, user. Superseded by D21 and D38: plural-only nouns are typed without `die` |
| D7 | A noun without gender data is checked on the word alone; no article is required | decided 2026-10-30, user. Sharpened by D16 |
| D8 | An app-checked meaning answer may be graded Hard. For meaning cards this reverses the earlier confirmed "correct -> Good, wrong -> Again"; the other checked card types are unaffected | decided 2026-10-30, user |
| D9 | The app has never been on the phone, so the phone has no learning.db. There are no schema migrations for restructuring work until about v0.9; the whole v1 schema stays in revision 0001 (design §7.6) | decided 2026-10-30, user (policy) |
| D10 | Daily new-card cap: 20. Confirmed in design §16; the spec's open question 7 is stale | decided earlier, user; reconfirmed 2026-10-30. Spec resolution: D39 |
| D11 | Sibling burying applies per (word, card type), not per word. Design §7.4 still says per word | decided earlier, user; reconfirmed 2026-10-30. Spec wording: D40 |
| D12 | Hard with escalation: on a noun with a gender, a wrong or missing article grades Hard. If the card's previous review also had a wrong article, it grades Again | decided 2026-10-30, user |
| D13 | Schema option (i): edit revision 0001 in place, changing `CARD_TYPES` and the fixed CHECK copy in `0001_initial.py` together, and recreate the empty dev learning.db. No new revision file | decided 2026-10-30, user |
| D14 | A right word whose only error is capitalisation grades Again | decided 2026-10-30, user. Narrowed by D23 on 2026-10-31 |
| D15 | Plural-only nouns are covered by D6 and D7. P30 (the importer gives gender "" to both) is an implementation detail | decided 2026-10-30, user. Settled further by D21 and D38 |
| D16 | A noun whose card has no gender must be typed without an article: the field label reads `Word` and the check compares the word alone. A card without article data is a data gap the learner is told about, not one silently accepted. Lexicon: 646 of 59,610 noun entries (about 1.1%) have no gender, 43 of them with a plural | decided 2026-10-30, user |
| D17 | The check cue: the front's button reads `Check (enter)` on English -> German and German -> German; the field label reads `Art. + noun` on nouns with a gender; heading and footer unchanged | decided 2026-10-30, user |
| D18 | No "I was right" override. The spec sentence "There is no undo of the last grade" stays unchanged. Item 5 (P33) and P36 are closed. The override comes back as a fallback only if the audit (D26) shows more than 5% of checked reviews wrongly failed | decided 2026-10-31, user ("the whole package") |
| D19 | An article typed on a card with no gender is refused: no grade, the message `No article stored - type the word alone`, and the text stays in the field (P38) | decided 2026-10-31, user |
| D20 | A noun added only from German-edition senses takes its gender from the German entry's label (P40) | decided 2026-10-31, user |
| D21 | Plural-only nouns: D16 wins. They arrive with gender "" and are typed without `die` (`Leute`). The importer is not changed and no rebuild is planned (P39) | decided 2026-10-31, user; reading confirmed 2026-11-01 (D38) |
| D22 | Typos that are not real words: Good with a note. 1 edit for 5-9 letters, 2 edits for 10 or more letters, none up to 4. Edits are substitution, insertion, deletion and adjacent swap. A typed text that is a known German word or word form is never a typo (P42) | decided 2026-10-31, user |
| D23 | D14 reopened narrowly: a capitalisation-only error is a typo (Good with a note) unless the other-case form is itself a headword. `essen`/`Essen`, `arm`/`Arm` and `laut`/`Laut` stay Again (P43) | decided 2026-10-31, user |
| D24 | Retry with first letter and length when the typed text is another real word of the same part of speech. Right on the retry is Hard; otherwise Again (P44) | decided 2026-10-31, user |
| D25 | Option A confirmed: noun and article are typed together, and the article card type is retired. D13 applies (edit revision 0001 in place). The opt-in article card (V5) is off the table (P3, P28) | decided 2026-10-31, user |
| D26 | Rollout: grade from the first review, and audit after 200 checked reviews or two weeks (Round 5 item 7, with Round 6's metrics) (P35) | decided 2026-10-31, user, by saying yes to "the whole package"; not asked separately |
| D27 | A learner-written note: a free-text hint or mnemonic, written when adding the card, shown on the front and the back of English -> German and German -> English cards. This overrules Round 7's "later, with issue 017". The user's reason: at Add word the learner sees the near-synonyms and already knows which word needs marking | decided 2026-10-31, user; confirmed by D36 |
| D28 | Entry: `h` on a picker row opens a one-line note box. Enter stores the note, the row shows `+ note`, and `h` also ticks the row. An `h Note` footer hint appears if it fits at 40 columns; the fallback is dropping `esc Cancel` from the footer (P50) | decided 2026-10-31, user |
| D29 | German-definition rows take a note the same way, for the German -> German card (P51) | decided 2026-10-31, user |
| D30 | The note is capped to one row at 40 columns, about 36 characters; the pilot test confirms the number (P53) | decided 2026-10-31, user |
| D31 | A note that contains the word itself gets a warning, not a refusal (P54) | decided 2026-10-31, user. The only note warning (D41) |
| D32 | The note is a second issue in the same feature, built right after the checker and before studying starts (P55) | decided 2026-10-31, user |
| D33 | Phrase notes and word notes share the field name `note` and the same look; phrase notes stay front-only (P56) | decided 2026-10-31, user |
| D34 | Notes only when a sense's cards are first created. Editing comes with issue 017, and `h` on a "(has cards)" row is refused with a message (P57) | decided 2026-10-31, user |
| D35 | No notes on Stammformen and conjugation cards (P58) | decided 2026-10-31, user |
| D36 | D27 stands: the note shows on both sides of English -> German and German -> English cards. The leak on the German -> English front, where the note may state the card's English answer, is accepted by design. P52 (back-only on German -> English) is declined. This is the main session's reading of "yes to all nine, keep the note on both sides"; the thinking partner reads it the same way | decided 2026-10-31, user |
| D37 | Context from the data (P41): the English -> German front shows the sense labels, the German -> German front shows the part of speech, and de_de content stores `labels` | decided 2026-11-01, user |
| D38 | D21's reading confirmed: plural-only nouns (gender "") are typed without `die` (`Leute`), and the importer is not changed. With D19, a typed `die Leute` is refused without a grade, like any article on a no-gender card | decided 2026-11-01, user |
| D39 | Spec question 7, second half (P48): fuzzy ranking applies to German and English -> German lookup, not to phrase search. Taken from design §16 | decided 2026-11-01, user |
| D40 | The spec's sibling-burying bullet is reworded per D11 to "from the same word or phrase, and of the same card type" (P47) | decided 2026-11-01, user |
| D41 | No gloss-overlap warning on German -> English. D31's lemma warning is the only note warning (P60) | decided 2026-11-01, user |
| D42 | German -> English after the reveal at 40x12 (P61): measure first. A pilot test records whether the screen scrolls, and by how many rows. If it is about a row, the scrolling is accepted. The front's example is dropped under `-short` only if the test shows the scrolling is worse than that. One reading is left to the measurement (P64) | decided 2026-11-01, user |
| D43 | Note box wording (P62): title `Note for this sense`; below the field `Shown before you answer, both sides`, on both the English and the German step; when D31's warning fires, that line reads `Contains the word - Enter keeps it` | decided 2026-11-01, user |
| D44 | The German -> English test list for the note slice (P63): all eight of Round 9's tests, six pilot and two component | decided 2026-11-01, user |

D42 needs one reading, and it is the thinking partner's, not the user's
(P64). The note adds exactly one row by D30. Measured as what the note
adds, the test always comes out at about a row, so the example is never
dropped. Measured as total overflow, a long German example already
scrolls today without any note (Round 9 estimates 12-17 rows after the
reveal; an inference), so the example would be dropped for scrolling the
note didn't cause. The pilot should therefore run the same card with and
without a note, at a short and at a three-row example, and record the
overflow of each. Which number "about a row" refers to is then read off
real rows instead of guessed now.

### Raised, with status

| # | Point (raised by) | Status | Depends on |
|---|-------------------|--------|------------|
| P1 | Scope: the app grades en_de and de_de; de_en and phrase cards stay self-graded (user, topic framing) | assumed scope; in the final spec draft. Adopting the draft settles it | F1 |
| P2 | Spec non-goal "No typed checking of meaning or phrase answers" must be revised (user) | wording final in Round 7; adopted at F1 (user) | F1 |
| P3 | Noun and article in one typed answer | decided: D25 | - |
| P4 | Budget argument (user, Round 3) | weighed in Rounds 3 and 4 | - |
| P5 | "Let's invent a scoring" (user) | decided: D12, D16, D19, D22, D23, D24 | - |
| P6 | Spec wording draft | final: Round 7's draft plus Round 9's note bullet; adopted at F1 (user) | F1 |
| P7 | Dry run before the checker grades | superseded by D26 | - |
| P8 | Round 1 read the wrong checkout (`change/spec-q5`) | superseded by Round 2 | - |
| P9 | "Change 2 not in code" and "de_de face backwards" (Round 1) | superseded: both are on 014 | - |
| P10 | `sich` for every verb or only reflexive ones | superseded by D2 | - |
| P11 | Hard from an app-checked answer | decided: D8 | - |
| P12 | Capitalisation-only miss | decided: D14, D23 | - |
| P13 | No near-miss matching (Round 1) | superseded by D22 | - |
| P14 | No Easy and no duration rule; fsrs 6.3.2 only logs `review_duration` | part of the accepted package and the spec draft | - |
| P15 | Synonyms: options (a), (b), (c) (Round 1) | superseded by P41, D24 and D27 | - |
| P16 | Key-2 reflex for the override | moot: D18 | - |
| P17 | Enter reveals vs checks | decided: D17 | - |
| P18 | Termux autocapitalisation and autocorrect (inference, untested) | open; verify in issue 009 (F5) | - |
| P19 | A de_de definition may contain the word or its family | open; lexicon measurement (F4) | - |
| P20 | Plural-only nouns | decided: D21, D38 | - |
| P21 | Nouns with no gender data | decided: D7, D16, D19 | - |
| P22 | Keyboard bounce around the article card | moot: D25 | - |
| P23 | 40x12 row budget | inference; verify with the pilot tests named in Rounds 8 and 9. German -> English after the reveal: D42 | - |
| P24 | The phone's learning.db | resolved: D9 | - |
| P25 | Cap default | resolved: D10; spec fix (F6) | - |
| P26 | Burying includes due reviews (Round 3) | superseded by D11 | - |
| P27 | Issue 015 isn't implemented on main | finding | - |
| P28 | Variant V5 | decided off: D25 | - |
| P29 | Strict, hard or escalation | decided: D12 | - |
| P30 | The importer gives gender "" to plural-only and gender-less nouns | settled by D21, D38 | - |
| P31 | With D11, Round 3's latency and contention figures are void | finding | - |
| P32 | Schema option | decided: D13 | - |
| P33 | The "I was right" override | closed: D18 | - |
| P34 | Check cue | decided: D17 | - |
| P35 | Rollout | decided: D26 | - |
| P36 | Spec "There is no undo of the last grade" | closed: D18, unchanged | - |
| P37 | Gender "": accept any article | superseded by D16 | - |
| P38-P40 | Article on a no-gender card; D16 vs D6; gender from the German label | decided: D19, D21, D20 | - |
| P41 | Context from the data: labels on the en_de front, part of speech on the de_de front, de_de labels stored | decided: D37 | - |
| P42-P45 | Near misses, D14 narrowing, retry, combined package | decided: D22-D24, D18-D26 | - |
| P46 | Note "later, with 017" (Round 7) | superseded by D27: the user decided otherwise | - |
| P47 | Spec sibling-burying bullet | decided: D40 | F1 |
| P48 | Spec question 7, second half | decided: D39 | F1 |
| P49 | Spec scheduling scopes lose `article` | follows from D25 | F1 |
| P50 | Note entry | decided: D28 | - |
| P51 | Notes on German-definition rows | decided: D29 | - |
| P52 | Back-only on German -> English | declined: D36 | - |
| P53 | One rendering on the front that persists; one-row cap | decided: D30, D36. The front stays on screen through the reveal, the check and the retry, so one front row shows the note on both sides | - |
| P54 | Warn, not refuse, on the word itself | decided: D31 | - |
| P55 | Slice placement | decided: D32 | - |
| P56 | Phrase notes | decided: D33 | - |
| P57 | Notes only at first add | decided: D34 | - |
| P58 | No notes on Stammformen and conjugation | decided: D35 | - |
| P59 | `harald check` (issue 021): "accept upstream" repairs must keep `note` and de_de `labels` | finding, for 021's design step | 021 |
| P60 | German -> English front: no warning on gloss overlap. A useful hint on that card states the meaning by design (D36), so a gloss-overlap warning would fire on nearly every useful note. Keep only D31's lemma warning, which protects English -> German (Round 9) | decided: D41 | D36 |
| P61 | German -> English at 40x12: the note takes one row between the part of speech and the German example. The front fits with an example of up to about three rows; after the reveal (front, divider, `you:`, gloss, translation, grade buttons) a long example already scrolls today, and the note adds a row (Round 9) | decided: D42 (measure first; accept about a row) | D30, D36 |
| P62 | Wording in the note box: title `Note for this sense`, and below the field `Shown before you answer, both sides` (36 cells). The same text on the German step, for German -> German. The D31 warning, when it fires, replaces that line with `Contains the word - Enter keeps it` (Round 9) | decided: D43 | D28, D31, D36 |
| P63 | Tests for the German -> English front note (listed in Round 9) | decided: D44 | D32 |
| P64 | D42's "about a row": the row the note adds, or the screen's total overflow? Under the first reading the example is never dropped; under the second, long examples trigger it with or without a note (thinking partner, Round 10) | finding; read off the pilot's with/without-note measurement in F12 (see the note under Decided) | D42 |

### Main session analysis of the note (Round 8, logged as given; comments in Round 8)

- The costs given in Round 7 (a new step for every word; fields on
  Confirm crowding 40x12; a pre-fill repeating the card) apply only to a
  mandatory step or a field on Confirm.
- Alternative: on the English-senses picker, a key such as `h` on the
  highlighted sense opens a one-line input for that sense's hint. Enter
  stores it and the row shows a marker. Nobody pays an extra step for a
  word that needs none, and Confirm is unchanged.
- A hint (it disambiguates the prompt, so it belongs on the front) and a
  mnemonic (a memory aid, better on the back) differ; the user wants one
  note shown on both sides.
- Not checked against the code.

### Dependencies

- F1, the spec revision (user), comes before everything built. Round 7
  holds the checker wording; Round 9 holds the note wording. Both are
  final.
- F2 is the checker slice (D12-D26, D37-D40). F12 is the note slice
  (D27-D36, D41-D44), its own issue right after F2 (D32). F12 is
  independent of F2 in code, but both touch `content.py`, `cards.py` and
  the faces in `tui/study.py`.
- D22, D23 and D24 need study-time lexicon access behind the
  lexicon-present check (F10).
- D26's audit (F7) needs 200 checked reviews, after F12 has landed, so it
  sees the notes too.
- The note's dedupe rule (`note` excluded from the key) is part of F12.
  Issue 017 relies on it (F13).
- D42's measurement can change F12's German -> English layout, but only
  if the scrolling is worse than about a row (P64).
- P59 constrains issue 021's repair design (F14).

### Follow-up work falling out

- F1 Spec revision: Round 7's draft plus Round 9's note bullet, both
  final (P47 and P48 decided as D40 and D39). Owner: user.
- F2 Checker slice (D12-D26, D37) through `new_feature`: issues, design,
  test strategy, implementation on a feature branch. Owner: main session,
  after F1.
- F3 The reflexive-pronoun change to `check_conjugation` (D3): a separate
  `change`.
- F4 Lexicon measurements:
  - de_de definitions containing their lemma (P19);
  - the share of English senses with labels (D37);
  - the guard's hit rate (D22).
- F5 Phone checks in issue 009:
  - autocorrect and autocapitalisation (P18);
  - the keyboard through check, retry and Next;
  - taps on `Check (enter)` and on `h Note`;
  - the note box with the keyboard up.
- F6 Resolve spec question 7 (D10, D39), as part of F1. Owner: user.
- F7 The audit script after 200 checked reviews or two weeks (D26).
- F8 Design §7.4 burying per (word, card type) (D11), in 015's design
  step. Owner: main session.
- F9 D9's migration policy in design §7.6. Owner: main session, if the
  user agrees.
- F10 The lexicon-present check before Study, in F2.
- F11 Superseded by F12.
- F12 Note slice (D27-D36, D41-D44): its own issue right after F2 and
  before studying starts. Includes D42's measurement and reading P64 off
  it. Owner: issue process, then the design step, then the implementer.
- F13 Issue 017: editing a card's `note`, including adding one to cards
  that have none (D34). Owner: issue process.
- F14 Issue 021: repairs keep `note` and labels (P59). Owner: 021's
  design step.

## Impact on the spec, design and issues

This covers the whole feature: the checker package (D12-D26, D37-D40)
plus the note (D27-D36, D41-D44). Spec line numbers refer to
`dev/specs/harald-v1.md` as it stands on main; the user's edit in
`dev/inbox/harald-v1.md` may shift them. Design sections refer to the
design on feature/014. Marks:
- [spec] for the spec revision (user);
- [design] for the design step (architect);
- [issue] for the issue process;
- [code] for the implementer.

Nothing here has been edited; this is the list of what has to change.

### Spec [spec], owner: user

| Where | Edit |
|---|---|
| Adding a word, lines 66-72 (two meaning-card bullets) | Replace with Round 7's "Adding a word" bullets: en_de checked, prompted with gloss and labels (D37); de_de checked, showing definition and part of speech (D37); gender from the German entry when only German senses are chosen (D20) |
| Adding a word, line 73 ("Nouns also get an article card...") | Delete; replace with "Nouns get no separate article card. The article is part of the typed answer." (D25) |
| Adding a word, new bullet | Round 9's final note bullet (D27-D36, D41) |
| After lines 78-79 ("Conjugation answers are typed and checked...") | Insert Round 7's "Checked meaning answers" block (D12, D16, D19, D21-D24, D26, D38, the lexicon dependency) |
| Phrase mode, line 114 | Unchanged. Phrase notes stay front-only (D33); the existing "optional note" (lines 109-110) is unchanged |
| Study, line 118 (sibling burying) | Round 7's wording, per (word, card type) (D11, D40) |
| Study, line 127 ("There is no undo of the last grade.") | Unchanged (D18) |
| Scheduling, line 131 (scopes) | Drop `article` (D25, P49) |
| Non-goals, lines 176-178 ("and nouns an article card") | Drop the parenthesis |
| Non-goals, line 179 | Round 7's non-goal: no typed checking of German -> English or phrase answers |
| Open questions, line 299 (question 7) | Round 7's resolution (D10, D39) |

### Design [design], owner: architect (design step of `new_feature`)

| Section | Edit |
|---|---|
| §5 Normalisation and answer checking | The meaning check: article parse, D16/D19, D22 near misses with the known-word guard, D23 case rule, D24 retry. `answer_matches` itself unchanged |
| §7.1 Schema | `card_type` CHECK without `article`; 0001 edited in place (D13) |
| §7.2 Card content table (lines 1490-1493 on 014) | Delete the `article` row. `meaning_de_en` and `meaning_en_de`: add `note?`, shown on the front under the part of speech and gloss, staying visible through reveal, check and retry (D27, D36). en_de: checked; front gloss, labels (D37), pos and note; field label `Art. + noun`/`Word`. `meaning_de_de`: add `labels` (D37) and `note?`; shows pos (D37) and note on the front; checked; gender from the German label (D20, D29) |
| §7.3 Adding a word | Remove the article card and the `missing: gender` refusal. Add: `h` on English and German picker rows opens the note box, ticks the row and marks it `+ note` (D28, D29); the box wording (D43); the one-row cap (D30); the lemma warning, the only note warning (D31, D41); refusal on "(has cards)" rows (D34); notes passed through `PlanWordCards` into both cards of an English sense, or the de_de card. Dedupe excludes `note` |
| §7.4 Study | Checked meaning cards may grade Hard (D8, D12, D24); the article card is gone; `AnswerMeaning` reads learning.db and the lexicon; the retry state is on screen only; burying per (word, card type) (D11, F8). The note needs no study logic, only faces (§12) |
| §7.6 Migrations | D9 policy; 0001 edited in place (F9) |
| §7.8 Audit trail | No change for the checker (D18). Note edits come with 017 and are audited like any content edit |
| §7.10 Deviations, 011 | Mark superseded by D25 |
| §7.12 Conjugation cards | D3 noted; `_answer_checked` takes a rating; no notes on these cards (D35) |
| §7.13 Self-graded cards | en_de and de_de leave the self-graded set; "Hard and Easy are gone" applies to self-graded cards only; the de_en face gains the front note (D36) |
| §8 `harald check` | Drop the `article` status row; "accept upstream" repairs keep `note` and labels (P59) |
| §9 `$EDITOR` template | Phrase and word notes share name and look (D33); 017's card-edit template gains `note` |
| §12.3/§12.4/§12.8 wireframes | Remove the article frames. Add: checked en_de/de_de fronts, feedback, retry, the D19 refusal; the note row on en_de, de_en and de_de fronts and after reveal or check; the de_en after-reveal frame at 40x12 as measured (D42); the Add word pickers with `+ note`, the `h Note` footer and the note box with its wording (D43); at 80x24, 80x12, 40x30 and 40x12 |
| §12.5 Touch buttons | Remove der/die/das; `Check (enter)`; the tap guard covers Next and the retry |
| §12.6 Layout decisions | The note row, its one-row cap, and its position (under pos, above the example). German -> English after the reveal at 40x12: about a row of scrolling is accepted; the front's example is dropped under `-short` only if D42's measurement shows worse (P64) |
| §14.1-§14.10 | §14.1: retry state on screen only. §14.2: lexicon errors in study. §14.4: reuse of `osa_within`, `fold` and the `PickEntryScreen` modal pattern. §14.7: one lexicon query function, no other abstraction. §14.8: rejected alternatives (override, deferred write, cloze, accepting synonyms, shadow mode, strict article, near misses without a guard, note only via 017, note back-only on de_en, a gloss-overlap warning on de_en (D41)). §14.9: `warm.grade` with the lexicon lookup |
| §15 Issue order | Add the checker issue(s) and the note issue (F2, F12); retire 011 |
| §16 Open items | Resolve typed checking; amend the confirmed "correct -> Good, wrong -> Again" (D8) |
| Article-card mentions elsewhere (about 14 on 014) | Remove or mark superseded (D25) |

### Issues [issue], owner: issue process

| Issue | Edit |
|---|---|
| 009 TUI verified in Termux | Add: autocorrect and autocapitalisation (P18); the keyboard through check, retry and Next; taps on `Check (enter)` and `h Note`; the note box with the soft keyboard up |
| 010 add word and meaning cards | Check that its criteria don't describe en_de as self-graded |
| 011 article cards | Retire, superseded by D25 |
| 014 German -> German cards | Becomes checked (D17-D24); shows the part of speech (D37); takes a note (D29) |
| 015 cap and burying | Burying per (word, card type) (D11, D40); cap 20 (D10) |
| 017 edit cards | A card's `note` is editable, including adding one to cards without (D34); dedupe ignores `note` |
| 019 save phrase card | Phrase note look shared with word notes; phrase notes stay front-only (D33); no behaviour change |
| 021 `harald check` | Repairs keep `note` and labels (P59) |
| New: checker slice (F2) | D12-D26, D37, F10; one issue, or two (article removal, checker) if smaller reviews are preferred |
| New: note slice (F12) | D27-D36, D41-D44; built right after the checker, before studying starts (D32) |
| Separate `change` (F3) | D3 |

### Docs [code], owner: implementer

| File | Edit |
|---|---|
| README.md (1 article-card mention) | Remove or replace |
| docs/user/getting-started.md (2) | Article-card text out; checked meaning cards, the retry, typo notes; the note key `h` and where notes show |
| docs/roadmap.md (1) | Article card out |

### Code [code], owner: implementer

| File | Checker slice (F2) | Note slice (F12) |
|---|---|---|
| `learning/models.py` | `CARD_TYPES` without `article` | - |
| `learning/migrations/versions/0001_initial.py` | CHECK literal without `article` (D13) | - |
| `learning/scheduling.py` | `CARD_SCOPE` without `article` | - |
| `learning/content.py` | no article card or refusal; de_de `labels` (D37); gender from the German label (D20) | `plan_word_cards` takes notes per English sense and per German sense, and writes `note` into the en dict before the de_en/en_de copy and into the de_de dict |
| `learning/cards.py` | `_ONCE_PER_WORD` without `article` | `_key` drops `note` before canonicalising |
| `learning/answers.py` | the pure rating function; `check_article` goes | - |
| `learning/study.py` | `answer_meaning`; `_answer_checked` takes a rating; `answer_article` goes | - |
| `lexicon/` | an exact folded-key query returning (lemma, pos, kind) | - |
| `use_cases/study.py` | `AnswerMeaning`; `AnswerArticle` goes | - |
| `use_cases/cards.py` | - | `PlanWordCards` passes notes |
| `tui/study.py` | article UI out; en_de/de_de checked; retry; refusal; labels and pos on faces (D37); `Check (enter)`; field labels | a note row on the en_de, de_en and de_de fronts; the de_en `-short` example drop only if D42's measurement calls for it |
| `tui/addword.py` | `_CARD_NAMES` without `article` | `h` binding; note modal (like `PickEntryScreen`) with `max_length`, the D43 wording and the D31 warning (no gloss warning, D41); `+ note` marker; ticking; refusal on "(has cards)" rows; footer hint |
| `tui/harald.tcss` | article rules out; `#check` under `-narrow` | note row style; note modal |

### Tests [code], owner: implementer

| File | Edit |
|---|---|
| `tests/tui/test_study_screen.py` | Remove 3 article tests; rewrite the de_de and digraph tests (Round 2); checker pilots at (40, 30) and (40, 12); note pilots from Round 8, plus Round 9's four German -> English pilots (D44), which replace Round 8's `test_note_on_german_english_card_fits_at_40x12`. `test_note_on_german_english_after_reveal_at_40x12` records the overflow in rows, with and without the note, at a short and a three-row example (D42, P64) |
| `tests/tui/test_add_word.py` | Article lines out; note key, box wording on both steps (D43, D44), marker, ticking, refusal, the warning keeping the note on Enter (D44), footer width |
| `tests/component/test_card_use_cases.py` | 13 article references out; `AnswerMeaning` against the fixture lexicon; both cards of a sense carry the note, and the de_de card carries its note (D44); dedupe ignores `note` |
| `tests/unit/test_answers.py` | Article tests out; every rating row |
| `tests/unit/test_study_scheduling.py` | 3 article references out |
| `tests/smoke/test_study_flow.py` | 1 article reference; the checked flow |
| `tests/component/test_learning_migrations.py` | unchanged; it can't catch a `CARD_TYPES`/0001 mismatch (Round 4) |
| Fixture lexicon | possibly Bar/Bär and essen/Essen pairs |

---

Round 1 was read against `change/spec-q5` (main plus the spec edit). That
checkout has none of the 013/014 work, so parts of it are wrong. Round 2
re-checks every point against `feature/014-german-to-german-cards`, which
has changes 1 and 2. Where the two rounds disagree, Round 2 wins.

## Round 1 (2026-10-30, read against the wrong checkout)

### Goal

English -> German (`meaning_en_de`) and German -> German (`meaning_de_de`)
cards are self-graded today, and self-grading has proved unreliable. The goal
is for Harald to grade these two card types from the typed word, as it
already does for Stammformen and conjugation cards. German -> English and
phrase cards stay self-graded because they have too many right answers.

### Decided

- Matching uses `answer_matches` in `src/harald/text.py`: exact,
  case-sensitive, whitespace collapsed, ae/oe/ue/ss accepted for ä/ö/ü/ß.
- An optional leading `sich` is accepted for reflexive verbs. Lemmas are
  stored bare, and reflexivity exists only as a free-text `[reflexive]` sense
  label.
- Conjugation cards will accept the reflexive pronoun separately. That is
  outside this change.

### Nouns: recommended option B (lemma checked, article card stays)

The learner types the lemma. An article may be typed in front of it. If it
is, Harald checks it against any of the card's genders. A wrong article does
not fail the card, but grades it Hard (see scoring). The single-keypress
article card stays as it is, with its own `article` scope.

Why not A (article plus lemma required, article card retired): one card
would carry two facts on one FSRS schedule. A wrong article then either
lapses a meaning the learner knows (Again) or leaves the gender
under-drilled (Hard), because the scheduler can't tell which half failed.
The quick keypress drill on the phone would go. The simplification is also
smaller than it looks: about 37 article-card references in code and 37 in
tests are deleted, but parsing the article, multiple genders, nouns without
a gender and the extra scoring rows move into the typed check.

Why not C (keep article code but stop creating article cards): it leaves a
card type in the code that nothing creates. It is the worst of both.

What B changes (nothing is removed; there is no migration because the card
types are unchanged):
- `learning/answers.py`: a pure meaning check plus a rating function.
- `learning/study.py`: `_answer_checked` hard-codes Good/Again from a bool. It
  must take a rating instead.
- `use_cases/study.py`: an `AnswerMeaning` use case. `Grade` stays for
  de_en and phrase cards.
- `tui/study.py`: en_de and de_de get an input field and feedback, like
  Stammformen. They join the "checked" set in `check_action` and `_show`.
- The de_de face. `_card_faces` currently shows the word on the front and
  the definition on the back, which contradicts the spec and issue 014. It
  must be definition -> word before typed checking makes sense. Otherwise
  the answer is on screen.
- Tests that walk a meaning card through Show answer and grade:
  tests/tui/test_study_screen.py, tests/smoke/test_study_flow.py,
  tests/component/test_card_use_cases.py.
- Spec bullets, the non-goal, and the design sections on the meaning study
  screen and on "Hard/Easy after a checked answer" (rejected in the design
  table). That rejection was about asking the learner. Here the app chooses
  the rating, so the reasoning doesn't carry over.

If the user still wants A, the break list is the orchestrator's article
inventory. It includes an alembic migration, because the card_type CHECK is
generated from `CARD_TYPES`, plus removal of the `article` scope. learning.db
is empty, so no data needs migrating.

### Scoring (en_de, de_de); one pure function

| Outcome                                            | Rating |
|----------------------------------------------------|--------|
| empty answer                                       | Again  |
| lemma matches (digraphs, optional `sich` on verbs) | Good   |
| noun: lemma matches, no article typed              | Good   |
| noun: lemma matches, typed article wrong           | Hard   |
| lemma matches except capitalisation                | Hard   |
| anything else (wrong word, synonym, typo)          | Again  |
| learner presses "I was right" after an Again       | Hard   |

- No near-miss matching. German has too many real words one edit apart
  (Bar/Bär, Miete/Mitte, legen/liegen). Typos go through the override.
- No Easy, and no duration rule. `duration_ms` covers reading the prompt,
  soft-keyboard typing that scales with word length, and phone
  interruptions. Any threshold would be noise, and Easy is the rating that
  inflates intervals most. The installed `fsrs` only logs `review_duration`;
  the scheduler never uses it. Duration is already stored, so it can be
  studied later from real data.
- After this change, Hard means "recalled, with a defect", decided by the
  app. Session summaries already count anything but Again as correct.

### Synonyms: option (b), but the override grades Hard

After a WRONG result, an "I was right" button replaces the Again with Hard.
It covers valid synonyms and typos.

Why Hard and not Good: the button is the self-grading this change removes,
in a narrower form. If it gives Hard, an override still counts as a pass and
avoids a lapse, but the interval grows slowly and the review log marks it.
That gives the optimiser something honest to learn from later.

(c) rejected: cards store a German entry's sense gloss, while
`en_translation` is keyed by English headwords from the other edition. The
mapping from gloss to English words is fuzzy, and "bank" would accept Ufer.
Its width has not been measured.

(a) rejected: systematic false Agains on synonyms would push the learner to
want an override anyway.

### Draft spec wording

Non-goal (replaces "No typed checking of meaning or phrase answers."):
- No typed checking of German -> English or phrase answers. They have too
  many right answers.

Requirements (replace the two meaning-card bullets):
- Each chosen English-edition sense yields two meaning cards:
  - German -> English, self-graded;
  - English -> German, prompted with that sense's gloss. The user types the
    German word and Harald checks it.
- Each chosen German-edition sense yields a German -> German card. It shows
  the German definition, the user types the German word and Harald checks
  it. There is no word -> definition direction, since that would mostly
  duplicate the German -> English card.
- Typed meaning answers are checked like conjugation answers. A verb may
  have a leading `sich`. A noun may have its article, and a wrong article
  still passes, graded Hard. After a wrong answer the user can claim it was
  right, and it is graded Hard.

### Pressure points

- False Agains from ambiguous English glosses ("to look": schauen, sehen,
  gucken) are the main way this becomes worse than self-grading. They make
  the learner stop trusting the grade.
- Phone input. Termux probably suppresses autocapitalisation and
  autocorrect (this is an inference, not tested). If it doesn't, verbs come
  out capitalised and every one fails the case-sensitive check.
- At 40 columns the soft keyboard covers half the screen. The Stammformen
  screen has already faced this.
- de_de definitions may contain the lemma or its word family, which gives
  the answer away.

### Dry run

There is nothing to run it on. learning.db has no cards and no reviews. On
this tree the TUI calls `Grade` without an answer, so `review.answer` is
written only for article and Stammformen cards. Lexicon-only measures are
possible today:
- how often a de_de definition contains its lemma;
- how many noun cards would have no gender or several genders;
- how many lemmas need characters that are awkward on a phone keyboard
  (hyphens, apostrophes, accents other than umlauts).

Once attempts exist, the measures are:
- counts per scoring row;
- among Agains, how many the learner calls right (the false-Again rate);
- how many Agains are one edit from the lemma.

### Open questions

- Is change 2 actually in the code? This branch has four grade buttons, no
  typed field on meaning cards, and `review.answer` is not stored for them.
- Does the user accept B over A, given the one-card-two-facts argument?
- Capitalisation-only miss: Hard (proposed) or Again (consistent with
  conjugation)?
- Should "I was right" grade Hard (proposed) or Good?
- `sich` for every verb, or only for cards whose labels say reflexive? de_de
  content has no labels, so "every verb" is the only rule both directions
  can apply.
- Plural-only nouns (Leute, Eltern): which article, if any, counts as right?
- de_de cards for a noun picked only from German-edition senses get gender
  "" (gender comes from the English entry). Is lemma-only acceptable there?
- Dry run: lexicon measures now, or a shadow mode that shows the checker's
  verdict next to self-grading for a week?

## Round 2 (2026-10-30, read against feature/014 at /home/hari/code/harald-014)

### Retracted from Round 1

- "Change 2 isn't in the code": wrong. On 014, every self-graded card has
  one "Answer" field. Enter reveals the back, with `you: <attempt>` above it.
  Only `1 Again` and `2 Good` are offered, stored as ratings 1 and 3. The
  attempt is passed to `Grade` and stored in `review.answer`, `''` for an
  empty one.
- "The de_de face is backwards": fixed in 7bbf142. `_card_faces` returns the
  front `[definition]` and the back `[_word(content)]`.
- "sich only for reflexive verbs, or for every verb?": already decided in
  design §16. A leading `sich` is accepted on any lemma. `sich kochen` is
  wrong German but harmless in a recall check, and no new data is needed.

### Recommendation held: B, and it is cheaper than Round 1 said

On 014 the input field, the attempt and the feedback-then-Next path already
exist for meaning cards. B therefore adds no widget. It needs:
- `tui/study.py`: en_de and de_de stop revealing on Enter and send the
  attempt to a check instead. Practically, they join `_TYPED`, which also
  turns on the existing digraph hint for them.
- One feedback function, `RIGHT/WRONG/... - graded X` plus the back.
- One use case. Either `_answer_checked`'s callback returns a `Rating`
  instead of a bool, so the article, Stammformen and conjugation callers
  map their bool themselves, or the meaning check calls `grade_card` with
  its rating directly.
- No model, migration or scope change. en_de and de_de stay in scope
  `meaning`.

The empty attempt's existing "No answer - graded Again" path can stay as it
is.

A recounted on 014, where it would delete the whole article card:
- Source: `tui/study.py` has 16 references. They cover `_ARTICLE_BUTTONS`
  and the three `art` buttons, the article branch of `check_action`,
  `action_answer_article`, and the `1`-`3` binding whose key 3 exists only
  for `das`.
- Other source: `use_cases/study.py` (`AnswerArticle`), `learning/study.py`
  (`answer_article`), `answers.py` (`check_article`, `ArticleCheck`),
  `content.py` (6: the card and the "gender" refusal), `cards.py`
  (`_ONCE_PER_WORD`), `scheduling.py` (`CARD_SCOPE`), `models.py`
  (`CARD_TYPES`), `addword.py`, `harald.tcss` (3).
- The card_type CHECK sits in `0001_initial.py`, the only migration, so A
  needs migration 0002.
- Tests: three pilot tests in `test_study_screen.py` (lines 170-263),
  `test_card_use_cases.py` (13), `test_answers.py` (4),
  `test_study_scheduling.py` (3), `test_add_word.py` (2), and the smoke
  test (1).
- Docs: issue 011, issue 014 (1), `docs/roadmap.md`, `getting-started.md`
  (2), and 14 "article card" mentions in the design.

014 shows one point in A's favour that Round 1 missed. Since §7.13 the
article card is the only card without a text field. On the phone the soft
keyboard may drop and rise around it, and whether it does is unverified
(issue 009). Removing it would make every card keyboard-up.

That still doesn't decide it. One card would carry two facts on one FSRS
schedule, and nothing on 014 changes that argument. B holds. If the
measurement in 009 shows the keyboard bouncing on article cards, that is a
reason to revisit.

C is unchanged: rejected.

### Scoring: three rows changed

| Outcome                                            | Rating           |
|----------------------------------------------------|------------------|
| empty answer (existing path)                       | Again            |
| lemma matches (digraphs, optional `sich`)          | Good             |
| noun: lemma matches, no article typed              | Good             |
| noun: lemma matches, typed article wrong           | Hard             |
| capitalisation differs                             | Again (was Hard) |
| anything else (wrong word, synonym, typo)          | Again            |
| "I was right" after an Again                       | Hard             |

- Capitalisation is now Again, for two reasons. German has case-only pairs
  that are different words: essen/Essen, arm/Arm, laut/Laut. And the de_de
  front on 014 shows only the definition, with no part of speech to tell
  them apart. The feedback should say "capitalisation" so the Again isn't
  confusing, and the override covers keyboard slips.
- Hard from a checked answer revises a user-confirmed decision. Design §16
  lists "correct -> Good, wrong -> Again" as confirmed, and §7.13 removed
  Hard as an unreliable self-judgement. An app-chosen Hard doesn't have
  that problem, but it is still a reversal for meaning cards, and the user
  should say yes to it explicitly. The other checked card types stay
  Good/Again.
- What has to change for Hard to come back from a checked answer:
  - `_answer_checked` hard-codes `Rating.Good if correct else Rating.Again`
    (learning/study.py:139). That is the one line that must change.
  - `Grade`/`grade_card` already pass any `Rating` through, `rating` is
    CHECKed `BETWEEN 1 AND 4`, and the scope comes from `CARD_SCOPE`. None
    of these change.
  - `session_summary` counts rating != 1 as correct, so Hard counts as
    answered correctly. That is the intended reading.
- Duration claim confirmed: the repo venv has fsrs 6.3.2. Its
  `Scheduler.review_card` passes `review_duration` only into `ReviewLog`
  (scheduler.py:510-515), and the schedule never reads it. Still no Easy.

### Answer on screen: no leak in the check flow

On 014, `_show` renders the back only when `_revealed`. Typed cards set
feedback and the review in one step after Enter, so the check commits
before anything of the back appears. Moving en_de and de_de into that flow
keeps it that way.

One leak remains: the de_de definition itself may name the lemma or its
word family. It is now the only content on the de_de front, so this is
worth measuring.

### New impacts found on 014

- Negative: key 2 is now Good by habit. de_en and phrase cards stay
  self-graded with `1 Again`/`2 Good`, and they sit in the same session as
  the checked en_de/de_de cards. If "I was right" were bound to `2` after a
  WRONG, reflex would turn the override into the old self-grade. It needs
  a button plus a key outside the grading habit (not 1 or 2), or a button
  only.
- Negative: there are two flows on one screen. Enter reveals on de_en and
  checks on en_de, so the learner has to read the heading to know which
  will happen. The feedback line "graded X" makes the outcome clear. The
  front doesn't.
- Neutral, by inference: the 40x12 row budget. A checked WRONG on en_de
  shows heading, front, verdict, `you:`, divider and back. That is one row
  more than today's self-graded reveal, minus the grade-button row, which
  becomes Next. The existing 40x12 pilot test already fits "No answer -
  graded Again" with `you:` and the back. Long glosses and examples scroll
  under §7.13 today as well. The digraph hint adds one row on the front
  while typing, as it already does on conjugation cards.
- Positive: the digraph hint ("ae/oe/ue/ss are accepted") already exists
  for `_TYPED` and applies for free.
- Positive: the shadow mode Round 1 proposed already exists. Every
  en_de/de_de review on 014 stores the attempt next to the learner's own
  Again/Good.
- Add word: no change under B. Under A, the confirm line ("... de>de;
  article") and `addword.py`'s label change.
- Tests to rewrite under B: `test_german_german_card_asks_for_the_word_from_the_definition`
  (presses 2 after the reveal), and `test_a_meaning_card_does_not_mention_the_digraphs`
  (its premise flips for en_de). Possibly also `test_study_reveal_grade_and_summary`
  and the smoke test, depending on which seeded card comes second. New:
  unit tests for the rating function and a component test for the use
  case.

### Dry run: what exists now

The code to collect data is ready (014 stores `(attempt, self-grade)`
pairs), but the data isn't. The desktop learning.db is empty, and 014 is
local and unpushed, so the phone can't have recorded attempts either.
Unconfirmed: learning.db lives on the phone, which may hold reviews from
main, but those carry no attempt (`answer` NULL).

Sequence: build the scoring function first, as pure code with no UI. Study
on 014 for a while. Then run the function over every en_de/de_de review
with a non-NULL answer, and only after that let it grade. Measures:
- the agreement matrix of checker verdict against self-grade, and in
  particular checker-Again with self-Good. That cell holds both the false
  Agains and the over-generous self-grades. The user labels each one, which
  is the honest test of "self-grading proved unreliable";
- counts per scoring row;
- how many Agains are one edit from the lemma, or differ only in case;
- from the lexicon, now: how many de_de definitions contain their lemma.

### Spec wording (updated)

Same non-goal and same two requirement bullets as Round 1. The third bullet
changes to:
- Typed meaning answers are checked like conjugation answers, and the
  lemma may be preceded by `sich`. A noun may be typed with its article;
  a wrong article still passes, graded Hard. After a wrong answer the user
  can claim it was right, which grades it Hard.

The spec line "Nouns also get an article card" stays, under B.

### Open questions (replaces Round 1's list)

- B over A, given the one-card-two-facts argument? If 009 shows the
  keyboard bouncing on article cards, is that enough to revisit?
- Hard from checked meaning answers revises the confirmed "correct -> Good,
  wrong -> Again". Is that accepted for meaning cards only?
- Override: should it grade Hard (proposed) or Good, and which key? Not 2.
- Capitalisation-only miss: Again (Round 2) or Hard (Round 1)?
- Plural-only nouns (Leute, Eltern): which article, if any, counts?
- Nouns picked only from German-edition senses have gender "" on de_de: is
  a lemma-only check acceptable there?
- How long to study on 014 in shadow before the checker grades, and does
  the phone's learning.db hold anything?

## Round 3 (2026-10-30): the user's budget argument

### Recommendation changes: A, soft

The thinking partner now recommends A. The typed answer on en_de and de_de
is article plus word wherever the card has a gender. A wrong or missing
article grades Hard, and the article card is retired. Variant V5 below is
the hedge if the user wants a dedicated gender drill to stay available.

The user's argument changes the value side, and one reframing removes most
of Round 1's objection. If the thing being learned is "der Hund" as one
unit, which is how German nouns are best learned for speaking, then the
card holds one fact, not two. The scheduling loss is real but smaller than
Round 1 made it (see "What a single schedule loses").

### Cards per word

Counted with one English sense picked, no German sense and no tense. Add
1 per German sense picked and 6 per conjugation tense.

| Word type | Today / B | A, V2 | V1 (B, article card opt-in, off by default) | V5 (A plus opt-in article card) | V3 (article card kept, en_de/de_de dropped for nouns) |
|---|---|---|---|---|---|
| noun | 3 (de_en, en_de, article) | 2 | 2 (3 if opted in) | 2 (3 if opted in) | 2 (de_en, article) |
| verb | 3 (+6 per tense) | 3 | 3 | 3 | 3 |
| adjective, other | 2 | 2 | 2 | 2 | 2 |
| phrase | 1 | 1 | 1 | 1 | 1 |

- V2 is A with the article required on en_de only, not on de_de. It has
  the same count as A.
- V3 is rejected. It removes noun production, which is the main point of
  typed checking.
- V1 is rejected. It keeps all the article code, and by default nouns get
  no gender drill at all, since B's article is optional.

The cap counts cards, not words (design §7.4: "fewer than
`new_cards_per_day` cards had their first review today"). The cap default
is listed as open in spec question 7, but design §16 lists "a daily cap of
20" as confirmed by the user, so that needs reconciling. 10 and 30 are
shown for range.

| Daily cap | New cards a week | Nouns a week, only nouns (B / A) | Verbs a week, no tense | Verbs a week, one tense each |
|---|---|---|---|---|
| 10 | 70 | 23 / 35 | 23 | 7 |
| 20 | 140 | 46 / 70 | 46 | 15 |
| 30 | 210 | 70 / 105 | 70 | 23 |

As a mixed week, take 15 nouns, 10 verbs with no tense, and 15 phrases.
That is 90 cards under B and 75 under A. At cap 10 it takes 9 days under B
and 7.5 under A. At cap 20 it takes 4.5 and 3.75. At cap 30, 3 and 2.5.

A saves exactly one card per noun. That is a third of a minimal noun, and
up to half the noun-only throughput. Tenses are the bigger lever, though:
one tense on 10 verbs costs 60 cards, four times what A saves on 15 nouns.

Sibling burying (design §7.4) excludes a card if any other card of the
same word has a review today, and that includes due reviews, not only new
cards. It has two effects:
- Latency. A noun takes at least 3 days to appear in full under B (4 with
  a German sense) and at least 2 under A (3). It takes longer whenever an
  earlier sibling falls due on the same day, because a due review
  outranks a new card.
- No throughput loss as long as the new queue holds enough distinct words,
  because other words fill the cap.

Every extra card per word keeps contending with its siblings for the
word's one slot a day, for as long as the word is studied. A removes that
contention for every noun. This point is new, and it is the strongest
budget argument, more than the new-card count.

Issue 015 isn't implemented on main. It couldn't be re-checked on 014
because the checkout at `/home/hari/code/harald-014` is no longer there.

### What a single schedule loses, and what can be kept

Lost: gender has no schedule of its own. Under the soft dial, a learner who
keeps typing "die Hund" gets Hard every time. The interval still grows,
only more slowly, so a persistent gender error is never forced back to
short intervals. Under the strict dial (wrong article is Again), the gender
is drilled hard, but a known meaning lapses each time. The post-lapse
stability drop under the default FSRS parameters is large.

Kept, without a new column:
- `review.answer` already stores the typed string. Whether the article was
  right can be recomputed later from the answer and the card content, so
  the data isn't lost, only unscheduled.
- The feedback line names the article result, for example
  `RIGHT  Hund - article: der (you: die)  graded Hard`.
- The dial is one row of a pure function. Soft (Hard) is the start, and
  the dry run (P7) shows how often the article is the half that fails. If
  that is often, switch to strict, or to V5 for the nouns that keep
  failing.

"Hard for the article half only" is exactly the soft dial. FSRS takes one
rating per card review, so no finer split exists on a single card.

### What the budget argument does and doesn't change in A's break list

It changes nothing on the cost side. A still needs:
- migration 0002, because the card_type CHECK sits in `0001_initial.py`;
- the removals from Round 2's recount;
- three pilot tests and about 23 unit and component references;
- the docs (issue 011, 014, the roadmap, getting-started, 14 design
  mentions).

It also adds new questions:
- What migration 0002 does with existing article cards depends on the
  phone's learning.db (P24). The options are delete, or keep the type in
  the CHECK as history.
- P20 (plural-only nouns) becomes blocking.
- P21 (no gender) becomes the "no article required" case.

The keyboard point (P22) now counts for A rather than being a footnote.
With every card keyboard-up, the article buttons, key 3 and the
article-only branch of `check_action` all go, and the study screen has one
input model.

V5 is the cheaper end state to reach. It is C fixed by an opt-in: the
article card stays as a type and is created only when ticked at Add word,
like tenses. That keeps the code, the tests and the migration as they are.
Its catch: you only know a gender is tricky after studying, so an opt-in
at Add word comes too early. Adding just the article card to an existing
word would need a new path.

### Scoring under A (soft); rows that differ from Round 2 are marked

| Outcome | Rating |
|---|---|
| empty answer | Again |
| article and word right (any listed gender; digraphs; optional `sich`) | Good |
| noun with a gender: word right, article missing or wrong | Hard (A); strict dial: Again |
| noun without gender data: word right, any or no article | Good (A, new) |
| capitalisation differs | Again |
| anything else | Again |
| "I was right" after an Again | Hard |

### Open questions (replaces Round 2's list; see the log for status)

Depending on the A/B choice:
- A (soft or strict), B, or V5? (P3, P4, P28)
- Under A: which article counts for plural-only nouns (P20)? Is a
  lemma-only check fine for nouns without gender (P21)? What does the
  phone's learning.db hold, which decides migration 0002 (P24)?
- Hard from checked meaning answers, revising the confirmed "correct ->
  Good, wrong -> Again" (P11). The soft dial needs it; strict A does not.

Not depending on it:
- Capitalisation-only miss: Again or Hard (P12)?
- The override: grade Hard or Good, which key (not 2), or a button only
  (P15, P16)?
- Enter reveals on de_en and phrase cards but checks on en_de and de_de;
  is that acceptable, or does the front need a cue (P17)?
- The cap default: is 20 confirmed (design) or still open (spec) (P25)?
- How long to study on 014 before the checker grades (P7)?

## Round 4 (2026-10-30): the user's answers applied

### Corrections to Round 3

- Burying is per (word, card type) (D11), not per word as design §7.4 says
  and Round 3 assumed. A noun's de_en, en_de and article cards are
  different types, so they can all appear on one day. Round 3's latency
  figures ("at least 3 days under B, 2 under A") and its "strongest budget
  argument" (A removes sibling contention) no longer hold.
  - What remains is the cap count: A saves one new-card slot per noun.
    Round 3's cards-per-word and cap tables stand.
  - Under per-type burying, a word with two English senses has two en_de
    cards, and those still bury each other. That is the same under A and B.
- No migration under A (D9), so Round 3's "migration 0002" and the
  question of what it does with existing cards are void.
- "Noun without gender data: any or no article -> Good" (Round 3's
  scoring) needs tightening against D6 and D7; see P30 below.

### Break list for A under D9 (no new revision file)

Common to (i) and (ii):
- `tui/study.py`:
  - remove `_ARTICLE_BUTTONS`, the three `art` buttons, the article branch
    of `check_action` and `_show`, `action_answer_article`, the `art`
    handling in `on_button_pressed`, and the article face in
    `_card_faces`;
  - the digit bindings shrink from 1-3 to 1-2, and key 3 is free;
  - `_TYPED` gains `meaning_en_de` and `meaning_de_de`;
  - add the check feedback.
- `use_cases/study.py`: remove `AnswerArticle` and add `AnswerMeaning`.
- `learning/study.py`:
  - remove `answer_article` and add `answer_meaning`;
  - `_answer_checked` line 139 must allow Hard (D8).
- `learning/answers.py`: `check_article`/`ArticleCheck` go. `ARTICLES` and
  the "any listed gender counts" rule move into the meaning check.
- `learning/content.py`: drop the article card and its "missing: gender"
  refusal. Under D7 a missing gender refuses nothing.
- `learning/cards.py`: `_ONCE_PER_WORD` loses `article`.
- `learning/scheduling.py`: `CARD_SCOPE` loses `article`. The `article`
  FSRS scope ends; no stored reviews use it (D9).
- `tui/addword.py`: drop the `"article": "Article"` label, which changes
  the confirm line.
- `harald.tcss`: 3 rules go.
- Tests:
  - three article pilot tests in `test_study_screen.py`;
  - `test_card_use_cases.py` (13 references), `test_answers.py` (4),
    `test_study_scheduling.py` (3), `test_add_word.py` (2), smoke (1);
  - the meaning-card pilot tests listed in Round 2;
  - new: rating-function unit tests and a use-case component test.
- Docs:
  - issue 011 (retired or marked superseded), issue 014 (1), the roadmap,
    getting-started (2);
  - about 14 design mentions, including §7.4's "The article card stays a
    single keypress";
  - the spec lines "Nouns also get an article card" and "and nouns an
    article card" (non-goals), at the unfreeze.

(i) Edit 0001 in place:
- `models.CARD_TYPES` loses `article`, and so does the literal CHECK string
  in `0001_initial.py` (line 83).
- That literal is not generated. It is a frozen copy of what `CARD_TYPES`
  generated, so both places must change together.
- Delete and recreate the local dev learning.db. It is empty, and nothing
  else exists (D9).
- Risk: a DB already at revision 0001 keeps the old CHECK silently, since
  Alembic sees nothing to do. No such DB exists outside dev.
- `test_models_and_revisions_agree` runs `alembic check`. As far as I know,
  Alembic's autogenerate doesn't compare CHECK constraints, so that test
  would not catch a mismatch between `CARD_TYPES` and 0001's literal. This
  is a belief, not verified here; the pair needs care either way.

(ii) Leave `article` in the CHECK:
- No schema file changes.
- To keep models and 0001 identical, `CARD_TYPES` must keep `article` too,
  as a value no code creates, with a comment saying why. Removing it from
  `CARD_TYPES` only would leave the models and the revision disagreeing,
  silently, per the note above.
- It carries C's leftover into the schema until about v0.9.

Recommendation: (i). It is a two-line edit plus deleting an empty file,
and it leaves no dead value in the schema. D9's policy (the whole v1
schema lives in 0001 until about v0.9) is exactly what makes an in-place
edit legitimate now. (ii) is only worth it if the user wants zero touches
to 0001 on principle.

Policy note (D9): from about v0.9, schema changes get new revisions. Until
then, restructuring edits 0001 and recreates dev databases.

### P30: applying D6 and D7 when both arrive as gender ""

As far as the importer shows, plural-only nouns can't be told apart from
gender-less ones. `wiktextract_en._gender` keeps only m/f/n tags or `m/f/n`
letters in the head template, so Leute and Eltern most likely arrive with
gender "". That is the same value a noun with missing gender data gets
(inferred from the code, not measured). Options, none decided:
- Simplest: for gender "", accept the word alone (D7) or the word with
  `die` (D6). Reject any other article as wrong, or accept it? Rejecting
  `der Leute` fits D6.
- Exact: the importer marks plural-only nouns (for example a `p` in
  gender), and the content carries it. This is a build change and a
  rebuild. F4's measurement would show how wiktextract tags them.

### Strict versus hard: main session analysis, with the thinking partner's comments

Main session analysis, as given to the user:
- Strict pros:
  - gender is drilled on a short interval;
  - one rule everywhere (correct -> Good, wrong -> Again, no Hard from the
    app);
  - the review log and session summary stay honest;
  - no reversal of a confirmed decision.
- Strict cons:
  - a word whose meaning is known lapses, so stability and interval reset
    and the card returns;
  - more lapses mean more due reviews competing with new cards, which
    works against the budget goal that motivated A;
  - discouraging while genders are shaky;
  - data gaps or wrong gender in the lexicon would lapse cards unfairly.
- Hard pros:
  - the meaning is kept (no lapse);
  - lighter review load, which fits the budget goal;
  - the interval still grows, only more slowly than Good;
  - the session summary counts it as answered (rating != 1).
- Hard cons:
  - a persistent wrong article is never drilled on a short interval;
  - the card keeps spacing out;
  - the summary's "answered correctly" overstates article errors;
  - FSRS means "recalled with difficulty" by Hard, which only
    approximates "right word, wrong article";
  - it adds a second rule and relies on the dry run to tune.
- Variant: Hard on the first wrong article, escalating to Again if the
  previous review of the same card also had a wrong article. The stored
  `review.answer` and rating make that checkable without new columns.

Thinking partner's comments (agreement unless stated):
- "No reversal of a confirmed decision" is moot after D8. And strict still
  produces Hard from the app if the override grades Hard (P15 open), so
  "no Hard from the app" holds only if the override grades Good.
- "Data gaps would lapse cards unfairly": partly overtaken. Under D7 a
  missing gender requires no article, so gaps can't lapse a card. Wrong
  gender data still can, under strict.
- "More lapses compete with new cards": the cap counts first reviews only
  (§7.4), so lapses don't consume new-card slots. They cost session time,
  and with per-type burying (D11) they don't block siblings of other
  types. The budget harm is real, but it is time, not cap.
- The rest is agreed.
- The escalation variant is the one the thinking partner would pick:
  - It answers Hard's main con (a persistent error does come back on a
    short interval) without strict's main con (a one-off slip on a known
    word doesn't lapse it).
  - It stays one pure function. The use case passes the previous review's
    answer, the rule recomputes that article result from the card's
    content, and nothing new is stored.
  - Edge cases to settle when it is built: a previous review that was
    empty, overridden or graded before change 3 counts as "not a wrong
    article". A same-day learning-step re-show counts as a previous
    review.
  - One sentence explains it: "A wrong article costs Hard; twice in a row
    costs Again."
  - Not decided; it is one of the options in P29.

### Open questions (replaces Round 3's list; see the log for status)

Waiting on the user:
- A strict, A hard, or the escalating variant (P29); and A versus V5 if
  that is still in play (P28).
- Capitalisation-only miss: Again or Hard (P12)?
- The override: its grade, and its key (not 2) or a button only (P15,
  P16).
- Enter reveals on de_en and phrase cards but checks on en_de and de_de;
  is that acceptable, or does the front need a cue (P17)?
- How long to study on 014 before the checker grades for real (P7)?
- How to apply D6 when plural-only and gender-less nouns both arrive as
  gender "" (P30)?
- Edit 0001 in place (i) or leave `article` in the CHECK (ii) (P32)?

## Round 5 (2026-10-30): the override, the Check cue, and the rollout

Re-read on feature/014: `tui/study.py`, `learning/study.py`,
`use_cases/study.py`, `learning/scheduling.py`, `learning/models.py`
(Review), `tests/tui/test_study_screen.py`, design §7.4, §7.8 and
§12.5-12.8, and `harald.tcss`.

Facts that shape the proposals:
- Review rows: `rating` is CHECKed 1-4, `answer`, `state_before` and
  `state_after` are stored, and there is no column marking an override.
- `grade_card` writes the review and reschedules the card in one
  transaction, immediately.
- `session_summary` counts a card as answered correctly if its first
  review in the session is not Again.
- Design §7.8: grades are audited for a future undo. "A future grade-undo
  should append a compensating record rather than delete the review row",
  and "no row is ever updated or deleted" in v1. The spec says "There is
  no undo of the last grade."
- Design §12.5: Termux's extra-keys row has no digits and no space, and
  Enter is on every soft keyboard. Buttons ignore presses for 300 ms
  after they appear. Stammformen and conjugation fronts deliberately have
  no button, because Enter submits.
- Footer: the digit bindings are hidden, because more hints overflow 40
  columns. `.field-label` is 12 cells wide. Under `-narrow` the buttons
  share the row (`1fr`).
- Today the TUI decides the self-grade, and `Grade(card_id, rating, ...,
  answer)` takes any rating.

### Item 5: the "I was right" override

Recommendation, as one yes/no:
- It grades Hard.
- It is a button labelled `3 I was right` plus key `3`.
- It is offered only on the feedback screen of a card the checker graded
  Again because the word was wrong, and only when the answer was
  non-empty.
- The checked grade is written when the learner leaves the feedback
  screen (Next, Enter, space or Esc), or as Hard when they press
  override. One review row either way; no row is ever updated.
- No limit beyond "once, on that screen".

Grade:
- Hard keeps Round 1's reasoning: no lapse, a slower-growing interval,
  and an honest record of a contested answer.
- Good would make the override full self-grading again, which is the
  thing change 1 and change 3 remove.

Key and label:
- Key 2 is ruled out (the reflex).
- Key 3 is free under A, since the article card and its `das` key go.
  No card type would use 3 any more, so no habit attaches to it. Today
  `2` on a feedback screen does nothing (`check_action` refuses it), so a
  stray 2 stays harmless.
- No footer hint. The button names its key, as `1 Again` does.
- At 40 columns: `[3 I was right] [Next (enter)]` is 13 + 13 cells plus
  gaps, inside the `-narrow` `1fr` layout. Under `-short` the buttons are
  one row high, so no extra rows.
- Both a button and a key. On the phone, digits are not on the extra-keys
  row, so the button is the real path; the key serves desktop and SSH.
- The 300 ms tap guard must cover the new button. It appears where
  `Check` was tapped, the same double-tap risk §12.5 guards against.
- Cost: one button, one binding, and two tcss rules (`-narrow` and the
  guard list).

Where it is offered:
- Yes: Again because the word didn't match. This includes the
  capitalisation-only Again (D14), since the override is the designed
  answer to keyboard slips and autocapitalisation.
- No:
  - an empty answer (there is nothing to claim);
  - a Hard for the article (D12), where the word was accepted already;
  - an escalated Again for a repeated wrong article. The word was right
    and the article wrong twice; "I was right" would be a claim about
    the gender, and the data is the judge there.
  - A wrong gender in the lexicon is the only case this blocks. It is
    rare, and the `check` repair path is the place for data errors.

How it is written. Three options:
- (a) A second review row (Again, then Hard). Rejected:
  - FSRS would apply a lapse followed by a near-immediate Hard on a
    relearning card, not the single Hard the learner meant;
  - `session_summary` counts the first row, so the card shows as missed;
  - the optimiser later sees two reviews where there was one.
- (b) Replace the first row: set its rating to 2, recompute `state_after`
  with `review_card(state_before, Hard, review_datetime=reviewed_at)`,
  and reschedule the card. Workable, and the audit trail records the old
  values. But it updates a review row, which §7.8 says v1 never does,
  and it is an undo of the last grade in all but name.
- (c) Defer the write. The check computes the verdict and rating without
  writing. The grade is written once, when the learner leaves the
  feedback screen: the checked rating on Next, Enter, space or Esc, or
  Hard on override.
  - One row, no update, no undo; FSRS and the summary see one honest
    review.
  - The spec's "killing the process loses at most the card on screen"
    still holds, because the unwritten grade is the card on screen.
  - Esc must write the pending grade before the summary.
  - `duration_ms` is measured at the check, not at Next.
  - A failed write shows the toast and keeps the feedback on screen, as
    a failed grade does today.
  - The empty-answer path stays immediate, since no override is offered
    there.
  - It means a lookup use case for the verdict, which reads the card and
    its previous review (for D12) and writes nothing, followed by the
    existing `Grade` with the final rating and the answer. That replaces
    the `AnswerMeaning` use case of earlier rounds.

  Recommended: (c).

With D12's escalation:
- The escalation recomputes "previous review had a wrong article" from
  that review's stored `answer` and the card's content, never from its
  rating.
- An overridden wrong word stored as Hard therefore doesn't count. Its
  answer has the wrong word, so the recomputation says "wrong word", not
  "wrong article".
- No marker column is needed. An override is also derivable later as
  "word doesn't match but rating 2".
- One side effect to accept: a self-graded en_de review from before
  change 3 whose answer was `die Hund` would count as a wrong article.
  That is correct, and there are no such reviews yet anyway (D9).

Limit:
- Once, on that screen, before Next. That is the natural limit and
  enough.
- A per-session cap adds state for little gain. A card the override
  turned into Hard doesn't come back in the same session through
  learn-ahead the way an Again does.
- The audit (Item 7) counts overrides, so creeping self-grading is
  visible.
- If overrides exceed about 10% of checked reviews, the cause is worth
  reading: synonyms suggest the gloss prompts are too vague; typos
  suggest near-miss handling. Act on that rather than on a cap.

Spec: the override is a narrow regrade. The spec revision must name it as
the one exception to "There is no undo of the last grade" (P36). Under
(c) it isn't technically an undo, but the spec reader will see it as one.

### Item 6: making "this card is checked" visible

Recommendation, as one yes/no:
- On en_de and de_de, the front's button reads `Check (enter)` where
  self-graded cards show `Show answer`. Same place, same tap, and it runs
  the check.
- On nouns with a gender, the field label reads `Art. + noun` instead of
  `Answer`.
- Heading and footer unchanged.

What a phone learner sees today:
- On self-graded cards, an `Answer` field with focus, a `Show answer`
  button, and the soft keyboard up. The soft keyboard's Enter submits
  the field.
- On Stammformen and conjugation fronts, no button at all; Enter is the
  only way to submit, by design (§12.5).
- So the learner always has the soft Enter. A touch button is a second
  path plus a cue, not a necessity.

Options:
- Button text (`Show answer` -> `Check (enter)`).
  - Cost: one label switch in `_show`, or a second button with its own
    `-narrow` rule.
  - The button sits where the thumb is, which makes it the most visible
    cue. Zero rows.
  - Recommended.
- Field label. `Answer` stays for self-graded cards. For checked meaning
  cards the label can say what to type:
  - `Art. + noun` (11 cells, fits the 12-cell label) on nouns with a
    gender. Under A a bare `Hund` grades Hard, so the learner must know
    to type `der Hund`. That makes this a correctness cue, not
    decoration.
  - `Answer` or `Word` elsewhere.
  - Recommended for nouns. Optional elsewhere; `Word` is marginally
    clearer.
- Heading, for example `English -> German  checked` (26 cells, fits). It
  is dim text read last, and it adds nothing the button doesn't say. Not
  recommended.
- Footer hint: it would overflow 40 columns (the §7.13 constraint). Not
  recommended.
- The digraph hint row is already shown while typing on `_TYPED` cards.
  It appears on en_de and de_de for free, and it is itself a cue that the
  answer will be checked.

Row budget at 40x12: zero added rows. The button replaces a button, the
label replaces a label, and the digraph row exists for `_TYPED` already.
This is inferred from the 014 code; verify with a pilot test at
(40, 12).

Optional, for consistency: give Stammformen and conjugation fronts the
same `Check (enter)` button. Small, and it reverses §12.5's "not added"
for them. That is the user's call and not part of this recommendation.

### Item 7: rollout

Facts: nothing has been studied yet. The desktop learning.db is empty,
and the app has never been on the phone (D9). 014 already stores typed
attempts on self-graded cards, so an offline comparison needs no build.

Options:
- (A) Build the checker and let it grade from the first review, with the
  override as the safety net. Audit offline after a fixed number of
  reviews.
  - Build cost: change 3 only.
  - Risk: false Agains on a new learner. On a new card, a false Again
    gives a much shorter first interval than Good. Rough FSRS-6 defaults,
    from memory and not checked: initial stability about 0.2 days for
    Again, 1.3 for Hard, 2.3 for Good. The override lifts it to Hard's.
    So an unnoticed false Again costs about a day or two on one card, and
    a noticed one costs a tap.
  - Every checked Again keeps its typed answer, so the audit can list
    them all, including the ones the learner didn't override.
- (B) Study self-graded on 014 for a fixed number of reviews, compare
  offline, then build.
  - Build cost: none now, the same later.
  - Risk: the first weeks run on the grading mode already judged
    unreliable, which is the worst time for it, because early stabilities
    set the first intervals.
  - Its comparison baseline is a self-grade known to be unreliable. And
    every disagreement still needs the learner's own label, which (A)'s
    audit gets the same way.
  - It delays the change for data (A) also produces.
- (C) Build the checker in shadow mode: the verdict is stored or shown
  beside the self-grade, then switched on.
  - Build cost: change 3 plus a shadow path, a column or display, and its
    removal later.
  - Showing the verdict anchors the self-grade and spoils the comparison.
    Storing it adds nothing, since the verdict can be recomputed from
    `answer` and content.
  - Rejected.

Recommendation: (A), with a fixed audit.
- Trigger: after 200 checked en_de/de_de reviews with a non-empty answer,
  or two weeks, whichever comes first. At cap 20, with en_de and de_de
  making up roughly a third to a half of new noun and verb cards, plus
  their reviews, that is about two weeks of study. This is an estimate.
- The audit is a script over `review` joined with `card`. No app change.
  For each checked review it recomputes the verdict row from `answer` and
  content. It lists:
  - every Again with a non-empty answer, for the learner to label "really
    wrong" or "I was right";
  - every override;
  - case-only Agains;
  - Agains one edit from the lemma (or lemma plus article);
  - wrong-article Hards and escalations.
- Thresholds. These are the thinking partner's judgement, not
  measurements:
  - Labelled false Agains, overridden or not, above 5% of checked
    reviews: look at what they are. Mostly synonyms means a synonym list
    or a gloss problem. Mostly one-edit typos means reconsider near-miss
    matching (P13).
  - Case-only Agains above 2%: check Termux autocapitalisation (P18)
    before touching D14.
  - Overrides above 10% of checked reviews: self-grading is creeping
    back. Read the overridden answers.
  - Escalations: no threshold. Read them to see whether D12 fires on data
    errors (a wrong gender in the lexicon).
- After the audit, each outcome is a small, separate change: a rule row in
  the pure function, or a data fix.

### Open questions (replaces Round 4's list; see the log for status)

Waiting on the user, each answerable yes or no:
- P33, the override as specified in Item 5: Hard; `3 I was right` button
  plus key 3; only after a wrong-word Again with a non-empty answer;
  written once on leaving the feedback screen; no extra limit.
- P34, the cue: `Check (enter)` replaces `Show answer` on en_de and de_de,
  and `Art. + noun` replaces `Answer` on gendered nouns.
- P35, the rollout: (A) build and grade at once, with the audit after 200
  checked reviews or two weeks and the thresholds above.
- P36: the spec revision names the override as the one exception to "no
  undo of the last grade".
- P37: for gender "", accept the word alone or with any article. Is that
  acceptable, rather than "alone or with `die` only"?
- P3: confirm A as implied by D12 and D13, and with it that V5 (P28) is
  off the table.

## Round 6 (2026-10-30): context, near misses, D16, and whether the override survives

Read on feature/014:
- `text.py` (`fold`, `answer_matches`);
- `lexicon/fuzzy.py` (`fuzzy_deletes`, `max_distance`, `osa_within`);
- `lexicon/lookup.py` (`_candidate_keys`, `_key_distances`, `lookup_de`);
- `lexicon/models.py` (search_key, key_headword, fuzzy_delete, verb_form,
  de_entry.label, de_sense.labels, de_example);
- `lexicon/db.py` (`LexiconMissing`);
- `build/wiktextract_de.py` (`_label`) and `build/wiktextract_en.py`
  (`_gender`);
- `learning/content.py`, `tui/study.py`, `tui/addword.py`,
  `harald.tcss`;
- design §12.5 and the §16 confirmed list.

I could not query lexicon.db: no SQL tool here. Counts come from the
coordinator, and the rest is from code.

### Recommendation: one combined package, no override

What the checker accepts, in order. One pure function, fed by one
lexicon lookup:
1. Empty answer: Again (existing path).
2. Noun card with no gender (D16), answer starts with der/die/das:
   refuse the submission. No grade; the text stays in the field; the
   message reads `No article stored - type the word alone` (P38).
3. Exact match: digraphs, optional `sich`, article rules (D1, D2, D12).
   Good, or Hard / escalated Again for the article.
4. The word differs only in capitalisation (D14). Proposed narrowing,
   P43:
   - if the typed form is itself another headword (`essen` for `Essen`,
     `arm`/`Arm`, `laut`/`Laut`): Again;
   - otherwise (`hund` for `Hund`): a near miss as in step 6.
   - If D14 stays as decided: Again in both cases.
5. The typed word's folded key is a known German key (another word or
   word form):
   - same part of speech as the card: one retry with a cue (P44);
   - otherwise: Again.
6. Not a known key, and within the near-miss distance of the expected
   word (P42): Good, with the note `typo - Hund` (P42). The article part
   is judged separately by D12.
7. Anything else: Again.

What it grades: Again, Hard or Good, never Easy. Hard comes only from the
article (D12) and from a right answer on the retry (P44).

No "I was right" override. The spec's "There is no undo of the last
grade" stays as it is (P36 needs no change). Each review is written once,
when its verdict is final (after the retry, if there is one).

At card creation, context is limited to data the content already holds
(P41):
- the sense labels on the en_de front;
- the part of speech on the de_de front;
- de_de labels added to the content.

Plus P40: a noun added only from German-edition senses takes its gender
from the German entry's label.

### (a) Context at card creation, to narrow synonyms

What each card type holds today (`content.py`):
- en_de: lemma, pos, gender, gloss, labels, and the first translated,
  non-quotation example of the sense (German text plus English
  translation). The en_de front shows the gloss, the pos and the
  example's English translation, but not the labels. The de_en front
  does show them, as `[labels] gloss`.
- de_de: lemma, pos, gender, definition. It stores no labels and no
  examples, though the lexicon has `de_sense.labels` and `de_example`
  (German text only). The de_de front shows only the definition.

| Candidate | Data per card | Rows at 40 cols / 40x12 | Leaks the answer? | Storage (D13: content is JSON, no schema change) | Cards without it | Verdict |
|---|---|---|---|---|---|---|
| Sense labels (`colloquial`, `formal`, `dated`, `reflexive`) | en_de: in content. de_de: in the lexicon, not in content | 0, as a prefix on the gloss line like de_en; may wrap | no | en_de: none; de_de: add `labels` at creation | most senses carry no label (inference; F4 measures it) | yes, cheap |
| Part of speech | both, in content | de_de +1 row; en_de shows it already | no | none | none | yes for de_de |
| Gender | both | - | yes under A: it gives the article away | - | - | no |
| Cloze of the example sentence | en_de: the German text of the first translated example. de_de: German examples in the lexicon, not in content | replaces the English example line on en_de: about the same 1-3 rows; de_de +1-3 rows | high. Blanking must find the inflected form (`ging`, `Hunde`), split separable verbs (`rufe ... an`) and compounds; a missed form shows the answer | en_de: none; de_de: add an example | senses without a translated example (coverage in build_stat; not read here) | no: leak risk and blanking complexity |
| Other glosses of the sense | the en_de gloss already is the whole gloss string | - | no | - | - | adds nothing that narrows to one German word |
| First letter and length | always (from the lemma) | 0, as the field's placeholder | it is a cue: free recall becomes cued recall | none, derived | none | not standing; yes as the retry cue (P44) |

Can context replace the override? Not by itself:
- Labels and pos narrow some cases (gucken is `colloquial`; a de_de
  definition plus `verb` excludes nouns).
- English glosses stay ambiguous ("to look").
- Only the first-letter cue narrows to practically one word, and as a
  standing hint it weakens the exercise.

Using it only after a miss that looks like a synonym (P44) gets the
narrowing without weakening first attempts. Context doesn't change what
is accepted: the card's lemma stays the only right word. The cue only
changes what the learner aims at on the retry.

### (b) Near misses, with the known-word guard

What exists:
- `fold` (NFC, casefold, ä/ö/ü to digraphs; casefold also turns ß into
  ss) builds every `search_key`.
- `lookup_de` finds candidates through `fuzzy_delete` (symmetric
  deletes over the first 7 characters), then ranks them with
  `osa_within` (restricted Damerau-Levenshtein) and `max_distance` (1 up
  to 4 letters, else 2).
- `key_headword.kind` marks lemma (0) or inflected form (1). search_key
  covers lemmas and inflected forms, about 1.2M German keys per the
  comment in `_candidate_keys`, and includes proper nouns.

What the check needs is smaller than fuzzy lookup:
- The guard is an exact key lookup: is `fold(typed)` in
  `search_key(lang='de')`? It uses the unique `(lang, key)` index, and a
  join to key_headword and headword gives the lemmas (with their case)
  and parts of speech. `fuzzy_delete` isn't needed.
- The distance is pure: `osa_within(typed, expected, k)` on two strings,
  reused as is.
- Cost at study time: one indexed query per checked answer. That is
  ms-scale, an inference, not benched. It is the first time Study reads
  lexicon.db: the use case gets a `Lexicon` handle next to learning.db.
  The design's confirmed list says a missing lexicon.db is refused at
  startup (`LexiconMissing` exists in `lexicon/db.py`); I did not verify
  that the 014 TUI enforces it before Study.

Proposal (P42):
- Compare the typed word (article split off) with the lemma, both through
  `answer_matches`' normalisation (whitespace collapsed, ä/ö/ü/ß to
  digraphs), case-sensitively.
- Edits: substitution, insertion, deletion and adjacent transposition
  (OSA, as `osa_within`). Transposition is the commonest phone slip.
- Thresholds, by the lemma's length: up to 4 letters, no near miss; 5-9
  letters, distance 1; 10 or more, distance 2.
  - This is stricter than lookup's `max_distance`: lookup wants to find,
    grading wants to be sure.
  - Short words are where real neighbours crowd. Most short-word typos
    would hit a known key anyway.
- Guard: only if `fold(typed)` is not a known German key. Bar/Bär,
  Miete/Mitte and legen/liegen are all known keys, so they stay wrong
  words. That answers Round 1's objection.
- Digraphs and umlauts: unchanged. `Maedchen` is exact. `Madchen` (no
  umlaut, not a known key) is distance 1, so a near miss. `schon` for
  `schön` is a known key, so a wrong word.
- Grade: Good, with a note on the feedback line: `typo - Mädchen`.
  - Hard would push FSRS difficulty up on every finger slip, and phone
    slips are frequent.
  - The cost of Good: a persistent misspelling such as a missing umlaut
    is never drilled, only shown each time.
  - Knowledge defects (the article) stay Hard; finger slips are Good.
- With D12: the article is judged separately. A near-miss noun with the
  right article is Good with the typo note. With a wrong or missing
  article it is Hard, and the escalation counts it. The escalation's
  recomputation of the previous answer uses the same parser and guard.
- Autocorrect (P18, unverified): if Termux's keyboard autocorrects, it
  turns typos into real words, which the guard then grades as wrong
  words. That would be worse than no autocorrect. Verify in 009.

Capitalisation under the guard (P43). The coordinator's premise needs
one correction: "hund" is a known key, because keys are case-folded and
`Hund`'s own key is `hund`. So the folded guard can't see case at all,
and a case-only slip must be decided before it, by D14 or by P43.
- With D14 as decided: `hund`, `essen`/`Essen`, `arm`/`Arm` and
  `laut`/`Laut` are all Again.
- With P43, the case-sensitive check uses the headword lemmas from the
  same lookup:
  - `essen` typed for `Essen`: `essen` is itself a headword (verb), so
    Again, a different word;
  - `Arm`/`arm` and `Laut`/`laut`: both forms are headwords, so Again;
  - `hund` for `Hund`: no headword `hund`, so a case slip, near miss,
    Good with `typo - Hund`.
- Would I reopen D14? Yes, narrowly. Both of D14's reasons are covered:
  - the homograph pairs, by the headword check;
  - de_de showing no part of speech, by P41.
  Nothing else in the package depends on it. If the user keeps D14, steps
  4 and 6 simply don't merge.

### D16: an article typed on a no-gender card (P38)

| Option | What the learner sees | Cost |
|---|---|---|
| Mark wrong, Again, with the message | `No article stored - type the word alone`, graded Again | a lapse for a data gap. `der Tisch` is correct German, so this punishes the learner for the lexicon's hole. Unfair, and it pollutes the review log |
| Strip silently, grade the word | normal feedback | contradicts D16's "tell, don't silently accept" |
| Refuse the submission: no grade, the text stays, the message shows | `No article stored - type the word alone`; the field stays; Enter again after editing | one validation branch before the check; no FSRS effect; it enforces D16 and tells the learner about the gap. The `Word` label (D17's counterpart) makes this rare |

Recommended: refuse the submission.

Two findings that change D16's population:
- P40, an app-made gap. `content.py` sets `gender = entry.gender if entry
  else ""`. A noun added only from German-edition senses therefore gets
  gender "" even when the lexicon knows it: the German entry's label
  reads `das Band` (`wiktextract_de._label` builds it from the gender
  tags). D16 would then label the card `Word` and refuse `das Band`.
  Proposal: when no English entry is chosen, take the gender from the
  picked German entry's label. A small `content.py` change. That brings
  D16 down to genuine data gaps (about 1.1% of noun entries).
- P39, D16 against D6. Plural-only nouns most likely arrive with gender
  "" (inferred from `wiktextract_en._gender`, which keeps m/f/n only). D16
  would refuse `die Leute`, which D6 calls right. Options:
  - accept that D16 wins for these (type `Leute`);
  - or mark plural-only nouns in the importer and show `die` (a build
    change and rebuild; F4 first measures how the source tags them).
  User's call.

### The retry with a cue (P44), which replaces the override

- Trigger: the answer isn't right, isn't a near miss, and `fold(typed)`
  is a known key whose headword has the card's part of speech. That is
  the signature of a synonym (`schauen` for `gucken`) or of a same-class
  confusion (`Bar` for `Bär`).
- Screen: the front stays.
  - One message line replaces the field's hint row: `Another verb. Try:
    g _ _ _ _ _`. For long words, `g... (12 letters)` keeps it within 40
    columns.
  - The field is cleared and focused.
  - It is one try. Enter (or Check) checks again.
- Grade:
  - right on the retry (article rules included): Hard;
  - wrong or empty on the retry: Again.
  - FSRS's own meaning of Hard ("recalled with difficulty") fits a recall
    that needed a cue better than any other row does.
- Stored: `review.answer = "schauen | gucken"`, both attempts, as
  Stammformen joins its fields. The escalation and the audit read the
  last segment.
- No self-grading anywhere. The learner never judges their own answer,
  and nothing is regraded, so the spec's "no undo" holds unchanged.
- Rows at 40x12: front plus one message row, with the field in its usual
  place. About the same as the front with the digraph hint (inference;
  pilot test at (40, 12)).
- What it doesn't cover:
  - typos in words of up to 4 letters;
  - typos that land on a word of another part of speech;
  - synonyms of a different part of speech;
  - wrong data on the card.

  These stay Again. Data errors go through card edit (issue 017) or
  `harald check`. The audit (P35) measures the residue.

Considered and rejected: "accept an alternative", which would store the
typed synonym on the card as a further right answer. The card exists to
make the learner produce the word they chose to learn. Accepting
`schauen` forever means never practising `gucken`. It also mutates
content from a study action, which is an edit (issue 017), not a grade.

### Is the override still needed?

No, not with the package:
- typos are covered by P42;
- case slips by P43;
- synonyms by P41 plus P44;
- data errors by the edit and repair paths.

What's left is small and measurable (P35's audit). If the audit shows
false Agains above the Round 5 threshold (5% of checked reviews), the
override (P33, Round 5 design) is the fallback. P36 is then decided with
it.

Spec wording (P36): leave line 127, "There is no undo of the last grade.",
unchanged, and add nothing about an override.

### Draft spec wording for the package (replaces the third bullet of Round 2)

- English -> German and German -> German answers are typed and checked.
  ae/oe/ue/ss are accepted for ä/ö/ü/ß, and a verb may be typed with a
  leading `sich`.
- A noun whose gender is known is typed with its article. A wrong or
  missing article passes, graded Hard, unless the previous answer on that
  card also had a wrong article, in which case it fails.
- A noun without gender data is typed without an article. If an article
  is typed, Harald says that none is stored and asks again.
- A slip that is not itself a German word passes with a note, within one
  letter for words of 5 to 9 letters and two letters for longer words.
  [If P43: including a capitalisation slip that does not make another
  word.]
- If the answer is another German word of the same part of speech,
  Harald shows the first letter and the length and allows one more try,
  which passes graded Hard.

### Effect on the break list, build size and tests (against Round 4 (i) and Round 5)

Dropped from Round 5:
- the override button, key 3 and its tcss rules;
- the deferred write;
- the spec exception.

Key 3 stays unbound. Bindings are 1-2, used only by self-graded cards.

Added:
- `lexicon/`: one query function. Given a folded key, it returns the
  (lemma, pos, kind) rows. Exact key, no fuzzy.
- `use_cases/study.py`:
  - an `AnswerMeaning` use case holding both the learning.db and lexicon
    handles. It reads the card, its previous review and the lexicon rows,
    calls the pure function, and on a final verdict calls `grade_card`
    once;
  - on a retry verdict it writes nothing and returns the cue.
- `learning/answers.py`: the pure rating function. It parses the article,
  then applies D16, D12, D14 or P43, the guard, P42 and P44. Inputs:
  content, typed, previous answer, lexicon rows. It reuses
  `fuzzy.osa_within` and `text.fold`/`answer_matches`.
- `learning/content.py`: de_de content gains `labels` (and the gender
  from the German label, P40).
- `tui/study.py`:
  - `_card_faces` shows labels on en_de and pos on de_de;
  - the retry state (message row, field cleared);
  - the D16 refusal;
  - D17's `Check (enter)` and the field labels `Art. + noun` / `Word`;
  - feedback texts (`RIGHT`, `RIGHT - typo - X`, `article: der (you:
    die) - graded Hard`, `WRONG - graded Again`).
- Tests:
  - unit tests for every row of the function, with lexicon rows faked;
  - a component test of `AnswerMeaning` against the built fixture
    lexicon. The fixture may need a near-neighbour pair such as Bar/Bär
    and a case pair such as essen/Essen;
  - pilot tests for the retry, the near-miss note, the D16 refusal and
    D17's labels at (40, 30) and (40, 12);
  - plus Round 4's article removals and Round 2's meaning-card rewrites.

Size, as a judgement: about the same as Round 5's package.
- Round 5's override and deferred write go, replaced by the retry state
  and the lexicon lookup.
- The pure function grows by three rows. It stays one function with one
  input record.

### Rollout (P35) with this package

Still (A): build and grade from the first review. The safety net is now
the near miss and the retry, not the override.

The audit after 200 checked reviews or two weeks reads:
- Agains with a non-empty answer, which the learner labels;
- near misses (are they slips, or persistent misspellings?);
- retries and their outcomes;
- D16 refusals (data gaps met);
- escalations.

Thresholds:
- labelled false Agains above 5% of checked reviews: reconsider the
  override;
- near misses on the same card in two reviews running: consider grading
  persistent misspellings Hard.

### Open questions (replaces Round 5's list), each yes or no

- P45: the combined package, without the override, with the spec's "no
  undo" sentence unchanged.
- P38: refuse an article typed on a no-gender card, with no grade and a
  message.
- P40: a noun added only from German senses takes its gender from the
  German entry's label.
- P39: plural-only nouns. Is it acceptable that D16 wins (type `Leute`),
  or should the importer mark them so `die Leute` counts?
- P42: near misses that aren't known German words, distance 1 for 5-9
  letters and 2 for 10 or more, graded Good with a typo note.
- P43: reopen D14 narrowly. A case slip that isn't another headword
  (`hund`) is a near miss; `essen`/`Essen`, `arm`/`Arm`, `laut`/`Laut`
  stay Again.
- P44: a retry with first letter and length when the answer is another
  word of the same part of speech, graded Hard if right.
- P41: show labels on the en_de front and pos on the de_de front, store
  de_de labels; no cloze, no standing first-letter hint.
- P3: confirm A (implied by D12 and D13), and with it that V5 is off the
  table.

## Round 7 (2026-10-31): a learner-written context, and the final spec draft

Read on feature/014:
- `tui/addword.py` (steps `en`, `de`, `tense`, `confirm`; `SelectionList`
  pickers; `_mark_existing` plans each sense alone to mark "has cards");
- `learning/content.py` (the content snapshot per card type);
- `learning/cards.py` (`_key`, `drop_live_duplicates`);
- issue 017 (three criteria; content is editable);
- design §7.2, §7.3, §9 (the `$EDITOR` template, shared by phrase entry
  and card editing) and §14.8.

`editor.py` doesn't exist on 014 yet, so neither 017 nor 020 has landed.

### Recommendation on question 8: yes to the idea, later, with issue 017

A short learner-written note on the card is worth having. It narrows the
prompt to the word the learner chose, which no data field can do. But it
doesn't belong in change 3's first slice. It should arrive with issue 017
(edit cards):
- stored as `note` in the card's content;
- excluded from the dedupe key;
- shown dimmed under the gloss on the English -> German front;
- entered through 017's `$EDITOR` template;
- an Add word entry point only if real use shows the note is wanted at
  creation.

Change 3 keeps P41 (labels and part of speech from the data), if the user
confirms it.

### 1. Where it would be entered

| Option | Steps | Typing at 40 columns | Rows at 40x12 | Verdict |
|---|---|---|---|---|
| A new Add word step, one optional field per picked sense | +1 step for every word, even when skipped (one more `n`) | one Input per sense in a 40-column row (label plus field); a phrase of 20-40 characters wraps out of view in a one-line Input | step title (2 rows), one row per sense, buttons, footer: fits for 1-4 senses with the keyboard up; more scroll | possible; it costs every Add word a step for an optional field |
| One optional line per card on Confirm | 0 new steps | as above, plus Confirm's summary competing for the same rows | Confirm already holds the summary and refusals; inputs below them scroll at 40x12 | crowded; Confirm becomes a form |
| Pre-filled from the example translation or a trimmed gloss, editable | as either above | less typing | as above | the en_de front already shows the gloss and the example translation, so a pre-fill repeats what is on screen unless edited |
| Later, through issue 017's edit | 0 Add word steps | `$EDITOR` (multi-line, real editor); design §14.8 already rejected one-line TUI inputs for card editing on the phone for this reason | none in Add word | recommended |

The deciding point is timing. The need for a note usually shows up during
study: a retry (D24) or an Again on a synonym tells the learner this card
clashes with `telefonieren`. At Add word the learner is guessing which
clash will come. 017's edit path is where that knowledge lands. Phrase
entry already has the same shape: an optional note in the `$EDITOR`
template, shown on the phrase card's front as "(+ note)" (design §7.2).

### 2. Where it is stored

- Content JSON, field `note`, the same name phrase cards use. No schema
  change (D13): content is JSON. Existing cards lack it and read as no
  note (`content.get("note")`). There are none yet (D9).
- Dedupe, a real catch. `cards._key` keys meaning cards by the canonical
  JSON of their whole content, and `_mark_existing` marks "has cards" by
  planning a sense without a note. A card with a note would then:
  - no longer match its own sense's plan;
  - lose its "(has cards)" mark;
  - be duplicated when that sense is picked again.
  `_key` must drop `note` before canonicalising. That is one line, but it
  is required whichever entry point is chosen. Editing other content
  fields through 017 meets the same issue; that is 017's design step.
- Plan and refusals: untouched. A note isn't part of planning. If it were
  entered at Add word, `CreateWordCards` would take a per-sense mapping
  of notes; refusals don't change.

### 3. What it does to the check

- It only narrows the prompt. Acceptance is unchanged: the card's lemma
  is still the only right word.
- Compared with P41's labels, it can make synonym Agains rarer:
  - Labels exist on a minority of senses and describe register
    (colloquial, formal), not meaning.
  - A note is written for exactly the ambiguity the learner perceives
    ("to call a person over phone" points at `anrufen`, not `rufen`).
- What it can't do:
  - A context can still fit two words: "to call a person over phone"
    fits `anrufen` and `telefonieren`. D24's retry still catches that
    case.
  - It can't help on cards the learner hasn't annotated, which is most
    of them.
  - It doesn't help German -> German much: the German definition is
    already the context, and an English note there would add an English
    cue to a German-only card. Show it on English -> German only.

### 4. Leaks

The learner may write the answer, or its family, into the note ("ruf
an", "anrufen someone"). Proposed: a warning, not a refusal, when
`fold(note)` contains `fold(lemma)`. The note is the learner's own, and a
warning lets them keep a deliberate cue. Word-family detection (`ruf` in
`anrufen`) isn't attempted; it would need stemming.

### 5. First slice or later

Later. The reasons:
- Change 3 is already large: the article removal, the checker with seven
  steps, the lexicon lookup, the retry, the refusal and D17's cue.
- The note needs an entry point. The good one is 017's editor, which
  doesn't exist yet.
- With D24's retry in place, a synonym costs a cue and a Hard, not a
  lapse. The note's benefit is an improvement, not a fix.

Interaction with D17 and the card face:
- `Check (enter)` and the field label are unaffected.
- The note costs one dimmed row on the en_de front, more if it wraps. At
  40x12, with heading, gloss, part of speech, example translation, field,
  digraph hint and buttons, it could push the example translation into
  scrolling. The 40x12 pilot test should seed a card with a note when
  F11 is built.

Not recommended: dropping it. It is the only lever that encodes the
learner's own intent, and its storage cost is nil.

### Final spec wording (paste-ready; replaces the earlier drafts)

In the spec's own style. Arrows are written `->` here; the spec uses `→`.
Updated 2026-11-01: every item below is confirmed (D37-D40); the note
bullet is in Round 9.

**Adding a word** (replaces the bullets "Each chosen English-edition
sense yields two self-graded meaning cards", "Each chosen German-edition
sense yields a self-graded German -> German card" and "Nouns also get an
article card, answered with a single keypress"):

- Each chosen English-edition sense yields two meaning cards:
  - German -> English, self-graded;
  - English -> German, prompted with that sense's gloss and labels. The
    user types the German word and Harald checks it.
- Each chosen German-edition sense yields a German -> German card. It
  shows the German definition and the part of speech; the user types the
  German word and Harald checks it. There is no word -> definition
  direction, since that would mostly duplicate the German -> English card.
- A noun's gender comes from the chosen English-edition entry or, when
  only German-edition senses are chosen, from the German entry.
- Nouns get no separate article card. The article is part of the typed
  answer.

**Checked meaning answers** (new block, after "Conjugation answers are
typed and checked exactly..."):

- On English -> German and German -> German cards, Enter checks the typed
  answer. German -> English and phrase cards stay self-graded: Enter
  shows the answer and the user grades it.
- A checked answer is graded as follows:
  - An empty answer is graded Again.
  - The right word passes, graded Good. ae/oe/ue/ss are always accepted
    for ä/ö/ü/ß, and a verb may be typed with a leading `sich`.
  - A noun whose gender is known is typed with its article (`der Hund`).
    Any of the word's genders counts. A wrong or missing article still
    passes, graded Hard; if the previous answer on that card also had a
    wrong article, it is graded Again.
  - A noun without gender data is typed without an article. This
    includes plural-only nouns (`Leute`). If an article is typed, Harald
    says that none is stored and asks again, without grading.
  - A slip that is not itself a German word or word form passes, graded
    Good, and the correct spelling is shown. A slip is one wrong, missing,
    extra or swapped letter in words of 5 to 9 letters, and up to two in
    longer words. Words of up to 4 letters allow none.
  - Wrong capitalisation alone counts as such a slip, unless the
    other-case form is itself a German word (essen and Essen, arm and
    Arm, laut and Laut); then it is graded Again.
  - If the answer is another German word of the same part of speech,
    Harald shows the first letter and the length of the expected word
    and allows one more try. A right answer on that try passes, graded
    Hard. Anything else is graded Again.
  - Any other answer is graded Again.
- Checked answers are graded Again, Hard or Good. Hard comes only from
  the article and from the second try. Easy is never given.
- Checking needs `lexicon.db` while studying, to tell a slip from another
  real word.
- Checked grading applies from the first review. After 200 checked
  reviews or two weeks, the checked answers are audited against the
  user's own judgement. If more than 5% were failed wrongly, a way to
  claim a right answer is reconsidered.

**Non-goals** (two edits):
- "No typed checking of meaning or phrase answers." becomes: "No typed
  checking of German -> English or phrase answers. They have too many
  right answers."
- "Nouns and adjectives get meaning cards (and nouns an article card)
  like any word." becomes: "Nouns and adjectives get meaning cards like
  any word."

**Scheduling** (one edit, P49):
- "Parameters are scoped per card type: meaning, article, conjugation,
  phrase." becomes: "Parameters are scoped per card type: meaning,
  conjugation, phrase."

Unchanged: "There is no undo of the last grade." (D18).

**Separate small item: open question 7** (D10, D39):
- "7. **Defaults.** The default daily cap on new cards. Whether fuzzy
  ranking also applies to English -> German lookup and phrase search, or
  only to German lookup." becomes: "7. ~~Defaults.~~ Resolved: the daily
  cap on new cards defaults to 20. Fuzzy ranking applies to German and
  English -> German lookup, not to phrase search."
- The second sentence comes from design §16's confirmed list, not from
  this discussion; the user confirmed it (D39).

**Separate small item: sibling burying** (D11, D40):
- "Sibling cards (from the same word or phrase) are buried for the day."
  becomes: "Sibling cards (from the same word or phrase, and of the same
  card type) are buried for the day."

### Follow-ups, in order

1. F1: the user pastes the wording above into the spec at the next
   unfreeze.
2. F2: `new_feature` for change 3. Issues, design, test strategy, then
   implementation on a feature branch, including F10 (the lexicon-present
   check before Study).
3. F5: Termux checks in issue 009 (autocorrect, autocapitalisation, the
   keyboard staying up, taps on `Check (enter)`).
4. F7: the audit script after 200 checked reviews or two weeks.
5. F11 (if P46 is accepted): the note, with issue 017.

### Open questions (replaces Round 6's list)

- P46: a learner-written note, later with issue 017: field `note`, out of
  the dedupe key, dimmed on the English -> German front, a warning if it
  contains the word. Yes or no?
- P41: confirm labels on the English -> German front and the part of
  speech on the German -> German front, with de_de labels stored. It was
  part of the accepted package; question 8 was answered with a question.
- D21: confirm the reading of "accepted": plural-only nouns are typed
  without `die`, and there is no importer change.
- P48: confirm question 7's second half (fuzzy ranking for German and
  English -> German, not phrases), taken from design §16.
- P47: the sibling-burying bullet, reworded per D11. Yes or no?

## Round 8 (2026-10-31): the note at add time (D27)

Read on feature/014:
- `tui/addword.py`:
  - `AddWordScreen` with screen bindings `n`, `c`, `b`, `escape`;
  - a single `SelectionList` (`#picker`) rebuilt per step in `_show`,
    with labels carrying "(has cards)";
  - `PickEntryScreen`, an existing `ModalScreen` pattern;
  - `_mark_existing` plans each sense alone;
  - `_show_confirm` and `action_create` call `PlanWordCards`.
- `learning/content.py`: the en content dict built once per English sense
  and copied into `meaning_de_en` and `meaning_en_de`; the de_de dict.
- `learning/cards.py`: `_key` over `_canonical(content)`;
  `drop_live_duplicates`.
- `tui/study.py`: `_card_faces`, `_show` (front always rendered; back
  appended on reveal; feedback between them; `-short` drops blank lines).
- `tui/harald.tcss`.
- Design §7.2 (content table, lines 1490-1493), §7.3, §8.1 (per-card
  status table), and the §12.8 Add word frames (footer `space Toggle  n
  Next  esc Cancel`).

The user decided against Round 7's "later with 017". Their scenario is
right, and it removes Round 7's main reason. At Add word the learner is
looking at the whole entry, with its sense list and often the English ->
German lookup that brought them there. So the near-synonyms are in view,
and they know which card will need marking. Round 7's "you'd be guessing
at Add word" doesn't fit that case. The note is now decided (D27); what
follows is how to build it.

### Recommendation

Build the note as its own issue in the same feature, right after the
checker slice and before studying starts (P55):
- Entry: key `h` on a picker row opens a small one-line modal (P50).
- One note per picked sense, written into both cards of that sense (P51).
- Shown once under the gloss on English -> German. On German -> English,
  shown on the back only, which amends D27 (P52, P53).
- A warning if the note contains the word (P54).
- Notes only at the first add (P57).
- The same look as phrase notes (P56).

### Main session analysis: tested against the code

- "The Round 7 costs only apply to a mandatory step or a field on
  Confirm": agreed. A per-row key costs nothing for words that need no
  note, and Confirm is unchanged.
- "A key `h` on the highlighted sense": feasible, with three
  qualifications.
  - The picker is a Textual `SelectionList`. As far as I know it
    consumes space and Enter (toggle) and the navigation keys, but not
    letters, so `h` reaches a screen binding as `n`, `c` and `b` already
    do. The handler reads `picker.highlighted` and gets the option's
    value (the sense index `i`, or `(e, i)` on the German step). Verify
    with a pilot test that `h` isn't swallowed by the list.
  - On the phone the soft keyboard is normally down on a picker step.
    Termux's extra-keys row has no letters (design §12.5), so `h` needs
    either the soft keyboard or a tap on a footer hint `h Note`. Design
    §12.5 already accepts footer taps for infrequent actions.
  - Footer width: the 40-column frame `space Toggle  n Next  esc Cancel`
    is 32 cells, and `  h Note` makes 40, exactly the screen width. On
    later steps `b Back` is shown too. It may overflow; a pilot at 40
    columns decides. Fallbacks: a short `h` label, or dropping `esc
    Cancel` from the footer (the Cancel button already exists).
- "A one-line input; Enter stores it; the row shows a marker": yes, as a
  modal like `PickEntryScreen`, not an inline row. A modal leaves the
  `SelectionList` alone, brings the soft keyboard up only for the note,
  and returns the text through `dismiss`.
  - At 40x12 with the keyboard up: a bordered `Input` with a title is 3
    rows, plus the footer.
  - The marker is a suffix on the rebuilt label, `  + note`, the way
    `(has cards)` is added in `_show`.
- "Hint and mnemonic differ; one note on both sides": the distinction
  matters for leaks, not for storage.
  - A hint ("over the phone") on the English -> German front is the
    point of D27.
  - A mnemonic usually contains the word's sound ("an-RUF-en, like
    roof"), so on the English -> German front it often gives the answer
    away. P54's warning will fire for those.
  - On German -> English both kinds state or imply the English meaning,
    which is that card's answer (P52).

### 1. Entry and attachment

- English picker: `h` on sense `i` stores `notes[i]`.
  `plan_word_cards(..., notes)` puts `note` into the shared content dict
  before it is copied (content.py: the dict at lines 111-117 on 014, then
  `NewCard("meaning_de_en", content)` and `NewCard("meaning_en_de",
  dict(content))`). Both cards of the sense get the same note.
- German picker: the same key on `(e, i)` would put `note` into the de_de
  dict. That card type wasn't mentioned by the user, so this is open
  (P51). Recommended yes for symmetry: it is the same key, the same code
  path and one more dict.
- Picking implies ticking: a note on an unticked row could tick it.
  Recommended: `h` also ticks the row, since a note on a card you don't
  create is lost work.
- Verbs: Stammformen and conjugation cards are per word or per form, and
  already carry a hint gloss. No note (P58, open). The verb's meaning
  cards take notes like any word's.
- Nouns: the same as any word. The article card no longer exists (D25).
- A word with several entries (Band): Add word works on one chosen entry
  (`PickEntryScreen`), and the entry decides the discriminator, so each
  entry is its own word with its own senses and notes. Nothing special.
- A word that already has cards: `_mark_existing` marks those senses
  "(has cards)". Picking one again plans cards that dedupe drops, so a
  note typed there would vanish.
  - Recommended: refuse `h` on "(has cards)" rows with a toast: `This
    sense has cards - notes on existing cards come with card editing`
    (P57). That keeps Add word a creation tool.
  - The alternative, writing the note into the existing cards from Add
    word, is a content edit (issue 017's territory). It would need an
    update use case and the audit path.
- Confirm: unchanged, apart from an optional line such as `2 notes`.
  Recommended for visibility; the cost is one row.

### 2. Storage, dedupe, snapshot

- Built in `learning/content.py`: the en dict (all English senses) and
  the de_de dict. `note` is added only when non-empty, so cards without
  one have no key and render nothing (`content.get("note")`).
- Compared in `learning/cards.py` `_key`: `(card_type,
  _canonical(content))` for meaning cards. It must drop `note` first, for
  example `_canonical({k: v for k, v in content.items() if k !=
  "note"})`. Without that, a noted card never matches a later plan of
  its sense, loses "(has cards)" and is duplicated on the next add.
  `_mark_existing` plans without notes, so it relies on this.
- Shown in `tui/study.py` `_card_faces`: the meaning_en_de and
  meaning_de_en branches (and meaning_de_de if P51).
- Snapshot rule (design §7.2: content is the card's own copy):
  - the note is part of that copy, so a rebuild never touches it;
  - issue 017's edit later changes `content["note"]` like any field, and
    dedupe stays stable because `note` isn't in the key;
  - issue 021's per-card status compares named fields (gloss,
    definition, principal parts; §8.1), so a note doesn't flag a card;
  - but "accept upstream" repairs rewrite content from the lexicon, and
    they must carry `note` (and the new de_de `labels`) over (P59).
- D13: no schema change. Content is JSON.

### 3. Study faces

| Card | Where the note sits | 40 columns | 40x12 (`-short`) | 100x30 |
|---|---|---|---|---|
| English -> German (checked) | front, dimmed, in parentheses, under the gloss and part of speech, above the example translation | one row, with the length capped (below) | front: heading, gloss, pos, note, example translation, field, digraph hint, buttons, footer. About 10-11 rows with a one-row gloss and example, so it fits; long glosses or examples already risk scrolling under §7.13 | no constraint |
| English -> German after the check | the front stays on screen above the feedback, so the note stays visible through RIGHT / typo / article Hard / WRONG and the back. That one rendering satisfies D27's "front and back" | - | front plus verdict plus `you:` plus the back (word and example) plus Next: the tightest screen. With the note it likely scrolls when the example sentences are long (inference) | fits |
| English -> German retry | front stays; the message row replaces the digraph hint | - | the same as the front plus one row | fits |
| German -> English (self-graded), D27 as decided | front, under the German word | one row | front: heading, word, pos, note, example, field, buttons | fits |
| German -> English, P52 back-only | back, after the gloss | one row | appears with the reveal; the front is a row shorter | fits |

- How it helps the checker flow: on English -> German the note narrows
  the prompt before the learner types, so fewer synonym retries (D24).
  It doesn't touch `Check (enter)` or the `Art. + noun` label.
- Wrap: cap the note's length at entry so it renders on one row at 40
  columns. Textual's `Input` takes `max_length`; the exact number is the
  card body's width at 40 columns, about 36, to be confirmed by the
  pilot. One row keeps the budget predictable. A longer mnemonic would
  wrap to two or three rows and push the field below the keyboard.
- Pilot tests to name, all at (40, 12) unless stated:
  - `test_note_on_english_german_front_fits_at_40x12`
  - `test_note_stays_visible_with_checked_feedback_at_40x12`
  - `test_note_stays_visible_on_retry_at_40x12`
  - `test_note_on_german_english_card_fits_at_40x12` (front or back, per
    P52)
  - `test_note_input_is_capped_to_one_row_at_40_columns` (40, 30)
  - `test_note_key_marks_the_sense_row` (Add word, 40, 30 and 40, 12)
  - `test_note_key_is_refused_on_a_sense_with_cards`
  - `test_add_word_footer_with_note_hint_fits_40_columns`
  - component: `test_dedupe_ignores_the_note`

### 4. Leaks

- English -> German front: a note containing the word, or a mnemonic
  built on its sound, gives the answer away. Proposed (P54): a warning in
  the modal when `fold(note)` contains `fold(lemma)` (after stripping a
  leading `sich`), for example `The note contains the word - keep it?`,
  where Enter keeps it and Esc goes back to editing. Not a refusal; the
  note is the learner's own. Word families aren't attempted. `ruf` in
  `anrufen` would need stemming, and the lemma check catches the common
  case.
- German -> English front: the card shows the German word, and its
  answer is the English meaning. A note written to separate near-synonyms
  ("over the phone") or a mnemonic ("call up") states that meaning, so on
  this front it is a leak by design, however the learner words it.
  Recommendation (P52): German -> English shows the note on the back
  only. That amends D27, so it is the user's call. If D27 stands as
  decided, no warning helps here, because the leak is the note's purpose.
- German -> German front (if P51): the answer is the German word, and an
  English note rarely contains it. The same lemma warning applies.

### 5. Slice placement

| Option | What it costs | Risk |
|---|---|---|
| Part of change 3's first slice | the largest single review: article removal, checker, lexicon lookup, retry, refusal, cue, plus Add word modal, content, dedupe and faces | the memory note on chunking slices applies. One slice touching both Add word and Study is hard to review |
| A second issue in the same feature, after the checker (recommended) | one more issue and review cycle; small: about one modal, one binding, a content parameter, one dedupe line, two face lines and the tests above | none to the checker. Built before studying starts, so the D26 audit sees the final behaviour |
| Later, with issue 017 | none now | decided against (D27) |

The user's "now rather than later" is met by the second option. It lands
in the same feature, before the first study session. It only waits for
the checker to settle the English -> German face it adds a row to.

### 6. Phrase notes

- Phrases already have a note: the `$EDITOR` template's optional note,
  stored on the `phrase` row (design §7.1, `note TEXT NOT NULL DEFAULT
  ''`), shown on the phrase card's front ("(+ note)", design §7.2).
- Field name: the same, `note`. That is clearer in code and docs.
  Storage differs for a reason: a phrase has one card and a row of its
  own, while a word's note belongs to a sense and lives in each card's
  content.
- Look: the same. Dimmed, in parentheses, on its own row under the
  prompt. A shared few-line render helper is optional; two call sites
  don't demand one.
- Side: phrase notes stay front-only. A phrase card's answer is the
  German sentence, and an English note doesn't give it away, so nothing
  changes there.

### Spec wording added for the note (extends Round 7's final draft)

Under **Adding a word**:
- When picking senses, the user can add a short note to a sense, a hint
  or mnemonic of their own, for example "to call someone on the phone".
  It is stored with that sense's cards and shown on English -> German
  cards with the prompt, and on German -> English cards with the answer.
  [If D27 stands unamended: "and on German -> English cards on both
  sides".] A note can only be added when the sense's cards are created.
- [If P51: "German-edition senses take a note the same way, shown with
  the German -> German prompt."]

### Open questions (replaces Round 7's list), each yes or no

- P52: on German -> English, show the note on the back only, because on
  the front it states that card's answer? This amends D27.
- P50: the `h` key on the picker opens a one-line note modal; the row
  shows `+ note`; `h` also ticks the row; the footer gains `h Note` if it
  fits 40 columns.
- P51: German-definition rows take a note the same way, for the German ->
  German card.
- P53: the note capped to one row at 40 columns (about 36 characters,
  confirmed by the pilot).
- P54: warn, not refuse, when the note contains the word.
- P55: the note as a second issue in the same feature, after the checker
  and before studying starts.
- P56: phrase notes and word notes share the name `note` and the same
  look; phrase notes stay front-only.
- P57: notes only when a sense's cards are created; editing existing
  cards' notes comes with issue 017.
- P58: no notes on Stammformen and conjugation cards.
- Still open from Round 7: P41 (labels and part of speech), D21's
  reading, P48 (question 7's second half), P47 (sibling-burying wording).

## Round 9 (2026-10-31): the note on the German -> English front

The user said "yes to all nine, keep the note on both sides". Read with
the main session: yes to questions 2-9 (D28-D35), and on question 1 D27
stands (D36). The note shows on the front and the back of German ->
English as well as English -> German, and the leak on the German ->
English front is accepted by design. The thinking partner reads the
answer the same way.

Everything below is open.

### 1. Which leak warning fits German -> English (P60)

- On that card the front shows the German word (`anrufen`), and the
  answer is the English meaning. A note written to tell near-synonyms
  apart ("to call someone on the phone") states that meaning. A mnemonic
  ("call up") does too. That isn't an accident to warn about; it is what
  a useful note on this card does.
- A warning on overlap with the English gloss would therefore fire on
  nearly every useful note. A whole-gloss substring match would almost
  never fire, because glosses are long ("to call (by telephone), to ring
  up"). A word-overlap match would fire on almost all. Either way it is
  noise.
- Recommended: no gloss warning. Keep only D31's lemma warning, which
  protects English -> German. Make the visibility explicit when the note
  is written instead (point 3), so accepting the German -> English leak
  is a choice the learner sees, not a surprise.
- A mild side effect to accept: on German -> English the note turns
  recall into cued recognition for that card. With D36 that is the
  learner's trade.

### 2. 40x12 budget on the German -> English front (P61)

`-short` hides the header and drops blank lines.

| State | Rows (one-row note, D30) | Fits 12? |
|---|---|---|
| Front | heading 1, `der Hund` 1, pos 1, note 1, German example 1-3, field 1, buttons 1 plus margin 1, footer 1 | 9-11: fits with an example of up to three rows |
| After reveal (self-graded) | front as above minus the field, plus divider 1, `you:` 1, gloss 1-2, translation 1-3, grade buttons 1 plus margin 1, footer 1 | 12-17: a long example already scrolls today under §7.13; the note adds one row |

- Position: under the part of speech, above the German example, the same
  slot as on English -> German. One look across the meaning cards.
- If the after-reveal state scrolls in the pilot, the mitigation is open.
  Candidates:
  - under `-short`, drop the front's example sentence once revealed (the
    back shows the translation);
  - or accept scrolling for long examples, as §7.13 does today.

  Not decided here.

### 3. What the learner sees when writing the note (P62)

The note box, at 40 columns:

```
+- Note for this sense ---------------+
| [to call someone on the phone      ]|
+-------------------------------------+
 Shown before you answer, both sides
enter Save  esc Cancel
```

- `Shown before you answer, both sides` is 36 cells. It tells the learner
  that the note is visible on the prompt side of both cards, including
  German -> English, where it stands next to the German word.
- On the German-definitions step the same box serves the German ->
  German card. It is the same line, which is true there too: the front
  stays on screen through the check.
- When D31's lemma warning fires, the line becomes `Contains the word -
  Enter keeps it` (34 cells). Enter keeps the note; editing and Enter
  again re-checks.
- Rows with the keyboard up: box 3, line 1, footer 1, so 5. That fits
  above the soft keyboard at 40x12.

### 4. Tests the note slice needs for German -> English (P63)

Pilot tests:
- `test_note_on_german_english_front_fits_at_40x12`, with a three-row
  German example;
- `test_note_on_german_english_after_reveal_at_40x12`. It records whether
  it scrolls, so P61's decision rests on a measurement;
- `test_note_on_german_english_front_sits_under_pos` at (40, 30) and
  (100, 30);
- `test_german_english_card_without_note_is_unchanged`, a regression
  check that existing de_en layouts and tests keep passing;
- `test_note_box_says_it_is_shown_before_answering` (Add word, both
  steps);
- `test_note_box_lemma_warning_keeps_the_note_on_enter`.

Component tests:
- `test_both_cards_of_a_sense_carry_its_note` (de_en and en_de);
- `test_de_de_card_carries_its_note`.

These sit next to Round 8's English -> German and Add word tests in the
note slice's test strategy (F12).

### Spec wording for the note (final; replaces Round 8's bracketed draft)

Confirmed 2026-11-01, unchanged by D41-D44: the warning sentence below is
the lemma warning, the only one (D41).

Under **Adding a word**:
- When picking senses, the user can add a one-line note to a sense: a
  hint or mnemonic of their own, for example "to call someone on the
  phone". It is stored with that sense's cards. On English -> German and
  German -> English cards it is shown on both sides, so it is visible
  before answering. A note on a German definition is shown on its German
  -> German card. Harald warns, but keeps the note, if it contains the
  word itself.
- A note can only be added when the sense's cards are created. Editing
  notes comes with card editing.
- Stammformen and conjugation cards take no note. Phrase notes are
  unchanged.

### Open questions (replaces Round 8's list)

Round 9, each yes or no:
- P60: no gloss-overlap warning on German -> English; only the lemma
  warning.
- P61: if the German -> English after-reveal screen scrolls at 40x12,
  drop the front's example sentence once revealed under `-short`, or
  accept scrolling as today.
- P62: the note box line `Shown before you answer, both sides`, and the
  warning line `Contains the word - Enter keeps it`.
- P63: the test list above, for the note slice's test strategy.

Waiting from earlier rounds: P41, D21's reading, P48 and P47 (see the
top of the log).

## Round 10 (2026-11-01): the answers, and the discussion settled

The user answered yes to all eight: Round 7's four (P41, D21's reading,
P48, P47) and Round 9's P60-P63. They are logged as D37-D44. P61 was an
either/or, and its answer took its own shape: measure first, accept
about a row of scrolling, and drop the front's example only if the
measurement shows worse (D42).

Checked against each other and against D1-D36:
- D42's threshold has two readings (P64, under the Decided table). Under
  one the fallback can never fire; under the other it fires on long
  examples whether or not there is a note. The pilot measures both, so
  the reading is taken from rows on screen.
- D44 names `test_note_on_german_english_after_reveal_at_40x12` as
  recording "whether it scrolls". D42 needs the number of rows, with and
  without the note. The Tests table in the impact section says so; the
  test's name is unchanged.
- D38 with D19: `die Leute` is correct German, and it is refused without
  a grade. That is consistent and already in the spec draft, but the
  learner will meet it on a right answer. The D26 audit counts D19
  refusals, so its frequency becomes visible.
- D37 includes storing de_de `labels`. The question asked for it, so it
  is logged as part of the yes, though the answer's summary named only
  the two fronts.
- D39: the answer says "fuzzy matching", the spec says "fuzzy ranking".
  The draft keeps the spec's term; they mean the same thing here.

Nothing else conflicts. The discussion is settled. What follows is F1
(the user pastes Rounds 7 and 9's wording at the next unfreeze), then F2
and F12 through `new_feature`.
