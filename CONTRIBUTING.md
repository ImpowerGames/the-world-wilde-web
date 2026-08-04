# Contributing

This is a map of documented queer relationships. It began with Oscar Wilde's circle because that
is where the surviving paper is thickest, but the intended scope is wider — the Paris salons, the
women's networks, the Uranian and Chaeronea circles, anyone whose attachments left a record. If
you know a corner of it we have not covered, please add it.

The one rule that matters: **every claim carries a quotation and a citation.** Nothing here rests
on received anecdote, and nothing asserts more than its evidence supports.

---

## Running it

```bash
python tools/serve.py     # or: npm start
```

That rebuilds the data bundle, checks it, and serves the site at <http://localhost:8000>. There is
no JavaScript toolchain and nothing to `npm install` — `package.json` just wraps the Python
scripts. Python 3.8+ is all you need.
Opening `index.html` by double-clicking will *not* work — the browser refuses to fetch
`data/circle.json` from a `file://` page, and you will get an empty map with an error in it.

To check your edits without starting a server:

```bash
python tools/validate.py --check
```

Non-zero exit means something is wrong, and it prints what.

### If you touch the layout

Measure it, do not eyeball it:

```bash
python tools/layout_report.py --save before.json   # or: npm run layout
# ... make your change ...
python tools/layout_report.py --compare before.json
```

It counts crossing connections, people sitting on a line they are not part of, overlapping nodes,
and how far the force pass dragged each person from where the radial tree seated them.

This is not ceremony. Two changes during development looked fine on screen and measured clearly
worse: holding nodes to their seeded positions took crossings from 27 to 54, and three placement
hints turned out to be costing five crossings apiece. Neither was visible by eye. The layout is
deterministic, so the numbers are comparable between runs.

---

## Where things live

```
index.html              markup
assets/css/circle.css   presentation
assets/js/circle.js     behaviour
data/people/*.json      one file per person          <- edit these
data/relationships/*.json  one file per connection   <- and these
data/works.json         the bibliography             <- and this
data/circle.json        GENERATED bundle, do not hand-edit
tools/validate.py       validator + bundler
tools/serve.py          local dev server
audits/                 the human verification ledger
dossiers/               long-form research notes, per cluster
```

One file per entity is deliberate: it keeps diffs small and means two people adding different
people rarely conflict. `data/circle.json` is generated from those files by `tools/validate.py` —
regenerate it before committing, and never edit it by hand.

---

## Adding a person

Create `data/people/<id>.json`. Ids are lowercase, hyphenated, and stable — other files reference
them, so choose one you will not want to change.

```jsonc
{
  "id": "levy",
  "name": "Amy Levy",
  "sort_name": "Levy, Amy",        // the node label is the part before the comma
  "aka": [],
  "born": {"y": 1861}, "died": {"y": 1889},   // y / m / d, any of them optional, or null
  "group": "aesthete",             // see the group list below
  "gender": "f",                   // "m", "f", or null if the record does not say
  "bio": "…",                      // a paragraph a reader can use
  "bio_note": "…",                 // where each fact came from; shown collapsed at the foot
  "bio_sources": ["beckman-2000-levy"],
  "context_engagements": [],
  "research_status": "phase-a"
}
```

