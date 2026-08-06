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

That rebuilds the data bundle, checks it, and serves the site at <http://localhost:8000>. There is no JavaScript toolchain. Python 3.8+ is all you need. Opening `index.html` by double-clicking will _not_ work — the browser refuses to fetch `data/circle.json` from a `file://` page, and you will get an empty map with an error in it.

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

It counts crossing connections, people sitting on a line they are not part of, overlapping nodes, and how far the force pass dragged each person from where the radial tree seated them. The layout is deterministic, so the numbers are comparable between runs.

---

## Where things live

```
index.html              markup
assets/css/circle.css   presentation
assets/js/circle.js     behaviour
content/ABOUT.md        the About panel's text       <- edit this for prose
data/people/*.json      one file per person          <- edit these
data/relationships/*.json  one file per connection   <- and these
data/works.json         the bibliography             <- and this
data/circle.json        GENERATED bundle, do not hand-edit
tools/validate.py       validator + bundler
tools/serve.py          local dev server
tools/layout_report.py  measure the drawing
tools/test_navigation.py / test_solo.py   assert the interactions
```

**To change what the About panel says, edit `content/ABOUT.md`**. It's a plain markdown file. `tools/validate.py` compiles it into the bundle. Two placeholders are filled by the page: `{{line:marriage}}` (and the other four certainties) draws the connection line, and
`{{colophon}}` becomes the generated build line. Writing `{{line:…}}` at the start of a bullet replaces the bullet's disc with the line itself.

Having one file per entity keeps diffs small and means two people adding different people rarely conflict. `data/circle.json` is generated from those files by `tools/validate.py` — regenerate it before committing, and never edit it by hand.

---

## Adding a person

Create `data/people/<id>.json`. Ids are lowercase, hyphenated, and stable — other files reference them, so choose one you will not want to change.

```jsonc
{
  "id": "levy",
  "name": "Amy Levy",
  "sort_name": "Levy, Amy", // the node label is the part before the comma
  "aka": [],
  "born": { "y": 1861 },
  "died": { "y": 1889 }, // y / m / d, any of them optional, or null
  "group": "aesthete", // see the group list below
  "gender": "f", // "m", "f", or null if the record does not say
  "bio": "…", // a paragraph a reader can use
  "bio_note": "…", // where each fact came from; shown collapsed at the foot
  "bio_sources": ["beckman-2000-levy"],
  "context_engagements": [],
  "research_status": "phase-a",
}
```

