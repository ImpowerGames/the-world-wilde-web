#!/usr/bin/env python3
"""Serve the site locally.

    python tools/serve.py            http://localhost:8000
    python tools/serve.py 8080       a different port
    python tools/serve.py --no-open  do not pop a browser tab (for a headless browser,
                                     which attaches to the port itself)

The browser will not fetch data/web.json from a file:// page, so opening index.html by
double-clicking shows an empty map. Run this instead.

Rebuilds the bundle first, so what you see reflects the JSON you just edited. Files are served
with no-cache headers, so a plain reload picks up changes.
"""
import http.server
import functools
import socket
import socketserver
import subprocess
import sys
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FLAGS = {"--no-open", "--force"}
ARGS = [a for a in sys.argv[1:] if a not in FLAGS]
OPEN_BROWSER = "--no-open" not in sys.argv[1:]
FORCE = "--force" in sys.argv[1:]
PORT = int(ARGS[0]) if ARGS else 8000


def listeners(port):
    """PIDs listening on `port`, with the command that started each."""
    out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True).stdout
    pids = set()
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 5 and "LISTENING" in line and parts[1].endswith(f":{port}"):
            pids.add(parts[-1])
    found = []
    for pid in sorted(pids):
        cmd = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             f"(Get-CimInstance Win32_Process -Filter \"ProcessId={pid}\").CommandLine"],
            capture_output=True, text=True).stdout.strip()
        found.append((pid, cmd or "(command line unavailable)"))
    return found


def free_port(port):
    """Stop whatever is listening, naming each process before killing it.

    Deliberately not automatic. On Windows a second server binds the SAME port without complaint
    and then receives nothing, so 'something is already there' is common and silent - but the
    something might be a service, not a stray dev server, and killing it unasked would be worse
    than the problem.
    """
    procs = listeners(port)
    if not procs:
        print(f"  nothing is listening on {port}")
        return
    for pid, cmd in procs:
        print(f"  killing {pid}  {cmd[:96]}")
        subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True, text=True)


class Handler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        """Never answer 304, so an edit can never be served stale.

        `Cache-Control: no-store` below stops the browser storing a copy, but it does nothing
        about a copy stored BEFORE the header existed, or one a browser holds on to anyway: that
        browser still sends If-Modified-Since, and the stdlib handler answers "not modified" by
        comparing whole seconds of mtime. Edit a file and reload inside the same second - which is
        exactly what editing a stylesheet and hitting refresh looks like - and you get the old one
        back with no way to tell. Dropping the conditional headers makes every request
        unconditional, which is what a dev server should do.
        """
        del self.headers["If-Modified-Since"]
        del self.headers["If-None-Match"]
        return super().send_head()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
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
    print("rebuilding data/web.json …")
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "validate.py")],
                       cwd=ROOT, capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        sys.exit("\nvalidation failed — fix the errors above, the site was not started")

    handler = functools.partial(Handler, directory=str(ROOT))

    class Server(socketserver.TCPServer):
        """Listen on IPv6 AND IPv4, and refuse to share the port.

        `localhost` resolves to ::1 before 127.0.0.1 on Windows, so an IPv4-only server is simply
        not there for a browser typing localhost. Binding IPv6 with V6ONLY off covers both.

        allow_reuse_address is deliberately OFF. On Windows it does not mean "reuse a dead socket",
        it means "bind anyway even though someone else is listening" - so a second serve.py starts
        cleanly, prints its banner, and receives nothing, while the stale process keeps answering.
        That failure is invisible and costs an afternoon. Better to fail loudly with an address-in-
        use error that names the real problem.
        """
        allow_reuse_address = False
        address_family = socket.AF_INET6

        def server_bind(self):
            try:
                self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
            except (AttributeError, OSError):
                pass  # a stack without dual-mode; IPv6 clients still work
            super().server_bind()

    if FORCE:
        free_port(PORT)

    try:
        httpd = Server(("", PORT), handler)
    except OSError as e:
        procs = listeners(PORT)
        detail = "\n".join(f"    {pid}  {cmd[:96]}" for pid, cmd in procs)
        sys.exit(f"\ncould not bind port {PORT}: {e}\n"
                 + (f"\n  already listening:\n{detail}\n" if detail else "")
                 + f"\n  stop it and retry:   python tools/serve.py --force"
                 + f"\n  or by hand:          taskkill /PID <pid> /F\n")
    with httpd:
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
