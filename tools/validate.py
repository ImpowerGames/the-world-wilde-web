#!/usr/bin/env python3
"""Validate the corpus and build the bundle the site loads.

The per-entity files under data/people and data/relationships are the source of truth: one file
per person, one per connection, so contributors get small diffs and few merge conflicts. This
script checks them against the house rules and writes data/circle.json, which is what the browser
actually fetches.

    python tools/validate.py              validate, then write data/circle.json
    python tools/validate.py --check      validate only, write nothing (use this in CI)
    python tools/validate.py --stats      validate, print a dashboard, write nothing
    python tools/validate.py --ledger     regenerate audits/QUOTE-AUDIT_circle.md
    python tools/validate.py --allow-dirty   let needs-fix / rejected quotes through

Exit code is non-zero when validation fails, so it can gate a pull request.
UTF-8 without BOM throughout.
"""
import argparse
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

CERTAINTY = {"self-reported", "second-hand", "uncorroborated", "marriage", "desire-expressed"}
OUTCOMES = {"declined", "unknown", "unreciprocated"}
CERTAINTY_STATUS = {"proposed", "confirmed"}
VERIFICATION = {"verified-exact", "verified-elision", "needs-fix", "rejected", "unverified"}
HOW = {"pdf-at-page", "repo-file", "archive-org", "web", "unverified"}
LOCATOR_TYPES = {"page", "diary-entry", "trial-day", "letter-date", "none"}
GROUPS = {"core", "family", "society", "aesthete", "trials", "chaeronea",
          "later", "liaisons", "beyond"}
GENDERS = {"m", "f", None}
VOICES = {"period", "modern", None}


def load(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"__load_error__": f"{p.name}: {e}"}


def check_date(d, where, errors):
    if d is None:
        return
    if not isinstance(d, dict):
        errors.append(f"{where}: date must be an object or null")
        return
    bad = {k for k in ("year", "month", "day") if k in d}
    if bad:
        errors.append(f"{where}: date uses {sorted(bad)}; the fields are y/m/d "
                      f"- such a date silently displays as 'date unknown'")
        return
    y = d.get("y")
    if y is not None and not (1700 < y < 2000):
        errors.append(f"{where}: implausible year {y}")


def validate_quote(q, where, works, errors):
    v = q.get("verification")
    if v not in VERIFICATION:
        errors.append(f"{where}: bad verification {v!r}")
    if q.get("how_verified") not in HOW:
        errors.append(f"{where}: bad how_verified {q.get('how_verified')!r}")
    if q.get("locator_type", "page") not in LOCATOR_TYPES:
        errors.append(f"{where}: bad locator_type")
    if q.get("voice") not in VOICES:
        errors.append(f"{where}: bad voice {q.get('voice')!r} (period / modern)")
    if (q.get("quote") or "").strip() and q.get("voice") is None:
        errors.append(f"{where}: a quote must say whose voice it is (period / modern)")
    if v in {"verified-exact", "verified-elision"} and not (q.get("provenance") or "").strip():
        errors.append(f"{where}: verified quote with empty provenance")
    if (q.get("quote") or "") == "" and v not in {None, "unverified"}:
        errors.append(f"{where}: pointer (empty quote) must be unverified")
    wk = q.get("work")
    if wk and wk not in works:
        errors.append(f"{where}: unknown work key {wk!r} (add it to data/works.json)")
    d = q.get("evidence_date")
    check_date(d, f"{where}.evidence_date", errors)
    if d and (d.get("y") or 0) > 1945:
        errors.append(f"{where}: evidence_date {d.get('y')} looks like a publication year. "
                      f"It should be the date of the thing evidenced - see works.json "
                      f"_evidence_date_note")


def validate(works, people, rels):
    errors, warnings = [], []
    pids = set()
    for p in people:
        if "__load_error__" in p:
            errors.append(p["__load_error__"]); continue
        pid = p.get("id", "?")
        if pid in pids:
            errors.append(f"duplicate person id {pid}")
        pids.add(pid)
        if not p.get("name"):
            errors.append(f"{pid}: missing name")
        if p.get("group") not in GROUPS:
            errors.append(f"{pid}: bad group {p.get('group')!r} (one of {sorted(GROUPS)})")
        if p.get("gender") not in GENDERS:
            errors.append(f"{pid}: bad gender {p.get('gender')!r} (m / f / null)")
        check_date(p.get("born"), f"{pid}.born", errors)
        check_date(p.get("died"), f"{pid}.died", errors)
        for ce in p.get("context_engagements", []) or []:
            if not (ce.get("partner_name") or "").strip():
                errors.append(f"{pid}: context_engagement missing partner_name")
            if "name" in ce:
                errors.append(f"{pid}: context_engagement uses 'name'; the field is 'partner_name'")
            for q in ce.get("sources", []) or []:
                validate_quote(q, f"{pid}.context[{ce.get('partner_name')}]", works, errors)

    rids = set()
    for r in rels:
        if "__load_error__" in r:
            errors.append(r["__load_error__"]); continue
        rid = r.get("id", "?")
        if rid in rids:
            errors.append(f"duplicate relationship id {rid}")
        rids.add(rid)
        ppl = r.get("people", [])
        if len(ppl) != 2 or sorted(ppl) != ppl:
            errors.append(f"{rid}: people must be exactly 2 ids in sorted order")
        if rid != "--".join(ppl):
            errors.append(f"{rid}: id must be the two ids joined by '--'")
        for pid in ppl:
            if pid not in pids:
                errors.append(f"{rid}: unknown person {pid!r}")
        if r.get("certainty") not in CERTAINTY:
            errors.append(f"{rid}: bad certainty {r.get('certainty')!r}")
        if r.get("certainty_status") not in CERTAINTY_STATUS:
            errors.append(f"{rid}: bad certainty_status")
        if r.get("certainty") == "uncorroborated" and not r.get("disputed"):
            errors.append(f"{rid}: uncorroborated requires a disputed block")
        if r.get("certainty") == "desire-expressed":
            if r.get("direction") not in ppl:
                errors.append(f"{rid}: desire-expressed requires direction = one of {ppl}")
            if r.get("outcome") not in OUTCOMES:
                errors.append(f"{rid}: desire-expressed requires outcome in {sorted(OUTCOMES)}")
        else:
            if r.get("direction") is not None and r.get("direction") not in ppl:
                errors.append(f"{rid}: direction must name one of {ppl}")
            if r.get("outcome") is not None:
                errors.append(f"{rid}: outcome is only for desire-expressed")
        check_date(r.get("start"), f"{rid}.start", errors)
        check_date(r.get("end"), f"{rid}.end", errors)
        s, e = r.get("start") or {}, r.get("end") or {}
        if s.get("y") and e.get("y") and s["y"] > e["y"]:
            errors.append(f"{rid}: start after end")
        if not r.get("sources"):
            warnings.append(f"{rid}: no sources at all")
        for q in r.get("sources", []) or []:
            validate_quote(q, rid, works, errors)

    orphans = pids - {p for r in rels if "__load_error__" not in r for p in r.get("people", [])}
    for o in sorted(orphans):
        warnings.append(f"{o}: on the roster but in no relationship")
    return errors, warnings


