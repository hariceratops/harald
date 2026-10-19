import gzip
import queue
import threading
import zlib
from collections.abc import Generator
from pathlib import Path

from harald.build.errors import SourceUnreadable

# Prefilter on the serialisation kaikki uses; the minimum-entries guard catches drift.
NEEDLE = b'"lang_code": "de"'
BLOCK_BYTES = 16 << 20
CHUNK_BYTES = 4 << 20
_EOF = object()


def read_german_chunks(path: Path, chunk_bytes: int = CHUNK_BYTES) -> Generator[tuple[int, bytes]]:
    """Yields (seq, chunk) of newline-terminated matching lines, in source order.

    Decompression and the block scan run in two threads (zlib releases the GIL); the
    consumer is the caller's thread. Closing the generator stops both threads.
    """
    stop = threading.Event()
    blocks: queue.Queue[object] = queue.Queue(maxsize=8)
    chunks: queue.Queue[object] = queue.Queue(maxsize=4)
    threads = [
        threading.Thread(target=_decompress, args=(path, blocks, stop), daemon=True),
        threading.Thread(target=_scan, args=(blocks, chunks, chunk_bytes, stop), daemon=True),
    ]
    for t in threads:
        t.start()
    try:
        seq = 0
        while True:
            item = chunks.get()
            if item is _EOF:
                return
            if isinstance(item, SourceUnreadable):
                raise item
            assert isinstance(item, bytes)
            yield seq, item
            seq += 1
    finally:
        stop.set()
        for q in (blocks, chunks):
            _drain(q)
        for t in threads:
            t.join()


def _put(q: queue.Queue[object], item: object, stop: threading.Event) -> bool:
    while not stop.is_set():
        try:
            q.put(item, timeout=0.1)
            return True
        except queue.Full:
            continue
    return False


def _get(q: queue.Queue[object], stop: threading.Event) -> object:
    while not stop.is_set():
        try:
            return q.get(timeout=0.1)
        except queue.Empty:
            continue
    return _EOF


def _drain(q: queue.Queue[object]) -> None:
    while True:
        try:
            q.get_nowait()
        except queue.Empty:
            return


def _decompress(path: Path, out: queue.Queue[object], stop: threading.Event) -> None:
    try:
        with gzip.open(path, "rb") as f:
            while not stop.is_set() and (block := f.read(BLOCK_BYTES)):
                if not _put(out, block, stop):
                    return
    except (OSError, EOFError, zlib.error) as e:
        _put(out, SourceUnreadable(path, str(e)), stop)
        return
    _put(out, _EOF, stop)


def _scan(
    blocks: queue.Queue[object],
    out: queue.Queue[object],
    chunk_bytes: int,
    stop: threading.Event,
) -> None:
    carry = b""
    pending: list[bytes] = []
    size = 0
    while True:
        block = _get(blocks, stop)
        if isinstance(block, SourceUnreadable):
            _put(out, block, stop)
            return
        last = block is _EOF
        if last:
            buf, carry = carry + b"\n" if carry else b"", b""
        else:
            assert isinstance(block, bytes)
            buf = carry + block
            cut = buf.rfind(b"\n") + 1
            buf, carry = buf[:cut], buf[cut:]
        pos = 0
        while (hit := buf.find(NEEDLE, pos)) != -1:
            start = buf.rfind(b"\n", 0, hit) + 1
            end = buf.find(b"\n", hit) + 1
            pending.append(buf[start:end])
            size += end - start
            pos = end
            if size >= chunk_bytes:
                if not _put(out, b"".join(pending), stop):
                    return
                pending, size = [], 0
        if last:
            if pending and not _put(out, b"".join(pending), stop):
                return
            _put(out, _EOF, stop)
            return
