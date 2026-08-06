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

CERTAINTY = {"self-reported", "second-hand", "uncorroborated", "married", "attraction-expressed"}
OUTCOMES = {"declined", "unknown", "unreciprocated"}
CERTAINTY_STATUS = {"proposed", "confirmed"}
VERIFICATION = {"verified-exact", "verified-elision", "needs-fix", "rejected", "unverified"}
HOW = {"pdf-at-page", "repo-file", "archive-org", "web", "unverified"}
LOCATOR_TYPES = {"page", "diary-entry", "trial-day", "letter-date", "none"}
GROUPS = {"core", "family", "society", "aesthete", "trials", "chaeronea",
          "later", "liaisons", "beyond"}
GENDERS = {"m", "f", None}
# "exchange" is period text with MORE THAN ONE speaker in it - courtroom question and answer,
# where counsel asks and a witness replies. It is not "period", which promises a single voice and
# is set in quotation marks accordingly; putting an exchange there both claimed one voice and let
# the heading attribute counsel's questions to the witness.
VOICES = {"period", "exchange", "modern", None}


def load(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"__load_error__": f"{p.name}: {e}"}


def date_sort_key(d):
    return (d.get("y") or 0, d.get("m") or 0, d.get("d") or 0)


def check_date(d, where, errors, _depth=0):
    if d is None:
        return
    if not isinstance(d, dict):
        errors.append(f"{where}: date must be an object or null")
        return
    # A date may be a RANGE: `to` holds the far end, and the display is derived from the two so
    # every range on the map reads the same way. `label` is the escape hatch for things a date
    # object genuinely cannot say, and it OVERRIDES the display - so having both is ambiguous
    # about which one the reader would see, and is refused.
    if "to" in d:
        if _depth:
            errors.append(f"{where}: a date range cannot itself have a `to`")
        elif d.get("label"):
            errors.append(f"{where}: has both `to` and `label` - `label` would win and the range "
                          f"would never be shown; keep one")
        else:
            check_date(d["to"], f"{where}.to", errors, _depth + 1)
            if isinstance(d["to"], dict) and d["to"].get("y") is not None:
                if date_sort_key(d["to"]) < date_sort_key(d):
                    errors.append(f"{where}: date range ends before it starts")
                if d.get("y") is None:
                    errors.append(f"{where}: a date range needs a start year")
    bad = {k for k in ("year", "month", "day") if k in d}
    if bad:
        errors.append(f"{where}: date uses {sorted(bad)}; the fields are y/m/d "
                      f"- such a date silently displays as 'date unknown'")
        return
    y = d.get("y")
    if y is not None and not (1700 < y < 2000):
        errors.append(f"{where}: implausible year {y}")


def check_order_hint(q, where, errors):
    """`order_hint` places a source in the reading order when its date is genuinely unknown.

    It exists so that nobody is tempted to invent an `evidence_date` to get the sequence right.
    evidence_date means "the date of the thing evidenced" and is a claim about the world;
    order_hint means "we do not know, and this is where it reads best", and must say why.
    """
    h = q.get("order_hint")
    if h is None:
        return
    if not isinstance(h, dict):
        errors.append(f"{where}: order_hint must be an object")
        return
    if q.get("evidence_date"):
        errors.append(f"{where}: has BOTH evidence_date and order_hint - if the date is known, "
                      f"drop the hint; if it is not, drop the date")
    check_date({k: v for k, v in h.items() if k != "why"}, f"{where}.order_hint", errors)
    if not (h.get("why") or "").strip():
        errors.append(f"{where}: order_hint needs a `why` saying what it rests on - an undated "
                      f"placement without its reasoning is an invented date in disguise")


def check_speaker_addressee(q, where, works, errors):
    """Nobody writes to themselves.

    A period quote with no `speaker` falls back to the WORK'S AUTHOR when it is displayed, so a
    letter written TO Wilde and printed in Wilde's own Collected Letters renders as Wilde speaking -
    and, once an addressee is recorded, as "Oscar Wilde to Oscar Wilde". That is the shape this
    catches: an absent speaker is as capable of misattributing a quotation as a wrong one.
    """
    to = (q.get("addressee") or "").strip()
    if not to:
        return
    wk = works.get(q.get("work")) or {}
    speaker = (q.get("speaker") or (wk.get("author") if q.get("voice") == "period" else "") or "").strip()
    if not speaker:
        return
    a, b = speaker.lower(), to.lower()
    if a == b or a.startswith(b + ",") or b in a.split(",")[0]:
        errors.append(f"{where}: speaker and addressee are the same person ({speaker!r} -> {to!r}). "
                      f"If the quote carries no `speaker` it inherits the work's author, which is "
                      f"wrong whenever the words are not that author's - name the real speaker")


