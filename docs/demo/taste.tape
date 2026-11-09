# Regenerate by hand from the repository root: vhs docs/demo/taste.tape
# See dev/docs/demo-gif.md. The visible Type lines must match the README block.
Output docs/demo/taste.gif

Set Shell bash
Set FontSize 14
Set Width 1000
Set Height 420
Set Padding 16
Set TypingSpeed 40ms
Set WaitPattern /\$$/
Set WaitTimeout 60s

Hide
Type "source .venv/bin/activate; export PS1='$ '" Enter
Type `D=$(mktemp -d); python -m tests.docs.sample "$D"` Enter
Type `export HOME=$D XDG_CONFIG_HOME=$D/.config XDG_DATA_HOME=$D/.local/share XDG_CACHE_HOME=$D/.cache COLUMNS=80; unset HARALD_CONFIG; cd "$D"; clear` Enter
Sleep 500ms
Wait
Show

Type "harald-cli lookup lief" Enter
Sleep 500ms
Wait
Sleep 3s

Hide
Type "clear" Enter
Show
Type "harald-cli lookup --en use" Enter
Sleep 500ms
Wait
Sleep 4s
