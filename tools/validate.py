#!/usr/bin/env python3
"""Validate the corpus and build the bundle the site loads.

The per-entity files under data/people and data/relationships are the source of truth: one file
per person, one per connection, so contributors get small diffs and few merge conflicts. This
script checks them against the house rules and writes data/web.json, which is what the browser
actually fetches.

    python tools/validate.py              validate, then write data/web.json
    python tools/validate.py --check      validate only, write nothing (use this in CI)
    python tools/validate.py --stats      validate, print a dashboard, write nothing
    python tools/validate.py --ledger     regenerate audits/QUOTE-AUDIT_web.md
    python tools/validate.py --allow-dirty   let needs-fix / rejected quotes through

Exit code is non-zero when validation fails, so it can gate a pull request.
UTF-8 without BOM throughout.
"""
import argparse
import calendar
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The public repository. {{repo}} in the markdown documents is replaced with this, so that a link
# to the issue forms works both on GitHub and on the published site, where a relative path to
# /issues would go nowhere. CHANGE THIS if the repository is named or owned differently.
REPO = "https://github.com/ImpowerGames/the-world-wilde-web"
DATA = ROOT / "data"

CERTAINTY = {"self-reported", "second-hand", "uncorroborated", "married", "attraction-expressed", "platonic"}
OUTCOMES = {"declined", "unknown", "unreciprocated"}
CERTAINTY_STATUS = {"proposed", "confirmed"}
VERIFICATION = {"verified-exact", "verified-elision", "needs-fix", "rejected", "unverified"}
# Verification asks three questions, and each has its own field, because one field answering all
# three produced values that overlapped and could not be told apart - "archive-org" and "web"
# named a medium, "pdf-text" named a reading method, "manuscript" named a document.
#
#   how_verified         HOW directly were the words read?
#   document             WHAT KIND of thing is quoted
#   citation_provenance           where the passage sits in the WORK CITED
#   original_provenance  what was read at the DOCUMENT, and seen there (absent = nobody has)
#   marks_verified       the marks were collated against the source and match
#
# There was a `verified_against: "original"` flag too, saying which document was read. It went:
# the validator required `original_provenance` for the flag and the flag for the note, so the two
# could never disagree and one of them was carrying nothing.
#
# The MEDIUM - PDF, archive.org, a website, an EPUB, a physical copy - is deliberately not here.
# `citation_provenance` already records it exactly ("IA in.ernet.dli.2015.499238, leaf 326"), and it says
# nothing about whether the reading can be trusted.
HOW = {
    # A photograph of the object: a scan, a IIIF image, microfilm, a plate. Called "page-image"
    # once, which said "page" of things that are not pages - an envelope, a leaf, an inscription -
    # and left the distinction that matters implicit. What separates this from the two below is
    # that somebody looked at the THING, not at a re-rendering of its text.
    "photo-reproduction",
    "text-layer",    # taken from extracted or OCR text; the page itself was NOT looked at
    "in-hand",       # read the physical object
    "as-published",  # born-digital - a web page, an EPUB - read as its publisher renders it
    "unverified",
}
# `marks_verified: true` says somebody has collated the MARKS of the quotation against the source
# and found them to match: emphasis, accents, punctuation - everything a transcription loses
# quietly. Absent means nobody has done it, which is the honest default and is not a criticism.
#
# It exists so a null finding is a FACT rather than a sentence. This flag on a quotation carrying
# no markup already says nobody found any marks in it, so the prose must NOT say it again: "no
# underlining anywhere in the quoted passage" written beside it is the same statement three times,
# and only one of the three can be checked, counted or filtered.
#
# `original_provenance` is for what this cannot say - which pages were read, marks found and
# where, and above all the things that LOOK like marks and are not: a stroke cancelling a
# letterhead, diagonals that are paragraph marks, the paraph before a signature.
MARKS_VERIFIED = {True, None}

# `verified_against_original: true` says somebody went to the document itself rather than reading
# it where it was reprinted. Absent means nobody has, which is the honest default.
#
# It is deliberately SEPARATE from `original_provenance`, the prose about what was read there.
# The two are established on different passes - a reader opens the manuscript today and writes up
# what they saw tomorrow - and an earlier version of this schema required each for the other,
# which made them agree by construction and then looked redundant for agreeing. The rule runs one
# way only: a note about the document implies the document was read, not the reverse.
VERIFIED_AGAINST_ORIGINAL = {True, None}

# What kind of thing is being quoted, and whether it was written out by hand. `hand` does NOT
# decide whether the original is worth reading - a printed copy can carry an inscription,
# marginalia, a correction or a cancelled leaf that the printing does not. It records what going
# to the original would settle: for something handwritten the document is the only authority for
# emphasis; for something printed the text is already fixed, and what a copy adds is whatever
# somebody later put on it.
#
# The second axis is whether the document is a UNIQUE object or IS the published work it was read
# in. It decides what "where is this" means when no archive has been recorded. For a letter the
# document and the work are different things - the letter is one sheet somewhere, the Complete
# Letters is a book - so a letter with no repository is a letter nobody has traced. For a
# biography the document IS the book, and the answer is that you get it from a library. Those two
# blanks used to be the same blank, and the biographies drowned the letters.
UNIQUE, PUBLISHED = "unique", "published"
DOCUMENTS = {
    "letter": (True, UNIQUE), "telegram": (True, UNIQUE), "postcard": (True, UNIQUE),
    "diary": (True, UNIQUE), "inscription": (True, UNIQUE), "manuscript": (True, UNIQUE),
    "typescript": (False, UNIQUE),
    "memoir": (False, PUBLISHED), "interview": (False, PUBLISHED),
    "pamphlet": (False, PUBLISHED), "novel": (False, PUBLISHED),
    "essay": (False, PUBLISHED), "poem": (False, PUBLISHED),
    # Court records are PUBLISHED because that is the honest answer for these ones: the shorthand
    # writers' transcripts of the Wilde trials do not survive as a public archive, and the text
    # everybody quotes - this map included - is Hyde's printed edition. A record that does trace
    # an original files a `manuscript`, which overrides this.
    "testimony": (False, PUBLISHED), "plea": (False, PUBLISHED), "verdict": (False, PUBLISHED),
    # What a later hand wrote ABOUT the subject, rather than what the subject wrote. These exist
    # because `document` used to be left unset here, on the reasoning that the work cited IS the
    # document - which was true, and which made "not applicable" indistinguishable from "nobody
    # has classified this yet".
    "biography": (False, PUBLISHED),       # a life of a person
    "study": (False, PUBLISHED),           # a scholarly book or monograph on a subject
    "article": (False, PUBLISHED),         # a piece in a periodical or journal
    "encyclopedia": (False, PUBLISHED),    # a reference entry
    "editorial-note": (False, PUBLISHED),  # an editor annotating somebody else's primary text
    "introduction": (False, PUBLISHED),    # a prefatory essay to somebody else's work
    "finding-aid": (False, PUBLISHED),     # an archive's own inventory of a collection
    "web-page": (False, PUBLISHED),        # born-digital, read where it is published
}
# What a work IS, in works.json. The `-web` suffix is the load-bearing part: it marks a work that
# is read where it is published, which no library can get for you and whoever put it up can take
# down. Everything else is a thing with a spine.
WORK_KINDS = {"primary", "primary-edition", "secondary", "secondary-web",
              "interview", "trial-transcript"}
LOCATOR_TYPES = {"page", "diary-entry", "trial-day", "letter-date", "none"}
GROUPS = {"core", "family", "society", "aesthete", "trials", "chaeronea",
          "later", "liaisons", "beyond"}
GENDERS = {"m", "f", None}
# "court" is text from the record of a court - sworn testimony, a plea, a verdict. It was called
# "exchange" and defined as period text with more than one speaker in it, which fitted neither
# end: nineteen records had a single speaker (a witness's answer quoted without the question),
# and a plea of justification is not dialogue at all. It is kept apart from "period" because a
# court record is not somebody speaking for themselves - it is speech taken down under compulsion
# and printed by the court - and the card sets the two differently to say so.
#
# `turns` are OPTIONAL here: with them the card draws a transcript, without them a continuous
# quotation, and both are styled as the court record they are.
VOICES = {"period", "court", "modern", None}


MANUSCRIPTS = ROOT / "manuscripts"
# Outside ROOT, so `publish.py` - which copies ROOT and nothing else - never sees it. The full
# text of every letter read from the printed edition lives there; only the cited ones cross.
TRANSCRIPTIONS = ROOT.parent / "transcriptions"
# Names the sibling block the text was read off: a record usually carries BOTH a
# `facsimile` and a `printed`, and this says which one was transcribed.
TRANSCRIBED_FROM = {"facsimile", "printed"}
# Four acts, in the order a letter goes through them. `received` is a receiving
# postmark or a docket - "[Date of receipt 2 July 1891]" - which the volume gives
# for 13 letters and which is neither writing, posting, nor handing in at a counter.
ACTS = ("written", "sent", "postmarked", "received")
ACT_FIELDS = {"date", "from", "time"}
LETTER_FOLIO = re.compile(r"^[^/]+/(\d+)")
YEAR = re.compile(r"\b(?:18|19|20)\d\d\b")

