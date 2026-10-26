import gzip
import zlib
from collections.abc import Iterator
from pathlib import Path

from harald.build.errors import SourceUnreadable

# Prefilter on the serialisation kaikki uses; the minimum-entries guard catches drift.
NEEDLE = b'"lang_code": "de"'


def read_german_lines(path: Path) -> Iterator[bytes]:
    try:
        with gzip.open(path, "rb") as f:
            for line in f:
                if NEEDLE in line:
                    yield line
    except (OSError, EOFError, zlib.error) as e:
        raise SourceUnreadable(path, str(e)) from e
