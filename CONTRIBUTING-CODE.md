# Contributing code and data

If you are comfortable editing code or json files, you are welcome to submit a pull request with your edits.

Every claim must carry a quotation and a citation. See [CONTRIBUTING.md](CONTRIBUTING.md).

(If you would rather just tell us what you know and let someone else update the site for you, [open a ticket]({{repo}}/issues/new/choose).)

---

## Running the map locally

Download the repo and run:

```bash
python tools/serve.py
```

That rebuilds the data bundle, checks it, and serves the site at <http://localhost:8000>. There is no JavaScript toolchain. Python 3.8+ is all you need. Opening `index.html` by double-clicking will _not_ work — the browser refuses to fetch `data/web.json` from a `file://` page, and you will get an empty map with an error in it.

To check your edits without starting a server:

```bash
python tools/validate.py --check
```

Non-zero exit means something is wrong. It will print errors if it encounters any.

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
  "sexuality_sources": [],
  "research_status": "phase-a",
}
```

Groups: `core`, `family`, `society`, `aesthete`, `trials`, `chaeronea`, `later`, `liaisons`, `beyond`. If your additions need a new one, propose it. Adding a group means adding a color. The color palette we use for spheres is [ColorBrewer](https://colorbrewer2.org/#type=qualitative&scheme=Paired&n=9).

Where the record gives no name and we are using a description in its place — "A fisherman, Napoule" — set `"name_is_descriptor": true`, and the map will show the label in quotation marks so it is not mistaken for a surname.

If they have a Wikipedia article, add `wikipedia` and `wikidata`. Confirm the entity by birth and death year before you trust it.

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
  "evidence_date": { "y": 1897, "m": 6, "d": 5 }, // When the thing HAPPENED (not when it was recorded/published)
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

### The certainty classes

These describe how we know, not what happened. The map deliberately makes **no claim about sexual acts** in either direction — criminal law was designed to keep that evidence out of the record, so treating its absence as a finding would mistake the effect of prosecution for a fact
about someone's life.

| Class                  | Means                                                                                                                                                                                                                                                                                      |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `married`              | a legal marriage                                                                                                                                                                                                                                                                           |
| `self-reported`        | a participant's own words survive — letters, diaries, sworn testimony                                                                                                                                                                                                                      |
| `second-hand`          | someone else who was there, or a historian, attests it                                                                                                                                                                                                                                     |
| `uncorroborated`       | asserted somewhere but nothing supports it; **requires a `disputed` block**                                                                                                                                                                                                                |
| `attraction-expressed` | the record is one-sided: a declaration, an approach, or admiration noted in passing, with a `direction` and an `outcome`. **The bar is low on purpose** — one sentence admiring the appearance of an individual qualifies. Use `outcome: unknown` if the result of the advance is unknown. |
| `platonic`             | a documented friendship or acquaintance — correspondence, visits, professional friendship — with no evidence of attraction or romance. Platonic connections draw no line on the map.                                                                                                       |

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
  "how_verified": "page-image", // how directly the words were read
  "document": "letter", // what is quoted, when it differs from the work
  "verified_against": "original", // only if you read the document itself
  "verified_on": "2026-08-04",
  "provenance": "which copy, which page, how it was read",
  "lang": "fr", // only when the quotation is not in English
  "translation": "…", // then this is REQUIRED
  "translation_note": "who translated it, and any published version that differs",

  // ONE of these two, at most — where the original document is. See "The document itself" below.
  "facsimile": { "archive": "hrc", "item": "2700", "pages": [1, 2, 3, 4] },
  "manuscript": {
    "repository": "William Andrews Clark Memorial Library, UCLA",
  },
}
```

**`speaker` is who is speaking, and after the comma in what capacity** — "examination-in-chief", "letter to John Gray". Not the work's title: the citation prints that already. The validator warns when a speaker's tail repeats its own work's title. The original stays the quotation — it is what you verified at the page and what the connection is evidenced by — and the English translation is printed beneath it. If a published English version exists and differs from yours, say so in `translation_note` rather than silently preferring either.