TURN_LABEL = re.compile(r"\b[A-Z][A-Z .'\-]*[A-Z]:\s*")
TURN_DASH = re.compile(r"(?<=\?)\s*[\u2014\u2013]\s*")
# Hyde attributes a third way: "The Clerk of Arraigns—Do you find…", a name and an em dash.
# This is a LITERAL LIST of the markers actually in the corpus, not a rule for spotting them.
# A general pattern was tried and was worse than useless: Hyde uses the same em dash inside
# answers, so it read "Men—young men from sixteen to thirty" as a speaker called Men, and
# "examined by Mr. Avory—" as Avory speaking words that are in fact the witness's. Four
# transcripts use this convention. A fifth will fail the check loudly and be added here once
# somebody has read it, which is the right way round.
TURN_ATTRIB = re.compile(r"(?:The Clerk of Arraigns|The Foreman|Mr\. Justice Wills)—")


def check_turns(q, where, errors):
    """An `exchange` is displayed as a transcript, and the transcript has to BE the quotation.

    The rows are split from the quoted text by a heuristic over two printing conventions, then read
    and corrected by hand, so the risk is not that the splitter fails loudly - it is that a row
    quietly drops or reworks a few words and the card then shows something the source does not say.
    So the turns are checked against the quotation itself: strip the markers that carry a change of
    speaker (a name label, or the dash after a question) and what remains must match exactly.
    """
    turns = q.get("turns")
    voice = q.get("voice")
    if voice != "exchange":
        if turns:
            errors.append(f"{where}: has `turns` but voice is {voice!r} - turns are for an "
                          f"exchange, which is period text with more than one speaker in it")
        return
    if (q.get("quote") or "").strip() and not turns:
        errors.append(f"{where}: voice is 'exchange' but there are no `turns` - run "
                      f"tools/dump_turns.py, read the split, and store it")
        return
    if not turns:
        return
    if not isinstance(turns, list) or any(not isinstance(t, dict) for t in turns):
        errors.append(f"{where}: `turns` must be a list of objects")
        return
    for n, t in enumerate(turns):
        if not (t.get("text") or "").strip():
            errors.append(f"{where}: turn {n} has no text")
        if "who" not in t:
            errors.append(f"{where}: turn {n} has no `who` (use \"\" when the record does not "
                          f"say which speaker it belongs to - better blank than guessed)")
    norm = lambda s: re.sub(r"\s+", " ", s or "").strip()
    joined = norm(" ".join(t.get("text", "") for t in turns))
    want = norm(TURN_ATTRIB.sub(" ", TURN_DASH.sub(" ", TURN_LABEL.sub("", q.get("quote") or ""))))
    if joined != want:
        errors.append(f"{where}: the turns do not reproduce the quotation - a transcript that "
                      f"drops or rewords the source is worse than none\n"
                      f"      turns: {joined[:120]}\n      quote: {want[:120]}")


# Function words common in the language and rare-to-absent in English. Deliberately NOT a language
# identifier: it only has to answer "is this obviously not English", and answer it from a passage of
# a few dozen words. Words English shares - que, no, in, a, me, non, per - are left out, so an
# English sentence cannot accumulate a score from them, and both spellings of the accented French
# forms are listed because the corpus prints them accented.
_FOREIGN = {
    "French": re.compile(
        r"\b(les|des|une|dans|pour|qui|est|était|etait|elle|nous|vous|mais|avec|sur|tout|comme"
        r"|cette|je|leur|plus|fut|aux|ses|même|meme|bien|sans|deux|toujours|jamais|alors"
        r"|[jlndcstm]’\w+|[jlndcstm]'\w+)\b", re.I),
    "German": re.compile(
        r"\b(der|die|das|und|ist|nicht|ich|sie|eine|einen|zu|mit|auf|von|dem|den|war|aber|sich"
        r"|auch|noch|wie|nur|wenn|dass|schon|immer)\b", re.I),
    "Italian": re.compile(
        r"\b(gli|che|gli|gliela|gliene|del|della|delle|sono|questo|questa|nel|nella|sua|suo"
        r"|più|piu|anche|perché|perche|quando|senza|sempre)\b", re.I),
    "Latin": re.compile(
        r"\b(quod|cum|sed|sunt|esse|atque|enim|autem|nec|ipse|omnia|nihil|quae|quam|tamen)\b",
        re.I),
}


