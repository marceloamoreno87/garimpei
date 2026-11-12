#!/usr/bin/env python3
"""Serve the isolated design artifacts locally, without application services."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--port', type=int, default=4173)
args = parser.parse_args()
root = Path(__file__).resolve().parent
handler = partial(SimpleHTTPRequestHandler, directory=str(root))
with ThreadingHTTPServer(('127.0.0.1', args.port), handler) as server:
    print(f'Garimpei · protótipo: http://127.0.0.1:{args.port}/prototypes/', flush=True)
    print('Dados fictícios; estado apenas em memória. Ctrl+C para encerrar.', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
