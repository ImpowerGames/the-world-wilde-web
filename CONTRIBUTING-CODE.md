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
| `platonic`             | a documented friendship or acquaintance — correspondence, visits, professional friendship — with no evidence of attraction or romance. Platonic connections draw no line on the map. |

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
  "verified_on": "2026-08-04",
  "provenance": "which copy, which page, how it was read",
  "lang": "fr", // only when the quotation is not in English
  "translation": "…", // then this is REQUIRED
  "translation_note": "who translated it, and any published version that differs",
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
