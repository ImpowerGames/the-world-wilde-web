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
  "born": { "date": { "y": 1861 } },
  "died": { "date": { "y": 1889 }, "place": "london" }, // an act: when, and where a source says
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
  "start": { "date": { "y": 1886 } }, // when and where the connection began
  "end": null, // when and where the connection ended
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
  "voice": "period", // "period", "court" or "modern" — see below
  "turns": [{ "who": "Carson", "text": "…" }], // optional, and only when voice is "court"
  "occurred": { "date": { "y": 1900, "m": 3 } }, // when the event described in the quote happened
  "supports": "what this quotation is here to establish",
  "verified": true, // somebody read this at the page
  "verified_on": "2026-08-04",
  "verified_against_original": true, // you read and collated against the original document itself
  "verified_marks": true, // you collated the marks against the original and verified they match
  "verified_with": "photo-reproduction", // what the quote was verified against
  "document": "letter", // what is quoted, when it differs from the work
  "written": { "place": "berneval-sur-mer" }, // and `sent`, `postmarked`, `received`
  "citation_provenance": "which copy, which page",
  "original_provenance": "…", // what you read and saw in the original document
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

**Anything from the record of a court is `voice: "court"`, not `period`.** Sworn testimony, a plea, a verdict. `period` promises somebody speaking for themselves and is set in quotation marks accordingly; a court record is speech taken down under compulsion and printed by the court, and the card sets the two differently to say so. All three are styled alike, so a plea and a cross-examination read as the same kind of thing.

`turns` are **optional**. Give them and the card draws a transcript; leave them off and the quotation runs as continuous prose. A question-and-answer needs them; a plea of justification does not, and requiring them is what produced eight pleas each carrying one invented "turn" attributed to Queensberry. Turns that are present must reproduce the quotation word for word, and `who` may be left empty where the record does not say who spoke.

This was called `exchange` and defined as period text with more than one speaker. Nineteen of its fifty-six records had exactly one — a witness's answer quoted without the question — and it could not hold a plea or a verdict at all.

**A quotation not in English keeps its own language and gains a translation.** Set `lang` and `translation`; the validator refuses one without the other. A quotation that reads as French, German, Italian or Latin and carries no `lang` draws a warning, and a translation parked inside `context` is a hard error. If the warning is wrong — an English quotation dense with French phrases — ignore it; it does not fail the build.

## Dates

**Date schema.** These fields apply to every date on the map:

| Field       | Value                               | Description                                                                 |
| ----------- | ----------------------------------- | --------------------------------------------------------------------------- |
| `y` `m` `d` |                                     | as far as the source goes — see below on what a date must say               |
| `t`         | `"15:50"`                           | a 24-hour time                                                              |
| `weekday`   | `monday` … `sunday`                 | the day of the week the writer gave                                         |
| `part`      | `early` `mid` `late`                | a part of the month                                                         |
| `season`    | `spring` `summer` `autumn` `winter` | in place of a month                                                         |
| `circa`     | `true`                              | approximately                                                               |
| `uncertain` | `true`                              | the date may be wrong                                                       |
| `inferred`  | `true`                              | the document does not record this date; it was inferred through other means |

Add `"circa": true` when the date is in the right neighbourhood but may be slightly off.

Add `"uncertain": true` if the date may be wrong altogether.

Add `inferred:true` if the date was not written on the document itself — somebody else worked it out, whether the volume's editors, a biographer, or you, dating a letter from its own contents.

For date ranges, use `to`. `{"y": 1897, "m": 1, "to": {"y": 1897, "m": 3}}` displays as _January–March 1897_.

`occurred` records when an event happened, not when the event was written down or published: a biography published in 2017 reporting a meeting of 1887 should record `occurred` as 1887.

A letter records the dates related to writing or sending the letter under `written`, `postmarked`, `sent`, or `received`. Give a letter an `occurred` only when it describes a specific event that happened at a different time or place from the writing.

Sources display in chronological order. If a source is undated, use **`order_hint`** instead:

```json
"order_hint": {"y": 1897, "m": 8, "why": "Sox says outright \"We do not know exactly when Fothergill appeared\". Wilde's letter of 21 September counts the six days as falling inside his last month at Berneval, so the visit sits in August or early September."}
```

It sorts exactly as a date would. The card will say — _"Undated — placed here for reading order: …"_.

## Locations

Locations are recorded in [`data/places.json`](data/places.json) as `{ venue?, street?, city?, region?, country? }`

**Places are referred to by id.** Read `places.json` before writing a place and use the id already there; if the place you need is missing, add it.