def dashboard(people, rels):
    vq, voice, pointers = Counter(), Counter(), 0
    for r in rels:
        for q in r.get("sources", []) or []:
            vq[q.get("verification", "unverified")] += 1
            if (q.get("quote") or "").strip():
                voice[q.get("voice")] += 1
            else:
                pointers += 1
    return "\n".join([
        f"people: {len(people)}",
        f"relationships: {len(rels)}  {dict(Counter(r.get('certainty') for r in rels))}",
        f"quotes: {sum(vq.values())}  {dict(vq)}  pointers: {pointers}",
        f"voice: {dict(voice)}",
    ]), vq


def write_ledger(works, rels):
    out = ROOT / "audits" / "QUOTE-AUDIT_circle.md"
    out.parent.mkdir(exist_ok=True)
    lines = ["# Quote audit — Wilde Circle", "",
             "Legend: ✓ verified exact · ✓* verified, honest elision · ! needs a wording fix · "
             "✗ error/rejected · ⧖ not yet audited", "",
             "Generated by `tools/validate.py --ledger`. The Status column is the HUMAN verdict and "
             "always starts ⧖; the Agent column records what the research pass did. Record a verdict "
             "here, mirror it into the JSON, rebuild.", ""]
    mark = {"verified-exact": "✓ at page", "verified-elision": "✓* at page",
            "unverified": "⧖", "needs-fix": "!", "rejected": "✗"}
    for r in sorted(rels, key=lambda x: x.get("id", "")):
        lines += [f"## {r['id']}  ·  {r.get('certainty')}", "",
                  "| Quote (opening) | Source | Agent | Status | Note |", "|---|---|---|---|---|"]
        for q in r.get("sources", []) or []:
            first = (q.get("quote") or "").replace("\n", " ")[:60]
            first = first + " …" if first else "[POINTER] " + (q.get("supports") or "")[:60]
            wk = works.get(q.get("work") or "", {})
            src = f"{wk.get('short_cite', q.get('work') or '—')}" \
                  f"{', ' + q['locator'] if q.get('locator') else ''}"
            lines.append(f"| {first} | {src} | {mark.get(q.get('verification'), '?')} | ⧖ | |")
        lines.append("")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"ledger written: {out.relative_to(ROOT)} ({len(rels)} sections)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="validate only, write nothing")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--ledger", action="store_true")
    ap.add_argument("--allow-dirty", action="store_true")
    args = ap.parse_args()

    works = json.loads((DATA / "works.json").read_text(encoding="utf-8"))
    people = [load(p) for p in sorted((DATA / "people").glob("*.json"))]
    rels = [load(p) for p in sorted((DATA / "relationships").glob("*.json"))]

    errors, warnings = validate(works, people, rels)
    dash, vq = dashboard([p for p in people if "__load_error__" not in p],
                         [r for r in rels if "__load_error__" not in r])
    print(dash)
    for w in warnings:
        print(f"  warn: {w}")
    if errors:
        print(f"\n{len(errors)} VALIDATION ERROR(S):")
        for e in errors:
            print(f"  ERROR: {e}")
        sys.exit(1)
    dirty = vq.get("needs-fix", 0) + vq.get("rejected", 0)
    if dirty and not args.allow_dirty:
        sys.exit(f"{dirty} needs-fix/rejected quotes — resolve them or pass --allow-dirty")

    if args.ledger:
        write_ledger(works, [r for r in rels if "__load_error__" not in r])
    if args.check or args.stats:
        print("\nvalidation passed" if not args.ledger else "")
        return

    # portraits are optional: the map works without them, and most of these people have none
    cred = ROOT / "portraits" / "credits.json"
    portraits = {}
    if cred.exists():
        for pid, c in json.loads(cred.read_text(encoding="utf-8")).items():
            if (ROOT / c["file"]).exists():
                portraits[pid] = c
    bundle = {"people": [p for p in people if "__load_error__" not in p],
              "relationships": [r for r in rels if "__load_error__" not in r],
              "works": works, "portraits": portraits, "built": date.today().isoformat()}
    out = DATA / "circle.json"
    out.write_text(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")) + "\n",
                   encoding="utf-8")
    print(f"\nwrote {out.relative_to(ROOT)} ({out.stat().st_size/1024:.0f} KB) — "
          f"generated, do not hand-edit")


main()