def _guess_foreign(text, min_hits=4, min_density=0.14):
    """Return (language, hits, words) when a quotation reads as clearly not English."""
    words = max(1, len(text.split()))
    best, best_hits = None, 0
    for name, rx in _FOREIGN.items():
        n = len(rx.findall(text))
        if n > best_hits:
            best, best_hits = name, n
    if best_hits >= min_hits and best_hits / words >= min_density:
        return best, best_hits, words
    return None, 0, words


def validate_quote(q, where, works, errors, warnings=None):
    warnings = warnings if warnings is not None else []
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
    check_order_hint(q, where, errors)
    check_speaker_addressee(q, where, works, errors)
    check_turns(q, where, errors)
    if q.get("addressee") is not None:
        if not isinstance(q["addressee"], str) or not q["addressee"].strip():
            errors.append(f"{where}: addressee must be a name, or absent - use null/omit when the "
                          f"source does not say who was being addressed")
        elif q.get("voice") not in ("period", "exchange"):
            errors.append(f"{where}: addressee is for a participant's own words; a modern voice "
                          f"(a historian writing about them) has no addressee")
    # The citation prints the work; a speaker that also names it says the book twice in one line.
    # After the comma belongs a CAPACITY - "examination-in-chief", "letter to John Gray" - which is
    # something the citation cannot supply and the reader cannot infer.
    sp_full = (q.get("speaker") or "")
    wk_here = works.get(q.get("work")) or {}
    if "," in sp_full and isinstance(wk_here, dict) and wk_here.get("title"):
        _n = lambda s: re.sub(r"[^a-z0-9]+", "", (s or "").lower())
        _tail = sp_full.split(",", 1)[1]
        if _n(_tail) and _n(_tail) in _n(wk_here["title"]):
            warnings.append(f"{where}: speaker repeats its own work's title ({_tail.strip()!r}); "
                            f"the citation already prints it")
    # A quotation not in English has to carry an English translation, and a translation has to say
    # what it is a translation OF. The original stays the quotation - it is what was verified at
    # the page and what the claim rests on - but printing it alone makes the evidence unreadable to
    # most of the people this map is for.
    lang = q.get("lang")
    if lang is not None and (not isinstance(lang, str) or not re.fullmatch(r"[a-z]{2,3}", lang)):
        errors.append(f"{where}: lang must be a short language code like 'fr', got {lang!r}")
    elif lang and lang != "en" and not (q.get("translation") or "").strip():
        errors.append(f"{where}: lang={lang!r} needs a `translation` - a non-English quotation is "
                      f"printed with an English translation beneath it")
    if (q.get("translation") or "").strip() and not lang:
        errors.append(f"{where}: has a translation but no `lang` saying what it is translated from")
    # Both rules above start from `lang`, so a quotation that never declared itself foreign slipped
    # past both - which is exactly how a French passage of Barney's reached the page untranslated
    # for four days, its English sitting in `context` where nothing rendered it. Ask the question
    # the other way round: does this look like it is not in English?
    if not lang and (q.get("quote") or "").strip():
        if re.search(r"\bTranslation:\s*['\"‘“]", q.get("context") or ""):
            errors.append(f"{where}: the context carries a labelled translation. A translation goes "
                          f"in `translation` with `lang` set, or the page never shows it")
        guess, hits, words = _guess_foreign(q["quote"])
        if guess:
            warnings.append(f"{where}: reads like {guess} ({hits} function words in {words}) but "
                            f"has no `lang`. Set lang and add a translation, or ignore this if the "
                            f"quotation really is English")
    if d and (d.get("y") or 0) > 1945:
        errors.append(f"{where}: evidence_date {d.get('y')} looks like a publication year. "
                      f"It should be the date of the thing evidenced - see works.json "
                      f"_evidence_date_note")


