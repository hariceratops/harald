from pathlib import Path


class LearningDbError(Exception):
    pass


class LearningDbTooNew(LearningDbError):
    def __init__(self, found: str, head: str) -> None:
        super().__init__(
            f"learning.db is at revision {found}, which this Harald does not know "
            f"(it knows up to {head}). Update Harald; it never downgrades the database."
        )
        self.found = found
        self.head = head


class NotALearningDb(LearningDbError):
    def __init__(self, path: Path) -> None:
        super().__init__(f"{path} holds tables but is not a Harald learning database")
        self.path = path


class MigrationFailed(LearningDbError):
    def __init__(self, stage: str, detail: str) -> None:
        super().__init__(f"learning.db {stage} failed: {detail}")
        self.stage = stage
        self.detail = detail


class StorageError(LearningDbError):
    def __init__(self, detail: str) -> None:
        super().__init__(f"learning.db write failed: {detail}")
        self.detail = detail


def as_learning_error(err: Exception) -> LearningDbError:
    return err if isinstance(err, LearningDbError) else StorageError(str(err))


class CardNotFound(LearningDbError):
    def __init__(self, card_id: int) -> None:
        super().__init__(f"no card {card_id}")
        self.card_id = card_id
