import json
import socket
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from garimpei.config.env import InferenceSettings
from garimpei.domain.inference.request import MODEL


@dataclass
class OllamaGatewayFake:
    mode: str = "valid"
    calls: list[str] = field(default_factory=list)
    digest: str = "sha256:d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04"
    resident: bool = True

    def respond(self, path: str) -> dict[str, object]:
        self.calls.append(path)
        if path == "/api/version":
            return {"version": "0.40.16"}
        if path == "/api/tags":
            return {"models": [{"name": MODEL, "digest": self.digest}]}
        if path == "/api/show":
            return {"capabilities": ["vision", "completion"]}
        if path == "/api/ps":
            return {
                "models": [{"name": MODEL, "size": 10, "size_vram": 10}] if self.resident else []
            }
        return {
            "done": True,
            "done_reason": "stop",
            "message": {
                "role": "assistant",
                "content": '{"findings":[],"unknowns":["Condição não determinada"],"limitations":[]}',
            },
            "prompt_eval_count": 100,
            "eval_count": 40,
        }


@contextmanager
def serve_inference(fake: OllamaGatewayFake) -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.respond()

        def do_POST(self) -> None:
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            if self.path == "/api/chat" and fake.mode == "disconnect":
                fake.calls.append(self.path)
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
                return
            if self.path == "/api/chat" and fake.mode == "drip":
                self.send_response(200)
                self.send_header("Content-Length", "1000")
                self.end_headers()
                try:
                    for _ in range(30):
                        self.wfile.write(b" ")
                        self.wfile.flush()
                        time.sleep(0.1)
                except (OSError, BrokenPipeError):
                    pass
                return
            self.respond()

        def respond(self) -> None:
            raw = json.dumps(fake.respond(self.path)).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def inference_settings(root: Path, endpoint: str) -> InferenceSettings:
    lock = root / "model-lock.json"
    approved = (
        Path(__file__).resolve().parents[4]
        / "docs/F19-inferencia-multimodal-local-em-docker/model-lock.json"
    )
    metadata = json.loads(approved.read_text())
    metadata["visual_profile"].pop("metrics", None)
    lock.write_text(json.dumps(metadata, separators=(",", ":")))
    return InferenceSettings(
        False, endpoint, root, lock, root / "tokenizer.json", root / "gpu.json", "test-owner"
    )
