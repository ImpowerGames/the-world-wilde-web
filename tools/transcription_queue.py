#!/usr/bin/env python3
"""Write the transcription checklist from the manifests, so it cannot drift from the holdings.

    python tools/transcription_queue.py            print the tally
    python tools/transcription_queue.py --write    rewrite research-notes/TRANSCRIPTION_QUEUE.md

Nothing here is hand-maintained. A box is ticked because a transcription with that `letter_id`
exists, not because somebody remembered to tick it, and a document appears because a manifest
says we hold it. Add a manifest entry and it joins the queue; write the transcription and it
ticks itself.

THE ORDER IS THE POINT. A transcription of an autograph nobody has printed is the only text of
that document anywhere. A transcription of an autograph the Complete Letters already print is
worth much less - it collates our reading against Holland and Hart-Davis, which is useful for
the marks their convention flattens, but the words are already published. So:

  1  autograph, unprinted   Wilde's hand and nobody's edition - the 4 in the outgoing folders
  2  autograph, incoming    letters TO Wilde; the volume prints his side only, so these are ours
  3  autograph, printed     Wilde's hand, text already in the volume: a collation
  4  photostat              photographic, so the marks survive the copying
  -  typescript             a typist already flattened the underlining; nothing to recover
  -  third party            20th-century scholarship ABOUT Wilde, a different corpus

Envelopes, catalogue clippings and printed leaves are held and identified but are not documents
to transcribe; they are counted at the foot so the numbers reconcile against the manifests.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WEB = Path(__file__).resolve().parents[1]
MANIFESTS = WEB / "manuscripts"
OUT = WEB.parent / "research-notes/TRANSCRIPTION_QUEUE.md"

# folders of letters written TO Wilde: the volume carries his outgoing side, so nothing prints these
INCOMING = {"2777", "2854", "2898"}
# ...but the direction is a property of the letter, not of the folder it was filed in. The Morgan's
# volume is bound in one item and holds Clegg's letter TO Wilde beside Wilde's four outgoing ones.
TO_WILDE = re.compile(r"\bto (?:Oscar )?Wilde\b", re.I)
# H. Montgomery Hyde, Franklin Rolfe, Reggie Turner and Sherard writing in the 1930s-50s
THIRD_PARTY = {"3286", "3305", "3401", "3411"}

NOT_A_DOCUMENT = re.compile(
    r"^\s*(dealer's catalogue|.*auction catalogue|parke-bernet|sotheby|not correspondence|"
    r"printed leaves|envelope|two envelopes)", re.I)
TYPESCRIPT = re.compile(r"^\s*(typed cop|typed extract|typescript|copy of)", re.I)
PHOTOSTAT = re.compile(r"^\s*photostat", re.I)


def transcribed():
    """Every letter_id that already has a transcription: one file each, so presence is the answer."""
    ids = set()
    for f in sorted(MANIFESTS.glob("*/transcriptions/*.json")):
        e = json.loads(f.read_text(encoding="utf-8"))
        if e.get("letter_id"):
            ids.add(e["letter_id"])
    return ids


def classify(archive, item, what, lid):
    if archive == "marland-blog":
        return "excluded"
    if NOT_A_DOCUMENT.match(what):
        return "not-a-document"
    if TYPESCRIPT.match(what):
        return "typescript"
    if PHOTOSTAT.match(what):
        return "photostat"
    if item in THIRD_PARTY:
        return "third-party"
    if lid.startswith("letters-2000/"):
        return "autograph-printed"
    if item in INCOMING or TO_WILDE.search(what):
        return "autograph-incoming"
    return "autograph-unprinted"


def collect():
    rows = defaultdict(list)
    for man in sorted(MANIFESTS.glob("*/MANIFEST.json")):
        archive = man.parent.name
        doc = json.loads(man.read_text(encoding="utf-8"))
        for it in doc.get("items") or []:
            item = str(it["itemId"])
            for m in it.get("matches") or []:
                what = m.get("what") or it.get("title") or ""
                lid = m.get("letter_id") or ""
                rows[classify(archive, item, what, lid)].append({
                    "archive": archive, "item": item, "pages": m.get("pages") or [],
                    "what": what, "letter_id": lid,
                    "box_folder": it.get("boxFolder") or "",
                })
    return rows


TIERS = [
    ("autograph-unprinted", "Tier 1 — Wilde's hand, no edition prints it",
     "The only text of these anywhere would be ours. They sit in the outgoing folders because "
     "that is where the Ransom Center filed them, not because the volume carries them."),
    ("autograph-incoming", "Tier 2 — letters TO Wilde, no edition prints them",
     "The Complete Letters print Wilde's outgoing side only, so every one of these is unpublished. "
     "The hand is the correspondent's, not Wilde's, which is the one thing that makes them harder: "
     "there is no printed reading to check yours against."),
    ("autograph-printed", "Tier 3 — Wilde's hand, already printed",
     "A transcription here is a collation against Holland and Hart-Davis. Worth doing for the marks "
     "their convention flattens - underline and double underline both become italic - but the words "
     "are already published."),
    ("photostat", "Tier 4 — photostats",
     "A photostat is photographic, so the marks survive the copying and can still be read."),
]
SKIP = [
    ("typescript", "Not worth transcribing — typescripts",
     "Whoever typed these had already read the underlining and dropped it. Nothing in a typescript "
     "can settle emphasis, so a transcription would record the typist rather than the writer."),
    ("third-party", "A different corpus — third-party papers",
     "Hyde, Rolfe, Turner and Sherard corresponding in the 1930s-50s. Autograph and unprinted, so "
     "by the rule above they would rank high; they are held back because they are scholarship "
     "ABOUT Wilde rather than documents of his circle. Promote them if that call is wrong."),
    ("excluded", "Out of scope — the blog facsimiles",
     "Rights are unresolved and largely auction-house photography, and that manifest can never back "
     "a `facsimile` record."),
]


def render(rows, done):
    L = ["# Transcription queue", "",
         "Generated by `web/tools/transcription_queue.py --write`. Do not hand-edit: a box is "
         "ticked because a transcription carries that `letter_id`, and a row exists because a "
         "manifest says we hold the document.", ""]

    total = sum(len(rows[k]) for k, _, _ in TIERS)
    left = sum(1 for k, _, _ in TIERS for r in rows[k] if r["letter_id"] not in done)
    L += [f"**{total - left} of {total} done**, {left} to go.", ""]

    for key, title, why in TIERS:
        rs = sorted(rows[key], key=lambda r: (r["archive"], r["item"], r["pages"][:1]))
        if not rs:
            continue
        n_done = sum(1 for r in rs if r["letter_id"] in done)
        L += [f"## {title}", "", why, "", f"_{n_done} of {len(rs)} done._", ""]
        last = None
        for r in rs:
            head = f"{r['archive']}/{r['item']}"
            if head != last:
                L += ["", f"**`{head}`**" + (f" — {r['box_folder']}" if r["box_folder"] else ""), ""]
                last = head
            box = "x" if r["letter_id"] in done else " "
            pp = ", ".join(str(p) for p in r["pages"][:6]) + ("…" if len(r["pages"]) > 6 else "")
            L.append(f"- [{box}] `{r['letter_id'] or '(no id)'}` — pp. {pp} — {r['what'][:150]}")
        L.append("")

    for key, title, why in SKIP:
        rs = rows[key]
        if not rs:
            continue
        L += [f"## {title}", "", why, "", f"_{len(rs)} documents._", ""]
        by = defaultdict(int)
        for r in rs:
            by[(r["archive"], r["item"], r["box_folder"])] += 1
        for (a, i, bf), n in sorted(by.items()):
            L.append(f"- `{a}/{i}`{f' — {bf}' if bf else ''}: {n}")
        L.append("")

    nd = rows["not-a-document"]
    L += ["## Held but not a document to transcribe", "",
          "Envelopes, catalogue clippings and printed leaves. Listed so the totals reconcile "
          "against the manifests rather than appearing to lose documents.", "",
          f"_{len(nd)} images._", ""]
    return "\n".join(L) + "\n"


def main():
    rows = collect()
    done = transcribed()
    for key, title, _ in TIERS + SKIP:
        rs = rows[key]
        n = sum(1 for r in rs if r["letter_id"] in done)
        print(f"  {key:<20} {len(rs):>4}  ({n} transcribed)")
    print(f"  {'not-a-document':<20} {len(rows['not-a-document']):>4}")
    if "--write" in sys.argv:
        OUT.write_text(render(rows, done), encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(WEB.parent)}")
    else:
        print("\ndry run - pass --write to rewrite the checklist")


main()
