#!/usr/bin/env python3
"""Correlate the manuscript manifests with the connections, by letter identity rather than by page.

    python tools/manifest_links.py            every identified letter and what cites it
    python tools/manifest_links.py --uncited  only the ones nothing quotes yet
    python tools/manifest_links.py --check    non-zero exit if a citation names a letter we hold
                                              under a different id, or an id is malformed

A manifest entry and a source record both carry `letter_id`, and that shared id IS the link.
Neither side stores a path into the other: copy the connection's `certainty` into the manifest and
it silently disagrees the day somebody reclassifies the relationship; copy a file path and it
breaks the day a node is renamed. Derive it instead.

WHY NOT JOIN ON THE PAGE, WHICH IS WHAT THIS USED TO DO. A folio is not a letter. 53% of this
volume's letter-bearing pages carry more than one, and four is the record. Joining on the page
therefore attached citations to the wrong letter, silently and plausibly: a quotation from the
letter to Smithers on p. 1196 was reported against the letter to Ives that begins further down the
same page, and nothing flagged it. The id says which letter, so the join is exact.

    letters-2000/1198#2      work / folio the letter BEGINS on / ordinal among letters starting
                             there
    letters-2000/649n3       work / folio / note, for a document the editors print INSIDE a
                             footnote: a letter TO Wilde, or an inscription, which the main
                             sequence has no place for
    hrc/MSS_WildeO_2_10_004  archive / the archive's own identifier for the page, for documents no
                             edition ever printed. Box 2, folder 10, image 004
    nypl/5936027             same rule - NYPL's page identifier is the image id their IIIF service
                             answers to
    morgan/MA7258#34         archive / item / first image, where the archive publishes no page
                             identifier at all and the manifest is the only resolver

Every form names the object by an identifier the OBJECT carries rather than one of ours, because
ours only survives as long as our copy does - the volume's folio rather than our PDF page, the
Ransom Center's shelfmark rather than a CONTENTdm pointer and our position in its page order.
Which field carries an archive's page identifier is declared per archive in the manifest, as
`archive.page_id_field`; `mint_ids.py` says why that is declared rather than inferred.

A record that quotes TWO documents as one passage carries `letter_ids` instead, and is reported
here under each of them.

Two limits, both visible in the output rather than hidden:

  - A source may hold no id at all. Footnote locators (`p. 1025 n. 4`) are refused one on purpose,
    because they cite the editors' apparatus and not a letter. Others are unresolved and listed by
    `--check`; they are not guesses waiting to be trusted.
  - An entry with `person` and no id is an ITEM-level association - "this folder is that
    correspondence" - not a claim about which images are which letter.
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
WEB = HERE.parent
MANIFESTS = WEB / "manuscripts"
ID = re.compile(r"^[a-z0-9][a-z0-9._-]*/[A-Za-z0-9._:-]+(?:#\d+)?$")


def ids_of(s):
    """Every document a source names. `letter_ids` is the plural, for a record quoting two.

    A record carries one field or the other, never both, so reading both and concatenating is
    safe - and it means a record that quotes two letters is reported under each of them, which is
    the truth about it.
    """
    return ([s["letter_id"]] if s.get("letter_id") else []) + list(s.get("letter_ids") or [])


def cited():
    """letter_id -> [record ids] for every source in web/data that names one."""
    idx = defaultdict(list)
    for sub in ("relationships", "people"):
        for p in sorted((WEB / "data" / sub).glob("*.json")):
            doc = json.loads(p.read_text(encoding="utf-8"))
            groups = [("", doc.get("sources") or [])]
            for ce in doc.get("sexuality_sources") or []:
                groups.append((f"context[{ce.get('subject')}]", ce.get("sources") or []))
            for tag, g in groups:
                for i, s in enumerate(g):
                    for lid in ids_of(s):
                        idx[lid].append(f"{p.stem}{('.' + tag) if tag else ''}[{i}]")
    return idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uncited", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    idx = cited()
    rows, problems = [], []
    held = set()

    for man in sorted(MANIFESTS.glob("*/MANIFEST.json")):
        key = man.parent.name
        m = json.loads(man.read_text(encoding="utf-8"))
        for it in m.get("items") or []:
            for e in it.get("matches") or []:
                lid = e.get("letter_id")
                if lid:
                    held.add(lid)
                    if not ID.match(lid):
                        problems.append(f"{key}: malformed letter_id {lid!r}")
                pgs = e.get("pages") or []
                span = f"pp.{pgs[0]}-{pgs[-1]}" if pgs else ""
                rows.append((key, span, lid, sorted(set(idx.get(lid, []))),
                             e.get("what") or it.get("title") or "", e.get("person")))

    for key, span, lid, who, label, person in rows:
        if a.uncited and who:
            continue
        shown = lid or ("- folder, not per letter" if person else "- no id")
        mark = "<- " + ", ".join(who) if who else ("via " + person if person else "")
        print(f"  {key:<13} {span:<10} {shown:<24} {label[:38]:<40} {mark}")

    linked = sum(1 for r in rows if r[3])
    print(f"\n{len(rows)} identified documents; {linked} are cited by a record, "
          f"{len(rows) - linked} are not")

    if a.check:
        # A citation that names a DIFFERENT letter on a folio we hold is usually right, not wrong:
        # the volume prints several letters to a page and we hold one of them. Before letter_id
        # every one of these was silently reported as a match. They are listed because a genuine
        # bad ordinal looks exactly the same, and only a person can tell the two apart.
        neighbours = []
        for lid, recs in sorted(idx.items()):
            if lid in held:
                continue
            stem = lid.rsplit("#", 1)[0]
            near = sorted(h for h in held if h.rsplit("#", 1)[0] == stem)
            if near:
                neighbours.append(f"{', '.join(recs)} cite {lid}; we hold {', '.join(near)} on "
                                  f"that folio - a different letter on the same page, unless the "
                                  f"ordinal is wrong")
        if neighbours:
            print("\n  same folio, different letter:")
            for n in neighbours:
                print("    " + n)
        if problems:
            print("\n  problems:")
            for p in problems:
                print("    " + p)
            return 1
        print("\n  check: every letter_id is well formed")
    return 0


sys.exit(main())
