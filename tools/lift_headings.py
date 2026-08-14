#!/usr/bin/env python3
"""Lift the volume's dateline and address out of each letter's quote.

Each transcription in transcriptions/letters-2000/ holds the full text of one
letter from the Complete Letters, with the volume's dateline and address sitting
at the head of the `quote` string. This tool parses that heading into the
structured acts (`written`, `postmarked`, `sent`, `received`) the map reads, and
trims the quote to begin at the salutation (or the first word of the letter's
text where there is no salutation).

The run is resumable: a file that already carries a date on any of the four
acts is treated as done and skipped, and each file is written before the next
is looked at.

    python tools/lift_headings.py --review     print what would change, write nothing
    python tools/lift_headings.py --apply      write the files

A heading the parser cannot resolve with confidence is FLAGGED and left alone,
so that a human resolves the list rather than a wrong date sorting silently.

Special cases carried in SPECIAL_HEADINGS: transcriptions whose head the OCR
lost entirely (the printed volume dates them, confirmed against the page
images), a postscript dated by its parent letter, three transcribed year
typos where the OCR glued a footnote digit onto the year (confirmed against the
printed pages: 26 February 1892, 8 May 1895, 5 April 1895, 7 October 1899),
a transcription that duplicated the petit bleu's first line (1166-3), and
0877-1 whose joke heading spans two paragraphs.
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # .../wilde/web
WILDE = ROOT.parent                                    # .../wilde
TRANSCRIPTIONS = WILDE / "transcriptions" / "letters-2000"
PLACES_FILE = ROOT / "data" / "places.json"

ACTS = ("written", "postmarked", "sent", "received")

# ---------------------------------------------------------------------------
# Date vocabulary
# ---------------------------------------------------------------------------
MONTHS = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5,
    "juin": 6, "juillet": 7, "août": 8, "aout": 8, "septembre": 9,
    "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
}
WEEKDAYS = {
    "monday": "monday", "tuesday": "tuesday", "wednesday": "wednesday",
    "thursday": "thursday", "friday": "friday", "saturday": "saturday",
    "sunday": "sunday",
    "lundi": "monday", "mardi": "tuesday", "mercredi": "wednesday",
    "jeudi": "thursday", "vendredi": "friday", "samedi": "saturday",
    "dimanche": "sunday",
}
SEASONS = {"spring": "spring", "summer": "summer", "autumn": "autumn",
           "fall": "autumn", "winter": "winter"}
PARTS = {"early": "early", "mid": "mid", "late": "late", "end": "late"}

ROMAN_DAY = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8,
    "IX": 9, "X": 10, "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
    "XVI": 16, "XVII": 17, "XVIII": 18, "XIX": 19, "XX": 20, "XXI": 21,
    "XXII": 22, "XXIII": 23, "XXIV": 24, "XXV": 25, "XXVI": 26, "XXVII": 27,
    "XXVIII": 28, "XXIX": 29, "XXX": 30, "XXXI": 31,
}

_MONTH_RE = "|".join(sorted(MONTHS, key=len, reverse=True))
_DAY_RE = r"\d{1,2}(?:st|nd|rd|th)?"
_YEAR_RE = r"(?:18|19|20)\d\d"

MONTH_TOKEN_RE = re.compile(rf"^({_MONTH_RE})\b", re.I)
YEAR_TOKEN_RE = re.compile(rf"^({_YEAR_RE})\b")
PART_TOKEN_RE = re.compile(r"^(early|mid-?|late|end)\b", re.I)
SEASON_TOKEN_RE = re.compile(rf"^({'|'.join(SEASONS)})\b", re.I)
WEEKDAY_TOKEN_RE = re.compile(
    r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|"
    r"Lundi|Mardi|Mercredi|Jeudi|Vendredi|Samedi|Dimanche)\b", re.I)
WEEKDAY_SUFFIX = re.compile(
    r"^(?:night|evening|morning|afternoon|noon|midnight)\b", re.I)

# am/pm may be printed "p.m.", "p.m" or "pm"; the trailing period is part of
# the token when followed by whitespace or end of line.
_AMPM = r"(?:a\.?m\.?|p\.?m\.?)"
AMPM_RE = re.compile(rf"^{_AMPM}(?=\s|\.\s|$|\.$)", re.I)
OCLOCK_RE = re.compile(
    rf"^(\d{{1,2}})\s+o'?clock\s+({_AMPM})(?=\s|\.\s|$|\.$)", re.I)
TIME_RE = re.compile(r"^(\d{1,2})[.](\d{2})(?:\s+o'?clock\b)?")


def eat(s):
    return re.sub(r"^[\s,;.:–—-]+", "", s)


def parse_day(s):
    """A day number (or roman) at the start of s. Returns (day, rest)."""
    s = eat(s)
    m = re.match(rf"^({_DAY_RE}|[IVXLC]+)(?=\b|$)", s)
    if not m:
        return None, s
    tok = m.group(1)
    if tok.isdigit():
        d = int(tok)
        rest = s[m.end():]
        # a bare year must not be read as a day: "1876" is a year, not 18 + 76
        if rest[:1].isdigit():
            return None, s
        return d, rest
    d = ROMAN_DAY.get(tok)
    return (d, s[m.end():]) if d else (None, s)


def parse_month(s):
    m = MONTH_TOKEN_RE.match(eat(s))
    return (MONTHS[m.group(1).lower()], eat(s)[m.end():]) if m else (None, s)


def parse_year(s):
    m = YEAR_TOKEN_RE.match(eat(s))
    return (int(m.group(1)), eat(s)[m.end():]) if m else (None, s)


def parse_part(s):
    m = PART_TOKEN_RE.match(eat(s))
    if not m:
        return None, s
    return PARTS[m.group(1).lower().rstrip("-")], eat(s)[m.end():]


def parse_season(s):
    m = SEASON_TOKEN_RE.match(eat(s))
    return (SEASONS[m.group(1).lower()], eat(s)[m.end():]) if m else (None, s)


def parse_weekday(s):
    es = eat(s)
    m = WEEKDAY_TOKEN_RE.match(es)
    if not m:
        return None, s
    wd = WEEKDAYS[m.group(1).lower()]
    rest = es[m.end():]
    m2 = WEEKDAY_SUFFIX.match(eat(rest))
    if m2:
        rest = eat(rest)[m2.end():]
    return wd, rest


def parse_time(s):
    """A clock time at the start of s. Returns (raw, "HH:MM" or None, rest)."""
    s = eat(s)
    m = OCLOCK_RE.match(s)
    if m:
        hh, ampm = int(m.group(1)), m.group(2)
        rest = s[m.end():]
        if rest[:1] == ".":
            rest = eat(rest[1:])
        hh = hh + 12 if ampm.lower().startswith("p") and hh < 12 else hh
        hh = 0 if ampm.lower().startswith("a") and hh == 12 else hh
        return m.group(0).strip(), f"{hh:02d}:00", rest
    m = TIME_RE.match(s)
    if not m:
        return None, None, s
    hh, mm = int(m.group(1)), int(m.group(2))
    if not (0 <= mm <= 59) or hh > 12:
        return None, None, s
    rest = eat(s[m.end():])
    m2 = AMPM_RE.match(rest)
    if m2:
        ampm = m2.group(0)
        rest = rest[m2.end():]
        if rest[:1] == ".":
            rest = eat(rest[1:])
        hh24 = hh + 12 if ampm.lower().startswith("p") and hh < 12 else hh
        hh24 = 0 if ampm.lower().startswith("a") and hh == 12 else hh24
        return f"{m.group(0).strip()} {ampm.strip()}", f"{hh24:02d}:{mm:02d}", rest
    return m.group(0).strip(), None, rest


# ---------------------------------------------------------------------------
# Date core: a token loop that accepts the parts in any order
# ---------------------------------------------------------------------------
def _flag(reason):
    return None, None, reason


def _finish(date, circa, uncertain, bound):
    if circa:
        date["circa"] = True
    if uncertain:
        date["uncertain"] = True
    if bound:
        date["bound"] = bound
    return date


BRACKET_DAY = re.compile(r"^\[\s*\??\s*(\d{1,2})(?:st|nd|rd|th)?\s*\]")
BRACKET_NAME = re.compile(r"^\[\s*\??\s*([A-Za-z]+)\s*(?:(\d{4}))?\s*\]")
BRACKET_ACTUALLY_D = re.compile(
    r"^\[\s*actually\s+(\d{1,2})(?:st|nd|rd|th)?\s*\]", re.I)
BRACKET_ACTUALLY_M = re.compile(
    r"^\[\s*actually\s+([A-Za-z]+)\s*\]", re.I)
DAY_RANGE = re.compile(
    rf"^({_DAY_RE})\s*[-–]\s*({_DAY_RE})\s+({_MONTH_RE})\b", re.I)


def parse_date_core(s, uncertain=False):
    """Parse one date expression from the start of s.

    Returns (date_dict, rest, flag_reason). Non-None flag_reason means the
    expression is ambiguous and must go to a human.
    """
    s0 = s
    circa = False
    m = re.match(r"^(?:Circa|c\.)\s*", s, re.I)
    if m:
        circa = True
        s = s[m.end():]
    bound = None
    m = re.match(r"^Week ending\b", s, re.I)
    if m:
        bound = "not-later-than"
        s = s[m.end():]
    m = re.match(r"^By hand\.?\s*", s, re.I)
    if m:
        s = s[m.end():]
    m = re.match(r"^AD\b\s*", s, re.I)
    if m:
        s = s[m.end():]

    # ranges and alternatives are a human's call
    m = re.match(rf"^Between\s+{_DAY_RE}\s+and\s+{_DAY_RE}\b", s, re.I)
    if m:
        return _flag(f"between-and range: {s0!r}")
    m = re.match(rf"^({_DAY_RE})\s+or\s+({_DAY_RE})\s+({_MONTH_RE})\b", s, re.I)
    if m:
        return _flag(f"two alternative days: {s0!r}")
    m = re.match(rf"^({_MONTH_RE})\s+or\s+({_MONTH_RE})\b", s, re.I)
    if m:
        return _flag(f"two alternative months: {s0!r}")
    if DAY_RANGE.match(s):
        return _flag(f"day range: {s0!r}")

    date = {}
    s = eat(s)
    guard = 0
    while s and guard < 12:
        guard += 1
        before = s
        s = eat(s)
        if re.match(r"^(or|to)\b", s, re.I):
            return _flag(f"alternative/range word: {s0!r}")
        if re.match(r"^and\b", s, re.I):
            break
        m = BRACKET_DAY.match(s)
        if m and "d" not in date:
            date["d"] = int(m.group(1))
            s = eat(s[m.end():])
            continue
        m = BRACKET_NAME.match(s)
        if m:
            name, yr = m.group(1).lower(), m.group(2)
            if name in MONTHS and "m" not in date:
                date["m"] = MONTHS[name]
                if yr:
                    date.setdefault("y", int(yr))
                s = eat(s[m.end():])
                continue
            if name in SEASONS and "season" not in date:
                date["season"] = SEASONS[name]
                if yr:
                    date.setdefault("y", int(yr))
                s = eat(s[m.end():])
                continue
        m = BRACKET_ACTUALLY_D.match(s)
        if m:
            date["d"] = int(m.group(1))
            s = eat(s[m.end():])
            continue
        m = BRACKET_ACTUALLY_M.match(s)
        if m and m.group(1).lower() in MONTHS:
            date["m"] = MONTHS[m.group(1).lower()]
            s = eat(s[m.end():])
            continue
        if "weekday" not in date:
            wd, s2 = parse_weekday(s)
            if wd:
                date["weekday"] = wd
                s = s2
                continue
        if "d" not in date:
            d, s2 = parse_day(s)
            if d is not None:
                date["d"] = d
                s = s2
                continue
        if "m" not in date:
            mo, s2 = parse_month(s)
            if mo is not None:
                date["m"] = mo
                s = s2
                continue
        if "y" not in date:
            y, s2 = parse_year(s)
            if y is not None:
                date["y"] = y
                s = s2
                continue
        if "part" not in date:
            p, s2 = parse_part(s)
            if p is not None:
                date["part"] = p
                s = s2
                continue
        if "season" not in date:
            se, s2 = parse_season(s)
            if se is not None:
                date["season"] = se
                s = s2
                continue
        if s == before:
            break

    if not date:
        return _flag(f"no date core recognised in {s0!r}")
    _finish(date, circa, uncertain, bound)

    # year ranges: "1899-1900", "1879/1880", "1880-1", "Late 1880-early 1881"
    m = re.match(rf"^[-–/]\s*(?:c\.\s*)?({_YEAR_RE})\b", s)
    if m:
        y2 = int(m.group(1))
        s = eat(s[m.end():])
        date["to"] = {"y": y2}
        return date, s, None
    m = re.match(r"^[-–/]\s*(\d{1,2})\b", s)
    if m and date.get("y") is not None:
        sh = int(m.group(1))
        if len(m.group(1)) == 1:
            y2 = (date["y"] // 10) * 10 + sh
        else:
            y2 = (date["y"] // 100) * 100 + sh
        s = eat(s[m.end():])
        date["to"] = {"y": y2}
        return date, s, None
    m = re.match(r"^[-–]\s*(early|mid-?|late|end)\b", s, re.I)
    if m:
        p2 = PARTS[m.group(1).lower().rstrip("-")]
        s = eat(s[m.end():])
        y2, s2 = parse_year(s)
        if y2 is not None:
            date["to"] = {"y": y2, "part": p2}
            s = s2
            return date, s, None
    return date, s, None


# ---------------------------------------------------------------------------
# Full date token: weekday, time, act prefixes, clauses, brackets
# ---------------------------------------------------------------------------
def _bracket_close(s):
    for i, ch in enumerate(s):
        if ch == "]":
            return i
    return -1


ACT_MARKER = re.compile(
    r"\b(Postmark of receipt|Postmark|Date of receipt|Received|Rec'd)\b", re.I)


def _act_from_label(label):
    return "received" if label.lower() in ("postmark of receipt",
                                           "date of receipt", "received",
                                           "rec'd") else "postmarked"


def _finish_date(expr, uncertain):
    """Parse the date expression a bracket (or bracket clause) holds."""
    q = uncertain or bool(re.match(r"^\?\s*", expr))
    expr = re.sub(r"^\?\s*", "", expr)
    date, rest, flag = parse_date_core(expr, uncertain=bool(q))
    if flag:
        return None, None, flag
    if date is None:
        return None, None, f"bracket contains no date: [{expr}]"
    return date, rest, None


def _mk_act(name, date, weekday=None, times=None):
    """Build (act_name, act_dict). times is [(raw, hhmm)]; raw goes on the act,
    an explicit 24-hour time on the date as `t`."""
    if date is None:
        date = {}
    if weekday:
        date.setdefault("weekday", weekday)
    act = {"date": date}
    if times:
        act["time"] = times[0][0]
        if times[0][1]:
            date.setdefault("t", times[0][1])
    return name, act


def parse_date_token(text):
    """Parse a complete date heading token from the start of text.

    Returns (acts, rest, flag_reason). acts is a list of (act_name, act_dict).
    A weekday outside the brackets is attached to `written` - the day Wilde
    wrote - per the project rule. times is threaded via a mutable holder.
    """
    s = text
    times = []
    weekday, s = parse_weekday(s)
    s = re.sub(r"^[,\s]+", "", s)
    m = re.match(r"^le\s+", s, re.I)      # French "Lundi, le 24 May 1897"
    if m:
        s = s[m.end():]
    t_raw, t_hhmm, s = parse_time(s)
    if t_raw:
        times.append((t_raw, t_hhmm))
        s = re.sub(r"^[,\s]+", "", s)
    m = re.match(r"^\(\s*Berneval time\s*\)\s*", s, re.I)
    if m:
        s = s[m.end():]
    if not s.strip():
        # "Saturday night" alone is a complete date - the day Wilde wrote
        return [_mk_act("written", {}, weekday, times)], "", None
    if s.startswith("["):
        return _parse_bracket_token(s, weekday, times)
    return _parse_unbracketed_token(s, weekday, times)


def _parse_bracket_token(s, weekday, times):
    end = _bracket_close(s)
    if end < 0:
        return None, None, f"unclosed bracket: {s[:40]!r}"
    inner, rest = s[1:end], s[end + 1:]

    hits = list(ACT_MARKER.finditer(inner))
    if hits:
        if len(hits) > 1:
            return None, None, f"multiple act markers inside one bracket: [{inner}]"
        m = hits[0]
        before, after = inner[:m.start()].strip(), inner[m.end():].strip()
        if not after:
            return None, None, f"empty clause after a postmark: [{inner}]"
        act2 = _act_from_label(m.group(1))
        d1 = None
        if before:
            d1, _, flag = _finish_date(before, False)
            if flag:
                return None, None, flag
        d2, _, flag = _finish_date(after, False)
        if flag:
            return None, None, flag
        d2["inferred"] = True
        if d1 is not None and d1.get("y") is None and d2.get("y"):
            d1["y"] = d2["y"]
            d1.setdefault("inferred", True)
        elif d2.get("y") is None and d1 is not None and d1.get("y"):
            d2["y"] = d1["y"]
            d2.setdefault("inferred", True)
        acts = []
        if d1 is not None:
            acts.append(_mk_act("written", d1, weekday, times))
        elif weekday or times:
            acts.append(_mk_act("written", {}, weekday, times))
        acts.append(_mk_act(act2, d2))
        return acts, rest, None

    d, _, flag = _finish_date(inner, False)
    if flag:
        return None, None, flag
    d["inferred"] = True
    # "[? 13] February 1895" - the bracket held only a day; the month and year
    # follow it. Merge only when the bracket said nothing a follow-on would
    # override.
    if set(d) <= {"d", "inferred", "uncertain", "circa", "weekday", "t"}:
        d2, rest2, flag = parse_date_core(rest)
        if flag is None and d2 is not None and (
                d2.get("m") or d2.get("y") or d2.get("season")):
            for k in ("m", "y", "season", "part", "weekday", "d"):
                if k in d2 and k not in d:
                    d[k] = d2[k]
            rest = rest2
        elif flag is None and d2 is not None:
            rest = rest2
    # a year may follow the bracket: "[? June] 1900 Grand Cafe..."
    y, rest2 = parse_year(rest)
    if y is not None and d.get("y") is None:
        d["y"] = y
        rest = rest2
    return [_mk_act("written", d, weekday, times)], rest, None


def _parse_unbracketed_token(s, weekday, times):
    s0 = s
    act = "written"
    m = ACT_MARKER.match(s)
    if m:
        act = _act_from_label(m.group(1))
        s = eat(s[m.end():])
    d, rest, flag = parse_date_core(s)
    if flag:
        return None, None, flag
    if d is None:
        return None, None, f"unbracketed date unreadable: {s0!r}"

    r = eat(rest)
    if r.startswith("["):
        end = _bracket_close(r)
        inner = r[1:end]
        after = r[end + 1:]
        m2 = ACT_MARKER.match(inner)
        if m2:
            act2 = _act_from_label(m2.group(1))
            expr = inner[m2.end():].strip()
            if expr and resolve_place(expr, act2) is not None:
                # "[Postmark La Varenne-St-Hilaire]" - the postmark's PLACE,
                # not a date; the structure parser keeps the bracket
                return [_mk_act(act, d, weekday, times)], rest, None
            if expr:
                d2, _, flag = _finish_date(expr, False)
                if flag:
                    return None, None, flag
                d2["inferred"] = True
                if d.get("y") is None and d2.get("y"):
                    d["y"] = d2["y"]
                    d.setdefault("inferred", True)
                elif d2.get("y") is None and d.get("y"):
                    d2["y"] = d["y"]
                    d2.setdefault("inferred", True)
                return [_mk_act("written", d, weekday, times),
                        _mk_act(act2, d2)], after, None
            return [_mk_act("written", d, weekday, times),
                    _mk_act(act2, {})], after, None
        # plain bracketed date: "Sunday night, 6 June [1897]"
        d2, _, flag = _finish_date(inner, False)
        if flag is None and d2 is not None and (
                d2.get("y") or d2.get("m") or d2.get("season")):
            d2["inferred"] = True
            for k in ("y", "m", "d", "weekday", "part", "season"):
                if d2.get(k) is not None and d.get(k) is None:
                    d[k] = d2[k]
            if d2.get("y"):
                d.setdefault("inferred", True)
            rest = after
        # else the bracket is a place ("[Paris]") - the structure parser keeps it
    return [_mk_act(act, d, weekday, times)], rest, None


# ---------------------------------------------------------------------------
# Heading structure
# ---------------------------------------------------------------------------
_TRAIL = r"(?:[,.!:\-]|\s|$)"
SALUTATION_RE = re.compile(
    r"(?:My\s+dear|My\s+dearest|My\s+darling|Dearest|Dear|Darling)"
    r"\s+[A-Za-z][\w'’.\-]*(?:\s+[A-Za-z][\w'’.\-]*)?(?:" + _TRAIL + r")")
SALUTATION_BARE = re.compile(
    r"(?:Sir|Madam|Gentlemen|Sirs|Ladies|Monsieur|Madame|Mademoiselle|"
    r"To\s+the\s+Right\s+Honourable)(?:" + _TRAIL + r")")
SALUTATION_FR = re.compile(
    r"(?:Cher|Ch[eè]re|Mon\s+cher|Ma\s+ch[eè]re)"
    r"\s+[A-Za-z][\w'’.\-]*(?:" + _TRAIL + r")")


def find_salutation(text):
    best = None
    for rx in (SALUTATION_RE, SALUTATION_BARE, SALUTATION_FR):
        m = rx.search(text)
        if m and (best is None or m.start() < best):
            best = m.start()
    return best


def match_salutation(text):
    m = find_salutation(text)
    return 0 if m == 0 else None


JUNK_RE = re.compile(
    r"^(?:MS|TS|IVIS|Wio)\s+[A-Za-z][\w'’.]*(?:\s+\([^)]*\))?\s*$|"
    r"^F\s+Br[eé]mont\s*$|"
    r"^yours\s*$|"
    r"^(?:1115\s+1\s+111\s+400|10\s+2014\s+121104\s+2\s+04814)\s*$|"
    r"^\[(?:Printed letter-heading|Sent by messenger|A letter of[^\]]*|"
    r"The rest of this letter is missing|Signature cut away|piece cut away|"
    r"On envelope)[^\]]*\]\s*$|"
    r"^(?:Private|Strictly Private)\s*$|"
    r"^de la part de M(?:onsieur)?\.?\s+[A-Za-z]+\s*$|"
    r"^Letter\s*[-–]\s*No\.?\s*[IVXLC\d]+\.?\s*$|"
    r"^\[On envelope\][^\]]*$|"
    r"^\[on verso\]\s*$")


def is_junk_paragraph(p):
    return bool(JUNK_RE.match(p.strip()))


def strip_heading_junk(text):
    text = re.sub(r"^\s*LETTER\s+NO\.?\s*\d+\s*", "", text)
    text = re.sub(r"^\s*(?:STRICTLY\s+)?PRIVATE\s*", "", text, flags=re.I)
    return text


# ---------------------------------------------------------------------------
# Places
# ---------------------------------------------------------------------------
def fold(s):
    """Normalise curly apostrophes to straight so keys and corpus agree."""
    return s.replace("\u2019", "'").replace("\u2018", "'")


PLACE_MAP = {
    "1 Merrion Square North": "1-merrion-square-north",
    "I Merrion Square North": "1-merrion-square-north",
    "I Merrion Square North, Dublin": "1-merrion-square-north",
    "1 Tite Street": "1-tite-street",
    "10 & 11 St James's Place": "10-11-st-jamess-place",
    "[10 & 11 St James's Place]": "10-11-st-jamess-place",
    "13 Salisbury Street": "13-salisbury-street",
    "[13 Salisbury Street]": "13-salisbury-street",
    "Thames House,13 Salisbury Street, Strand": "13-salisbury-street",
    "146 Oakley Street, Chelsea": "146-oakley-street",
    "[146 Oakley Street, Chelsea]": "146-oakley-street",
    "[? 146 Oakley Street]": "146-oakley-street",
    "16 Tite Street": "16-tite-street",
    "16 Tite Street, Chelsea": "16-tite-street",
    "16Tite Street": "16-tite-street",
    "I6 Tite Street": "16-tite-street",
    "Tite Street": "16-tite-street",
    "Tite Street, Chelsea": "16-tite-street",
    "[16 Tite Street]": "16-tite-street",
    "[? 16 Tite Street]": "16-tite-street",
    "4 Albert Street, [London] SW": "4-albert-street",
    "8 Mount Street, Grosvenor Square, London": "8-mount-street",
    "29 boulevard des Capucines": "29-boulevard-des-capucines",
    "29 boulevard des Capucines, Paris": "29-boulevard-des-capucines",
    "[29] boulevard des Capucines": "29-boulevard-des-capucines",
    "13 Pont Street": "13-pont-street",
    "18 Pont Street, [London] SW": "18-pont-street",
    "[? 2 Courtfield Gardens]": "2-courtfield-gardens",
    "7 Great College Street, Westminster, SW": "7-great-college-street",
    "9 Charles Street": "9-charles-street",
    "9 Charles Street, Grosvenor Square": "9-charles-street",
    "[? 9 Charles Street]": "9-charles-street",
    "85 Clinton Place, New York": "85-clinton-place",
    "85 Jermyn Street, [London] SW": "85-jermyn-street",
    "31 Santa Lucia [Naples]": "31-santa-lucia",
    "34 High Street, Oxford": "34-high-street-oxford",
    "46 West 28th Street [New York]": "46-west-28th-street",
    "48 West 11th Street [New York]": "48-west-11th-street",
    "1267 Broadway, New York": "1267-broadway",
    "1267 Broadway [New York]": "1267-broadway",
    "5 Esplanade, Worthing": "5-esplanade-worthing",
    "The Haven, 5 Esplanade, Worthing": "5-esplanade-worthing",
    "[The Haven, 5 Esplanade, Worthing]": "5-esplanade-worthing",
    "51 Kaiser-Friedrichs Promenade": "51-kaiser-friedrichs-promenade",
    "51 Kaiser-Friedrichs Promenade, Bad-Homburg": "51-kaiser-friedrichs-promenade",
    "St James's Street": "st-jamess-street",
    "Regent Street": "regent-street",
    "Piccadilly": "piccadilly",
    "Albemarle Chambers, Piccadilly": "albemarle-chambers",
    "Albemarle Club": "albemarle-club",
    "Albemarle Club, 13 Albemarle Street": "albemarle-club",
    "Albemarle Club, 25 Albemarle Street, W2": "albemarle-club",
    "Albergo di Firenze, Genoa": "albergo-di-firenze",
    "Arlington Hotel, Washington": "arlington-hotel-washington",
    "Athenaeum Club": "athenaeum-club",
    "Box F [St James's Theatre]": "st-jamess-theatre",
    "Cadogan Hotel": "cadogan-hotel",
    "Castle Hotel, Windsor": "castle-hotel-windsor",
    "Central Station Hotel [Glasgow]": "central-station-hotel",
    "Central Station Hotel, Glasgow": "central-station-hotel",
    "Chalet Bourgeat, Berneval-sur-Mer": "chalet-bourgeat",
    "[Chalet Bourgeat] Berneval-sur-Mer": "chalet-bourgeat",
    "Grand Hôtel de France, Rouen": "grand-hotel-de-france",
    "Grand Pacific Hotel, Chicago": "grand-pacific-hotel",
    "Harker's York Hotel, York": "harkers-york-hotel",
    "Haymarket Theatre": "haymarket-theatre",
    "Hotel Albemarle": "hotel-albemarle",
    "Hotel Albemarle, Piccadilly": "hotel-albemarle",
    "Hotel Avondale, Piccadilly": "hotel-avondale",
    "Hotel Metropole, Brighton": "hotel-metropole-brighton",
    "Hotel St George, Corfu": "hotel-st-george-corfu",
    "Hôtel Marsollier": "hotel-marsollier",
    "Hôtel Marsollier, rue Marsollier, Paris": "hotel-marsollier",
    "Hôtel Normandie": "hotel-normandie",
    "Hôtel Normandie, rue de l'Echelle, Paris": "hotel-normandie",
    "Hôtel Royal des Étrangers, Naples": "hotel-royal-des-etrangers",
    "Hôtel Sandwich, Dieppe": "hotel-sandwich",
    "Hôtel Terminus & Cosmopolitain, Monte Carlo": "hotel-terminus-cosmopolitain",
    "Hôtel Terminus, Nice": "hotel-terminus",
    "Hôtel Voltaire": "hotel-voltaire",
    "Hôtel Voltaire, Quai Voltaire, Paris": "hotel-voltaire",
    "Hôtel Continental, Paris": "hotel-continental-paris",
    "Metropolitan Hotel, St Paul, Minnesota": "metropolitan-hotel-st-paul",
    "116 Park Street, Grosvenor Square [London]": "116-park-street",
    "Beaufort Club, 32 Dover Street": "beaufort-club",
    "Hôtel d'Alsace": "hotel-d-alsace",
    "Hôtel d'Alsace, Paris": "hotel-d-alsace",
    "Hôtel d'Alsace, rue des Beaux-Arts": "hotel-d-alsace",
    "Hôtel d'Alsace, rue des Beaux-Arts, Paris From Sebastian Melmoth": "hotel-d-alsace",
    "De la part de Monsieur Sebastian Melmoth Hôtel d'Alsace, rue des Beaux-Arts": "hotel-d-alsace",
    "[Hôtel d'Alsace]": "hotel-d-alsace",
    "Hôtel de Nice": "hotel-de-nice",
    "Hôtel de Nice, rue des Beaux-Arts, Paris": "hotel-de-nice",
    "[Hôtel de Nice]": "hotel-de-nice",
    "Hôtel de l'Athénée": "hotel-de-l-athenee",
    "Hôtel de l'Athénée, 15 rue Scribe, Paris": "hotel-de-l-athenee",
    "Hôtel de l'Europe, Algiers": "hotel-de-l-europe-algiers",
    "Hôtel de l'Écu, Chennevières-sur-Marne": "hotel-de-l-ecu",
    "Hôtel de I'Écu, Chennevières-sur-Marne": "hotel-de-l-ecu",
    "Hôtel de l'Écu, Chennevières-sur-Marne, Seine-et-Oise": "hotel-de-l-ecu",
    "Hôtel de la Néva": "hotel-de-la-neva",
    "Hôtel de la Néva, rue Montigny, Paris": "hotel-de-la-neva",
    "Hôtel de la Plage, Berneval-sur-Mer": "hotel-de-la-plage",
    "Hôtel de la Plage, Berneval-sur-Mer Private and Confidential": "hotel-de-la-plage",
    "Hôtel de la Plage, Berneval-sur-Mer, Dieppe": "hotel-de-la-plage",
    "Private Hôtel de la Plage, Berneval-sur-Mer": "hotel-de-la-plage",
    "[Hôtel de la Plage, Berneval-sur-Mer]": "hotel-de-la-plage",
    "Hôtel des Alpes-Maritimes, rue d'Angleterre, Nice": "hotel-des-alpes-maritimes",
    "Hôtel des Bains, Napoule": "hotel-des-bains-napoule",
    "Hôtel des Deux Mondes 22 Avenue de l'Opéra, Paris": "hotel-des-deux-mondes",
    "Keats House": "keats-house",
    "Keats House, Chelsea": "keats-house",
    "Keats House, Tite Street": "keats-house",
    "Keats House. Tite Street": "keats-house",
    "Lyric Club": "lyric-club",
    "Lyric Club, Piccadilly East": "lyric-club",
    "New Lyric Club, 63 St James's Street": "lyric-club",
    "New Travellers Club": "new-travellers-club",
    "New Travellers Club, Piccadilly": "new-travellers-club",
    "Pavillon d'Armenonville, Bois de Boulogne": "pavillon-d-armenonville",
    "Queens Hotel, Eastbourne": "queens-hotel-eastbourne",
    "Raven Hotel, Shrewsbury": "raven-hotel",
    "HM Prison, Reading": "reading",
    "[HM Prison, Reading]": "reading",
    "[HM Prison] Reading": "reading",
    "[? HM Prison, Reading]": "reading",
    "Reading Prison": "reading",
    "The Prison, Reading": "reading",
    "HM Prison, Holloway": "holloway",
    "[HM Prison, Holloway]": "holloway",
    "Royal Albion Hotel, Brighton": "royal-albion-hotel",
    "Royal Bath Hotel, Bournemouth": "royal-bath-hotel",
    "Royal Palace Hotel, Kensington": "royal-palace-hotel",
    "Royal Victoria Hotel, Sheffield": "royal-victoria-hotel",
    "Savoy Hotel, London": "savoy-hotel",
    "Savoy Theatre": "savoy-theatre",
    "St Stephen's Club": "st-stephens-club",
    "St Stephen's Club, Westminster": "st-stephens-club",
    "Station Hotel, Leeds": "station-hotel-leeds",
    "The Balmoral, Edinburgh": "the-balmoral",
    "The Bodley Head": "bodley-head",
    "The Bodley Head, Vigo Street": "bodley-head",
    "The Cottage, Goring-on-Thames": "the-cottage-goring",
    "The Palace Hotel, San Francisco": "the-palace-hotel",
    "The Pilot, 597 Washington Street, Boston": "the-pilot",
    "The Reform Club": "the-reform-club",
    "The Royal Hotel, Bristol": "the-royal-hotel-bristol",
    "The Vicarage, West Ashby": "the-vicarage-west-ashby",
    "The Windsor, Topeka, Kansas": "the-windsor-topeka",
    "Thos Cook & Son, 33 Piccadilly": "thos-cook-and-son",
    "Vendome Hotel, Boston": "vendome-hotel",
    "Windsor Hotel, Montreal": "windsor-hotel-montreal",
    "Office of the Yellow Book": "office-of-the-yellow-book",
    "Café Suisse, Dieppe": "cafe-suisse-dieppe",
    "Café Suisse [Dieppe]": "cafe-suisse-dieppe",
    "Café des Tribunaux, Dieppe": "cafe-des-tribunaux",
    "Café de l'Univers [Paris]": "cafe-de-l-univers",
    "Café du Nord, Geneva": "cafe-du-nord-geneva",
    "Grand Café Glacier, Nice": "grand-cafe-glacier",
    "Grand Café, 14 boulevard des Capucines, Paris": "grand-cafe",
    "Grand Hôtel [Post Office] [boulevard des Capucines] Paris": "grand-hotel-paris",
    "La Belle Sauvage": "la-belle-sauvage",
    "La Belle Sauvage, Ludgate Hill": "la-belle-sauvage",
    "[? La Belle Sauvage]": "la-belle-sauvage",
    "Woman's World, La Belle Sauvage": "la-belle-sauvage",
    "[Woman's World, La Belle Sauvage]": "la-belle-sauvage",
    "L'Idée, Le Perreux, Nogent-sur-Marne": "l-idee-le-perreux",
    "L'Île d'Amour, Chennevières-sur-Marne": "l-ile-d-amour",
    "La Maison Rouge, Hôtel, Café, Restaurant, La Roche-Guyon, Seine-et-Oise": "la-maison-rouge",
    "Taverne F. Pousset, 14 boulevard des Italiens, Paris": "taverne-f-pousset",
    "Taverne F. Pousset, 14 boulevard des Italiens [Paris]": "taverne-f-pousset",
    "Taverne F. Pousset [Paris]": "taverne-f-pousset",
    "c/o Cook & Son, Piazza di Spagna, Rome": "cooks-office-rome",
    "c/o Cook and Son, Rome": "cooks-office-rome",
    "chez Cook et Fils, Rome": "cooks-office-rome",
    "c/o Stoker and Hansell, 14 Gray's Inn Square,": "stoker-and-hansell",
    "Babbacombe Cliff": "babbacombe-cliff",
    "Babbacombe Cliff [near Torquay, South Devon]": "babbacombe-cliff",
    "[Babbacombe Cliff]": "babbacombe-cliff",
    "Berneval-sur-Mer": "berneval-sur-mer",
    "[Berneval-sur-Mer]": "berneval-sur-mer",
    "(Postcard No.1) [Berneval-sur-Mer]": "berneval-sur-mer",
    "(Postcard No.2) [Berneval-sur-Mer]": "berneval-sur-mer",
    "10.30 a.m. [Berneval-sur-Mer]": "berneval-sur-mer",
    "Boston": "boston",
    "[Boston]": "boston",
    "Brighton": "brighton",
    "Chelsea": "chelsea",
    "Chicago": "chicago",
    "[Chicago]": "chicago",
    "Cincinnati": "cincinnati",
    "[Cincinnati]": "cincinnati",
    "Corfu": "corfu",
    "[? Corfu]": "corfu",
    "Dieppe": "dieppe",
    "[Dieppe]": "dieppe",
    "Havre": "havre",
    "[Havre]": "havre",
    "Homburg": "homburg",
    "Kansas City": "kansas-city",
    "Kansas City, Missouri": "kansas-city",
    "Kreuznach": "kreuznach",
    "London": "london",
    "[London]": "london",
    "[? London]": "london",
    "[?London]": "london",
    "Montreal": "montreal",
    "[Montreal]": "montreal",
    "Naples": "naples",
    "[Naples]": "naples",
    "Napoule": "la-napoule",
    "[Napoule]": "la-napoule",
    "New York": "new-york",
    "[New York]": "new-york",
    "Niagara": "niagara",
    "Nice": "nice",
    "[Nice]": "nice",
    "Ottawa": "ottawa",
    "[? Ottawa]": "ottawa",
    "Oxford": "oxford",
    "[Oxford]": "oxford",
    "Palermo": "palermo",
    "Paris": "paris",
    "[Paris]": "paris",
    "[? Paris]": "paris",
    "Lausanne": "lausanne",
    "[? Lausanne]": "lausanne",
    "Philadelphia": "philadelphia",
    "[Philadelphia]": "philadelphia",
    "[? Philadelphia]": "philadelphia",
    "Posilippo": "posilippo",
    "Rapallo": "rapallo",
    "[Rapallo]": "rapallo",
    "Rome": "rome",
    "[Rome]": "rome",
    "San Francisco": "san-francisco",
    "[San Francisco]": "san-francisco",
    "San Fruttuoso": "san-fruttuoso",
    "[San Fruttuoso]": "san-fruttuoso",
    "Santa Margherita": "santa-margherita",
    "Santa Margherita, Ligure": "santa-margherita",
    "Sioux City": "sioux-city",
    "[? Sioux City]": "sioux-city",
    "St Joseph, Missouri": "st-joseph-missouri",
    "St Louis": "st-louis",
    "St Louis [Missouri]": "st-louis",
    "Toronto": "toronto",
    "Torquay": "torquay",
    "Trouville": "trouville",
    "US": "us",
    "Worthing": "worthing",
    "[Worthing]": "worthing",
    "[? Worthing]": "worthing",
    "Milan": "milan",
    "Bingham": "bingham",
    "Bingham Rectory, Notts": "bingham-rectory",
    "Bamff, Alyth, Perthshire": "bamff-alyth",
    "Clumber, near Worksop": "clumber",
    "Grove Farm, Felbrigg, Cromer": "grove-farm-felbrigg",
    "Illaunroe Lodge": "illaunroe-lodge",
    "Illaunroe Lodge, Connemara": "illaunroe-lodge",
    "Illaunroe Lodge, Lough Fee": "illaunroe-lodge",
    "Moytura House [Cong, Co. Mayo]": "moytura-house",
    "O'Neill House, Woodstock, Ontario": "oneill-house",
    "Ocean House, Newport [Rhode Island]": "ocean-house-newport",
    "Park Avenue Hotel, New York": "park-avenue-hotel",
    "Park Avenue Hotel [New York]": "park-avenue-hotel",
    "Prospect House, Niagara Falls, Canada Side": "prospect-house-niagara",
    "Springwood Park, Kelso": "springwood-park",
    "Villa Giudice": "villa-giudice",
    "Villa Giudice [Posilippo]": "villa-giudice",
    "Villa Giudice, Posilippo": "villa-giudice",
    "Villa Giudice, Posilippo, Naples": "villa-giudice",
    "Withnell House, Omaha, Nebraska": "withnell-house",
    "Newport, Rhode Island": "newport-rhode-island",
    "[Newport, Rhode Island]": "newport-rhode-island",
    "Omaha, Nebraska": "omaha",
    "[Omaha, Nebraska]": "omaha",
    "Bloomington, Illinois": "bloomington",
    "Augusta, Georgia": "augusta-georgia",
    "Columbus, Ohio": "columbus-ohio",
    "Fremont, Nebraska": "fremont-nebraska",
    "Salt Lake City, Utah": "salt-lake-city",
    "Halifax, Nova Scotia": "halifax",
    "Gland, Switzerland": "gland",
    "Gland, Canton Vaud, Switzerland": "gland",
    "Gland, Switzerland At the House of the Enemy Among the Cities of the Plain": "gland",
    "[Gland, Switzerland]": "gland",
    "Nogent-sur-Marne": "nogent-sur-marne",
    "[Nogent-sur-Marne]": "nogent-sur-marne",
    "Portofino": "portofino",
    "[Portofino]": "portofino",
    "Élysée Palace Hôtel, avenue des Champs Élysées": "elysee-palace-hotel",
    "Magdalen College": "magdalen-college",
    "Magdalen College, Oxford": "magdalen-college",
    "Paddington": "paddington",
    "Holborn Viaduct Hotel": "holborn-viaduct-hotel",
    "Newlyn's Family Hotel, Bournemouth": "newlyns-family-hotel",
    "The World's Hotel, St Joseph, Missouri": "the-worlds-hotel-st-joseph",
    "Sloane Square": "sloane-square",
    "Albergo della Francia, Milan": "albergo-della-francia-milan",
    "Grand Hotel, Monte Carlo": "grand-hotel-monte-carlo",
    "County Hotel, Ulverston, Lancs": "county-hotel-ulverston",
    "Great Western Hotel, Birmingham": "great-western-hotel-birmingham",
    "Dowdeswell & Dowdeswell, Fine Art Publishers": "dowdeswell",
    "160 New Bond Street": "160-new-bond-street",
    "Griggsville [Illinois]": "griggsville",
    "In Bed, Paris": "in-bed-paris",
    "Newhaven": "newhaven",
    "Kalisaya [Paris]": "kalisaya",
    "Villa Giudice, Posilippo [Postmark 28 October 1897]": "villa-giudice",
    "Posilippo [Postmark Capri]": "posilippo",
    "[Postmark Paris]": "paris",
    "[Postmark Torquay]": "torquay",
    "[Postmark Capri]": "capri",
    "[Postmark Dieppe]": "dieppe",
    "[Postmark Chicago]": "chicago",
    "[Postmark Florence]": "florence",
    "[Postmark Havre]": "havre",
    "[Postmark La Varenne-St-Hilaire]": "la-varenne-st-hilaire",
    "La Varenne-St-Hilaire": "la-varenne-st-hilaire",
    "[Postmark Boston]": "boston",
    "[Postmark New York]": "new-york",
    "St James's Theatre": "st-jamess-theatre",
    "St James's Theatre [London]": "st-jamess-theatre",
}

# City names are their own places even when the volume prints no street.
PLACE_MAP.update({
    "Algiers": "algiers",
    "Bristol": "bristol",
    "Chennevières-sur-Marne": "chenneviers-sur-marne",
    "Eastbourne": "eastbourne",
    "Glasgow": "glasgow",
    "Kelso": "kelso",
    "Leeds": "leeds",
    "Rouen": "rouen",
    "Sheffield": "sheffield",
    "Shrewsbury": "shrewsbury",
    "Windsor": "windsor",
    "York": "york",
    "Worksop": "worksop",
    "Washington": "washington",
    "[? Washington]": "washington",
    "Worthing, England": "worthing",
    "Hôtel Sandwich": "hotel-sandwich",
})

# a "[Postmark X]" bracket whose X is a PLACE (no digits) - the postmark's
# stamp, not a date
POSTMARK_PLACE_RE = re.compile(r"^\[\s*Postmark\s+([^\]]*?)\s*\]$", re.I)


def is_postmark_place(raw):
    m = POSTMARK_PLACE_RE.match(raw.strip())
    return m is not None and not re.search(r"\d", m.group(1))


def norm_addr(raw):
    """The canonical address string a raw heading fragment names.

    Strips bracket ornament, question marks, postcard markers, leading times,
    and the 'From Sebastian Melmoth' / privacy flourishes the volume prints
    around an address.
    """
    s = fold(raw.strip())
    s = re.sub(r"^\(\s*Postcard No\.?\s*\d+\s*\)", "", s)
    s = re.sub(r"^\d{1,2}[.:]\d{2}\s*(?:o'?clock\s*)?(?:a\.?m\.?|p\.?m\.?)?\s*", "", s)
    s = re.sub(r"^\d{1,2}\s+o'?clock\s+(?:a\.?m\.?|p\.?m\.?)\s*", "", s)
    s = re.sub(r"^[,;:–—-]+\s*", "", s)
    s = re.sub(
        r"\s*(?:Private and Confidential|Strictly Private|Private|By hand\.?|"
        r"Sent by messenger|From Sebastian Melmoth)\s*$", "", s, flags=re.I)
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1].strip()
    s = re.sub(r"^\?\s*", "", s)
    s = re.sub(r"^I\s+", "1 ", s)
    s = re.sub(r"^I6\s+", "16 ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


_FOLDED = {fold(k): k for k in PLACE_MAP}


def resolve_place(raw, act):
    """Map a raw address string to (place_id, act). None if unknown."""
    if raw is None or not raw.strip():
        return None
    r = raw.strip()
    if r in PLACE_MAP:
        return PLACE_MAP[r], act
    fr = fold(r)
    if fr in _FOLDED:
        return PLACE_MAP[_FOLDED[fr]], act
    n = norm_addr(fr)
    if n in _FOLDED:
        return PLACE_MAP[_FOLDED[n]], act
    return None


def match_known_address(text):
    """If text starts with a known address, return (raw_address, rest)."""
    t = text.lstrip()
    lead = len(text) - len(t)
    f = fold(t)
    best = None
    for fk in _FOLDED:
        if f.startswith(fk) and (best is None or len(fk) > len(best)):
            best = fk
    if best:
        k = _FOLDED[best]
        return k, t[len(best):]
    m = re.match(r"^(\[[^\]]+\])\s*", t)
    if m:
        n = norm_addr(m.group(1))
        if n in _FOLDED:
            return m.group(1), t[m.end():]
    return None, t


def split_postmark(raw):
    """An address carrying ' [Postmark X]': returns (main, postmark_part).

    A pure '[Postmark X]' bracket is itself the postmark's place/date, so it is
    left whole (main = raw, postmark_part = None); the caller routes it by its
    own bracket form.
    """
    if POSTMARK_PLACE_RE.match(raw.strip()) or re.match(
            r"^\[\s*Postmark\b[^\]]*\d{4}[^\]]*\]$", raw.strip(), re.I):
        return raw, None
    m = re.search(r"\[\s*Postmark\b\s*([^\]]*)\]", raw, re.I)
    if not m:
        return raw, None
    return raw[:m.start()].strip(), m.group(1).strip()


def looks_like_address(t):
    """A short line with no sentence punctuation, e.g. '16 Tite Street'."""
    t = t.strip()
    if not t or len(t) > 130:
        return False
    if match_salutation(t) is not None:
        return False
    if is_junk_paragraph(t):
        return False
    if len(t.split()) > 13:
        return False
    # an address is a noun phrase; a verb or a pronoun means this is the body
    if re.search(r"\b(?:may|might|would|should|could|shall|will|is|are|was|"
                 r"were|have|has|had|do|does|did|be|been|am)\b", t, re.I):
        return False
    if re.search(r"[.!?:](?:\s|$)", t) and not re.search(
            r"\b(?:St|St\.|No\.|W2?|SW|NW|SE|NE|EC|WC|Co\.|Dr\.|W\.C\.)\b", t):
        return False
    return True


# ---------------------------------------------------------------------------
# Special cases - confirmed against the printed page images
# ---------------------------------------------------------------------------
# 0027-1 is the postscript to 0025-1, whose heading dates it Wednesday
# [26 July 1876. Postmark 27 July 1876]; the postscript shares that letter's
# date and place.
SPECIAL_HEADINGS = {
    "0027-1.json": {
        "prepend_heading": "[26 July 1876]\n\n1 Merrion Square North",
        "note": "postscript to the letter of 26 July 1876",
    },
    # the OCR text mirror dropped the two-column date line; the page prints
    # "19 April [1882]"; the transcription already carries the address
    "0164-2.json": {
        "prepend_heading": "19 April [1882]",
        "note": "date read from the printed page (OCR dropped it)",
    },
    # the page prints "[? 5 June 1897]"; transcription keeps only the address
    "0881-1.json": {
        "prepend_heading": "[? 5 June 1897]",
        "note": "date read from the printed page (OCR dropped it)",
    },
    # the page prints "6 July [1897]"; transcription keeps only the address
    "0910-1.json": {
        "prepend_heading": "6 July [1897]",
        "note": "date read from the printed page (OCR dropped it)",
    },
    "0811-1.json": {
        "addressee": "Robert Ross",
        "note": "volume prints no year; weekday and day-month from the heading",
    },
    # the joke heading runs across two paragraphs; the page prints it on one
    # line as "Thursday 3 June 2.45 p.m. (Berneval time) AD 1897"
    "0877-1.json": {
        "fix": [("2.45 p.m. (Berneval time)\n\nAD 1897 Latitude and Longitude "
                 "not marked on the sea", "1897 2.45 p.m.")],
        "note": "joke heading flattened to one line",
    },
    # the transcription duplicated the petit bleu's first line; the page shows
    # the message begins once, after the place line
    "1166-3.json": {
        "fix": [("Wednesday [Postmark 4 October 1899]\n\n"
                 "Dear Will I have heard nothing from you\n\nKalisaya [Paris]",
                 "Wednesday [Postmark 4 October 1899]\n\nKalisaya [Paris]")],
        "note": "duplicated first line dropped (page shows it once)",
    },
    # year typos: the footnote digit was OCR'd onto the year
    "0521-3.json": {"fix": [("26 February 18923", "26 February 1892")],
                    "note": "printed page reads 26 February 1892 (footnote 3)"},
    "0649-1.json": {"fix": [("8 May 18951", "8 May 1895")],
                    "note": "printed page reads 8 May 1895 (footnote 1)"},
    "0637-2.json": {"fix": [("5 April 18952", "5 April 1895")],
                    "note": "printed page reads 5 April 1895 (footnote 2)"},
    "1167-1.json": {"fix": [("7 October 18991", "7 October 1899")],
                    "note": "printed page reads 7 October 1899 (footnote 1)"},
    "0237-2.json": {"fix": [("[9 Charles Street", "[9 Charles Street]")],
                    "note": "closing bracket lost in transcription"},
}


# ---------------------------------------------------------------------------
# Heading parsing
# ---------------------------------------------------------------------------
def parse_heading(quote):
    """Split a quote into (acts, places, new_quote, flags).

    acts: list of (act_name, act_dict). places: list of (act, raw_address).
    """
    paras = quote.split("\n\n")
    j = 0
    while j < len(paras) and is_junk_paragraph(paras[j]):
        j += 1
    if j >= len(paras):
        return None, None, None, ["quote is all leading matter, no heading"]

    text = paras[j].strip()
    acts = []
    places = []
    times = []

    # address-first: "Chalet Bourgeat, Berneval-sur-Mer 22 August 1897 Dear..."
    addr, rest = match_known_address(text)
    if addr:
        acts, rest, flag = parse_date_token(rest)
        if flag:
            return None, None, None, [f"heading date unreadable ({flag}) "
                                      f"after address: {text[:70]!r}"]
        if not acts:
            return None, None, None, [f"address but no date: {text[:70]!r}"]
        places.append(("written", addr))
        body_idx, body_prefix, flag = consume_tail(
            acts, places, times, rest, paras, j)
        if flag:
            return None, None, None, flag
        return finalize(acts, places, times, paras, body_idx, body_prefix)

    acts, rest, flag = parse_date_token(text)
    if flag:
        return None, None, None, [f"heading date unreadable ({flag}): "
                                  f"{text[:70]!r}"]
    if acts is None:
        return None, None, None, [f"heading date unreadable: {text[:70]!r}"]

    body_idx, body_prefix, flag = consume_tail(acts, places, times, rest,
                                               paras, j)
    if flag:
        return None, None, None, flag
    return finalize(acts, places, times, paras, body_idx, body_prefix)


def finalize(acts, places, times, paras, body_idx, body_prefix):
    """Attach the collected places and times, and cut the quote."""
    if not acts:
        return None, None, None, ["no act carried a date"]

    # merge repeated written dates into one (a tail bracket must never add a
    # second written date, but be safe rather than lossy)
    ws = [i for i, (a, _) in enumerate(acts) if a == "written"]
    if len(ws) > 1:
        first = ws[0]
        for i in ws[1:]:
            for k, v in acts[i][1].get("date", {}).items():
                if k not in acts[first][1].setdefault("date", {}):
                    acts[first][1]["date"][k] = v
        for i in reversed(ws[1:]):
            del acts[i]

    # times collected during the tail scan belong to written
    if times:
        for a, act in acts:
            if a == "written":
                act["time"] = times[0][0]
                if times[0][1]:
                    act["date"].setdefault("t", times[0][1])
                break

    for act, raw in places:
        main, pm = split_postmark(raw)
        pid = resolve_place(main, act)
        if pid is None:
            continue
        acts.append((f"{act}-place", pid))
        if pm:
            pm = pm.strip()
            date, rest2, flag = parse_date_core(pm)
            if flag is None and date is not None and not rest2.strip():
                date["inferred"] = True
                acts.append(("postmarked", {"date": date}))
            else:
                pid2 = resolve_place(pm, "postmarked")
                if pid2:
                    acts.append(("postmarked-place", pid2))

    # skip junk paragraphs between the heading and the body
    while body_idx < len(paras) and is_junk_paragraph(paras[body_idx]):
        body_idx += 1
    body = "\n\n".join(paras[body_idx:])
    if body_prefix is not None:
        body = (body_prefix + "\n\n" + body).strip() if body else body_prefix
    return acts, places, body.strip(), None


def _tail_bracket_is_date(cont):
    """A tail bracket is a date only when it says more than a bare day: a
    bare "[29]" in "[29] boulevard des Capucines" is the address fragment."""
    for a, act in cont:
        d = act.get("date") or {}
        if a in ("postmarked", "received", "sent"):
            return True
        if any(d.get(k) for k in ("y", "m", "season", "weekday")):
            return True
    return False


def consume_tail(acts, places, times, rest, paras, j):
    """Consume time/place/salutation/body after the date token.

    Mutates acts/places/times. Returns (body_idx, body_prefix, flags).
    """
    guard = 0
    while guard < 12:
        guard += 1
        rest = rest.strip()
        rest = strip_heading_junk(rest)
        if not rest:
            # paragraph ended - next paragraphs: date continuation, address,
            # or the body
            k = j + 1
            while k < len(paras) and is_junk_paragraph(paras[k]):
                k += 1
            if k >= len(paras):
                return k, None, None
            nxt = paras[k].strip()
            # a date bracket continues the heading: "Saturday night\n\n
            # [15 May 1897, Postmark 16 May 1897] [HM Prison, Reading]"
            if nxt.startswith("["):
                cont, rest2, flag = parse_date_token(nxt)
                if flag is None and cont and _tail_bracket_is_date(cont):
                    acts.extend(cont)
                    j = k
                    rest = rest2
                    continue
                # a pure postmark-place bracket: "[Postmark Paris]"
                if is_postmark_place(nxt):
                    places.append(("postmarked", nxt))
                    j = k
                    rest = ""
                    continue
            addr, r2 = match_known_address(nxt)
            if addr:
                act = "postmarked" if POSTMARK_PLACE_RE.match(addr) else "written"
                places.append((act, addr))
                j = k
                rest = r2
                continue
            if looks_like_address(nxt):
                places.append(("written", nxt))
                return k + 1, None, None
            return k, None, None

        # clock time: "Friday, 3.30 [Postmark 11 June 1897]"
        t_raw, t_hhmm, rest2 = parse_time(rest)
        if t_raw:
            times.append((t_raw, t_hhmm))
            rest = rest2
            continue

        m = re.match(r"^\(\s*Postcard No\.?\s*\d+\s*\)\s*", rest, re.I)
        if m:
            rest = rest[m.end():]
            continue

        # a bracketed place or date before the salutation:
        # "[Hôtel de la Plage, Berneval-sur-Mer] My dear Robbie, ..."
        # "Friday [15 October 1897] [Postmark 16 October 1897]"
        m = re.match(r"^(\[[^\]]+\])\s*", rest)
        if m:
            br = m.group(1)
            # a postmark DATE bracket continues the heading:
            # "Friday [15 October 1897] [Postmark 16 October 1897]"
            cont, rest2, flag = parse_date_token(br)
            if flag is None and cont and _tail_bracket_is_date(cont):
                acts.extend(cont)
                rest = rest[m.end():]
                continue
            if is_postmark_place(br):
                places.append(("postmarked", br))
                rest = rest[m.end():]
                continue
            if br in PLACE_MAP or norm_addr(br) in _FOLDED:
                places.append(("written", br))
                rest = rest[m.end():]
                continue

        sp = find_salutation(rest)
        if sp is not None:
            addr = rest[:sp].strip()
            if addr:
                places.append(("written", addr))
            return j + 1, rest[sp:], None

        addr, r2 = match_known_address(rest)
        if addr:
            act = "postmarked" if POSTMARK_PLACE_RE.match(addr) else "written"
            places.append((act, addr))
            if r2.strip():
                rest = r2
                continue
            return j + 1, None, None

        if looks_like_address(rest):
            places.append(("written", rest))
            return j + 1, None, None

        # no address - the rest is the body itself
        return j + 1, rest, None

    return None, None, ["tail scan did not terminate"]


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def date_on_any_act(doc):
    # `written: null` is the declared-undated marker (validate.py accepts it): a letter the
    # volume gives no date and no place for. It counts as done, like a date does, so a re-run
    # does not re-flag a letter a human has already decided about.
    return any(doc.get(a) is None and a in doc or bool((doc.get(a) or {}).get("date"))
               for a in ACTS)


def fmt_acts(acts):
    parts = []
    for a, act in acts:
        if a.endswith("-place"):
            parts.append(f"{a}={act}")
        else:
            parts.append(f"{a}.date={json.dumps(act.get('date'), ensure_ascii=False)}")
            if act.get("time"):
                parts.append(f"{a}.time={act['time']!r}")
    return "; ".join(parts)


def apply_acts(doc, acts):
    for a, act in acts:
        if a.endswith("-place"):
            # resolve_place returns (id, act); only the id is stored
            doc.setdefault(a[:-len("-place")], {})["place"] = act[0]
        else:
            doc[a] = act


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--review", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    files = sorted(TRANSCRIPTIONS.glob("*.json"))
    parsed, flagged, skipped, changed = [], [], 0, 0
    unknown_places = {}
    for f in files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        if date_on_any_act(doc):
            skipped += 1
            continue
        quote = doc["quote"]
        sp = SPECIAL_HEADINGS.get(f.name)
        note = None
        if sp:
            if "fix" in sp:
                for old, new in sp["fix"]:
                    quote = quote.replace(old, new, 1)
                doc["quote"] = quote
            if "prepend_heading" in sp:
                quote = sp["prepend_heading"] + "\n\n" + quote
                doc["quote"] = quote
            if "addressee" in sp:
                doc["addressee"] = sp["addressee"]
            note = sp.get("note")
        acts, places, new_quote, flags = parse_heading(quote)
        if flags:
            flagged.append((f.name, doc.get("addressee", ""), flags,
                            doc["quote"][:140]))
            continue
        if acts is None or new_quote is None:
            flagged.append((f.name, doc.get("addressee", ""),
                            ["no heading parsed"], doc["quote"][:140]))
            continue
        pl = []
        ok = True
        for act, raw in places:
            main, _pm = split_postmark(raw)
            pid = resolve_place(main, act)
            if pid is None:
                unknown_places.setdefault(main or raw, []).append(f.name)
                ok = False
            else:
                pl.append(f"{act}:{pid}")
        if not ok:
            flagged.append((f.name, doc.get("addressee", ""),
                            ["unmapped place"], doc["quote"][:140]))
            continue
        parsed.append((f.name, fmt_acts(acts), ",".join(pl) or "-",
                       (note or ""), new_quote[:50].replace("\n", " / ")))
        if args.apply:
            apply_acts(doc, acts)
            doc["quote"] = new_quote
            f.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
            changed += 1

    for line in parsed:
        print("\t".join(line))
    print("=" * 90)
    for name, add, flags, head in flagged:
        print(f"FLAG\t{name}\t{add}\t{'; '.join(flags)}\t{head!r}")
    if unknown_places:
        print("=" * 90)
        print("UNMAPPED PLACES (add to PLACE_MAP):")
        for raw, names in sorted(unknown_places.items()):
            print(f"  {raw!r}\t({len(names)} files, e.g. {names[0]})")
    print("=" * 90)
    print(f"total {len(files)}  parsed {len(parsed)}  flagged {len(flagged)}  "
          f"skipped {skipped}  changed {changed}")


if __name__ == "__main__":
    main()
