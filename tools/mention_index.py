"""Mention index: every person on the map -> every repo PDF page that NAMES them.

Built 2026-08-05 for the completeness protocol. The old workflow read letters by addressee, which
loses everyone who appears inside someone else's letter - that is how Charles Conder was described
twice on pages already read and logged from neither.

For each person this reports:
  TO      pages carrying a 'To <name>' letter heading
  MENTION pages where the name appears in any other position (body, footnote, editors' note)
  READ    pages already read at the page, from 'Repo PDF page(s) N' strings in data/
  OWED    MENTION + TO, minus READ

Surnames that are ordinary English words are matched on full name only and flagged LOOSE=no, so
'Strong', 'Wood', 'Gray', 'Miles' etc. do not swamp the index with false hits.

Usage:
    python tools/mention_index.py                 # whole-map summary, most owed first
    python tools/mention_index.py ross douglas    # detail for named ids
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parents[5]
MIRROR = (ROOT / "docs/research/queer-history/victorian/wilde/sources/_pdf-text-mirror"
          / "Oscar Wilde, Merlin Holland, Rupert Hart-Davis - The Complete Letters of Oscar "
            "Wilde-Fourth Estate (2000).txt")

# surnames that are also ordinary words, or shared by several people in the volume:
# full-name match only, never a bare-surname sweep
COMMON = {"strong", "wood", "gray", "miles", "mason", "parker", "smith", "young", "white", "hunt",
          "ward", "bell", "king", "cook", "green", "hill", "moore", "bright", "small", "field",
          "lee", "day", "long", "marshall", "shannon", "burton", "clifton", "horne", "reid",
          "adey", "gilbert", "harding", "atkins", "scarfe", "conway", "taylor", "turner", "ross",
          "hall", "cooper", "stafford", "walter", "andre", "joseph", "lips", "goddard", "brooks",
          "west", "thomas", "alexander", "bradley", "wilde", "douglas", "boy", "faun", "god",
          "sea", "velvet", "brown", "kit", "amy", "puss", "kitten", "sphinx"}


# bare given names: never swept alone, they are everywhere in a volume of letters
GIVEN = {"john", "henry", "harry", "hank", "kit", "angel", "field", "jim", "jack", "bill", "tom",
         "will", "fred", "george", "charlie", "bobbie", "robbie", "reggie", "bosie", "oscar",
         "maurice", "arthur", "frank", "alfred", "edward", "james", "charles", "william"}


def descriptive(name):
    """True for nodes named by description rather than by a surname - "A 'Sea-God', Naples",
    'A boy in grey velvet, Paris'. Their trailing word is a PLACE, not a surname, and sweeping it
    returns every mention of that city in the volume."""
    if "," in name or name.startswith(("A ", "An ", "The ", "a ", "an ")):
        return True
    words = [w for w in re.split(r"[^A-Za-z]+", name) if w]
    return len(words) < 2 or all(w.lower() in COMMON for w in words)


def fold(s):
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def load():
    text = fold(MIRROR.read_text(encoding="utf-8", errors="replace"))
    marks = [(m.start(), int(m.group(1)))
             for m in re.finditer(r"=== \[PDF p\. (\d+)\] ===", text)]
    return text, marks


def page_of(marks, off):
    lo, hi, ans = 0, len(marks) - 1, None
    while lo <= hi:
        mid = (lo + hi) // 2
        if marks[mid][0] <= off:
            ans = marks[mid][1]
            lo = mid + 1
        else:
            hi = mid - 1
    return ans


def read_pages(circle):
    got = set()
    for f in circle.rglob("data/**/*.json"):
        if f.name == "circle.json":
            continue
        for m in re.finditer(r"Repo PDF pages?\s+(\d+)(?:\s*[-–]\s*(\d+))?",
                             f.read_text(encoding="utf-8")):
            a = int(m.group(1))
            b = int(m.group(2)) if m.group(2) else a
            got.update(range(a, b + 1))
    return got


def patterns_for(p):
    """Full names and aka always; a bare-surname sweep only when the surname is distinctive.

    Descriptive nodes ('The Sea-God') get their exact phrase and nothing else - their component
    words are ordinary English and a bare-word sweep on them is worthless.
    """
    pats, loose = [], False
    for n in [p["name"]] + (p.get("aka") or []):
        n = fold(n).strip()
        if len(n) <= 2 or n.lower() in GIVEN:
            continue          # a bare given name matches half the volume
        # word-boundaried, always: without this 'Hank' matches inside 'thanks'
        pats.append(r"\b" + re.escape(n) + r"\b")
    if not descriptive(p["name"]):
        surname = fold(p["name"].split()[-1]).strip(".")
        if len(surname) > 3 and surname.lower() not in COMMON:
            pats.append(r"\b" + re.escape(surname) + r"\b")
            loose = True
    return re.compile("|".join(pats), re.I) if pats else None, loose


def main():
    circle = HERE
    text, marks = load()
    C = json.loads((circle / "data/circle.json").read_text(encoding="utf-8"))
    already = read_pages(circle)
    head = re.compile(r"^\s*(?:Postcard: |Telegram: )?To\s+", re.M)
    heads = {m.start() for m in head.finditer(text)}

    want = {a.lower() for a in sys.argv[1:]}
    rows = []
    for p in C["people"]:
        rx, loose = patterns_for(p)
        if rx is None:
            continue
        to, mention = set(), set()
        for m in rx.finditer(text):
            pg = page_of(marks, m.start())
            if pg is None:
                continue
            line_start = text.rfind("\n", 0, m.start()) + 1
            (to if line_start in heads else mention).add(pg)
        allp = to | mention
        owed = sorted(allp - already)
        rows.append((len(owed), p["id"], p["name"], sorted(to), sorted(mention), owed, loose))

    rows.sort(reverse=True)
    if want:
        rows = [r for r in rows if r[1].lower() in want]
        for owed_n, pid, name, to, mention, owed, loose in rows:
            print(f"\n=== {name} ({pid}) {'' if loose else '[full-name match only]'}")
            print(f"  letters TO   ({len(to):>3}): {to}")
            print(f"  mentions     ({len(mention):>3}): {mention}")
            print(f"  OWED         ({len(owed):>3}): {owed}")
        return

    print(f"{'owed':>5} {'to':>4} {'ment':>5}  id")
    print("-" * 62)
    tot = 0
    for owed_n, pid, name, to, mention, owed, loose in rows[:40]:
        tot += owed_n
        print(f"{owed_n:>5} {len(to):>4} {len(mention):>5}  {pid}{'' if loose else '  (strict)'}")
    print(f"\n{len(rows)} people indexed; "
          f"{sum(r[0] for r in rows)} person-pages owed across the map "
          f"({len(set().union(*[set(r[5]) for r in rows]) if rows else set())} distinct PDF pages).")


if __name__ == "__main__":
    main()