**The citation's byline links itself, on a match of the whole name.** Write `speaker` the way the person's file writes their `name` and the link appears; if you write it any other way and the citation will fallback to plain text. Case, accents and punctuation are folded, and `aka` and `sort_name` are matched too, so _Renée Vivien_ reaches a node spelled _Renee_. If a name you expect to link does not, add the variant to `aka`.

**`voice` is per quotation, not per book.** `period` means the text is _entirely_ in the words of someone alive at the time — a letter, a diary, sworn testimony. `modern` means a historian or editor is writing _about_ them. An editor's footnote inside a volume of Wilde's letters is modern; a letter of Douglas's printed inside that same footnote is period; a biographer's sentence that merely quotes a period phrase within itself is modern, because it is not entirely theirs. Period quotations are set between large quotation marks so first-hand evidence is legible at a glance.

**A courtroom exchange is `voice: "exchange"`, not `period`.** `period` promises a single voice and is set in quotation marks accordingly; a cross-examination has counsel and witness in it. An exchange is drawn as a transcript from its `turns`. The validator refuses an exchange with no turns, and refuses turns that do not reproduce the quotation word for word. Leave `who` empty where the record does not say whose turn it is.

**A quotation not in English keeps its own language and gains a translation.** Set `lang` and `translation`; the validator refuses one without the other. A quotation that reads as French, German, Italian or Latin and carries no `lang` draws a warning, and a translation parked inside `context` is a hard error. If the warning is wrong — an English quotation dense with French phrases — ignore it; it does not fail the build.

### Dates

`evidence_date` is **the date of the thing evidenced** — the day the letter was written, the diary entry made, the testimony sworn. It is a claim about the event itself, not the date the source was published later. Add `"circa": true` when it is approximate — approximate meaning **the value itself is in doubt**, not that a finer unit is missing: Wilde and Douglas met in 1891, a year the editors state outright with only the month uncertain, so that is not `circa`.

When the thing happened across a **span**, give the date a `to` rather than writing the range into a `label`: `{"y": 1897, "m": 1, "to": {"y": 1897, "m": 3}}` displays as _January–March 1897_, and every range on the map is then spelled the same way. `label` is for what a date object cannot say at all; the validator refuses a date carrying both.

Sources display in chronological order. If a source is undated, use **`order_hint`** instead:

```json
"evidence_date": null,
"order_hint": {"y": 1897, "m": 8, "why": "Sox says outright \"We do not know exactly when Fothergill appeared\". Wilde's letter of 21 September counts the six days as falling inside his last month at Berneval, so the visit sits in August or early September."}
```

It sorts exactly as a date would, and it is not a date. The card will say — _"Undated — placed here for reading order: …"_. The validator enforces both: a source may not carry `evidence_date` and `order_hint` together, and an `order_hint` without a `why` is an error.

### Verification

Unverified quotes are marked with an `⧖ unverified` chip and means the passage was located in an index or OCR dump but never checked against the page. ⧖ also marks **leads**: pointers to a potential source with nothing transcribed yet.

Never mark something verified you have not seen on the page. A text layer, an OCR dump or a search index is for _finding_; the rendered page is for _verifying_. Page offsets in scanned books are frequently not reliable enough for citation.

Verification asks **three separate questions**, and each has its own field. One field answering all three produced values that overlapped and could not be told apart — `archive-org` and `web` named a *medium*, `pdf-text` named a *reading method*, `manuscript` named a *document*.

**`how_verified` — how directly were the words read?**

| value          | means                                                                   |
| -------------- | ----------------------------------------------------------------------- |
| `page-image`   | read on a reproduction of the page: a scan, a IIIF image, microfilm     |
| `text-layer`   | taken from extracted or OCR text; **the page itself was not looked at** |
| `in-hand`      | read in the physical object                                             |
| `as-published` | born-digital — a web page, an EPUB — read as its publisher renders it   |
| `unverified`   | not yet established                                                     |

**The medium is deliberately absent.** Whether it was a PDF, archive.org, a website or a shelf copy belongs in `provenance`, which already records it exactly — _"IA in.ernet.dli.2015.499238, leaf 326"_ — and which says nothing about whether the reading can be trusted. What matters here is only whether somebody looked at the page or trusted a machine's transcription of it.