# What the `MS …` chip prints. The full name is the citation and stays in the record; this is the
# label, and mostly it is the volume's own abbreviation from its key at pp. xxii-xxv - a reader of
# the Complete Letters already knows "Clark" and "Berg" and reads them faster than the full form.
#
# A repository with no entry here falls back to the text before its first comma, which is right
# often enough ("Bodleian Library, Oxford" -> "Bodleian Library") and never wrong enough to
# mislead. Add an entry when that reads badly.
REPOSITORY_SHORT = {
    "William Andrews Clark Memorial Library, UCLA": "Clark, UCLA",
    "British Library, London (Lady Eccles Oscar Wilde Collection)": "British Library, Eccles",
    "British Library, London": "British Library",
    "Magdalen College, Oxford": "Magdalen, Oxford",
    "Bryn Mawr College Library, Bryn Mawr, Pennsylvania": "Bryn Mawr",
    "Arents Tobacco Collection, New York Public Library": "Arents, NYPL",
    "Henry W. and Albert A. Berg Collection, New York Public Library": "Berg, NYPL",
    "Montague Collection, New York Public Library": "Montague, NYPL",
    "Vaughan Library, Harrow School, London": "Harrow School",
    "Princeton University Library, Princeton, New Jersey": "Princeton",
    "Henry E. Huntington Library, San Marino, California": "Huntington",
    "Yale University Library, New Haven, Connecticut": "Yale",
    "Beinecke Rare Book and Manuscript Library, Yale University": "Beinecke, Yale",
    "The Frederick R. Koch Collection (in part at Yale)": "Koch, Yale",
    "The Morgan Library & Museum, New York": "Morgan",
    "Bodleian Library, Oxford": "Bodleian",
    "Harvard University Library, Cambridge, Massachusetts": "Harvard",
    "University of Virginia Library, Charlottesville, Virginia": "Virginia",
    "State University of New York Library, Buffalo, New York": "Buffalo",
    "Haliburton Fales Collection, New York University": "Fales, NYU",
    "Rosenbach Museum and Library, Philadelphia": "Rosenbach",
    "Somerset County Library, Street, Somerset": "Somerset",
    "Library of Trinity College, Dublin": "Trinity, Dublin",
    "Dartmouth College Library, Hanover, New Hampshire": "Dartmouth",
    "Harry Ransom Center, The University of Texas at Austin": "Ransom Center",
    "Biblioth\u00e8que Doucet, Paris": "Doucet, Paris",
    "Biblioth\u00e8que nationale de France, Paris": "BnF, Paris",
    "Sterling Library, University of London": "Sterling, London",
}


def short_repository(name):
    """The chip's label for a repository name. Never longer than the name it stands for."""
    name = (name or "").strip()
    if not name:
        return ""
    if name in REPOSITORY_SHORT:
        return REPOSITORY_SHORT[name]
    head = name.split(",")[0].strip()
    head = head[4:] if head.lower().startswith("the ") else head
    return head or name


# RightsStatements.org markers as the archives apply them, in words a reader can act on. A page
# whose marker is not in here still displays - it just shows the bare URI, which is honest about
# the fact that nobody has read it yet.
RIGHTS_LABEL = {
    "http://rightsstatements.org/vocab/NoC-US/1.0/": "No Copyright – United States",
    "http://rightsstatements.org/vocab/UND/1.0/": "Copyright Undetermined",
    "http://rightsstatements.org/vocab/InC/1.0/": "In Copyright",
    "http://rightsstatements.org/vocab/NKC/1.0/": "No Known Copyright",
}


