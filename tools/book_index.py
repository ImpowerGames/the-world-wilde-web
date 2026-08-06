"""Parse the volume's OWN two indexes — the authoritative spine for the sweep.

The Complete Letters carries two indexes, listed on its contents page:
    Index of Recipients   printed 1231   every letter ADDRESSED TO each person
    General Index         printed 1237   every MENTION, plus recipients again

These are curated and disambiguated by the editors, which a regex over the OCR mirror is not: the
index separates 'Georges, Monsieur' from 'Georges (boy)', knows that Herbert Horne and Herbert P.
Horne are one man, and files G. H. Kersley where a search for 'George Kersley' finds nothing.

*** THE FOLIO LISTS THIS TOOL PRODUCES ARE INCOMPLETE AND PARTLY WRONG. DO NOT TRUST THEM. ***

The indexes are set in TWO COLUMNS, and long entries wrap onto indented number-only continuation
lines. The OCR mirror strips the indentation and interleaves the columns unpredictably, so a
continuation line cannot be reliably attached to the entry it belongs to. Measured against the
rendered image of printed 1232: Clifton's 7 letters come out as 5, Douglas's 33 come out as 19 —
and those 19 include six folios that actually belong to Godwin in the facing column.

So this tool is a LOCATOR, not a source:
  - use it to find WHICH index page an entry is on, and as a rough first pass;
  - then read that index page as a rendered image and transcribe the entry by eye.

That is the same rule the rest of this project runs on, and the index is not exempt from it. The
index also carries its own errors - its 'Georges (boy)' entry includes 1097, which belongs to
Monsieur Georges the hotelier - so even a correct transcription needs checking at the cited page.

    python tools/book_index.py --build          write data/_book_index.json (first pass only)
    python tools/book_index.py <surname>        locate an entry
    python tools/book_index.py --pages          list the index pages to read at the page
"""
import json
import re
import sys
import bisect
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parents[5]
MIRROR = (ROOT / "docs/research/queer-history/victorian/wilde/sources/_pdf-text-mirror"
          / "Oscar Wilde, Merlin Holland, Rupert Hart-Davis - The Complete Letters of Oscar "
            "Wilde-Fourth Estate (2000).txt")
OUT = HERE / "data/_book_index.json"

# printed folio -> repo PDF page. Confirmed points, read at the page this session; the offset
# drifts across the volume so it is interpolated between anchors rather than assumed constant.
ANCHORS = [(21, 46), (28, 53), (59, 86), (66, 93), (251, 273), (283, 305), (352, 374),
           (410, 432), (420, 442), (423, 445), (443, 465), (463, 483), (484, 504), (496, 516),
           (528, 548), (557, 609), (561, 613), (623, 675), (650, 701), (845, 895), (894, 944),
           (911, 961), (923, 973), (1006, 1054), (1024, 1070), (1097, 1143), (1108, 1154),
           (1113, 1159), (1141, 1187), (1232, 1277)]


def folio_to_pdf(folio):
    """Interpolate between confirmed anchors. Returns (pdf_page, exact?)."""
    fol = [a for a, _ in ANCHORS]
    i = bisect.bisect_left(fol, folio)
    if i < len(fol) and fol[i] == folio:
        return ANCHORS[i][1], True
    lo = ANCHORS[i - 1] if i > 0 else ANCHORS[0]
    hi = ANCHORS[i] if i < len(ANCHORS) else ANCHORS[-1]
    off = round((lo[1] - lo[0] + hi[1] - hi[0]) / 2)
    return folio + off, False


ENTRY = re.compile(r"^([A-Z][^,\n]{1,44}(?:,\s*[^,\n0-9]{1,34})?),\s*((?:\d{1,4}[n\s,]*)+)$")
# long entries wrap onto an indented, number-only continuation line belonging to the entry above.
# Dropping these cost 2 of Clifton's 7 letters on the first build.
CONT = re.compile(r"^\s*\d{1,4}[n]?(?:\s*,\s*\d{1,4}[n]?)*\s*,?\s*$")


def build():
    text = MIRROR.read_text(encoding="utf-8", errors="replace")
    marks = sorted((m.start(), int(m.group(1)))
                   for m in re.finditer(r"=== \[PDF p\. (\d+)\] ===", text))
    starts = [s for s, _ in marks]

    def pdf_of(off):
        i = bisect.bisect_right(starts, off) - 1
        return marks[i][1] if i >= 0 else None

    rec_start, _ = folio_to_pdf(1231)
    gen_start, _ = folio_to_pdf(1237)
    out = {"recipients": {}, "general": {}, "_note":
           "Parsed from the OCR mirror; digits are unreliable until confirmed on the rendered "
           "index page. Recipients = letters addressed to. General = mentions."}

    cursor = 0
    last = None                      # (bucket, name) of the entry a continuation line belongs to
    for raw in text.split("\n"):
        off = text.find(raw, cursor)
        cursor = off + len(raw) if off >= 0 else cursor
        line = raw.strip()
        pg = pdf_of(off) or 0
        if pg < rec_start - 2 or not line:
            last = None
            continue
        bucket = "recipients" if pg < gen_start else "general"

        m = ENTRY.match(line)
        if m:
            name = re.sub(r"\s+", " ", m.group(1)).strip()
            folios = {int(x) for x in re.findall(r"\d{1,4}", m.group(2)) if 1 <= int(x) <= 1230}
            if not folios:
                last = None
                continue
            out[bucket][name] = sorted(set(out[bucket].get(name, [])) | folios)
            last = (bucket, name)
            continue

        # NB: no indentation test. The index indents continuation lines on the page, but the OCR
        # mirror strips leading whitespace, so any number-only line following an entry is one.
        if last and CONT.match(line):
            b, name = last
            more = {int(x) for x in re.findall(r"\d{1,4}", line) if 1 <= int(x) <= 1230}
            out[b][name] = sorted(set(out[b].get(name, [])) | more)
            continue
        last = None

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {OUT.name}: {len(out['recipients'])} recipients, "
          f"{len(out['general'])} general-index entries")
    print(f"(Index of Recipients from repo PDF {rec_start}; General Index from {gen_start})")


def lookup(term):
    idx = json.loads(OUT.read_text(encoding="utf-8"))
    t = term.lower()
    for bucket in ("recipients", "general"):
        for name, folios in sorted(idx[bucket].items()):
            if t in name.lower():
                pdfs = [f"{f}->{folio_to_pdf(f)[0]}{'' if folio_to_pdf(f)[1] else '~'}"
                        for f in folios]
                print(f"\n[{bucket}] {name}  ({len(folios)} entries)")
                print("   printed->pdf: " + ", ".join(pdfs))


def pages():
    """The index pages themselves, which are what actually need reading."""
    rec, _ = folio_to_pdf(1231)
    gen, _ = folio_to_pdf(1237)
    end = 1315
    print(f"Index of Recipients : repo PDF {rec}-{gen - 1}   ({gen - rec} pages)")
    print(f"General Index       : repo PDF {gen}-{end}      ({end - gen + 1} pages)")
    print(f"\nTOTAL {end - rec + 1} index pages to read at the page.")
    print("Transcribe each entry by eye; the OCR cannot resolve the two-column continuation lines.")


if __name__ == "__main__":
    if "--pages" in sys.argv:
        pages()
    elif "--build" in sys.argv:
        build()
    elif len(sys.argv) > 1:
        lookup(sys.argv[1])
    else:
        print(__doc__)
