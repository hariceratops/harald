from pathlib import Path


class BuildError(Exception):
    pass


class SourceMissing(BuildError):
    def __init__(self, file: Path) -> None:
        super().__init__(
            f"source file {file} is missing. Run 'harald-cli build --fetch' to download it,"
            " or place the English dump there."
        )
        self.file = file


class SourceUnreadable(BuildError):
    def __init__(self, file: Path, detail: str) -> None:
        super().__init__(f"cannot read {file}: {detail}")
        self.file = file
        self.detail = detail


class FetchFailed(BuildError):
    def __init__(self, file: str, detail: str) -> None:
        super().__init__(f"fetching {file} failed: {detail}. The previous copy was kept.")
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


class BuildLocked(BuildError):
    def __init__(self, lock: Path) -> None:
        super().__init__(f"another build holds {lock}")
        self.lock = lock


class StagingNotSameFilesystem(BuildError):
    def __init__(self, staging: Path, target: Path) -> None:
        super().__init__(
            f"staging dir {staging} and {target} are on different filesystems, "
            "so the publish could not be an atomic rename. Point staging_dir at the same "
            "filesystem, outside the synced folder."
        )
        self.staging = staging
        self.target = target


class TaskFailed(BuildError):
    def __init__(self, task: str, detail: str) -> None:
        super().__init__(f"task {task} failed: {detail}")
        self.task = task
        self.detail = detail

    def __reduce__(self) -> tuple[type["TaskFailed"], tuple[str, str]]:
        # crosses the process boundary inside a Result; the default would re-call __init__ wrongly
        return (TaskFailed, (self.task, self.detail))
