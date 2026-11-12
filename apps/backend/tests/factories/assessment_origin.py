from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread


@contextmanager
def serve_assessment_images(
    extra_files: dict[str, Path] | None = None,
) -> Iterator[tuple[str, list[dict[str, str]]]]:
    root = Path(__file__).parents[1] / "fixtures/listing"
    files = {p.name: p for p in (root / "assessment_images").glob("*.png")}
    files.update({p.name: p for p in (root / "media").iterdir() if p.is_file()})
    files.update(extra_files or {})
    requests: list[dict[str, str]] = []

    class CorpusOrigin(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            requests.append(dict(self.headers))
            path = files.get(self.path.removeprefix("/"))
            if path is None:
                self.send_error(404)
                return
            raw = path.read_bytes()
            self.send_response(200)
            self.send_header(
                "Content-Type",
                "image/jpeg"
                if path.suffix == ".jpg"
                else "image/webp"
                if path.suffix == ".webp"
                else "image/png",
            )
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), CorpusOrigin)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
