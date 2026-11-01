# [feat] Save a found phrase as a production card

Depends on 010 and 018.

Spec: `dev/specs/harald-v1.md`

## Acceptance Criteria

- A found pair can be saved from search results.
- A saved pair keeps its own copy in `learning.db` and yields a self-graded English → German phrase card in the phrase FSRS scope. The learner types their German phrase before the reveal and sees it beside the saved one; the attempt is stored with the review, never graded automatically, and an empty attempt is graded Again.