```jsonc
"berneval-sur-mer": { "city": "Berneval-sur-Mer", "country": "France" },
"hotel-d-alsace":   { "venue": "Hôtel d'Alsace", "city": "Paris", "country": "France" },
"16-tite-street":   { "street": "16 Tite Street", "city": "London", "country": "England" },
"gland":            { "city": "Gland", "region": "Canton Vaud", "country": "Switzerland" }
```

| Field              | On                        | Describes                                                                                                    |
| ------------------ | ------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `written.place`    | a source or transcription | where that document was written.                                                                             |
| `postmarked.place` | a source or transcription | where that document was postmarked.                                                                          |
| `sent.place`       | a source or transcription | where that document was sent from.                                                                           |
| `received.place`   | a source or transcription | where that document was received.                                                                            |
| `occurred.place`   | a source                  | where the event a quotation attests happened. Unlike the four acts above, it may go on any kind of document. |

`written`/`postmarked`/`sent`/`received` belong only to something written on one occasion at one place: a `letter`, `telegram`, `postcard`, `diary`, `inscription`, `manuscript` or `typescript`. A biography is usually written over years in multiple places, so the date/place of its writing should not be recorded under `written`.

## Verification

Unverified quotes are marked with an `⧖ unverified` chip and means the passage was located in an index or OCR dump but never checked against the page. ⧖ also marks **leads**: pointers to a potential source with nothing transcribed yet.

Never mark something verified you have not seen on the page. A text layer, an OCR dump or a search index is for _finding_; the rendered page is for _verifying_.

Verification asks **four separate questions:** `document` for what kind of thing is quoted, `verified_with` for how directly it was read, `verified_against_original` for whether anyone went to the document itself, and `citation_provenance` / `original_provenance` for the provenance of each — the publication and the original.

**`verified_with` — how directly were the words read?**

| value                | means                                                                            |
| -------------------- | -------------------------------------------------------------------------------- |
| `in-hand`            | read directly from the physical object itself                                    |
| `photo-reproduction` | read in a photograph of the object: a scan, a IIIF image, microfilm, a plate     |
| `as-published`       | an official publication — a web page, an EPUB — read as its publisher renders it |
| `text-layer`         | taken from extracted or OCR text; **the page itself was not looked at**          |
| `unverified`         | not yet established                                                              |

**`document` — what kind of thing is being quoted?** Name the document the source originates from:

Written by hand: `letter`, `telegram`, `postcard`, `diary`, `inscription`, `manuscript`.
Printed by the subject themselves: `memoir`, `pamphlet`, `novel`, `essay`, `poem`, `typescript`.
Spoken and taken down: `testimony`, `plea`, `verdict`, `interview`.
Written about the subject: `biography`, `study`, `article`, `encyclopedia`, `editorial-note`, `introduction`, `finding-aid`, `web-page`.

**Provenance:**

| field                 | says                                                                                                                                                                                      |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `citation_provenance` | where the passage sits in the **work cited**, and how it was read — _"PDF p. 1090."_, _"IA in.ernet.dli.2015.499238, leaf 326"_                                                           |
| `original_provenance` | which pages were read **at the document**, and what was found there — _"HRC MSS_WildeO_2_7_001-002, the bifolium; the long diagonal strokes are Wilde's paragraph marks, not underlines"_ |

**`verified_against_original`** Set to true if you've read the original document; It requires a `document` field as well, since it has to say which original was read.

**`verified_marks: true`** says the quotation's marks have been collated against the source and match — emphasis, accents, punctuation, everything a transcription loses quietly.

**`original_provenance`**: Which pages you read. Marks you found and where. And above all **the things that look like marks and are not** — the stroke that cancels a letterhead, the diagonals that are paragraph marks, the rising paraph before a signature that is not a rule under the words above it. Those are what stops the next reader opening the same sheet to re-decide the same mark.

The card shows the document as a chip, ticked when the original has been read — **✓ Letter** against a bare **Letter**. So a reader can tell at a glance which quotations rest on Wilde's own hand and which rest on his editors.

**Document Location.** The location comes from `facsimile.archive` or `manuscript.repository`, whichever the record carries, resolved to one `location` field at build time so the card and the filter never disagree.

**Every location is a _last known_ location.** Very few items on this map have been confirmed by going to an archive. So the chip names the last known location and when it was located there — _"Last recorded by Wilde, Complete Letters (2000) at the Clark"_. **The one exception is a `facsimile`**, where the page draws the archive's own image service live: that holding is proved by the picture in front of you, so its chip stays present tense.

**The chip prints an abbreviation, the tooltip the full name.** _Clark, UCLA_ stands for _William Andrews Clark Memorial Library, UCLA_. The abbreviations are mostly from the _The Complete Letters of Oscar Wilde_'s key at pp. xxii–xxv. A repository with no entry falls back to the text before its first comma. **Add an entry when that reads badly**.

