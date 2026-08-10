"""Find quotes that render TWICE on the same person's panel.

A person's panel aggregates three streams:
  1. quotes on their own sexuality_sources
  2. quotes on every relationship they are a party to
  3. quotes on OTHER people's sexuality_sources naming them as subject (the two-ended rendering)

If the same excerpt reaches one panel by two routes it is printed twice.

Duplicate key is (work, locator, normalised quote text) — the same excerpt of the same source.
Different excerpts of the same letter are NOT duplicates; a letter can legitimately evidence several
distinct claims.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent.parent


def norm(q):
    return re.sub(r"\W+", " ", (q or "")).strip().lower()


def main():
    C = json.loads((HERE / "data/web.json").read_text(encoding="utf-8"))
    people = {p["id"]: p for p in C["people"]}
    name_to_id = {}
    for p in C["people"]:
        name_to_id[p["name"]] = p["id"]
        for a in p.get("aka") or []:
            name_to_id[a] = p["id"]

    # person id -> list of (key, where)
    panel = defaultdict(list)

    for p in C["people"]:
        for ce in p.get("sexuality_sources") or []:
            other = name_to_id.get(ce.get("subject") or "")
            for q in ce.get("sources") or []:
                key = (q.get("work"), q.get("locator"), norm(q.get("quote")))
                panel[p["id"]].append((key, f"own sexuality_source (subject={ce.get('subject')})"))
                if other and other != p["id"]:
                    panel[other].append((key, f"sexuality_source on {p['id']}"))

    for r in C["relationships"]:
        for q in r.get("sources") or []:
            key = (q.get("work"), q.get("locator"), norm(q.get("quote")))
            for pid in r["people"]:
                panel[pid].append((key, f"relationship {r['id']}"))

    bad = 0
    for pid, entries in sorted(panel.items()):
        seen = defaultdict(list)
        for key, where in entries:
            if not key[2]:
                continue
            seen[key].append(where)
        for key, wheres in seen.items():
            if len(wheres) > 1:
                bad += 1
                nm = people[pid]["name"] if pid in people else pid
                print(f"\nDUPLICATE on {nm} ({pid})  —  {key[0]} {key[1]}")
                for w in wheres:
                    print(f"    via {w}")
                print(f"    \"{key[2][:110]}...\"")

    print(f"\n{bad} duplicate quote(s) across {len(panel)} panels.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
