from pathlib import Path


class BuildError(Exception):
    pass


class SourceMissing(BuildError):
    def __init__(self, file: Path) -> None:
        super().__init__(f"source file {file} is missing. Place the English dump there.")
        self.file = file


class SourceUnreadable(BuildError):
    def __init__(self, file: Path, detail: str) -> None:
        super().__init__(f"cannot read {file}: {detail}")
        self.file = file
        self.detail = detail


class TooFewEntries(BuildError):
    def __init__(self, found: int, minimum: int) -> None:
        super().__init__(
            f"only {found} German entries found, expected at least {minimum}; "
            "the source format may have changed. Nothing was published."
        )
        self.found = found
        self.minimum = minimum


class BuildFailed(BuildError):
    def __init__(self, stage: str, detail: str) -> None:
        super().__init__(f"build failed in {stage}: {detail}")
        self.stage = stage
        self.detail = detail