**`document` — what kind of thing is being quoted?** Set it only when the document differs from the work it was read in: a letter printed in an edition of the letters, testimony printed in a trial transcript. A historian's own sentence leaves it unset, because there the work *is* the document and a label would say nothing.

Written by hand: `letter`, `telegram`, `postcard`, `diary`, `inscription`, `manuscript`.
Printed or spoken: `memoir`, `testimony`, `interview`, `pamphlet`, `novel`, `essay`, `poem`, `typescript`.

**`verified_against` — which document was read?** Omit it, and the reader understands you read the work you cite. Set it to `"original"` when you went to the document itself, or to a photograph of it.

That claim only means something for something **written by hand**. A printed pamphlet has no original behind the print and no emphasis a compositor did not set, so the validator refuses `verified_against: "original"` on one. It also refuses the claim alongside `text-layer`, since reading an original means seeing it.

The card shows the document as a chip, ticked when the original has been read — **Letter ✓** against a bare **Letter**. So a reader can tell at a glance which quotations rest on Wilde's own hand and which rest on his editors.

**The chip is also a filter.** Clicking it narrows the panel to that kind of document, and clicking it again lets go. Where a panel holds more than one kind, a select appears beside the year range listing them with counts — _Letters · 251_, _Testimony · 42_ — and the two controls move the same piece of state, so either follows the other.

### Formatting & emphasis

**Source emphasis is preserved in the quote.** Mark it inside the `quote` text with `*italics*`, `_underline_`, `__double underline__`, `**bold**`, or `~~strikethrough~~`; the renderer converts the markers to real type when the card is drawn. The number of underscores is the number of underlines. Use markers only for emphasis that is actually in the source, never for editorial highlighting of your own.

**A printed edition cannot settle emphasis, and the Complete Letters say so themselves.** Their note on the text: _"The printing of titles has been standardised: those of poems, stories and articles are printed in roman type between quotation marks; those of books, plays, periodicals and ships in italics. All foreign words are printed in italics unless the whole letter is in French. All underlined words are italicised, but no indication is given of the occasional words which have more than one underlining."_ One italic therefore stands for three unrelated things — Wilde's underline, a title, a foreign word — and the difference between one underline and three is thrown away.

So: use `*italics*` for what is plainly a title or a foreign word, and `_underline_` for an English word italicised for stress. That second call is **provisional until someone reads the manuscript**, and it should say so in `provenance`. When the document has been read, set `verified_against` to `original` and record any emphasis found there — including a null finding.

### The rule: follow the manuscript, except for italics

**Whatever mark is on the page is the mark that goes in the quote.** If it's underlined in the letter, underline it in the quote. If it's struck through in the letter, strike through it in the quote. If the writer put quotation marks round a title, keep them — even where the printed edition has taken them away. The number of underscores in the markup should reflect the number of underlines in the letter: `_one_`, `__two__`.

**Italics are the one deliberate departure.** Handwritten text cannot italicise, which is the whole reason italics need a separate rule: the only marks available to someone writing by hand are the underline and the strike-through, so a writer underlines a title as an instruction to a compositor, not for stress. Italics are applied here as an editorial consistency — books, plays, periodicals, ships and foreign words — on top of whatever the hand actually did. Where he underlined the title as well, **both marks are written**:

| In the manuscript                                       | Markup                           | Reads as                                    |
| ------------------------------------------------------- | -------------------------------- | ------------------------------------------- |
| `do` with one underline under it                        | `_do_`                           | stress, in Wilde's own hand                 |
| `me` with two underlines under it                       | `__me__`                         | stress, doubled                             |
| _Salomé_ with a underline under it                      | `_*Salomé*_`                     | a title, and he underlined it               |
| `'Ballad of Reading Gaol'`, single quotes, no underline | `'*The Ballad of Reading Gaol*'` | his quotation marks kept, our italic added  |
| a title nobody has checked yet                          | `*Lady Windermere's Fan*`        | italicised by convention; manuscript unread |

