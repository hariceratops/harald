import ast
from pathlib import Path

import harald

SRC = Path(harald.__file__).parent
ALLOWED = (
    "harald.use_cases",
    "harald.render",
    "harald.config",
    "harald.core.result",
    "harald.lexicon.errors",
    "harald.lexicon.model",
)


def _harald_imports(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            found.update(a.name for a in node.names if a.name.split(".")[0] == "harald")
        elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "harald":
            found.add(node.module or "")
    return found


def test_front_ends_import_only_use_cases_and_their_neighbours() -> None:
    front_ends = [SRC / "cli.py", *(SRC / "tui").rglob("*.py")]

    for path in front_ends:
        for module in _harald_imports(path):
            assert any(module == a or module.startswith(a + ".") for a in ALLOWED), (
                f"{path.name} imports {module}"
            )
