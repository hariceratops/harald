from collections import Counter
from datetime import UTC, datetime

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.content import Content
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Footer, Header, OptionList, SelectionList, Static
from textual.widgets.option_list import Option
from textual.widgets.selection_list import Selection

from harald.config import Config
from harald.lexicon.model import Headword
from harald.use_cases.cards import CreateWordCards, PlanWordCards

_ARTICLES = {"m": "der", "f": "die", "n": "das"}
_CARD_NAMES = {
    "meaning_de_en": "German -> English",
    "meaning_en_de": "English -> German",
    "meaning_de_de": "German -> German",
    "article": "Article",
    "stammformen": "Stammformen",
}


def entry_label(hw: Headword, entry_index: int) -> str:
    entry = hw.entries[entry_index]
    article = "/".join(_ARTICLES.get(g, "") for g in entry.gender)
    parts = [f"{article} {hw.lemma}".strip()]
    if entry.plural:
        parts.append(f"pl. {entry.plural}")
    if entry.senses:
        parts.append(entry.senses[0].gloss)
    return "  ".join(parts)


class PickEntryScreen(ModalScreen[int | None]):
    BINDINGS = [Binding("escape", "dismiss(None)", "Cancel")]

    def __init__(self, headword: Headword) -> None:
        super().__init__()
        self._headword = headword

    def compose(self) -> ComposeResult:
        yield OptionList(
            *(
                Option(Content(entry_label(self._headword, i)))
                for i in range(len(self._headword.entries))
            ),
            id="pick-entry",
        )
        yield Footer(compact=True)

    def on_mount(self) -> None:
        picker = self.query_one(OptionList)
        picker.border_title = "Add which entry?"
        picker.highlighted = 0

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option_index)