def load(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return {"__load_error__": f"{p.name}: {e}"}


# Text may carry a tab, a newline and a carriage return. Every other C0 control, and DEL, is
# damage: nothing here types one on purpose.
LEGAL_CONTROL = {0x09, 0x0A, 0x0D}
CONTROL_NAME = {0x00: "NUL", 0x07: "BEL", 0x08: "BACKSPACE", 0x0B: "VERTICAL TAB",
                0x0C: "FORM FEED", 0x1A: "SUB", 0x1B: "ESC", 0x7F: "DEL"}
TEXT_SUFFIXES = {".json", ".jsonc", ".js", ".css", ".html", ".md", ".py", ".txt", ".svg"}


def check_control_characters(errors):
    """Refuse a source file carrying a control character nobody typed.

    This catches a specific, silent failure. Sending a script through a shell heredoc in this
    environment eats one level of backslash, so `\b` reaches the interpreter as a BACKSPACE byte
    and `\00` as a NUL, and the byte is written into whatever the script was editing. Nothing
    complains: the file still parses, an editor still renders it, and grep still matches around
    it. It has happened twice - a NUL into circle.css, two backspaces into this very file - and
    both times it was found by eye, long after.

    A build is the right place to catch it because the damage is invisible at every other stage.
    """
    seen = 0
    for f in sorted(ROOT.rglob("*")) + sorted(TRANSCRIPTIONS.rglob("*")):
        if not f.is_file() or f.suffix.lower() not in TEXT_SUFFIXES:
            continue
        seen += 1
        try:
            raw = f.read_bytes()
        except OSError:
            continue
        for i, b in enumerate(raw):
            if b in LEGAL_CONTROL or (b >= 0x20 and b != 0x7F):
                continue
            line = raw.count(b"\n", 0, i) + 1
            col = i - (raw.rfind(b"\n", 0, i) + 1) + 1
            try:
                where = f.relative_to(ROOT.parent)
            except ValueError:
                where = f
            errors.append(
                f"{where}: {CONTROL_NAME.get(b, hex(b))} control character at line {line}, "
                f"column {col}. Nobody types one of these - it is almost always a backslash "
                f"escape that a shell ate before the interpreter saw it. Rewrite the file with "
                f"the byte removed, and write the script that produced it to a FILE rather than "
                f"piping it through a heredoc")
            break  # one report per file; the fix is the same for all of them
    return seen


def load_transcriptions(errors, people=()):
    """Every full-text transcription we hold, from both stores, keyed by letter_id.

    TWO STORES, one shape. A transcription read from a FACSIMILE is our own reading of a
    public-domain document: it lives beside the images under manuscripts/<archive>/, publishes
    whole, and is the only kind that can witness emphasis. A transcription read from the printed
    EDITION lives in the private tree, cannot witness emphasis - the editors print Wilde's
    underlining, titles and foreign words as one italic and do not mark multiple underlining at
    all - and publishes only where this map cites the letter.

    Both are loaded here because the reader wants one answer to "is there a full text of this
    document", and which store it came from is the build's problem, not the browser's.

    THE TWO STORES ARE SHAPED DIFFERENTLY, for reasons that belong to each. The facsimile store is
    one file per transcription, `<archive>/transcriptions/<item>-<image>.json`, so that two people
    transcribing different letters never touch the same file and an interrupted run leaves its
    finished work behind. That matters most for the edition store, which a long agent run fills a
    letter at a time and which this environment will interrupt.
    """
    known, surnames = set(), {}
    for pp in people:
        for n in [pp.get("name")] + list(pp.get("aka") or []):
            if not n:
                continue
            known.add(n.lower())
            # Keyed on the surname of the NAME OR ANY AKA, so "Wilde" finds Constance Lloyd too;
            # valued by the person's canonical name, deduped because a name and an aka often
            # share a surname and listing somebody twice reads like two people.
            who = surnames.setdefault(n.split()[-1].lower(), [])
            if pp["name"] not in who:
                who.append(pp["name"])
    out = {}
    files = (sorted(MANUSCRIPTS.glob("*/transcriptions/*.json")) +
             sorted(TRANSCRIPTIONS.glob("*/*.json")))
    for f in files:
        where = f.parent.name + "/" + f.name
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"{where}: unreadable ({e})")
            continue
        for t in [doc]:
            at = where
            lid = t.get("letter_id")
            if not isinstance(lid, str) or not LETTER_ID.match(lid or ""):
                errors.append(f"{at}: letter_id is what joins a transcription to the quotations "
                              f"of the same document, and must be present and well formed, "
                              f"got {lid!r}")
                continue
            # NOT inferred from the presence of a facsimile block. It was, for entries that
            # predated the field - none remain - and the inference quietly accepted a record
            # whose field name was mistyped, on the one field that decides whether a
            # transcription publishes at all. Stated or refused.
            kind = t.get("transcribed_from")
            if kind not in TRANSCRIBED_FROM:
                errors.append(f"{at}: transcribed_from must be 'facsimile' or 'printed' - it decides "
                              f"both whether this publishes and whether it can be read for "
                              f"emphasis, so it is not inferred, got {t.get('transcribed_from')!r}")
            if kind == "printed" and t.get("marks_verified"):
                errors.append(f"{at}: marks_verified on a transcription taken from the printed "
                              f"edition. There is nothing there to verify: the editors print "
                              f"underlining, titles and foreign words as one italic. Only a "
                              f"facsimile settles emphasis")
            if kind == "printed" and t.get("facsimile"):
                errors.append(f"{at}: carries a facsimile but says transcribed_from 'printed'. If the "
                              f"text was read off the images, it belongs in that archive's "
                              f"transcriptions/ folder and publishes whole")
            if not (t.get("quote") or "").strip():
                errors.append(f"{at}: a transcription with no text")
            # The id and the locator describe the same letter here, so they have to agree. This
            # is the mistyped id the run will actually produce: one that matches no citation
            # publishes nothing, in silence, and looks just like a letter nobody has cited yet.
            fol = LETTER_FOLIO.match(lid)
            loc_n = re.search(r"\d+", (t.get("printed") or {}).get("locator") or "")
            if fol and loc_n and fol.group(1) != loc_n.group(0):
                errors.append(f"{at}: letter_id says folio {fol.group(1)} but printed.locator "
                              f"says {(t.get('printed') or {}).get('locator')!r}. They name the "
                              f"same letter, so one of them is mistyped - and a wrong id "
                              f"publishes nothing, silently")
            # The reader builds its header from these - "Wilde to George Ives, postmarked
            # 21 March 1898, Paris" - rather than cutting the first sentence out of `context`,
            # which needed a regex that knew about initials and abbreviations to recover what the
            # transcriber knew all along. `written_from` is optional because some letters give none.
            # Written as the person's own `name`, the way `speaker` is on a source, so the two
            # ends of a letter read alike and can be linked to their nodes. The volume's idiom is
            # a surname - "Wilde to George Ives" - and copying that leaves one end of every
            # letter in a different register from the other.
            for field in ("sender", "addressee"):
                v = (t.get(field) or "").strip()
                who = surnames.get(v.lower(), ())
                if v and v.lower() not in known and who:
                    # Fires however many people share the surname. An earlier version only spoke
                    # up when it could name ONE replacement, which let through the commonest case
                    # on this map: "Wilde", where the ambiguity is the whole problem - there are
                    # three of them, and the volume's idiom means the sender field.
                    errors.append(f"{at}: {field} {v!r} is a surname, and "
                                  f"{'more than one person here has it: ' if len(who) > 1 else 'this map has '}"
                                  f"{', '.join(repr(x) for x in sorted(who))}. Write the full name "
                                  f"as the person's own `name` - the rule `speaker` follows, and "
                                  f"what lets a correspondent be linked to their node")
            # ONE FIELD PER ACT, each carrying when and where that act happened:
            #
            #   "written":    {"date": {...}, "from": "New Travellers Club, Piccadilly"}
            #   "postmarked": {"date": {...}, "from": "Paris"}
            #   "sent":       {"date": {...}, "from": "Paris", "time": "3.50 p.m."}
            #
            # Writing, posting and handing in are ACTS, and an act has a when and a where, so the
            # two travel together and the three fields are parallel by construction. The earlier
            # `written_on` / `written_from` pairs were not: `written_on` reads as the paper it was
            # written on, and nothing sensible lines up beside `postmarked_from`.
            #
            # EITHER HALF MAY BE MISSING, and which is missing is itself the finding. A letter
            # headed "postmarked 21 March 1898" from Paris knows where he wrote it and not when,
            # so `written` carries a `from` and no date while `postmarked` carries the date.
            dated_acts = 0
            for a in [a for a in ACTS if t.get(a) is not None]:
                act = t[a]
                if not isinstance(act, dict):
                    errors.append(f"{at}.{a}: must be an object with a `date` and/or a `from`")
                    continue
                unknown = set(act) - ACT_FIELDS
                if unknown:
                    errors.append(f"{at}.{a}: unknown field(s) {sorted(unknown)} - an act carries "
                                  f"{', '.join(sorted(ACT_FIELDS))}")
                if not (act.get("date") or act.get("from")):
                    errors.append(f"{at}.{a}: an act with neither a date nor a place says "
                                  f"nothing; leave it out")
                for f2 in ("from", "time"):
                    if f2 in act and not (isinstance(act[f2], str) and act[f2].strip()):
                        errors.append(f"{at}.{a}.{f2}: must be a non-empty string")
                dt = act.get("date")
                if dt is None:
                    continue
                if not isinstance(dt, dict):
                    errors.append(f"{at}.{a}.date: must be an object like {{'y': 1900, 'm': 9}}")
                    continue
                dated_acts += 1
                check_date({k: v for k, v in dt.items() if k != "certainty"},
                           f"{at}.{a}.date", errors)
                # NOT `y` required. The volume dates a few letters "Saturday night" or
                # "Thursday 3 June" - the writer's own heading, which the editors could not pin
                # to a year - and demanding one would force an invention. A date must say
                # something; a weekday alone is something. It sorts last, which is honest.
                if not any(isinstance(dt.get(k), int) for k in ("y", "m", "d")) \
                        and not dt.get("weekday") and not dt.get("season"):
                    errors.append(f"{at}.{a}.date: says nothing - give it a year, a month, a "
                                  f"day, a season or the weekday the writer wrote. An empty "
                                  f"date is an act with no date, so leave the date out instead")
                # `certainty` belongs to the DATE, not the letter: in "Tuesday [? early October
                # 1899]" the day-name is Wilde's and the date is the editors' guess.
                if dt.get("certainty") not in (None, "conjectured"):
                    errors.append(f"{at}.{a}.date: certainty is 'conjectured' or absent, got "
                                  f"{dt.get('certainty')!r}. There is no 'stated' - a date the "
                                  f"volume prints plainly simply carries nothing")
            if not dated_acts:
                errors.append(f"{at}: no structured date on any of {', '.join(ACTS)} - the "
                              f"letter sorts nowhere and the reader cannot name it")
            for field in ("sender", "addressee"):
                if not (t.get(field) or "").strip():
                    errors.append(f"{at}: {field} is required - the reader names the "
                                  f"document from these fields, and the dating from `written`, "
                                  f"`postmarked` and `sent`")
            if kind == "facsimile":
                # The filename is chosen so that it FOLLOWS from the file's own facsimile block -
                # archive, item, first image - with nothing to look up. That is the reason it is
                # not the archive's page identifier, which would need a manifest join to derive,
                # and which two of the five archives do not publish at all. Worth enforcing, or it
                # is only a convention until the first hand-made file drifts from it.
                fac = t.get("facsimile") or {}
                pages = fac.get("pages") or []
                if fac.get("archive") and fac.get("item") and pages:
                    want = f"{f.parts[-3]}-{fac['item']}-{pages[0]:03d}"
                    if f.stem != want:
                        errors.append(f"{at}: filename does not match its own facsimile block - "
                                      f"expected {want}.json")
            if lid in out:
                errors.append(f"{at}: letter_id {lid!r} is transcribed twice, in {out[lid]['at']} "
                              f"as well. One document, one transcription")
                continue
            out[lid] = {**t, "transcribed_from": kind, "at": at}
    return out


def load_archives():
    """Index the manuscript pages described under manuscripts/, one archive per subdirectory.

    Metadata only. The IMAGES are not here and are not published by this repository: each page is
    drawn from the holding archive's own IIIF image service, addressed by the pointer recorded in
    the manifest. That is deliberate - it leaves every scan being served by the institution that
    made it, under the rights statement that institution attached to it, and it keeps a research
    corpus from turning into an image host.

    A source record therefore cites an item and a page NUMBER, and the manifest resolves it. The
    numbers are stable across a re-fetch in a way filenames and pointers are not.

    Returns {} when no manifest is present; the map is meant to build without one.
    """
    archives = {}
    if not MANUSCRIPTS.is_dir():
        return archives
    for man in sorted(MANUSCRIPTS.glob("*/MANIFEST.json")):
        key = man.parent.name
        m = load(man)
        if "__load_error__" in m:
            archives[key] = {"__load_error__": m["__load_error__"]}
            continue
        meta = m.get("archive") or {}
        items = {}
        for it in m.get("items") or []:
            pages = []
            for pg in it.get("pages") or []:
                rights = pg.get("rights") or ""
                pages.append({
                    "n": pg.get("page"),
                    "shelfmark": pg.get("shelfmark") or "",
                    "pointer": str(pg.get("pointer") or ""),
                    "rights": rights,
                    "rights_label": RIGHTS_LABEL.get(rights, rights),
                })
            items[str(it.get("itemId"))] = {
                "title": it.get("title") or "",
                "box_folder": it.get("boxFolder") or "",
                "pages": pages,
            }
        archives[key] = {
            "key": key,
            "name": meta.get("name") or m.get("collection") or key,
            "short_name": meta.get("short_name") or meta.get("name") or key,
            "collection": meta.get("collection") or "",
            "collection_url": meta.get("collection_url") or m.get("download_url") or "",
            "record_url": meta.get("record_url") or "",
            "iiif_url": meta.get("iiif_url") or "",
            "items": items,
        }
    return archives