Groups: `core`, `family`, `society`, `aesthete`, `trials`, `chaeronea`, `later`, `liaisons`, `beyond`. If your additions need a new one, propose it — adding a group means adding a colour, and the palette is [ColorBrewer](https://colorbrewer2.org/#type=qualitative&scheme=Paired&n=9).

Where the record gives no name and we are using a description in its place — "A fisherman, Napoule" — set `"name_is_descriptor": true`, and the map will show the label in quotation marks so it is not mistaken for a surname.

If they have a Wikipedia article, add `wikipedia` and `wikidata`. **Confirm the entity by birth and death year before you trust it**.

For a portrait, use the image at the top of that article, not Wikidata's image property. The two are separate databases and disagree often, and the article's is the one a reader will see when they follow the link. Check the licence on the file page — everything here is public domain or a
public-domain dedication — then crop it to the sitter's face and record it in `portraits/credits.json`.

---

## Adding a connection

Create `data/relationships/<a>--<b>.json`, where the two ids are **in alphabetical order** and the filename matches the `id` field. The validator enforces both.

```jsonc
{
  "id": "levy--lee",
  "people": ["lee", "levy"], // sorted
  "certainty": "attraction-expressed",
  "certainty_status": "proposed",
  "start": { "y": 1886 },
  "end": null,
  "date_label": "…", // free text shown under the names
  "evidence_date": { "y": 1897, "m": 6, "d": 5 }, // WHEN THE THING EVIDENCED HAPPENED
  "order_hint": { "y": 1897, "m": 8, "why": "..." }, // only when the date is genuinely unknown
  "direction": "levy", // attraction-expressed only: who expressed it
  "outcome": "unreciprocated", // attraction-expressed only: declined / unknown / unreciprocated
  "summary": "…",
  "certainty_reasoning": "…", // why this class and not a stronger one
  "sources": [
    /* see below */
  ],
}
```

### The five certainty classes

These describe **how we know**, not what happened. The map deliberately makes **no claim about sexual acts** in either direction — criminal law was designed to keep that evidence out of the record, so treating its absence as a finding would mistake the effect of prosecution for a fact
about someone's life.

| Class                  | Means                                                                                                                                                                                                                                                                                      |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `married`              | a legal marriage                                                                                                                                                                                                                                                                           |
| `self-reported`        | a participant's own words survive — letters, diaries, sworn testimony                                                                                                                                                                                                                      |
| `second-hand`          | someone else who was there, or a historian, attests it                                                                                                                                                                                                                                     |
| `uncorroborated`       | asserted somewhere but nothing supports it; **requires a `disputed` block**                                                                                                                                                                                                                |
| `attraction-expressed` | the record is one-sided: a declaration, an approach, or admiration noted in passing, with a `direction` and an `outcome`. **The bar is low on purpose** — one sentence admiring the appearance of an individual qualifies. Use `outcome: unknown` if the result of the advance is unknown. |

An `uncorroborated` connection must carry `disputed` with `claim`, `asserted_by`, `disputed_by` and `grounds`. Leave `disputed_by` **null** when nothing actually disputes the claim.

---

## Adding a source

```jsonc
{
  "work": "letters-2000", // a key in data/works.json
  "locator": "p. 1177",
  "locator_type": "page",
  "quote": "…", // transcribed exactly; "…" marks an honest cut
  "context": "Wilde to Robert Ross, late March 1900, Paris",
  "speaker": "Lord Alfred Douglas", // only when the words are not the work-author's
  // write it EXACTLY as the person's `name` (or an `aka`) and the
  // citation links to their node; anything else stays plain text
  "voice": "period", // "period", "exchange" or "modern" — see below
  "turns": [{ "who": "Carson", "text": "…" }], // REQUIRED when voice is "exchange"
  "evidence_date": { "y": 1900, "m": 3 },
  // …or a RANGE, when the thing happened across a span:
  // "evidence_date": {"y": 1897, "m": 1, "to": {"y": 1897, "m": 3}}   -> "January–March 1897"
  "supports": "what this quotation is here to establish",
  "verification": "verified-exact",
  "how_verified": "pdf-image",
  "verified_by": "…",
  "verified_on": "2026-08-04",
  "provenance": "which copy, which page, how it was read",
  "lang": "fr", // only when the quotation is not in English
  "translation": "…", // then this is REQUIRED
  "translation_note": "who translated it, and any published version that differs",
}
```

**Quote the whole letter, and elide only what does not characterise the relationship.** This is the reverse of the obvious habit, which is to lift the sentence that proves the point. Do not do that. Start from the whole letter and cut only what says nothing about the two people — an address, a standing order, a train time — marking each cut with an ellipsis as usual.

**Friendship counts.** A quotation does not have to reach romance to be worth recording, and a person does not have to carry a connection line to belong on the map. Warmth between men in this period is part of what the record shows and part of what the map is for; George Alexander and
Graham Hill are here as nodes with no line, holding letters that are simply fond. Record the friendship, let the certainty class stay empty, and let a reader see the affection and make a judgement for themselves.

**Read it at the page yourself.** Either in a physical copy or a digital reproduction. Do not rely on OCR. An OCR mirror's attribution can often drift by a few pages. Locate with the mirror; cite from the page.

**A quotation not in English keeps its own language and gains a translation.** Set `lang` and `translation`; the validator refuses one without the other. A quotation that reads as French, German, Italian or Latin and carries no `lang` draws a warning, and a translation parked inside `context` is a hard error. If the warning is wrong — an English quotation dense with French phrases — ignore it; it does not fail the build.

**`speaker` is who is speaking, and after the comma in what capacity** — "examination-in-chief", "letter to John Gray". Not the work's title: the citation prints that already. The validator warns when a speaker's tail repeats its own work's title. The original stays the quotation — it is what you verified at the page and what the connection is evidenced by — and the English translation is printed beneath it. If a published English version exists and differs from yours, say so in `translation_note` rather than silently preferring either.

**Anything you put in a source is searchable from its page.** The sources filter reads the quotation, the translation and its note, the context line, the speaker, the addressee, what it supports, the work title and author, the locator, the provenance and the turn labels. You do not have to register a new field anywhere for it to be findable - but a fact recorded ONLY in a relationship-level note (certainty_reasoning, a disputed block) is reachable from the map search and not from the source filter, because the filter is per quotation. The filter appears from four sources up; below that a page shows its sources plain. Matches are highlighted in place by walking text nodes - if you add markup to a card, do not introduce a text-node-splitting wrapper mid-phrase, or the highlight will stop finding phrases that cross it.

**The citation's byline links itself, on a match of the whole name.** Write `speaker` the way the person's file writes their `name` and the link appears; if you write it any other way and the citation will fallback to plain text. Case, accents and punctuation are folded, and `aka` and `sort_name` are matched too, so _Renée Vivien_ reaches a node spelled _Renee_. If a name you expect to link does not, add the variant to `aka`.

**A courtroom exchange is `voice: "exchange"`, not `period`.** `period` promises a single voice and is set in quotation marks accordingly; a cross-examination has counsel and witness in it. An exchange is drawn as a transcript from its `turns`. The validator refuses an exchange with no turns, and refuses turns that do not reproduce the quotation word for word. Leave `who` empty where the record does not say whose turn it is.

**`voice` is per quotation, not per book.** `period` means the text is _entirely_ in the words of someone alive at the time — a letter, a diary, sworn testimony. `modern` means a historian or editor is writing _about_ them. An editor's footnote inside a volume of Wilde's letters is modern; a letter of Douglas's printed inside that same footnote is period; a biographer's sentence that merely quotes a period phrase within itself is modern, because it is not entirely theirs. Period quotations are set between large quotation marks so first-hand evidence is legible at a glance.

**`evidence_date` is the date of the thing evidenced**, never the publication year of the book quoting it. A 1985 biography describing a 1908 holiday carries 1908. Sources are shown in this order, so a publication year files modern commentary among the contemporary record. Leave it null where a quotation evidences no dated event.

**Verification chips.** `verified-exact` and `verified-elision` both display as ✓ and mean someone opened the source, found the passage on the page, and transcribed it. `unverified` displays as ⧖ and means either a passage located in a text layer but never checked against the page, or a
**pointer**. Pointers are claims recorded with nothing transcribed yet, naming only where to look.

Never mark something verified you have not seen on the page. A text layer, an OCR dump or a search index is for _finding_; the rendered page is for _verifying_. Several sources in `works.json` carry warnings about this — page offsets in scanned books are frequently not constant.

---

## Adding a source book

Add a key to `data/works.json` with `author`, `title`, `year`, `short_cite`, and `kind` (`primary`, `primary-edition`, `trial-transcript`, `interview`, `secondary`, `secondary-web`). Include a `note` recording anything a future reader needs: the printed-to-PDF offset you
established and the pages you verified it at, whether the scan has folios at all, which edition you actually read. Those notes will save others a great deal of re-work.

---

## What gets rejected

- A claim with no quotation behind it.
- A quotation marked verified that was read in a search index rather than on the page.
- Inferring an age, a date or a relationship the source does not state. If the record says "boy", it says "boy" — that word was often used affectionately to refer to grown men at the time, and the inference is not ours to make.
- Reading absence of evidence as evidence of absence, in either direction.

## What is welcome

Corrections most of all, including to things already marked verified. If a locator is wrong, a transcription drifts, or a classification overstates its evidence, open an issue or a pull request and say what you checked. Null findings are worth recording too.

## Dates

`evidence_date` is **the date of the thing evidenced** — the day the letter was written, the diary entry made, the testimony sworn. It is a claim about the world. Add `"circa": true` when it is approximate — approximate meaning **the value itself is in doubt**, not that a finer unit is missing: Wilde and Douglas met in 1891, a year the editors state outright with only the month uncertain, so that is not `circa`.

When the thing happened across a **span**, give the date a `to` rather than writing the range into a `label`: `{"y": 1897, "m": 1, "to": {"y": 1897, "m": 3}}` displays as _January–March 1897_, and every range on the map is then spelled the same way. `label` is for what a date object cannot say at all; the validator refuses a date carrying both.

Sources display in date order, so it is tempting, when a run reads out of sequence, to give an undated source a plausible date and move on. Do not do this. Use **`order_hint`** instead:

```json
"evidence_date": null,
"order_hint": {"y": 1897, "m": 8, "why": "Sox says outright \"We do not know exactly when Fothergill appeared\". Wilde's letter of 21 September counts the six days as falling inside his last month at Berneval, so the visit sits in August or early September."}
```

It sorts exactly as a date would, and it is not a date. The card will say — _"Undated — placed here for reading order: …"_. The validator enforces both: a source may not carry `evidence_date` and `order_hint` together, and an `order_hint` without a `why` is an error.

# Verification

The `how_verified` field records how a source was verified.

| value           | means                                        |
| --------------- | -------------------------------------------- |
| `pdf-image`     | read from a rendered image of a page         |
| `pdf-text`      | read from a PDF's text layer or OCR mirror   |
| `archive-org`   | read from the Internet Archive (archive.org) |
| `web`           | read from a webpage (not archive.org)        |
| `digital-copy`  | read from a local digital copy of a source   |
| `physical-copy` | read from a physical copy of a source        |
| `unverified`    | not yet established                          |
