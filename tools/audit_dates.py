"""Find sources whose context states a SPAN but whose evidence_date is a single point.

Now that a date can hold a range, the mismatches are worth hunting rather than waiting to be
spotted: a card reading "c. 1890" over a note that says "c. 1889-90" is the map disagreeing with
itself in the same square inch.

This only reports. Every hit still has to be read, because a date in a context note very often
belongs to something else - a different letter, a death, the subject of a footnote - and only the
date of the thing actually quoted belongs in evidence_date.
"""
import json
import re
from pathlib import Path

CIRCLE = Path(r"C:\Users\Lovelle\Documents\GitHub\raffles-and-bunny-screenplay"
              r"\docs\research\queer-history\victorian\wilde\circle")
M = ("January|February|March|April|May|June|July|August|September|October|November|December")
DASH = r"[-\u2013\u2014]"

PATTERNS = [
    # 1889-90 / 1889–1890
    (re.compile(rf"\b(1[89]\d\d)\s*{DASH}\s*((?:1[89])?\d\d)\b"), "year span"),
    # May–June 1892
    (re.compile(rf"\b({M})\s*{DASH}\s*({M})\s+(1[89]\d\d)\b"), "month span in one year"),
    # May 1892 – June 1893
    (re.compile(rf"\b({M})\s+(1[89]\d\d)\s*{DASH}\s*({M})\s+(1[89]\d\d)\b"), "month span across years"),
]

rows = []
for fn in sorted((CIRCLE / "data/relationships").glob("*.json")):
    d = json.loads(fn.read_text(encoding="utf-8"))
    for i, q in enumerate(d.get("sources") or []):
        ed = q.get("evidence_date") or {}
        if ed.get("y") is None or ed.get("to"):
            continue                                   # undated, or already a range
        blob = " ".join(str(q.get(k) or "") for k in ("context", "supports"))
        for pat, kind in PATTERNS:
            m = pat.search(blob)
            if not m:
                continue
            years = [int(g) for g in m.groups() if g and g.isdigit() and len(g) == 4]
            # only interesting if the span actually touches the date we display
            if ed["y"] in years or any(abs(ed["y"] - y) <= 1 for y in years):
                rows.append((fn.stem, i, kind, m.group(0), ed, blob[:150]))
            break

print(f"{len(rows)} single-point dates whose context states a span nearby:\n")
for f, i, kind, got, ed, ctx in rows:
    print(f"  {f} #{i}  [{kind}]")
    print(f"      shows : {json.dumps(ed, ensure_ascii=False)}")
    print(f"      context says: {got!r}")
    print(f"      {ctx}")
    print()
