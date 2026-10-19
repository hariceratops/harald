from pathlib import Path


class LexiconError(Exception):
    pass


class LexiconMissing(LexiconError):
    def __init__(self, path: Path) -> None:
        super().__init__(f"{path} does not exist. Run 'harald build' on the desktop first.")
        self.path = path


class NotALexicon(LexiconError):
    def __init__(self, path: Path, detail: str) -> None:
        super().__init__(f"{path} is not a lexicon database: {detail}")
        self.path = path
        self.detail = detail


class SchemaMismatch(LexiconError):
    def __init__(self, found: int, expected: int, harald_version: str) -> None:
        super().__init__(
            f"lexicon.db has schema {found}, but Harald {harald_version} needs schema "
            f"{expected}. Rebuild on the desktop or update Harald."
        )
        self.found = found
        self.expected = expected
        self.harald_version = harald_version