BARE_LABEL = re.compile(r"^\s*(c\.\s*)?(\d{4})\s*(?:[-–—]\s*(c\.\s*)?(\d{4})\s*)?$")


def check_bare_label(r, rid, errors):
    """A date_label that only restates the dates must agree with their `circa` flags.

    `date_label` is free prose, and that is deliberate - most of them say things a date object
    cannot ("known only from a letter of 2 September 1900, by which time he had returned"). But six
    of them are just a year or a year-range, written by hand to give a short display, and two had
    drifted from the flags underneath: one showed "1891-1900" over a start marked circa, another
    showed "c. 1903-1928" over a start with no flag. That is what put "1889" beside "c. 1889" on
    the same screen. Prose labels are left alone; a bare one has to match.
    """
    label = r.get("date_label")
    if not isinstance(label, str):
        return
    m = BARE_LABEL.match(label)
    if not m:
        return                      # prose: it can say whatever the record needs it to say
    s, e = r.get("start") or {}, r.get("end") or {}
    for got, date, which in ((m.group(1), s, "start"), (m.group(3), e, "end")):
        if date.get("y") is None and which == "end":
            continue
        want = bool(date.get("circa"))
        if bool(got) != want:
            errors.append(
                f"{rid}: date_label {label!r} {'has' if got else 'lacks'} 'c.' on its {which} "
                f"year, but {which}.circa is {want} - a bare date label must agree with the flags "
                f"it restates (write prose if it needs to say more)")
    if "-" in label or "—" in label:
        errors.append(f"{rid}: date_label {label!r} joins its years with the wrong dash - a bare "
                      f"range uses ' – ', the same as a generated one, so hand-written and "
                      f"generated labels cannot look different")


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
                validate_quote(q, f"{pid}.context[{ce.get('partner_name')}]", works, errors, warnings)

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
        if r.get("certainty") == "attraction-expressed":
            if r.get("direction") not in ppl:
                errors.append(f"{rid}: attraction-expressed requires direction = one of {ppl}")
            if r.get("outcome") not in OUTCOMES:
                errors.append(f"{rid}: attraction-expressed requires outcome in {sorted(OUTCOMES)}")
        else:
            if r.get("direction") is not None and r.get("direction") not in ppl:
                errors.append(f"{rid}: direction must name one of {ppl}")
            if r.get("outcome") is not None:
                errors.append(f"{rid}: outcome is only for attraction-expressed")
        check_date(r.get("start"), f"{rid}.start", errors)
        check_date(r.get("end"), f"{rid}.end", errors)
        check_bare_label(r, rid, errors)
        s, e = r.get("start") or {}, r.get("end") or {}
        if s.get("y") and e.get("y") and s["y"] > e["y"]:
            errors.append(f"{rid}: start after end")
        if not r.get("sources"):
            warnings.append(f"{rid}: no sources at all")
        for q in r.get("sources", []) or []:
            validate_quote(q, rid, works, errors, warnings)

    orphans = pids - {p for r in rels if "__load_error__" not in r for p in r.get("people", [])}
    for o in sorted(orphans):
        warnings.append(f"{o}: on the roster but in no relationship")

    # THE SAME EXCERPT TWICE IN ONE FILE, or on both a person and their own connection. One source
    # legitimately evidences several DIFFERENT connections - the letter naming Raphael and Fortune
    # is cited on both, and the panel collapses them at render time - but the same excerpt repeated
    # inside a single record, or on a person AND a connection they are party to, is duplication with
    # nothing to distinguish it. `alphonse` shipped that way: the letter appeared once on a context
    # engagement with Wilde and again on alphonse--turner, printing the paragraph twice and implying
    # a pairing the source never made.
    def _qkey(q):
        return (q.get("work"), q.get("locator"),
                re.sub(r"\W+", " ", (q.get("quote") or "")).strip().lower())

    for holder, sources in ([(r.get("id", "?"), r.get("sources") or []) for r in rels] +
                            [(f"{p.get('id','?')}.context[{ce.get('partner_name','?')}]",
                              ce.get("sources") or [])
                             for p in people for ce in p.get("context_engagements") or []]):
        seen = set()
        for q in sources:
            k = _qkey(q)
            if not k[2]:
                continue                      # pointers carry no text and never collide
            if k in seen:
                errors.append(f"{holder}: the same excerpt of {k[0]} {k[1]} appears twice in this "
                              f"record - quote it once")
            seen.add(k)

    by_person = {}
    for r in rels:
        for pid in r.get("people", []) or []:
            for q in r.get("sources") or []:
                by_person.setdefault(pid, {}).setdefault(_qkey(q), []).append(r.get("id", "?"))
    for p in people:
        pid = p.get("id")
        for ce in p.get("context_engagements") or []:
            for q in ce.get("sources") or []:
                k = _qkey(q)
                if not k[2]:
                    continue
                where = by_person.get(pid, {}).get(k)
                if where:
                    errors.append(
                        f"{pid}: the excerpt of {k[0]} {k[1]} is on this person's context "
                        f"engagement AND on their own connection {where[0]} - keep it on the "
                        f"connection only")
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
             "✗ error/rejected · ⧖ pending verification", "",
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