**Private owners are named, as of the date the edition names them.** Where the volume's headnote gives an individual — `MS Mason`, `MS Maguire`, `MS Holland, M.` — write the repository as **`Private collection`** and the person in **`manuscript.owner`**, expanded from the volume's key at pp. xxiv–xxv (`MS Mason` is Mr Jeremy Mason). The name sits beside the repository rather than replacing it, so the location facet stays one bucket a reader can filter on instead of fragmenting into thirty-five owners. `MS Private` names no specific owner and so should not have a `manuscript.owner` field.

**The location comes from the edition that prints the text.** The Complete Letters put it in a headnote above each letter; a biography puts it in an endnote (Murray's note 52: _"Lord Alfred Douglas to Robert Ross, 1 March 1909. Ross TS. Clark."_); a scholarly edition puts it in the letter's own footnote (the Vernon Lee letters name _"Bibliothèque Nationale de France, Manuscrits, Anglais 243"_) or in a manuscript-sources list arranged by correspondent (Delaney's biography of Ricketts, which is the only thing that locates the letters Sturge Moore printed in _Self-Portrait_ without saying where any of them were). Look in all three before concluding an edition is silent.

**Say when the archive holds a typescript rather than the writer's hand.** `manuscript.archived_as` takes **`autograph`** or **`typescript`**, and you write it only where it contradicts what the document type already implies — a letter is an autograph unless somebody says otherwise, so `archived_as: "autograph"` on a letter says nothing and the validator refuses it. Its presence therefore always means _not what you assumed_.

**A saleroom is a location.** Where the Complete Letters print a letter from an auction or dealer's listing, write the house as the repository and the sale date as **`manuscript.as_of`**, which replaces the citing edition's date in the chip: _"Last known at American Art Association, New York, 9 February 1927. Nothing has been recorded of it since, and whoever took it home is not named."_ The editors reporting the sale in 2000 had not seen the letter either, so dating the claim to their volume would be wrong.

The same holds for the volume's `F` headnotes, which name a **published book reproducing the letter in facsimile** (Keller, Brémont, Cantel) rather than an archive: if the autograph has since been traced, name the archive that holds it; if it has not, the facsimile belongs in `citation_provenance` too.

**Filtering works the way the legend does.** Beside the year range sit two dropdowns. **Document** lists every document type and archive, with counts — _Letters · 251_, _Testimony · 30_, _Biographies · 27_. **Place** lists where the documents were written, keyed on the city, so a letter headed from the Hôtel de Nice files under Paris. The two answer different questions: an archive is where the paper is kept now, a place is where the writing happened.

Uncheck a row to hide it. Check it to show it again. **Right-click a row** or click a document chip on any card to solo that filter. Clicking a soloed filter unsolos it, restoring the previous filter state. The Location dropdown is drawn only where something in the panel records a place, since a list whose one row reads _Not recorded_ offers no choice.

## Formatting & emphasis

**How to transcribe a document, and what its marks mean, are in [CONTRIBUTING.md](CONTRIBUTING.md)** — spelling and abbreviations, dashes, split words, the `[…?]` / `[illegible]` / `[inserted: …]` / `[annotated: …]` bracket forms, the emphasis markup and the italics departure, and the rule that a later hand's marks never enter the quote. They apply to anyone transcribing, ticket or pull request alike.

**The markers are rendered.** `*italics*`, `_underline_`, `__double underline__`, `**bold**` and `~~strikethrough~~` inside `quote` are converted to real type when the card is drawn, so they must be the source's own emphasis and never editorial highlighting of your own.

**Deviations from the printed edition.** The editors of _The Complete Letters of Oscar Wilde_ silently convert title quotation marks and underlines to italics and additionally italicize any titles and foreign words present in the letter. They make no differentiation between words that were single-underlined or double-underlined (both are italicized in the printed edition). Due to this convention, when the printed edition italicizes an ordinary English word, it is usually because the word was `_underlined_` in the original document. When the printed edition italicizes a title or foreign word, this usually does not correspond to any real underlines in the original document. Say which it is in `citation_provenance`. When the document has been read, write `original_provenance`, record what was found there, and set `verified_marks` to `true` once the marks are collated. Withhold `verified_marks` while any part of the quotation is unread or any mark is unresolved.

**Record what you changed against the page you cite.** Where restoring a mark makes the quotation differ from the printed page — or where you normalised a mark that existed only because of a line break — say so in `citation_provenance`. The citation still locates the passage; the manuscript tells us how it was normalized.

### `letter_id` uniquely identifies each letter

A citation of `letters-2000` + `p. 1198` does not say which letter it means. So each source record, a manifest entry and a transcription carry a `letter_id` field. That shared value is how they are linked together:

| Form                      | Means                           | Use when                                             |
| ------------------------- | ------------------------------- | ---------------------------------------------------- |
| `letters-2000/1198#2`     | <work>/<folio>#<letter number>  | the letter is printed in an edition                  |
| `letters-2000/649n3`      | <work>/<folio>n<note number>    | the editors print the document **inside a footnote** |
| `hrc/MSS_WildeO_2_10_004` | <archive>/<shelfmark>           | archived with shelfmark                              |
| `nypl/5936027`            | <archive>/<uuid>                | archived with globally unique identifier             |
| `morgan/MA7258#34`        | <archive>/<item>#<image number> | archived with no unique document identifier          |

Printed form wins where both apply, because it identifies the letter for the ~280 records that cite the volume without holding a scan.

**The folio is the printed page number where the letter begins, and the number after `#` is the number of the letter amongst the letters on that page.**

**`archive.page_id_field` records an archive's page identifier**:

| Archive        | `page_id_field` | Example value                     |
| -------------- | --------------- | --------------------------------- |
| `hrc`          | `shelfmark`     | `MSS_WildeO_2_10_004`             |
| `nypl`         | `pointer`       | `5936027`                         |
| `loc`          | `pointer`       | `service:mss:mss18630:019:09:001` |
| `morgan`       | `null`          | —                                 |
| `marland-blog` | `null`          | —                                 |

One caution about ordinals generally: the Library of Congress numbers by **scan order**, which for the Whitman letter is not the order the leaves are read (8, 9, 12, 13, 10).

**The footnote form is for documents, not commentary.** This volume's main sequence carries Wilde's _outgoing_ letters, so a letter **to** him is printed in the note where it is relevant — Douglas's of 15 May 1895 at `p. 649 n. 3`, Langtry's at `p. 91 n. 5` — and so are two inscriptions Wilde wrote in presentation copies. Those are documents and they take an id. Footnotes that only contain the editors' own writing does not: see the refusals below.

**A typed copy or photostat takes the id of the letter it copies**, not one of its own — it is another witness of the same document.

**Use `letter_ids` when a record quotes more than one document.** A few records quote two letters as a single passage because the pairing is the evidence: two postcards Wilde sent Ross from different towns on one day, or the 1876 and 1877 letters to Ward that show the same thing about the friendship. They carry a `letter_ids` string array, instead of a `letter_id` string. The two fields are mutually exclusive. Use the singular whenever you can.

Ids are minted by `research-tools/source-volume/mint_ids.py` (manifests, transcriptions) and `mint_source_ids.py` (connection sources); both dry-run by default. `tools/manifest_links.py --check` reports malformed ids, and lists citations that name a different letter on a folio we hold.

## The document itself

Two optional fields say where the original is. A source may carry at most one of them.

**`facsimile`** — the archive publishes page images, and a photo/scan of it can be viewed by clicking the _View original_ button.

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

Write the repository out in full, as it should read on the card — not the abbreviation the Complete Letters print. This is the most common case by far: of the letters this map quotes from that volume, eight have manuscripts at the Ransom Center and around a hundred are at the Clark.

## Transcriptions

A transcription file should be included for each letter:

```jsonc
// web/manuscripts/hrc/transcriptions/hrc-2700-019.json
{
  "letter_id": "letters-2000/1044#1", // links the transcription with every quotation of it
  "transcribed_from": "facsimile", // or "printed"
  "printed": { "work": "letters-2000", "locator": "p. 1044" },
  "facsimile": { "archive": "hrc", "item": "2700", "pages": [19, 20] },
  "sender": "Oscar Wilde", // the full name of the sender
  "addressee": "George Ives", // the full name of the receiver
  "postmarked": { "date": { "y": 1898, "m": 3, "d": 21 } },
  "written": { "place": "paris" }, // an id from data/places.json
  "quote": "…", // the whole letter, salutation to signature
  "verified_marks": true,
  "transcribed_on": "2026-08-10",
}
```

**Transcribe the whole letter, salutation to signature.**

**A letter may be transcribed twice: once from the document, once from a printed edition.** They are different objects — what Wilde wrote, and what an editor printed — and `transcribed_from` says which you read. They share a `letter_id`, since that names the letter rather than the reading of it, and the reader is shown the one taken from the document, which is the only kind that settles emphasis. Two transcriptions of the same letter from the same source are a duplicate and fail the build.

**Keep the paragraphing.** A letter's paragraph breaks are often important to their meaning. Separate paragraphs with a blank line (`\n\n`) inside the `quote` string, and give the signature its own paragraph. Wilde ends a letter to Harry Marillier _"You are certainly not to call me Mr Wilde. What should you call me but"_ and then, on a line of its own, _"Oscar"_ — the sentence finishes in the signature. If you run them together into one line, the joke disappears.

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
