# Regenerate by hand from the repository root: vhs docs/demo/tui.tape
# See dev/docs/demo-gif.md. Every key typed while shown must be in a guide key table.
Output docs/demo/tui.gif

Set Shell bash
Set FontSize 14
Set Width 1000
Set Height 560
Set Padding 16
Set TypingSpeed 80ms
Set WaitPattern /\$$/
Set WaitTimeout 60s

Hide
Type "source .venv/bin/activate; export PS1='$ '" Enter
Type `D=$(mktemp -d); python -m tests.docs.sample "$D"` Enter
Type `export HOME=$D XDG_CONFIG_HOME=$D/.config XDG_DATA_HOME=$D/.local/share XDG_CACHE_HOME=$D/.cache COLUMNS=80; unset HARALD_CONFIG; cd "$D"; clear` Enter
Sleep 500ms
Wait
Show

Type "harald" Enter
Sleep 2s

Type "l"
Sleep 1s
Type "Hund"
Sleep 800ms
Enter
Sleep 2s
Enter
Sleep 2s

Type "a"
Sleep 2s
Space
Sleep 1500ms
Type "n"
Sleep 2500ms
Type "c"
Sleep 3s

Escape
Sleep 1s
Escape
Sleep 1s
Escape
Sleep 1500ms

Type "s"
Sleep 2s
Type "dog"
Sleep 800ms
Enter
Sleep 2s
Type "2"
Sleep 2s
Type "der Hund"
Sleep 800ms
Enter
Sleep 2500ms
Escape
Sleep 3s
Enter
Sleep 1500ms
Type "q"
Sleep 1s
