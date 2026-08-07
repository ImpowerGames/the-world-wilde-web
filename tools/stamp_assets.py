#!/usr/bin/env python3
"""Stamp the stylesheet and script URLs with a hash of their contents.

    python tools/stamp_assets.py _site

GitHub Pages serves assets with `Cache-Control: max-age=600`, so for ten minutes after a deploy a
returning reader can be handed yesterday's stylesheet against today's markup - which looks like a
broken site, not a stale one. A URL that changes when the bytes change ends that: the browser has
no cached copy of `circle.css?v=9f2a1c04` until this build exists, so it must fetch it, and when
nothing changed the URL is identical and the cached copy is still used.

Run against the STAGED copy, never the working tree. index.html in the repository stays clean, so
the file a contributor opens has plain unversioned paths and diffs do not churn on every build.
"""
import hashlib
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
# href="assets/css/circle.css" / src="assets/js/circle.js", with or without a stamp already on it.
REF = re.compile(r'((?:href|src)=")((?:assets|content)/[^"?]+\.(?:css|js))(?:\?v=[0-9a-f]+)?(")')


def main(root):
    root = Path(root)
    page = root / "index.html"
    if not page.exists():
        sys.exit(f"No index.html under {root}")
    html = page.read_text(encoding="utf-8")
    stamped = []

    def repl(m):
        target = root / m.group(2)
        if not target.exists():
            # A reference to a file that is not there is a real problem, but it is not this
            # script's to fix - leave it exactly as written so it fails visibly.
            return m.group(0)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()[:8]
        stamped.append(f"{m.group(2)}?v={digest}")
        return f"{m.group(1)}{m.group(2)}?v={digest}{m.group(3)}"

    out = REF.sub(repl, html)
    if out != html:
        page.write_text(out, encoding="utf-8")
    for s in stamped:
        print(f"  {s}")
    print(f"  {len(stamped)} asset reference(s) stamped")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "_site"))
