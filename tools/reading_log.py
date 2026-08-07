"""READING_LOG.md — a durable record of every page read at the page, and what was on it.

Why this exists: quotes that got USED are in data/ with provenance. Quotes read and passed over
were living only in the working conversation, which is disposable. When someone verifies the map
node by node he needs to know what else was on a page, not only what was taken from it - and the
next sweep session needs to know a page is genuinely done rather than merely cited once.

  python tools/reading_log.py --sync     refresh the 'pages cited in data/' table from data/
  python tools/reading_log.py --add 1054 "printed 1006" "notes..."   append a page entry
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent.parent
LOG = HERE / "READING_LOG.md"

HEADER = """# Reading log — pages read at the page

Every PDF page that has been opened as a rendered image, what was on it, and what was taken
from it. **A page is only "done" when everything on it has been triaged, not when one quote has been
lifted from it.**

Kept because quotes that were *used* live in `data/` with provenance, but quotes read and passed
over used to live only in a working conversation. This file is the durable half.

Conventions:
- **printed folio** is always confirmed on the rendered image; the OCR mirror's attribution drifts.
- **also on this page** lists every other letter or note on the folio, whether or not it was used —
  that is the column that catches the next Conder.
- `→ node` means the material was written to that node.

---

"""


def cited_pages():
    """Pages named in a provenance string somewhere in data/, with the nodes that cite them."""
    out = {}
    for f in HERE.rglob("data/**/*.json"):
        if f.name == "circle.json":
            continue
        blob = f.read_text(encoding="utf-8")
        for m in re.finditer(r"\bPDF pages?\s+(\d+)(?:\s*[-–]\s*(\d+))?", blob):
            a = int(m.group(1))
            b = int(m.group(2)) if m.group(2) else a
            for pg in range(a, b + 1):
                out.setdefault(pg, set()).add(f.stem)
    return out


def sync():
    cited = cited_pages()
    body = LOG.read_text(encoding="utf-8") if LOG.exists() else HEADER
    body = body.split("<!-- CITED-TABLE -->")[0].rstrip()
    rows = ["", "<!-- CITED-TABLE -->", "", "## Pages cited in `data/` (auto-synced)", "",
            f"{len(cited)} distinct PDF pages are cited by at least one node. This table is "
            "generated; the narrative entries above it are written by hand and are the useful part.",
            "", "| PDF p. | cited by |", "|---|---|"]
    for pg in sorted(cited):
        rows.append(f"| {pg} | {', '.join(sorted(cited[pg]))} |")
    LOG.write_text(body + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    print(f"READING_LOG.md synced: {len(cited)} cited pages")


def add(pdf, folio, notes):
    body = LOG.read_text(encoding="utf-8") if LOG.exists() else HEADER
    head, _, tail = body.partition("<!-- CITED-TABLE -->")
    entry = f"- **PDF {pdf}** = {folio} — {notes}\n"
    LOG.write_text(head.rstrip() + "\n" + entry +
                   ("\n<!-- CITED-TABLE -->" + tail if tail else "\n"), encoding="utf-8")
    print(f"logged PDF {pdf}")


if __name__ == "__main__":
    if "--sync" in sys.argv:
        sync()
    elif "--add" in sys.argv:
        i = sys.argv.index("--add")
        add(sys.argv[i + 1], sys.argv[i + 2], sys.argv[i + 3])
    else:
        print(__doc__)