def check_facsimile(q, where, archives, errors, warnings):
    """A source may point at the scanned pages of the document it quotes.

        "facsimile": {"archive": "hrc", "item": "2700", "pages": [5, 6, 7],
                      "caption": "the letter runs across two folded sheets"}

    `pages` are page numbers WITHIN the item, as the manifest numbers them, and they are the
    pages of the LETTER - not of the quoted sentence. A reader who opens a facsimile wants the
    document, and a letter that runs over four sides is misrepresented by the one side its
    quotable line happens to fall on.
    """
    f = q.get("facsimile")
    if f is None:
        return
    if not isinstance(f, dict):
        errors.append(f"{where}: facsimile must be an object with archive/item/pages")
        return
    for k in ("archive", "item"):
        if not isinstance(f.get(k), str) or not f[k].strip():
            errors.append(f"{where}.facsimile: {k} is required and must be a string")
            return
    ak, ik = f["archive"], f["item"]
    if ak not in archives:
        errors.append(f"{where}.facsimile: unknown archive {ak!r} - expected a directory under "
                      f"manuscripts/ with a MANIFEST.json "
                      f"({', '.join(sorted(archives)) or 'none present'})")
        return
    arc = archives[ak]
    if "__load_error__" in arc:
        errors.append(f"{where}.facsimile: archive {ak!r} has an unreadable manifest: "
                      f"{arc['__load_error__']}")
        return
    if not (arc.get("iiif_url") or "").strip():
        errors.append(f"{where}.facsimile: archive {ak!r} has no `iiif_url`, so the reader would "
                      f"draw a 'View original' button that resolves to nothing. An archive with "
                      f"no image service can be indexed and cited, but it cannot back a "
                      f"facsimile - use `manuscript` with a `url` instead")
        return
    if ik not in arc["items"]:
        errors.append(f"{where}.facsimile: {ak} has no item {ik!r}")
        return
    pages = f.get("pages")
    if not isinstance(pages, list) or not pages:
        errors.append(f"{where}.facsimile: pages must be a non-empty list of page numbers")
        return
    have = {p["n"]: p for p in arc["items"][ik]["pages"]}
    if pages != sorted(pages):
        errors.append(f"{where}.facsimile: pages must be in ascending order, got {pages}")
    if len(set(pages)) != len(pages):
        errors.append(f"{where}.facsimile: the same page is listed twice: {pages}")
    for n in pages:
        if not isinstance(n, int):
            errors.append(f"{where}.facsimile: page {n!r} is not a number - pages are numbered "
                          f"within the item, not named by file")
        elif n not in have:
            errors.append(f"{where}.facsimile: {ak} item {ik} has no page {n} "
                          f"(1-{len(have)})")
        elif not have[n]["pointer"]:
            errors.append(f"{where}.facsimile: {ak} item {ik} page {n} has no archive pointer, "
                          f"so the page cannot be addressed at the archive's image service")
    check_document(q, where, errors)


SHELFMARK_IN_NAME = re.compile(r"\b(?:MA|MS|MSS|Add\.? ?MS|b?MS)\s*\d", re.I)


ARCHIVED_AS = {"autograph", "typescript", None}


def check_manuscript(q, where, errors):
    """Where the original survives, for a source whose document is not scanned here.

        "manuscript": {"repository": "William Andrews Clark Memorial Library, UCLA",
                       "url": "https://…", "archived_as": "typescript"}

    The counterpart to `facsimile`, and the commoner case by far: of the letters this map quotes
    from the Complete Letters, 8 have manuscripts at the Harry Ransom Center and roughly 100 at
    the Clark. Naming the repository is not a substitute for the image, but it is the difference
    between "we cannot show you this" and "nobody knows where this is" - and for a handful of
    letters printed from a dealer's catalogue or a memoir, the second is the true answer.

    `archived_as` says what KIND OF OBJECT is in that repository - an `autograph`, in the
    writer's own hand, or a `typescript`, somebody's typed copy of it. It exists because those two answer the
    emphasis question differently. A letter in Wilde's hand can be read for underlining; a
    typescript of the same letter cannot, because whoever typed it had already read the
    underlining and decided what it meant. Murray read Douglas's 1909 letter to Ross as "Ross TS.
    Clark." The Clark is where the text is, and it is not where the letter is.

    It is NOT `how_verified`, which is a fact about us - how we read the text we quote. Here that
    is `photo-reproduction`, meaning a scan of Murray's book; nobody on this project has been to
    the Clark. `archived_as` is a fact about the archive, and it is usually known - as here -
    precisely when nobody has been near the document. One is our act, the other is the object.

    Write `archived_as` only when it DIFFERS from what the document implies: a letter is an
    autograph unless somebody says otherwise, a typescript is typed. Restating the default says
    nothing, so the validator refuses it, and its presence always means "not what you assumed".

    `owner` names the individual a private holding was last known to belong to, expanded from the
    volume's own key at pp. xxiv-xxv - `MS Mason` is Mr Jeremy Mason. It sits beside a repository
    of "Private collection" rather than replacing it, so the location facet stays one bucket a
    reader can filter on instead of fragmenting into thirty-five owners. Absent for `MS Private`,
    which names nobody by design.

    `recorded_by` says WHO placed the document there, for the records where that is not the work
    being quoted. Three letters here are quoted from Ricketts's Self-Portrait (1939), which names
    no locations at all; what locates them is Delaney's 1990 biography, whose manuscript-sources
    list is arranged by correspondent. Crediting the location to Sturge Moore would be inventing
    an editorial act he never performed. Leave it out when the citing work IS the authority, and
    the card names that work's editors - because it is the editors of a collected edition who
    write the headnotes, not its long-dead author.

    `as_of` says WHEN the holding was last attested, for the cases where that is not the date of
    the edition citing it. A letter last seen in a saleroom is why it exists: the American Art
    Association had Wilde's letter to Smithers on 9 February 1927, and the Complete Letters
    report that in 2000 without anybody having seen it in between. Free text, because what is
    known varies - a date, a year, a sale.
    """
    m = q.get("manuscript")
    if m is None:
        return
    if not isinstance(m, dict):
        errors.append(f"{where}: manuscript must be an object with a repository")
        return
    if not isinstance(m.get("repository"), str) or not m["repository"].strip():
        errors.append(f"{where}.manuscript: repository is required - write it out in full, as it "
                      f"appears on the card ('William Andrews Clark Memorial Library, UCLA'), "
                      f"not as the abbreviation the Complete Letters print")
    # A shelfmark is not part of an institution's name. Left in, the next letter from the same
    # archive under a different shelfmark becomes a second "repository", and the field turns into
    # a citation - which is what `original_provenance` is for. Named COLLECTIONS are fine and
    # common ("(Lady Eccles Oscar Wilde Collection)"), so the test is specifically for a mark
    # followed by digits.
    if SHELFMARK_IN_NAME.search(m.get("repository") or ""):
        errors.append(f"{where}.manuscript: repository {m['repository']!r} carries a shelfmark. "
                      f"Name the institution or the named collection only, and put the shelfmark "
                      f"in `original_provenance`")
    held = m.get("archived_as")
    if held not in ARCHIVED_AS:
        errors.append(f"{where}.manuscript: archived_as must be 'autograph', "
                      f"'typescript' or absent, "
                      f"got {held!r}")
    elif held is not None:
        kind = DOCUMENTS.get(q.get("document"))
        implied = "autograph" if kind and kind[0] else "typescript"
        if held == implied:
            errors.append(f"{where}.manuscript: archived_as {held!r} is what a "
                          f"{q.get('document')!r} already implies, so it says nothing. Write "
                          f"`archived_as` only where the held document contradicts its type - a letter "
                          f"surviving as somebody's typescript, a printed text corrected by hand")
    ow = m.get("owner")
    if ow is not None and not (isinstance(ow, str) and ow.strip()):
        errors.append(f"{where}.manuscript: owner must be a non-empty string - the individual "
                      f"named in the volume's key ('Mr Jeremy Mason')")
    elif ow and (m.get("repository") or "") != "Private collection":
        errors.append(f"{where}.manuscript: owner is for a `Private collection` holding. An "
                      f"institution's name goes in `repository`, not here")
    rb = m.get("recorded_by")
    if rb is not None and not (isinstance(rb, str) and rb.strip()):
        errors.append(f"{where}.manuscript: recorded_by must be a non-empty string - who placed "
                      f"the document there, where that is not the work being quoted "
                      f"('Delaney, Charles Ricketts (1990)')")
    if m.get("as_of") is not None and not (isinstance(m["as_of"], str) and m["as_of"].strip()):
        errors.append(f"{where}.manuscript: as_of must be a non-empty string - when the holding "
                      f"was last attested ('9 February 1927'), where that is not the date of the "
                      f"edition citing it")
    u = m.get("url")
    if u is not None and (not isinstance(u, str) or not u.startswith(("http://", "https://"))):
        errors.append(f"{where}.manuscript: url must be an http(s) address, got {u!r}")
    if q.get("facsimile") is not None:
        errors.append(f"{where}: carries both a facsimile and a manuscript pointer - the "
                      f"facsimile already names the archive holding the pages it shows")


