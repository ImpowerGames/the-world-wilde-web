#!/usr/bin/env python3
"""Serve the site locally.

    python tools/serve.py            http://localhost:8000
    python tools/serve.py 8080       a different port
    python tools/serve.py --no-open  do not pop a browser tab (for a headless browser,
                                     which attaches to the port itself)

The browser will not fetch data/circle.json from a file:// page, so opening index.html by
double-clicking shows an empty map. Run this instead.

Rebuilds the bundle first, so what you see reflects the JSON you just edited. Files are served
with no-cache headers, so a plain reload picks up changes.
"""
import http.server
import functools
import socketserver
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARGS = [a for a in sys.argv[1:] if a != "--no-open"]
OPEN_BROWSER = "--no-open" not in sys.argv[1:]
PORT = int(ARGS[0]) if ARGS else 8000


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    # One tidy line per request. These are split out rather than filtered inside log_message,
    # because log_error passes a format string and an HTTPStatus - not the request line - and
    # anything that assumes the shape of log_message's arguments crashes the moment a 404 or a
    # broken pipe goes through it.
    def log_request(self, code="-", size="-"):
        print(f"  {self.path.split('?')[0]}  {int(code) if isinstance(code, int) else code}")

    def log_error(self, *a):
        pass                                 # the status already went out through log_request

    def log_message(self, *a):
        pass


def main():
    print("rebuilding data/circle.json …")
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "validate.py")],
                       cwd=ROOT, capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        sys.exit("\nvalidation failed — fix the errors above, the site was not started")

    handler = functools.partial(Handler, directory=str(ROOT))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        url = f"http://localhost:{PORT}/"
        print(f"\nserving {ROOT.name}/ at {url}   (ctrl-c to stop)\n")
        if OPEN_BROWSER:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


main()