Two consequences worth having. **The markup records whether anyone has looked** — `*Salomé*` is a title italicised by convention, manuscript unread or unmarked; `_*Salomé*_` means someone opened the letter and found the stroke. And **the punctuation stays his**, so a reader can see where the editors' italic replaced a pair of inverted commas rather than translating an underline.

**A mark that only exists because of where the line ended is not preserved.** These transcriptions do not keep non-paragraph line breaks, so anything that is an artefact of them goes too. Wilde wrote the Ballad's title across three lines and repeated the quotation mark at each break —

```
             'The
'Ballad of Reading'
Gaol'
```

— which is a line-wrap convention, not four quotations. It normalises to one opening and one closing mark: `'The Ballad of Reading Gaol'`. The same goes for a word broken by a hyphen at the edge of a sheet. Note the normalisation in `provenance`, and keep it to marks that the line break alone produced.

Where restoring a mark makes the quotation differ from the printed page it cites, say so in `provenance`. The citation still locates the passage; the manuscript governs how it was marked.

**Typed and printed sources are matched exactly.** A typescript, a printed book, a typed transcript can all italicise, embolden, underline and strike through, so there is no convention to apply — reproduce what is set, mark for mark.

**Deviations in the printed edition.** The editors of _The Complete Letters of Oscar Wilde_ silently convert title quotation marks to italics: Wilde wrote `'Ballad of Reading Gaol'` in single quotes and the page prints it in italic with no quotation marks at all. They also flatten every multiple underline to a single italic, by their own account — `me` and `groom` in the Harris letter of 13 June 1897 are both underlined twice and both printed as ordinary italic.

**Not every horizontal stroke is an underline.** Wilde's long diagonal strokes between paragraphs are paragraph marks. A rule under an interlineated phrase — `lighter as well as`, carried above the line on a caret in that same Harris letter — is an insertion mark. A stroke across a printed letterhead cancels it, as on the Albemarle Club sheet to Alexander.

### The document itself

Two optional fields say where the original is. A source may carry at most one of them.

**`facsimile`** — the archive publishes page images, and the card gets a _Read the manuscript_ button opening the reader.

```jsonc
"facsimile": {
  "archive": "hrc",       // a directory under manuscripts/ with a MANIFEST.json
  "item": "2700",         // an itemId in that manifest
  "pages": [1, 2, 3, 4],  // page numbers WITHIN the item, ascending, no repeats
  "caption": "one folded sheet and its envelope: sheet 1 shows sides 1 and 4…"
}
```

`pages` are the pages of the **letter**, not of the sentence you quoted.

**Images are linked.** They come from the holding archive's IIIF service at request time, so each scan is served by the institution that made it, under the rights marker that institution attached to it — which the reader prints beneath the page. We keep a local copy in our _private_ repository for safety.

**`manuscript`** — the original survives, but not in a place it can be easily viewed online.

```jsonc
"manuscript": {
  "repository": "William Andrews Clark Memorial Library, UCLA",
  "url": "https://…"    // optional, if the archive has a record page for it
}
```

Write the repository out in full, as it should read on the card — not the abbreviation the Complete Letters print. This is the common case by far: of the letters this map quotes from that volume, eight have manuscripts at the Ransom Center and around a hundred are at the Clark.

---

## Adding a source book

Add a key to `data/works.json` with `author`, `title`, `year`, `short_cite`, and `kind` (`primary`, `primary-edition`, `trial-transcript`, `interview`, `secondary`, `secondary-web`). Include a `note` recording anything a future reader needs: the printed-to-PDF offset you established and the pages you verified it at, whether the scan has folios at all, which edition you actually read. Those notes will save others a great deal of re-work.

---

### If you touch the layout code

Please measure the result and make sure it doesn't increase the crossing or overlap counts:

```bash
python tools/layout_report.py --save before.json
python tools/layout_report.py --compare before.json
```

The layout report counts crossing connections, nodes overlapping a line they are not part of, nodes overlapping each other, and how far the force pass dragged each person from where the radial tree seated them. The layout is deterministic, so the numbers are comparable between runs.
