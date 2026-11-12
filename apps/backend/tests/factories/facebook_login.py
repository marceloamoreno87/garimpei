from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread


@dataclass
class FacebookLoginSite:
    authorized: bool = False


@contextmanager
def serve_facebook_login(site: FacebookLoginSite) -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            signed_in = site.authorized or "c_user=123" in self.headers.get("Cookie", "")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            if site.authorized:
                self.send_header("Set-Cookie", "c_user=123; Path=/; Max-Age=3600")
                self.send_header("Set-Cookie", "xs=synthetic-session; Path=/; Max-Age=3600")
            self.end_headers()
            initialize = "localStorage.setItem('identity','123');" if site.authorized else ""
            page = (
                "<!doctype html><html lang='pt-BR'><title>Login de teste local</title>"
                + (
                    "<h1>Marketplace de teste</h1>"
                    if signed_in
                    else "<input name='email'><input name='pass'>"
                )
                + "<script>"
                + initialize
                + "window.require=()=>({USER_ID:localStorage.getItem('identity')});</script></html>"
            )
            self.wfile.write(page.encode())

        def log_message(self, _format: str, *args: object) -> None:
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}"
        finally:
            server.shutdown()
            thread.join()
