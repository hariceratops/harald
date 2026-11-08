# Cards and study

Everything here runs in the TUI:

```sh
uv run harald
```

Cards live in `learning.db`, created on first use. Harald refuses one written
by a newer version.

## Add a word

Open an entry (`l`, search, pick a result), then press `a`.

- Pick English senses: each gives a **German → English** and an
  **English → German** card.
- Pick German definitions: each gives a **German → German** card.
- Verbs also get a **Stammformen** card and offer tenses (none ticked): each
  ticked tense gives six **conjugation** cards, one per person.
- Nouns get no article card. The article is part of the answer.

<!-- docs: keys add-word -->
| Key | Does |
|---|---|
| `space` | tick or untick a row |
| `n` / `b` | next / back |
| `h` | add a note to the row |
| `c` | confirm and create |
| `esc` | cancel |

- Rows that already have cards are marked `(has cards)`.
- A verb whose data lacks a form is refused that card, and the confirm step
  names the missing forms.

## Notes

- `h` on a sense opens a one-line note, up to 36 characters:
  `to call someone on the phone`.
- `enter` keeps it and marks the row `+ note`. An empty `enter` removes it.
  `esc` leaves it as it was.
- If the note contains the word itself, the box warns
  `Contains the word - Enter keeps it`. The note is still kept.
- A sense that already has cards takes no note.
- The note shows as a dim row under the part of speech, on both sides of the
  card, until you grade it.

## Study

Press `s` on Home. Cards come due by FSRS. Each grade is saved at once, and a
summary ends the session.

| Card | You | Grades |
|---|---|---|
| English → German, German → German | type the word, `enter` | Again, Hard or Good, by Harald |
| German → English | type a guess, `enter`, then grade | `1` Again, `2` Good |
| Stammformen | type three forms | Again or Good, by Harald |
| Conjugation | type one form | Again or Good, by Harald |

- An empty answer counts as not knowing: Again.
- On a touch screen the same actions are buttons.

## Typing a word

- Nouns with a known gender take the article: `der Hund`. The field reads
  `Art. + noun`.
- Other words are typed alone: `laufen`. Names and nouns with no stored gender
  are typed without an article too, and the field reads `Word`.
- A verb may start with `sich`: `sich beeilen`.
- `ae`, `oe`, `ue`, `ss` count for `ä`, `ö`, `ü`, `ß`.
- Conjugation cards: no subject pronoun. Type `rufe an`, not `ich rufe an`. On a
  reflexive verb the reflexive pronoun is accepted after the first word:
  `freue` and `freue mich` both count.
- Stammformen cards: 3rd person singular, Präteritum, Perfekt, such as
  `ruft an`, `rief an`, `hat angerufen`. Move between fields with `enter`.

## How a checked answer is graded

| You typed | Grade |
|---|---|
| the right word | Good |
| the right word, wrong or missing article | Hard |
| a wrong article again on the same card | Again |
| a one-letter slip that is not itself a German word | Good, with the right spelling shown |
| wrong capitalisation, other case is not a word | Good |
| wrong capitalisation, other case is a word (`essen` for `Essen`) | Again |
| another German word of the same part of speech | one retry |
| the right word on the retry | Hard |
| anything else, or nothing | Again |

- Slips: one wrong, missing, extra or swapped letter in words of 5 to 9
  letters, two in longer words, none in words of up to 4 letters.
- The retry shows a hint and clears the field: `Another noun. Try: H _ _ _`.
- A noun with no stored gender refuses a typed article: the card says so and
  you type again, ungraded.
- Checking needs `lexicon.db`. If it has gone, study returns to Home with a
  message.

## Audit your grades

After 200 checked reviews or two weeks, see how often Harald failed you
wrongly. Work on a copy:

```sh
cp ~/.local/share/harald/learning.db /tmp/learning-copy.db
python3 dev/audit/checked_answers.py /tmp/learning-copy.db
```

- It shows each failed answer beside the right one. Press `y` if you were
  right, `n` or `enter` if not, `q` to stop.
- It prints the share of checked reviews you marked `y`. Above 5%, the
  checking needs another look.
- It reads the copy only and stores nothing.