def about_html():
    """Compile content/ABOUT.md into the HTML the About panel shows.

    The panel's text used to live inside index.html, which meant editing prose in among the markup.
    It is a markdown file now, compiled here rather than parsed in the browser: the site's bargain
    is one script and no toolchain, and shipping a markdown parser to every reader to render one
    static document would be a poor trade. `python tools/validate.py` already has to run before the
    site is served, so this costs nothing new.

    The subset is deliberately small - headings, paragraphs, bullets, bold, italic, links - because
    it only has to serve one document that we control. Two placeholders survive into the HTML for
    the page to fill in: {{line:<certainty>}} becomes the real connection line, drawn from the same
    definitions the legend uses, and {{colophon}} becomes the generated build line.
    """
    src = ROOT / "content" / "ABOUT.md"
    if not src.exists():
        return ""
    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    def inline(s):
        s = esc(s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                   r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
        # Both spellings of emphasis. A markdown formatter rewrites *this* to _this_ whenever it
        # runs over ABOUT.md, so reading only the asterisks meant the page printed the underscores.
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"(?<![A-Za-z0-9_])__(.+?)__(?![A-Za-z0-9_])", r"<b>\1</b>", s)
        s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", s)
        # ...but the underscore form only between word boundaries, or `evidence_date` and
        # `order_hint` - ordinary words here - would come out with their middles in italics.
        s = re.sub(r"(?<![A-Za-z0-9_])_([^_\n]+)_(?![A-Za-z0-9_])", r"<i>\1</i>", s)
        return s
    out, ul = [], False
    def close_ul():
        nonlocal ul
        if ul:
            out.append("</ul>")
            ul = False
    for raw in src.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip():
            close_ul(); continue
        if line.startswith("## "):
            close_ul(); out.append(f'<div class="sect">{inline(line[3:])}</div>')
        elif line.startswith("# "):
            close_ul(); out.append(f"<h2>{inline(line[2:])}</h2>")
        elif line.startswith("- "):
            if not ul:
                out.append("<ul>"); ul = True
            body = line[2:]
            # A bullet that opens with a line sample IS the sample - no disc as well.
            # NOT "lrow" - that is the All-relationships list's row button, and About renders
            # into the same panel on desktop, so the two would share a stylesheet rule.
            cls = ' class="lkey"' if body.startswith("{{line:") else ""
            out.append(f"<li{cls}>{inline(body)}</li>")
        elif line.strip() == "{{colophon}}":
            close_ul(); out.append('<p id="colophon"></p>')
        else:
            close_ul()
            # The subtitle is a whole line in italics, in either spelling.
            wrapped = ((line.startswith("*") and line.endswith("*") and not line.startswith("**"))
                       or (line.startswith("_") and line.endswith("_")
                           and not line.startswith("__")))
            cls = ' class="sub" style="font-style:italic"' if wrapped else ""
            body = inline(line[1:-1]) if cls else inline(line)
            out.append(f"<p{cls}>{body}</p>")
    close_ul()
    return "\n".join(out)


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
              "works": works, "portraits": portraits, "about": about_html(),
              "built": date.today().isoformat()}
    out = DATA / "circle.json"
    out.write_text(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")) + "\n",
                   encoding="utf-8")
    print(f"\nwrote {out.relative_to(ROOT)} ({out.stat().st_size/1024:.0f} KB) — "
          f"generated, do not hand-edit")


main()
