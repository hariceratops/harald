import functools
import http.server
import threading
from collections.abc import Iterator
from pathlib import Path

import pytest

from harald.build.errors import FetchFailed
from harald.build.fetch import fetch_all, sidecar_path, source_date
from harald.build.publish import sha256_file
from harald.build.sources import SourceFile

LAST_MODIFIED = "Sat, 03 Oct 2026 10:00:00 GMT"
ETAG = '"v1"'


class _Handler(http.server.SimpleHTTPRequestHandler):
    body = b"payload-one"
    truncate = False
    requests: list[dict[str, str]] = []

    def do_GET(self) -> None:
        self.requests.append({k: v for k, v in self.headers.items()})
        if self.headers.get("If-None-Match") == ETAG:
            self.send_response(304)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("ETag", ETAG)
        self.send_header("Last-Modified", LAST_MODIFIED)
        self.send_header("Content-Length", str(len(self.body) + (5 if self.truncate else 0)))
        self.end_headers()
        self.wfile.write(self.body)

    def log_message(self, *args: object) -> None:
        pass


@pytest.fixture
def server() -> Iterator[tuple[str, type[_Handler]]]:
    handler = type("Handler", (_Handler,), {"requests": [], "body": b"payload-one"})
    httpd = http.server.HTTPServer(("127.0.0.1", 0), functools.partial(handler))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}", handler
    httpd.shutdown()
    httpd.server_close()


def _file(base: str) -> SourceFile:
    return SourceFile("dump.gz", f"{base}/dump.gz", "wiktionary-en")


def test_fetch_keeps_one_copy_with_sidecar_and_date(
    tmp_path: Path, server: tuple[str, type[_Handler]]
) -> None:
    base, _ = server

    res = fetch_all(tmp_path, [_file(base)])

    assert res.unwrap().outcomes[0].downloaded
    assert (tmp_path / "dump.gz").read_bytes() == b"payload-one"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["dump.gz", "dump.gz.meta.json"]
    assert source_date(tmp_path, "dump.gz", sha256_file(tmp_path / "dump.gz")) == "2026-10-03"


def test_second_fetch_is_conditional_and_downloads_nothing(
    tmp_path: Path, server: tuple[str, type[_Handler]]
) -> None:
    base, handler = server
    fetch_all(tmp_path, [_file(base)])

    res = fetch_all(tmp_path, [_file(base)])

    assert not res.unwrap().outcomes[0].downloaded
    assert handler.requests[-1]["If-None-Match"] == ETAG
    assert handler.requests[-1]["If-Modified-Since"] == LAST_MODIFIED


def test_failed_fetch_keeps_previous_copy_and_leaves_no_part_file(
    tmp_path: Path, server: tuple[str, type[_Handler]]
) -> None:
    base, handler = server
    fetch_all(tmp_path, [_file(base)])
    sidecar_path(tmp_path, "dump.gz").unlink()
    handler.body = b"payload-two"
    handler.truncate = True

    res = fetch_all(tmp_path, [_file(base)])

    assert isinstance(res.unwrap_err(), FetchFailed)
    assert (tmp_path / "dump.gz").read_bytes() == b"payload-one"
    assert [p.name for p in tmp_path.iterdir()] == ["dump.gz"]


def test_date_is_unknown_when_sidecar_does_not_match_the_file(
    tmp_path: Path, server: tuple[str, type[_Handler]]
) -> None:
    base, _ = server
    fetch_all(tmp_path, [_file(base)])
    (tmp_path / "dump.gz").write_bytes(b"replaced by hand")

    assert source_date(tmp_path, "dump.gz", sha256_file(tmp_path / "dump.gz")) == "unknown"
    assert source_date(tmp_path, "absent.gz", "x") == "unknown"