LETTER_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*/[A-Za-z0-9._:-]+(?:#\d+)?$")


def check_letter_id(q, where, errors):
    """`letter_id` / `letter_ids`: WHICH document is quoted. At most one of the two.

    A folio is not a letter - 53% of this volume's letter-bearing pages carry more than one - so
    the citation alone cannot say which, and the id is what joins a quotation to a manifest entry
    or a transcription of the same document.

    `letter_ids` is the plural, for the few records that quote two documents as one passage. It
    exists because splitting those records would destroy what they were written to show: two
    postcards sent on one day prove something neither proves alone. Carrying both fields would
    leave two answers to one question, so they are mutually exclusive.
    """
    one, many = q.get("letter_id"), q.get("letter_ids")
    if one is not None and many is not None:
        errors.append(f"{where}: carries both letter_id and letter_ids - use the plural alone "
                      f"when a record quotes more than one document, and the singular otherwise")
    if one is not None and (not isinstance(one, str) or not LETTER_ID.match(one)):
        errors.append(f"{where}: letter_id must read work/folio#ordinal, or archive then the "
                      f"archive's own page identifier ('letters-2000/1198#2', "
                      f"'hrc/MSS_WildeO_2_10_004'), got {one!r}")
    if many is not None:
        if not isinstance(many, list) or len(many) < 2:
            errors.append(f"{where}: letter_ids is for a record quoting two or more documents; "
                          f"with one, use letter_id")
        else:
            for v in many:
                if not isinstance(v, str) or not LETTER_ID.match(v):
                    errors.append(f"{where}.letter_ids: malformed id {v!r}")
            if len(set(many)) != len(many):
                errors.append(f"{where}.letter_ids: the same id twice - a record quoting one "
                              f"document once takes letter_id")


def check_document(q, where, errors):
    """`document` and `verified_against`: what is quoted, and whether the original was read.

    A quotation is nearly always read in something other than the thing it was written on - a
    letter in a printed edition of the letters, testimony in a trial transcript. `document` names
    the artifact when it differs from the work; a historian's own sentence leaves it unset,
    because there the work IS the document and a label would say nothing.

    `original_provenance` is the claim to have gone to that artifact rather than reading it where
    it was reprinted - and that is worth doing for a printed document as well as a written one. A
    copy carries what the printing does not: an inscription, marginalia, a correction, a cancelled
    leaf, a variant state. `inscription` is a document type here precisely because a hand-written
    mark in a printed book is a thing this map quotes.

    `verified_against_original` is the fact; `original_provenance` is the write-up. Either may
    arrive first, so only the write-up implies the fact.

    What the claim cannot survive is being made from a text layer, or being made where the work
    cited IS the document and there is no second thing to have read.
    """
    doc = q.get("document")
    if doc is None:
        errors.append(f"{where}: every source names its `document` - what kind of thing is being "
                      f"quoted. Where the work cited IS the document, say what the work is: a "
                      f"biography, a study, an article, an editorial note. One of "
                      f"{', '.join(sorted(DOCUMENTS))}")
    elif doc not in DOCUMENTS:
        errors.append(f"{where}: unknown document {doc!r} - one of "
                      f"{', '.join(sorted(DOCUMENTS))}")
    if q.get("verified_against") is not None:
        errors.append(f"{where}: `verified_against` was renamed - write "
                      f"`verified_against_original: true`, and put what you read at the document "
                      f"in `original_provenance`")
    va = q.get("verified_against_original")
    if va not in VERIFIED_AGAINST_ORIGINAL:
        errors.append(f"{where}: verified_against_original must be true or absent, got {va!r} - "
                      f"there is no false. A document nobody has opened simply does not carry it")
    elif va:
        if doc is None:
            errors.append(f"{where}: verified_against_original needs a `document` saying WHICH "
                          f"original was read")
        if q.get("how_verified") not in {"photo-reproduction", "in-hand"}:
            errors.append(f"{where}: verified_against_original but how_verified is "
                          f"{q.get('how_verified')!r} - reading the original means seeing it, in "
                          f"hand or as a photographic reproduction")
    mv = q.get("marks_verified")
    if mv not in MARKS_VERIFIED:
        errors.append(f"{where}: marks_verified must be true or absent, got {mv!r} - there is no "
                      f"false. A quotation nobody has collated simply does not carry the field")
    elif mv and q.get("how_verified") == "text-layer":
        errors.append(f"{where}: marks_verified with how_verified 'text-layer' - a text layer "
                      f"drops italics and accents, so it cannot be what the marks were checked "
                      f"against. This is how a whole postscript came to be marked as underlined")
    if not (q.get("original_provenance") or "").strip():
        return
    # One way only. Writing up what you saw at the document says you were there; being there does
    # not oblige you to have written it up yet.
    if not q.get("verified_against_original"):
        errors.append(f"{where}: `original_provenance` without `verified_against_original: true` "
                      f"- a note about what was read at the document says the document was read")
    if not (q.get("citation_provenance") or "").strip():
        errors.append(f"{where}: `original_provenance` with empty `citation_provenance` - the "
                      f"record still has to say where the passage sits in the work being cited")
    # The claim lives in its OWN field. Previously it rested on `citation_provenance`, which is about the
    # reprinting, and the rule could only look for a shelfmark inside prose - so "PDF pp.
    # 1070-1071." satisfied a claim about a manuscript, and a well-written note in other words
    # would have failed. A separate field cannot be satisfied by accident.
# Three answers to "where is this" that are not archives. They are what the question comes to
# when the document is a published work, a page on the web, or a unique object nobody has traced,
# and every source lands on one of them if it lands on no archive - so the filter has no residue
# left in it at all. Sorted below the archives in the browser, because they are not places.
DERIVED_LOCATION = {
    "published": {"short": "Published", "full": "Published work"},
    "online": {"short": "Online", "full": "Published on the web"},
    "unknown": {"short": "Unknown", "full": "Location unknown"},
}


def work_availability(wk):
    """Whether a copy of this WORK can be had, and how. Nothing to do with the document in it.

    A `-web` work is read where it is published and a library cannot get it for you. Everything
    with a publisher or a scan on the Internet Archive is a book somebody can borrow - the
    Internet Archive counts because it is evidence of publication, not because we would send a
    reader there, which matters for the one 1924 volume whose publisher we have not confirmed.
    What is left is genuinely unpublished: a lecture text, a personal communication.
    """
    wk = wk or {}
    if (wk.get("kind") or "").endswith("-web"):
        return "online"
    return "published" if (wk.get("publisher") or wk.get("ia_id")) else "unknown"


def resolve_location(q, archives, works):
    """Where the document is, in the one shape the card and the filter both read.

    A facsimile names an archive we hold a manifest for; a manuscript names a repository in
    prose. They are the same question asked twice by the corpus, so they get one answer here and
    the browser is spared knowing that.

    The SHORT form is what the filter groups on, deliberately: "Pierpont Morgan Library, New
    York" and "The Morgan Library & Museum, New York (MA 7258)" are one institution written two
    ways, and a reader asking what the Morgan holds means both.

    Where no archive is recorded the answer is derived, and which way round it goes depends on
    whether the document is its own object or is the work: an untraced letter is Unknown, and a
    biography is wherever the biography is. A recorded archive always wins, so tracing one
    later is the only edit needed.
    """
    f = q.get("facsimile")
    if isinstance(f, dict):
        arc = archives.get(f.get("archive")) or {}
        full = arc.get("name") or ""
        # The abbreviations table wins over the manifest's own short_name, so an archive that is
        # ALSO named as a repository by other records lands on one label and groups with them.
        short = REPOSITORY_SHORT.get(full) or arc.get("short_name") or short_repository(full)
        if short:
            return {"short": short, "full": full}
    m = q.get("manuscript")
    if isinstance(m, dict) and (m.get("repository") or "").strip():
        full = m["repository"].strip()
        out = {"short": short_repository(full), "full": full}
        # Carried through so the card can say what is actually in that repository. It rides on
        # the location rather than being read off `manuscript` in the browser for the same reason
        # the location does: one shape, resolved once, and the chip and the filter cannot drift.
        if m.get("archived_as"):
            out["archived_as"] = m["archived_as"]
        if m.get("as_of"):
            out["as_of"] = m["as_of"]
        if m.get("recorded_by"):
            out["recorded_by"] = m["recorded_by"]
        if m.get("owner"):
            out["owner"] = m["owner"]
        return out
    kind = DOCUMENTS.get(q.get("document"))
    if kind and kind[1] == UNIQUE:
        return dict(DERIVED_LOCATION["unknown"])
    return dict(DERIVED_LOCATION[work_availability(works.get(q.get("work")))])


def resolve_facsimile(q, archives):
    """Reduce a source's facsimile to the reference the browser can resolve, or drop it.

    Deliberately NOT expanded here. The page records - file, shelfmark, pointer, rights - go into
    the bundle once, under `archives`, and a source keeps nothing but the item and the page
    numbers. Expanding them into each source instead would copy the same records into every
    quotation from the same letter, and the reader needs the WHOLE folder available anyway to
    page past the letter's own sheets.
    """
    f = q.get("facsimile")
    if not isinstance(f, dict):
        return None
    arc = archives.get(f.get("archive")) or {}
    item = (arc.get("items") or {}).get(str(f.get("item"))) or {}
    have = {p["n"] for p in item.get("pages") or []}
    pages = [n for n in (f.get("pages") or []) if n in have]
    if not pages:
        return None
    out = {"archive": f["archive"], "item": str(f["item"]), "pages": pages}
    if (f.get("caption") or "").strip():
        out["caption"] = f["caption"].strip()
    return out


def date_sort_key(d):
    return (d.get("y") or 0, d.get("m") or 0, d.get("d") or 0)


# What a date object may contain, and nothing else. `check_date` used to reject only
# year/month/day, so any other key - a typo'd `dd`, a `mm` - passed silently on all 1037 dates in
# the corpus and sorted wrong forever. The vocabulary is one vocabulary: `circa` is spelled that
# way because 138 dates already use it and the browser already prints it "c.".
#
#   y m d      as far as the source goes
#   t          time, 24-hour "HH:MM", normalised so it sorts; the wording it came from is gone
#   weekday    a day-name the WRITER gave, which is evidence even when the date is a guess
#   part       early | mid | late - a part of the month
#   season     instead of a month
#   circa      approximately
#   uncertain  the editors' question mark
#   inferred   the document does not bear this date; somebody worked it out.
#              Names no agent on purpose - it may be the edition's editors, a
#              biographer, or us, dating a letter from its own contents
#   to label   a range, and the escape hatch for what a date object cannot say
DATE_FIELDS = {"y", "m", "d", "t", "weekday", "part", "season",
               "circa", "uncertain", "inferred", "to", "label"}
DATE_PARTS = {"early", "mid", "late"}
DATE_SEASONS = {"spring", "summer", "autumn", "winter"}
# Lowercase like every other enum here. English capitalises a day-name; that is the
# renderer's business, not the record's.
WEEKDAY_ORDER = ["monday", "tuesday", "wednesday", "thursday", "friday",
                 "saturday", "sunday"]
WEEKDAYS = set(WEEKDAY_ORDER)
TIME_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


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
    unknown = set(d) - DATE_FIELDS - {"why"}
    if unknown:
        errors.append(f"{where}: date has unknown field(s) {sorted(unknown)}. A date carries "
                      f"{', '.join(sorted(DATE_FIELDS))} - anything else is a typo that would "
                      f"sort wrong in silence")
    if d.get("part") is not None and d["part"] not in DATE_PARTS:
        errors.append(f"{where}: part is {', '.join(sorted(DATE_PARTS))}, got {d['part']!r}")
    if d.get("season") is not None and d["season"] not in DATE_SEASONS:
        errors.append(f"{where}: season is {', '.join(sorted(DATE_SEASONS))}, "
                      f"got {d['season']!r}")
    wd = d.get("weekday")
    if wd is not None and wd not in WEEKDAYS:
        errors.append(f"{where}: weekday is one of "
                      f"{', '.join(sorted(WEEKDAYS, key=WEEKDAY_ORDER.index))} - the day-name "
                      f"the writer gave, spelled out. Got {wd!r}")
    # Where the date is complete the weekday can be checked against the calendar, and a clash is
    # worth stopping for. Usually it is a slip in transcription. Occasionally it is a real
    # finding: the writer wrote "Tuesday", the editors supplied a date, and the date they chose
    # was not a Tuesday - which is the editors being wrong, and worth saying out loud rather
    # than storing a contradiction in silence. Six of the seven weekdays on this map are
    # checkable and all six agree, four of them on dates the editors supplied.
    elif wd and all(isinstance(d.get(k), int) for k in ("y", "m", "d")):
        try:
            real = calendar.day_name[calendar.weekday(d["y"], d["m"], d["d"])].lower()
        except ValueError:
            real = None
        if real and real != wd:
            errors.append(f"{where}: weekday says {wd!r} but "
                          f"{d['d']}/{d['m']}/{d['y']} was a {real}. Either the transcription "
                          f"slipped, or the date the editors supplied contradicts the day-name "
                          f"the writer gave - which is a finding, and belongs in "
                          f"`transcription_note` with the weekday dropped")
    if d.get("t") is not None and not (isinstance(d["t"], str) and TIME_HHMM.match(d["t"])):
        errors.append(f"{where}: t is a 24-hour time, \"HH:MM\" - normalised so it sorts, with "
                      f"the source's own wording nowhere near it. Got {d.get('t')!r}")
    for flag in ("circa", "uncertain", "inferred"):
        if flag in d and d[flag] is not True:
            errors.append(f"{where}: {flag} is true or absent - there is no false, an absent "
                          f"flag already says so. Got {d[flag]!r}")
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
# This is a LITERAL LIST of the markers actually in the corpus, not a rule for spotting them:
# Hyde uses the same em dash inside answers, so a general pattern reads "Men—young men from
# sixteen to thirty" as a speaker called Men, and "examined by Mr. Avory—" as Avory speaking
# words that are in fact the witness's. Four transcripts use this convention; a fifth fails the
# check loudly and is added here once somebody has read it.
TURN_ATTRIB = re.compile(r"(?:The Clerk of Arraigns|The Foreman|Mr\. Justice Wills)—")


def check_turns(q, where, errors):
    """A court record MAY be displayed as a transcript, and the transcript has to BE the quotation.

    The rows are split from the quoted text by a heuristic over two printing conventions, then read
    and corrected by hand, so the risk is not that the splitter fails loudly - it is that a row
    quietly drops or reworks a few words and the card then shows something the source does not say.
    So the turns are checked against the quotation itself: strip the markers that carry a change of
    speaker (a name label, or the dash after a question) and what remains must match exactly.
    """
    turns = q.get("turns")
    voice = q.get("voice")
    if voice != "court":
        if turns:
            errors.append(f"{where}: has `turns` but voice is {voice!r} - turns are for a court "
                          f"record set out as a transcript")
        return
    if not turns:
        # A plea or a verdict is continuous prose in one voice. Only a genuine question-and-answer
        # needs splitting, and demanding turns of everything is what produced pleas carrying a
        # single invented turn attributed to Queensberry.
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


def validate_quote(q, where, works, errors, warnings=None, archives=None):
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
    if v in {"verified-exact", "verified-elision"} and not (q.get("citation_provenance") or "").strip():
        errors.append(f"{where}: verified quote with empty citation_provenance")
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
    check_facsimile(q, where, archives if archives is not None else {}, errors, warnings)
    check_manuscript(q, where, errors)
    check_letter_id(q, where, errors)
    if q.get("addressee") is not None:
        if not isinstance(q["addressee"], str) or not q["addressee"].strip():
            errors.append(f"{where}: addressee must be a name, or absent - use null/omit when the "
                          f"source does not say who was being addressed")
        elif q.get("voice") not in ("period", "court"):
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
    # past both. Ask the question the other way round: does this look like it is not in English?
    if not lang and (q.get("quote") or "").strip():
        if re.search(r"\bTranslation:\s*['\"‘“]", q.get("context") or ""):
            errors.append(f"{where}: the context carries a labelled translation. A translation goes "
                          f"in `translation` with `lang` set, or the page never shows it")
        guess, hits, words = _guess_foreign(q["quote"])
        if guess:
            warnings.append(f"{where}: reads like {guess} ({hits} function words in {words}) but "
                            f"has no `lang`. Set lang and add a translation, or ignore this if the "
                            f"quotation really is English")
    # Emphasis markup in the quoted text: *italics*, **bold**, _underline_,
    # ~~strikethrough~~. The renderer pairs the markers after escaping, so an odd
    # marker would print literally - an unbalanced pair is a data error, not a
    # rendering choice.
    for _fld, _txt in ([("quote", q.get("quote") or "")] +
                       [("translation", q.get("translation") or "")] +
                       [(f"turns[{_i}].text", (t.get("text") or ""))
                        for _i, t in enumerate(q.get("turns") or [])]):
        if not _txt:
            continue
        # Markers NEST: `_*Salome*_` is a title Wilde underlined, italic inside underline. Each
        # matched pair collapses to a placeholder rather than to nothing, exactly as the renderer
        # leaves HTML behind - strip to "" instead and the inner pair hands the outer one an
        # empty `__`, which then reads as a stray marker and fails a sound quotation.
        _t = _txt
        for _pat in (r"\*\*[^*\n]+\*\*", r"\*[^*\n]+\*",
                     r"__[^_\n]+__", r"_[^_\n]+_",     # __ before _, as the renderer does
                     r"~~[^~\n]+~~"):
            _t = re.sub(_pat, "x", _t)
        if re.search(r"[*_~]", _t):
            errors.append(f"{where}.{_fld}: unbalanced emphasis marker - use *italics*, "
                          f"**bold**, _underline_, __double underline__, ~~strikethrough~~ "
                          f"in pairs (they may nest: _*Title*_ is an underlined title)")
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


def validate(works, people, rels, archives=None):
    archives = archives if archives is not None else {}
    errors, warnings = [], []
    # `kind` used to be free text nothing read, so a typo cost nothing. It now decides whether a
    # source with no archive of its own is reported as Published or as Online, and a misspelled
    # "-web" would quietly send a web page to the shelves.
    for wid, wk in works.items():
        if (wk or {}).get("kind") not in WORK_KINDS:
            errors.append(f"works.json {wid}: unknown kind {(wk or {}).get('kind')!r} - one of "
                          f"{', '.join(sorted(WORK_KINDS))}")
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
        for ce in p.get("sexuality_sources", []) or []:
            if not (ce.get("subject") or "").strip():
                errors.append(f"{pid}: sexuality_source missing subject")
            if "name" in ce:
                errors.append(f"{pid}: sexuality_source uses 'name'; the field is 'subject'")
            for q in ce.get("sources", []) or []:
                validate_quote(q, f"{pid}.sexuality[{ce.get('subject')}]", works, errors,
                               warnings, archives)

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
            validate_quote(q, rid, works, errors, warnings, archives)

    orphans = pids - {p for r in rels if "__load_error__" not in r for p in r.get("people", [])}
    for o in sorted(orphans):
        warnings.append(f"{o}: on the roster but in no relationship")

    # THE SAME EXCERPT TWICE IN ONE FILE, or on both a person and their own connection. One source
    # legitimately evidences several DIFFERENT connections - the letter naming Raphael and Fortune
    # is cited on both, and the panel collapses them at render time - but the same excerpt repeated
    # inside a single record, or on a person AND a connection they are party to, is duplication with
    # nothing to distinguish it.
    def _qkey(q):
        return (q.get("work"), q.get("locator"),
                re.sub(r"\W+", " ", (q.get("quote") or "")).strip().lower())

    for holder, sources in ([(r.get("id", "?"), r.get("sources") or []) for r in rels] +
                            [(f"{p.get('id','?')}.context[{ce.get('subject','?')}]",
                              ce.get("sources") or [])
                             for p in people for ce in p.get("sexuality_sources") or []]):
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
        for ce in p.get("sexuality_sources") or []:
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
    out = ROOT / "audits" / "QUOTE-AUDIT_web.md"
    out.parent.mkdir(exist_ok=True)
    lines = ["# Quote audit — Wilde's Web", "",
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


# Syntax highlighting is done HERE, at build time, for the same reason the markdown is: the site
# ships one script and no toolchain, and a highlighter is a lot of bytes to send every reader so
# that eight code samples can have coloured comments. The scanner is deliberately shallow - it
# knows comments, strings, keys, numbers and keywords, and nothing about grammar - because that is
# all these samples need. An unrecognised language is escaped and left plain rather than guessed at.
JSONC_TOK = re.compile(r"""
      (?P<str>"(?:[^"\\]|\\.)*")
    | (?P<com>//[^\n]*)
    | (?P<num>-?\b\d+(?:\.\d+)?\b)
    | (?P<kw>\b(?:true|false|null)\b)
""", re.X)
SH_TOK = re.compile(r"""
      (?P<com>\#[^\n]*)
    | (?P<str>'[^']*'|"(?:[^"\\]|\\.)*")
    | (?P<flag>(?<![\w-])--?[A-Za-z][\w-]*)
""", re.X)


def highlight(code, lang):
    """Wrap the tokens of one code sample in spans. Returns escaped HTML either way."""
    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    lang = (lang or "").strip().lower()
    if lang in ("json", "jsonc"):
        rx, first_word = JSONC_TOK, False
    elif lang in ("bash", "sh", "shell", "console"):
        rx, first_word = SH_TOK, True
    else:
        return esc(code)
    out, pos = [], 0
    for m in rx.finditer(code):
        out.append(esc(code[pos:m.start()]))
        kind = m.lastgroup
        text = m.group()
        # A JSON string followed by a colon is a key, not a value, and the two want to look
        # different - that is most of what makes a sample readable at a glance.
        if kind == "str" and rx is JSONC_TOK and code[m.end():].lstrip(" \t").startswith(":"):
            kind = "key"
        out.append(f'<span class="t-{kind}">{esc(text)}</span>')
        pos = m.end()
    out.append(esc(code[pos:]))
    html = "".join(out)
    if first_word:
        # The command itself, once per line, so `python` reads as the verb it is.
        html = re.sub(r"(?m)^(\s*)([\w./-]+)", r'\1<span class="t-cmd">\2</span>', html)
    return html

def md_html(src):
    """Compile one of the site's markdown documents into the HTML a panel shows.

    Compiled here rather than parsed in the browser: the site's bargain is one script and no
    toolchain, and shipping a markdown parser to every reader to render two static documents
    would be a poor trade. `python tools/validate.py` already has to run before the site is
    served, so this costs nothing new.

    The subset is only as large as the two documents need - headings, paragraphs, bullets, bold,
    italic, links, and for CONTRIBUTING.md also fenced code, tables, rules and inline code. Two
    placeholders survive into the HTML for the page to fill in: {{line:<certainty>}} becomes the
    real connection line, drawn from the same definitions the legend uses, and {{colophon}} becomes
    the generated build line.
    """
    if not src.exists():
        return ""
    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    def inline(s):
        s = esc(s)
        # Code spans first, and their contents are held out of every rule below, so that a path
        # like `docs/**/*.json` cannot have its asterisks read as emphasis.
        spans = []
        def hold(m):
            spans.append(m.group(1))
            return f"\x00{len(spans) - 1}\x00"
        s = re.sub(r"`([^`]+)`", hold, s)
        
        # Restore <br> tags so multiline table cells work. Doing this after 'hold' 
        # ensures `<br>` inside code backticks stays safely escaped as &lt;br&gt;
        s = re.sub(r"(?i)&lt;br\s*/?&gt;", "<br>", s)

        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
                   r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
        # Autolinks: <https://example.com> survives escaping as &lt;https://…&gt;.
        s = re.sub(r"&lt;(https?://[^\s&]+)&gt;",
                   r'<a href="\1" target="_blank" rel="noopener">\1</a>', s)
        # Both spellings of emphasis: a markdown formatter rewrites *this* to _this_ whenever it
        # runs over ABOUT.md, so both must be read.
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"(?<![A-Za-z0-9_])__(.+?)__(?![A-Za-z0-9_])", r"<b>\1</b>", s)
        s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", s)
        # ...but the underscore form only between word boundaries, or `evidence_date` and
        # `order_hint` - ordinary words here - would come out with their middles in italics.
        s = re.sub(r"(?<![A-Za-z0-9_])_([^_\n]+)_(?![A-Za-z0-9_])", r"<i>\1</i>", s)
        return re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{spans[int(m.group(1))]}</code>", s)

    out, ul, ol, fence, fence_lang, table, para = [], False, False, None, "", [], []
    def close_para():
        """Consecutive prose lines are ONE paragraph, as markdown says. ABOUT.md happens to keep
        each paragraph on a single line, so splitting per line looked right until CONTRIBUTING.md
        arrived soft-wrapped and broke sentences in half mid-clause."""
        if not para:
            return
        line = " ".join(para)
        para.clear()
        # The subtitle is a whole paragraph in italics, in either spelling.
        wrapped = ((line.startswith("*") and line.endswith("*") and not line.startswith("**"))
                   or (line.startswith("_") and line.endswith("_") and not line.startswith("__")))
        cls = ' class="sub" style="font-style:italic"' if wrapped else ""
        body = inline(line[1:-1]) if cls else inline(line)
        out.append(f"<p{cls}>{body}</p>")
        
    def close_lists():
        nonlocal ul, ol
        close_para()
        if ul:
            out.append("</ul>")
            ul = False
        if ol:
            out.append("</ol>")
            ol = False
            
    def close_table():
        """A markdown table becomes a real table; the alignment row is dropped, not rendered."""
        if not table:
            return
        rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in table]
        body = [r for r in rows[1:] if not all(re.fullmatch(r":?-{2,}:?", c) for c in r)]
        cells = "".join(f"<th>{inline(c)}</th>" for c in rows[0])
        out.append(f"<table><thead><tr>{cells}</tr></thead><tbody>")
        for r in body:
            out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
        out.append("</tbody></table>")
        table.clear()

    for raw in src.read_text(encoding="utf-8").replace("{{repo}}", REPO).splitlines():
        line = raw.rstrip()
        # Inside a fence every line is literal, including blanks and anything that looks like syntax.
        if fence is not None:
            if line.startswith("```"):
                body = highlight("\n".join(fence), fence_lang)
                cls = f' class="lang-{fence_lang}"' if fence_lang else ""
                out.append(f"<pre><code{cls}>{body}</code></pre>")
                fence = None
            else:
                fence.append(line)
            continue
        if line.startswith("```"):
            close_lists(); close_table()
            fence, fence_lang = [], re.sub(r"[^a-z]", "", line[3:].strip().lower())
            continue
        if line.lstrip().startswith("|") and line.rstrip().endswith("|"):
            close_lists(); table.append(line)
            continue
        close_table()
        
        # A bullet continued on the next line belongs to that bullet, not to a new paragraph.
        if (ul or ol) and para == [] and raw[:1].isspace() and line.strip() and out and out[-1].endswith("</li>"):
            out[-1] = out[-1][:-5] + " " + inline(line.strip()) + "</li>"
            continue
            
        if not line.strip():
            close_lists(); continue
        if line.strip() in ("---", "***", "___"):
            close_lists(); out.append("<hr>")
        elif line.startswith("### "):
            close_lists(); out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            close_lists(); out.append(f'<div class="sect">{inline(line[3:])}</div>')
        elif line.startswith("# "):
            close_lists(); out.append(f"<h2>{inline(line[2:])}</h2>")
        elif line.startswith("- "):
            close_para()
            if ol:
                out.append("</ol>"); ol = False
            if not ul:
                out.append("<ul>"); ul = True
            body = line[2:]
            # A bullet that opens with a line sample IS the sample - no disc as well.
            # NOT "lrow" - that is the All-relationships list's row button, and About renders
            # into the same panel on desktop, so the two would share a stylesheet rule.
            cls = ' class="lkey"' if body.startswith("{{line:") else ""
            out.append(f"<li{cls}>{inline(body)}</li>")
        elif re.match(r"^\d+\.\s+", line):
            close_para()
            if ul:
                out.append("</ul>"); ul = False
            if not ol:
                out.append("<ol>"); ol = True
            body = line.split(maxsplit=1)[1]
            cls = ' class="lkey"' if body.startswith("{{line:") else ""
            out.append(f"<li{cls}>{inline(body)}</li>")
        elif line.strip() == "{{colophon}}":
            close_lists(); out.append('<p id="colophon"></p>')
        else:
            para.append(line.strip())
            
    close_lists()
    close_table()
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
    archives = load_archives()

    errors, warnings = validate(works, people, rels, archives)
    # Loaded after the sources so its own errors join theirs and one run reports everything.
    scanned = check_control_characters(errors)
    transcriptions = load_transcriptions(
        errors, [p for p in people if "__load_error__" not in p])
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
    # Facsimiles are resolved in place: every source that cites scanned pages carries its files,
    # shelfmarks and rights by the time the browser sees it. `archives` then holds only what a
    # facsimile cannot say for itself - who holds the papers, and how to reach their own record.
    kept_rels = [r for r in rels if "__load_error__" not in r]
    kept_people = [p for p in people if "__load_error__" not in p]
    fac_count = 0
    for sources in ([r.get("sources") or [] for r in kept_rels] +
                    [ce.get("sources") or [] for p in kept_people
                     for ce in p.get("sexuality_sources") or []]):
        for q in sources:
            if q.get("facsimile") is None:
                continue
            resolved = resolve_facsimile(q, archives)
            if resolved:
                q["facsimile"] = resolved
                fac_count += 1
            else:
                q.pop("facsimile", None)

    # Where the document is, resolved once for every source rather than twice in the browser.
    # Runs over ALL sources, not only the ones with a facsimile: most say where the original is
    # through `manuscript` instead, and the rest get the derived answer.
    loc_count = 0
    for sources in ([r.get("sources") or [] for r in kept_rels] +
                    [ce.get("sources") or [] for p2 in kept_people
                     for ce in p2.get("sexuality_sources") or []]):
        for q in sources:
            loc = resolve_location(q, archives, works)
            if loc:
                q["location"] = loc
                if loc["short"] not in ("Published", "Online", "Unknown"):
                    loc_count += 1

    # Archives that nothing cites are still bundled whole. The scans are published, and the
    # reader lets you walk out of a quoted letter into the folder it is kept in - which is only
    # possible if the browser holds the folder's page list, not just the cited sheets.
    #
    # An archive with no `iiif_url` is left OUT: with no image service there is nothing to walk
    # into, so shipping its page list to every visitor buys a reader nothing. All the manifests
    # live here now, including ones for material held only as a private reference copy, and
    # marland-blog alone is 97 items.
    arc_meta = {k: a for k, a in archives.items()
                if "__load_error__" not in a and (a.get("iiif_url") or "").strip()}

    # ---- the transcriptions the map cites, and only those ------------------------------------
    # A separate file rather than a key in the bundle: most readers never open a letter, and this
    # is the one part of the corpus that grows without bound as the reading checklist is worked
    # through. Fetched on demand.
    #
    # THE GATE. Everything read from the printed edition is private; what crosses is the letters
    # this map quotes, each one selected because a card carries an excerpt of it and a reader may
    # need the rest to judge the excerpt. Derived from the citations, never curated - the one time
    # two copies of anything here were kept in step by hand they needed a script to police them.
    cited = set()
    for sources in ([r.get("sources") or [] for r in kept_rels] +
                    [ce.get("sources") or [] for p2 in kept_people
                     for ce in p2.get("sexuality_sources") or []]):
        for q in sources:
            if q.get("letter_id"):
                cited.add(q["letter_id"])
            cited.update(q.get("letter_ids") or [])
    public = {k: {f: v for f, v in t.items() if f != "at"}
              for k, t in transcriptions.items() if k in cited}
    # Leakage is a build failure, not something anybody has to remember. By construction nothing
    # uncited is here; the assertion is what keeps that true after somebody edits the loop above.
    leaked = sorted(k for k, t in public.items()
                    if k not in cited and t.get("transcribed_from") == "printed")
    if leaked:
        sys.exit(f"REFUSING TO WRITE: {len(leaked)} transcription(s) from the printed edition "
                 f"that nothing cites would have been published — {', '.join(leaked[:5])}")
    tout = DATA / "transcriptions.json"
    tout.write_text(json.dumps({"letters": public}, ensure_ascii=False,
                               separators=(",", ":")) + "\n", encoding="utf-8")

    bundle = {"people": kept_people,
              "relationships": kept_rels,
              "works": works, "portraits": portraits, "archives": arc_meta,
              # Ids only. A card has to decide whether to offer "read the whole letter" while it
              # is being drawn, and drawing happens on every filter keystroke; the letters
              # themselves are a separate fetch made once, on the first click.
              "transcribed": sorted(public),
              "about": md_html(ROOT / "ABOUT.md"),
              "contributing": md_html(ROOT / "CONTRIBUTING.md"),
              "built": date.today().isoformat()}
    out = DATA / "web.json"
    out.write_text(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")) + "\n",
                   encoding="utf-8")
    print(f"\nwrote {out.relative_to(ROOT)} ({out.stat().st_size/1024:.0f} KB) — "
          f"generated, do not hand-edit")
    if archives:
        pages = sum(len(i["pages"]) for a in archives.values() if "__load_error__" not in a
                    for i in a["items"].values())
        print(f"{pages} manuscript pages indexed in {len(arc_meta)} archive(s); "
              f"{fac_count} source(s) show a facsimile, {loc_count} name where the document is")
    held = len(transcriptions)
    from_ed = sum(1 for t in transcriptions.values() if t["transcribed_from"] == "printed")
    print(f"{scanned} text files scanned for stray control characters")
    waiting = sorted(k for k, t in transcriptions.items()
                     if t["transcribed_from"] == "printed" and k not in cited)
    if waiting:
        print(f"{len(waiting)} edition transcription(s) cite-less and therefore unpublished - "
              f"expected while the reading runs ahead of the map, worth a look if it climbs")
    print(f"wrote {tout.relative_to(ROOT)}: {len(public)} of {len(cited)} cited letters have a "
          f"full text ({held} transcribed in all, {from_ed} from the printed edition and private "
          f"unless cited)")


main()