Groups: `core`, `family`, `society`, `aesthete`, `trials`, `chaeronea`, `later`, `liaisons`,
`beyond`. If your additions need a new one, propose it — adding a group means adding a colour, and
the palette is [ColorBrewer *Paired*](https://colorbrewer2.org/#type=qualitative&scheme=Paired&n=9),
whose light/dark pairs are used to put related groups side by side.

Where the record gives no name and we are using a description in its place — "A fisherman,
Napoule" — set `"name_is_descriptor": true`, and the map will show the label in quotation marks so
it is not mistaken for a surname.

If they have a Wikipedia article, add `wikipedia` and `wikidata`. **Confirm the entity by birth and
death year before you trust it** — our Alfred Taylor was linked for a day to a Boer War officer of
almost the same age, and name matching has twice returned a different person entirely. Someone with
no article is the normal case here rather than an omission: most of the men in the trials records
left nothing to write an article from.

For a portrait, use the image at the top of that article, not Wikidata's image property. The two are
separate databases and disagree often, and the article's is the one a reader will see when they
follow the link. Check the licence on the file page — everything here is public domain or a
public-domain dedication — then run `python tools/crop_faces.py` and record it in
`portraits/credits.json`.

### Nudging a node that lands badly

The layout is a force simulation, and a hub distorts it: Wilde holds 35 connections, so his spokes
sweep the whole ring around him and a node can settle on top of lines it has nothing to do with.
When that happens, give the person a placement hint:

```jsonc
"layout": {"x": 1045, "y": 180, "why": "why this node needed moving"}
```

**Try without one first.** Three hints were added while the layout was force-only; after radial
seeding landed they measured *worse* than no hints at all (crossings 32 → 27) and were removed. If
you find yourself adding several, that is a sign the layout needs fixing rather than overriding.

Coordinates are in the 1200×800 viewBox. It is a **pull, not a pin** — the node is drawn hard
toward the point but still takes part in collision and line-clearance, so it settles near the hint
rather than on top of whatever is already there. Include `why`, so the next person knows whether
the reason still applies after the surrounding data changes.

---

## Adding a connection

Create `data/relationships/<a>--<b>.json`, where the two ids are **in alphabetical order** and the
filename matches the `id` field. The validator enforces both.

```jsonc
{
  "id": "levy--lee",
  "people": ["lee", "levy"],       // sorted
  "certainty": "desire-expressed",
  "certainty_status": "proposed",
  "start": {"y": 1886}, "end": null,
  "date_label": "…",               // free text shown under the names
  "direction": "levy",             // desire-expressed only: who expressed it
  "outcome": "unreciprocated",     // desire-expressed only: declined / unknown / unreciprocated
  "summary": "…",
  "certainty_reasoning": "…",      // why this class and not a stronger one
  "sources": [ /* see below */ ]
}
```

### The five certainty classes

These describe **how we know**, not what happened. The map deliberately makes **no claim about
sexual acts** in either direction — criminal law was designed to keep that evidence out of the
record, so treating its absence as a finding would mistake the effect of prosecution for a fact
about someone's life.

| Class | Means |
|---|---|
| `marriage` | a legal marriage |
| `self-reported` | a participant's own words survive — letters, diaries, sworn testimony |
| `second-hand` | someone else who was there, or a historian, attests it |
| `uncorroborated` | asserted somewhere but nothing supports it; **requires a `disputed` block** |
| `desire-expressed` | the record is one-sided: an approach or a declaration, with a `direction` and an `outcome` |

An `uncorroborated` connection must carry `disputed` with `claim`, `asserted_by`, `disputed_by`
and `grounds`. Leave `disputed_by` **null** when nothing actually disputes the claim — a statement
of absence is not a party, and the map renders the fields as labelled lines.

---

## Sources: the part that matters

```jsonc
{
  "work": "letters-2000",          // a key in data/works.json
  "locator": "p. 1177",
  "locator_type": "page",
  "quote": "…",                    // transcribed exactly; "…" marks an honest cut
  "context": "Wilde to Robert Ross, late March 1900, Paris",
  "speaker": "Lord Alfred Douglas",// only when the words are not the work-author's
  "voice": "period",               // "period" or "modern" — see below
  "evidence_date": {"y": 1900, "m": 3},
  "supports": "what this quotation is here to establish",
  "verification": "verified-exact",
  "how_verified": "pdf-at-page",
  "verified_by": "…", "verified_on": "2026-08-04",
  "provenance": "which copy, which page, how it was read"
}
```

**`voice` is per quotation, not per book.** `period` means the text is *entirely* in the words of
someone alive at the time — a letter, a diary, sworn testimony. `modern` means a historian or
editor is writing *about* them. An editor's footnote inside a volume of Wilde's letters is modern;
a letter of Douglas's printed inside that same footnote is period; a biographer's sentence that
merely quotes a period phrase within itself is modern, because it is not entirely theirs. Period
quotations are set between large quotation marks so first-hand evidence is legible at a glance.

**`evidence_date` is the date of the thing evidenced**, never the publication year of the book
quoting it. A 1985 biography describing a 1908 holiday carries 1908. Sources are shown in this
order, so a publication year files modern commentary among the contemporary record. Leave it null
where a quotation evidences no dated event.

**Verification chips.** `verified-exact` and `verified-elision` both display as ✓ and mean someone
opened the source, found the passage on the page, and transcribed it. `unverified` displays as ⧖
and means either a passage located in a text layer but never checked against the page, or a
**pointer** — a claim recorded with nothing transcribed yet, naming only where to look. Pointers
have an empty `quote` and say so on their face.

Never mark something verified you have not seen on the page. A text layer, an OCR dump or a search
index is for *finding*; the rendered page is for *verifying*. Several sources in `works.json` carry
warnings about this — page offsets in scanned books are frequently not constant, and at least two
of ours shift by several pages partway through.

---

## Adding a source book

Add a key to `data/works.json` with `author`, `title`, `year`, `short_cite`, and `kind`
(`primary`, `primary-edition`, `trial-transcript`, `interview`, `secondary`, `secondary-web`).
Include a `note` recording anything a future reader needs: the printed-to-PDF offset you
established and the pages you verified it at, whether the scan has folios at all, which edition
you actually read. Those notes have saved a great deal of re-work.

---

## What gets rejected

- A claim with no quotation behind it.
- A quotation marked verified that was read in a search index rather than on the page.
- Inferring an age, a date or a relationship the source does not state. If the record says "boy",
  it says "boy" — that word was used of grown men, and the inference is not ours to make.
- Reading absence of evidence as evidence of absence, in either direction.

## What is welcome

Corrections most of all, including to things already marked verified. If a locator is wrong, a
transcription drifts, or a classification overstates its evidence, open an issue or a pull request
and say what you checked. Null findings are worth recording too: several entries here note that a
named biographer, searched in full, never makes a claim commonly attributed to them, and that is a
useful thing for the next person to know.