class AddWordScreen(Screen[None]):
    TITLE = "Add word"
    BINDINGS = [
        Binding("n", "next", "Next"),
        Binding("c", "create", "Create"),
        Binding("b", "back", "Back"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, config: Config, headword: Headword, entry_index: int | None) -> None:
        super().__init__()
        self._config = config
        self._headword = headword
        self._entry_index = entry_index
        self._steps = [
            *(["en"] if entry_index is not None and headword.entries[entry_index].senses else []),
            *(["de"] if headword.german else []),
            "confirm",
        ]
        self._at = 0
        self._en_picked: list[int] = []
        self._de_picked: list[tuple[int, int]] = []
        self._en_have: set[int] = set()
        self._de_have: set[tuple[int, int]] = set()
        self._new_count = 0

    def compose(self) -> ComposeResult:
        yield Header(icon="")
        yield Static(id="step")
        yield SelectionList[object](id="picker")
        with VerticalScroll(id="confirm"):
            yield Static(id="summary")
        with Horizontal(id="buttons"):
            yield self._button("Cancel", "back")
            yield self._button("Next >", "next")
        yield Footer(compact=True)

    @staticmethod
    def _button(label: str, id: str) -> Button:
        button = Button(label, id=id)
        button.can_focus = False
        return button

    def on_mount(self) -> None:
        self.sub_title = (
            entry_label(self._headword, self._entry_index or 0)
            if (self._entry_index is not None)
            else self._headword.lemma
        )
        if not self._mark_existing():
            self.app.pop_screen()
            return
        self._show()

    def _mark_existing(self) -> bool:
        """Senses whose cards all exist already: their plan, after dedupe, is empty."""
        entry = self._headword.entries[self._entry_index] if self._entry_index is not None else None
        for i in range(len(entry.senses) if entry else 0):
            planned = PlanWordCards(self._config).execute(
                self._headword, self._entry_index, [i], []
            )
            if planned.is_err:
                self.notify(str(planned.unwrap_err()), severity="error")
                return False
            if not planned.unwrap().cards:
                self._en_have.add(i)
        for e, de_entry in enumerate(self._headword.german):
            for i, sense in enumerate(de_entry.senses):
                if sense.index is None:
                    continue
                planned = PlanWordCards(self._config).execute(
                    self._headword, self._entry_index, [], [(e, i)]
                )
                if planned.is_err:
                    self.notify(str(planned.unwrap_err()), severity="error")
                    return False
                if not planned.unwrap().cards:
                    self._de_have.add((e, i))
        return True

    @property
    def _step(self) -> str:
        return self._steps[self._at]

    def _capture(self) -> None:
        if self._step == "en":
            self._en_picked = [
                v for v in self.query_one(SelectionList).selected if isinstance(v, int)
            ]
        elif self._step == "de":
            self._de_picked = [
                v for v in self.query_one(SelectionList).selected if isinstance(v, tuple)
            ]

    def _show(self) -> None:
        picker = self.query_one("#picker", SelectionList)
        confirm = self.query_one("#confirm")
        step = self._step
        picker.display = step != "confirm"
        confirm.display = step == "confirm"
        total = len(self._steps)
        titles = {
            "en": "English senses (each gives a de->en and an en->de card)",
            "de": "German definitions (each gives a de->de card)",
            "confirm": "Confirm",
        }
        self.query_one("#step", Static).update(
            Content(f"Step {self._at + 1} of {total}: {titles[step]}")
        )
        picker.clear_options()
        if step == "en":
            entry = self._headword.entries[self._entry_index or 0]
            for i, sense in enumerate(entry.senses):
                label = f"{i + 1}. {_labelled(sense.labels, sense.gloss)}"
                if i in self._en_have:
                    label += "  (has cards)"
                picker.add_option(Selection(Content(label), i, i in self._en_picked))
            picker.highlighted = 0
            picker.focus()
        elif step == "de":
            for e, de_entry in enumerate(self._headword.german):
                picker.add_option(Selection(Content(de_entry.label), (e, -1), disabled=True))
                for i, de_sense in enumerate(de_entry.senses):
                    if de_sense.index is None:
                        picker.add_option(
                            Selection(Content(f"    {de_sense.gloss}"), (e, i), disabled=True)
                        )
                        continue
                    label = f"[{de_sense.index}] {_labelled(de_sense.labels, de_sense.gloss)}"
                    if (e, i) in self._de_have:
                        label += "  (has cards)"
                    picker.add_option(Selection(Content(label), (e, i), (e, i) in self._de_picked))
            picker.highlighted = next(
                i for i in range(picker.option_count) if not picker.get_option_at_index(i).disabled
            )
            picker.focus()
        else:
            self._show_confirm()
        self.query_one("#back", Button).label = "Cancel" if self._at == 0 else "< Back"
        advance = self.query_one("#next", Button)
        advance.label = f"Create {self._new_count} cards" if step == "confirm" else "Next >"
        advance.disabled = step == "confirm" and self._new_count == 0
        self.refresh_bindings()

    def _show_confirm(self) -> None:
        planned = PlanWordCards(self._config).execute(
            self._headword, self._entry_index, self._en_picked, self._de_picked
        )
        summary = self.query_one("#summary", Static)
        if planned.is_err:
            self._new_count = 0
            summary.update(Content(str(planned.unwrap_err())))
            return
        plan = planned.unwrap()
        by_type = Counter(c.card_type for c in plan.cards)
        picked = 2 * len(self._en_picked) + len(self._de_picked)
        lines = ["Cards to create"]
        lines += [f"  {n} x {_CARD_NAMES[t]}" for t, n in by_type.items()]
        if not plan.cards:
            lines.append("  nothing new")
        if picked > len(plan.cards):
            lines.append(f"Already have: {picked - len(plan.cards)}")
        lines.append("Refused")
        lines += [
            f"  {_CARD_NAMES.get(r.card_type, r.card_type)} - missing: {', '.join(r.missing)}"
            for r in plan.refusals
        ] or ["  none"]
        self._new_count = len(plan.cards)
        summary.update(Content("\n".join(lines)))

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        last = self._step == "confirm"
        if action == "next":
            return not last
        if action == "create":
            return last and self._new_count > 0
        return True

    def action_next(self) -> None:
        self._capture()
        self._at += 1
        self._show()

    def action_back(self) -> None:
        if self._at == 0:
            self.action_cancel()
            return
        self._capture()
        self._at -= 1
        self._show()

    def action_cancel(self) -> None:
        self.app.pop_screen()

    def action_create(self) -> None:
        planned = PlanWordCards(self._config).execute(
            self._headword, self._entry_index, self._en_picked, self._de_picked
        )
        if planned.is_err:
            self.notify(str(planned.unwrap_err()), severity="error")
            return
        plan = planned.unwrap()
        created = CreateWordCards(self._config).execute(plan, datetime.now(UTC))
        if created.is_err:
            self.notify(str(created.unwrap_err()), severity="error")
            return
        refused = "".join(
            f" {r.card_type} refused - missing: {', '.join(r.missing)}." for r in plan.refusals
        )
        self.notify(f"{len(created.unwrap())} cards created.{refused}")
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        if event.button.id == "next":
            if self._step == "confirm":
                self.action_create()
            else:
                self.action_next()
        else:
            self.action_back()


def _labelled(labels: tuple[str, ...], gloss: str) -> str:
    return f"[{', '.join(labels)}] {gloss}" if labels else gloss
