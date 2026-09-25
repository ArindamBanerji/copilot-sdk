"""Exercise preseed transport over real loopback HTTP, without scorer doubles."""
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread

import pytest

from scripts.preseed_all_copilots import ApiError, api_get, api_post


@pytest.fixture
def server() -> Iterator[tuple[str, list[str]]]:
    calls: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def respond(self) -> None:
            calls.append(self.path)
            if self.command == "POST":
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
            status = 423 if self.path == "/blocked" else 200
            body = b"not json" if self.path == "/invalid" else json.dumps({
                "points": ["measured data"] * 20000,
                "blocked": status == 423,
            }).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        do_GET = respond
        do_POST = respond

        def log_message(self, format: str, *args: object) -> None:
            pass

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}", calls
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=5)


def test_large_curve_response_consumed_completely(server: tuple[str, list[str]]) -> None:
    base, calls = server
    result = api_get(base, "/curves?limit=20000")
    assert len(result["points"]) == 20000
    assert calls == ["/curves?limit=20000"]


def test_failed_write_is_not_retried(server: tuple[str, list[str]]) -> None:
    base, calls = server
    with pytest.raises(ApiError, match="HTTP 423"):
        api_post(base, "/blocked", {"decision_id": "one"})
    assert calls == ["/blocked"]


def test_invalid_json_is_explicit_error(server: tuple[str, list[str]]) -> None:
    with pytest.raises(ApiError, match="invalid JSON"):
        api_get(server[0], "/invalid")


def test_transport_rejects_non_http_urls() -> None:
    with pytest.raises(ApiError, match="http or https"):
        api_get("file:///tmp", "/unexpected")
