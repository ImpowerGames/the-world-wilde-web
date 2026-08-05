"""Run the exchange splitter over every exchange quotation and print the result for review.

The splitter is a heuristic over two printing conventions, and a heuristic on a corpus this small
should be read rather than trusted. It calls parseExchange directly through window.circle, so each
result is tied to its own source - an earlier version scraped the rendered cards and matched them
by position, which is wrong, because a relationship page renders its sources in DATE order.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

CIRCLE = Path(r"C:\Users\Lovelle\Documents\GitHub\raffles-and-bunny-screenplay"
              r"\docs\research\queer-history\victorian\wilde\circle")

jobs = []
for p in sorted((CIRCLE / "data/relationships").glob("*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    for i, q in enumerate(d.get("sources") or []):
        if q.get("voice") == "exchange":
            jobs.append((f"{p.stem}#{i}", q))
for p in sorted((CIRCLE / "data/people").glob("*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    for ci, ce in enumerate(d.get("context_engagements") or []):
        for i, q in enumerate(ce.get("sources") or []):
            if q.get("voice") == "exchange":
                jobs.append((f"{p.stem}/ce{ci}#{i}", q))

out, review = {}, []
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page()
    pg.goto("http://localhost:8000/", wait_until="load")
    pg.wait_for_timeout(2500)
    for key, q in jobs:
        turns = pg.evaluate("q=>window.circle.parseExchange(q)",
                            {"quote": q.get("quote"), "speaker": q.get("speaker"),
                             "addressee": q.get("addressee")})
        out[key] = turns
        review.append(f"### {key}")
        review.append(f"    speaker={q.get('speaker')!r}   addressee={q.get('addressee')!r}")
        if not turns:
            review.append("    !! DID NOT PARSE")
            review.append(f"    {q.get('quote')}")
        else:
            for t in turns:
                review.append(f"    {(t['who'] or '(none)'):<18}| {t['text']}")
        review.append("")
    b.close()

Path("turns.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
Path("turns_review.txt").write_text("\n".join(review), encoding="utf-8")
print(f"{len(out)} transcripts; {sum(1 for v in out.values() if not v)} did not parse")
