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
Opening `index.html` by double-clicking will _not_ work — the browser refuses to fetch
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
content/ABOUT.md        the About panel's text       <- edit this for prose
data/people/*.json      one file per person          <- edit these
data/relationships/*.json  one file per connection   <- and these
data/works.json         the bibliography             <- and this
data/circle.json        GENERATED bundle, do not hand-edit
tools/validate.py       validator + bundler
tools/serve.py          local dev server
tools/layout_report.py  measure the drawing
tools/test_navigation.py / test_solo.py   assert the interactions
audits/                 the human verification ledger
dossiers/               long-form research notes, per cluster
```

**To change what the About panel says, edit `content/ABOUT.md`** — plain markdown, no markup, and
`tools/validate.py` compiles it into the bundle. Two placeholders are filled by the page:
`{{line:marriage}}` (and the other four certainties) draws the real connection line, and
`{{colophon}}` becomes the generated build line. Writing `{{line:…}}` at the start of a bullet
replaces the bullet's disc with the line itself, which is how the certainty key is built.

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

Groups: `core`, `family`, `society`, `aesthete`, `trials`, `chaeronea`, `later`, `liaisons`,
`beyond`. If your additions need a new one, propose it — adding a group means adding a colour, and
the palette is [ColorBrewer](https://colorbrewer2.org/#type=qualitative&scheme=Paired&n=9),
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

---

## Adding a connection

Create `data/relationships/<a>--<b>.json`, where the two ids are **in alphabetical order** and the
filename matches the `id` field. The validator enforces both.

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

These describe **how we know**, not what happened. The map deliberately makes **no claim about
sexual acts** in either direction — criminal law was designed to keep that evidence out of the
record, so treating its absence as a finding would mistake the effect of prosecution for a fact
about someone's life.

| Class                  | Means                                                                                                                                                                                                                                                                                                                  |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `married`             | a legal marriage                                                                                                                                                                                                                                                                                                       |
| `self-reported`        | a participant's own words survive — letters, diaries, sworn testimony                                                                                                                                                                                                                                                  |
| `second-hand`          | someone else who was there, or a historian, attests it                                                                                                                                                                                                                                                                 |
| `uncorroborated`       | asserted somewhere but nothing supports it; **requires a `disputed` block**                                                                                                                                                                                                                                            |
| `attraction-expressed` | the record is one-sided: a declaration, an approach, or admiration noted in passing, with a `direction` and an `outcome`. **The bar is low on purpose** — one admiring sentence about a named or describable individual qualifies. Use `outcome: unknown` when nothing followed, which for a passing mention is usual. |

An `uncorroborated` connection must carry `disputed` with `claim`, `asserted_by`, `disputed_by`
and `grounds`. Leave `disputed_by` **null** when nothing actually disputes the claim — a statement
of absence is not a party, and the map renders the fields as labelled lines.

---

## Sources: the part that matters

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
  "voice": "period",               // "period", "exchange" or "modern" — see below
  "turns": [ {"who": "Carson", "text": "…"} ],  // REQUIRED when voice is "exchange"
  "evidence_date": { "y": 1900, "m": 3 },
  // …or a RANGE, when the thing happened across a span:
  // "evidence_date": {"y": 1897, "m": 1, "to": {"y": 1897, "m": 3}}   -> "January–March 1897"
  "supports": "what this quotation is here to establish",
  "verification": "verified-exact",
  "how_verified": "pdf-at-page",
  "verified_by": "…",
  "verified_on": "2026-08-04",
  "provenance": "which copy, which page, how it was read",
  "lang": "fr", // only when the quotation is not in English
  "translation": "…", // then this is REQUIRED
  "translation_note": "who translated it, and any published version that differs",
}
```

**QUOTE THE WHOLE LETTER, AND ELIDE ONLY WHAT DOES NOT CHARACTERISE THE RELATIONSHIP.** This is
the reverse of the obvious habit, which is to lift the sentence that proves the point. Do not do
that. Start from the whole letter and cut only what says nothing about the two people — an address,
a standing order, a train time — marking each cut with an ellipsis as usual.

The reason is not tidiness, it is accuracy. A quotation trimmed to its strongest phrase decides the
case before the reader sees it, and it decides it wrong often enough to matter: the 2026-08-04
sweep quoted Wilde's letter to Sherard from *"how could I refuse"* onward and concluded *warm, and
not desire* — the excerpt began four lines after *"Your letter was as loveable as yourself"* and the
*"memories of moonlit meanderings, and sunset strolls"*. The verdict followed the trim. The same
sweep, reading only its lexicon hit in a letter to Graham Hill, filed a warm three-letter
correspondence as nothing.

**FRIENDSHIP COUNTS.** A quotation does not have to reach romance to be worth recording, and a
person does not have to carry a connection line to belong on the map. Warmth between men in this
period is part of what the record shows and part of what the map is for; George Alexander and
Graham Hill are here as nodes with no line, holding letters that are simply fond. Record the
friendship, let the certainty class stay empty, and let a reader see the affection without being
told it was desire.

**READ IT AT THE PAGE YOURSELF.** Not an agent, not a text layer, not an OCR mirror — the rendered
page image, with the printed folio visible on it. The mirror's page attribution drifts by one or
two: it put the Sherard letter at 202 (it is 210), the valet at Cannes at ~1119 (1121), the
Alexander letter at 1192 (1193), and the Hill letters at 379 (380). Locate with the mirror; cite
from the page.

**A quotation not in English keeps its own language and gains a translation.** Set `lang` and
`translation`; the validator refuses one without the other. **It also now asks the question the
other way round** — a quotation that reads as French, German, Italian or Latin and carries no `lang`
draws a warning, and a translation parked inside `context` is a hard error. Both rules exist
because a French passage of Barney's reached the page untranslated with its English sitting in the
context line: every check keyed off `lang`, so a source that never declared itself foreign was
invisible to all of them. If the warning is wrong — an English quotation dense with French phrases —
ignore it; it does not fail the build.

**`speaker` is who is speaking, and after the comma in what capacity** — "examination-in-chief",
"letter to John Gray". Not the work's title: the citation prints that already, and four Barney
quotations used to render as *Barney, Souvenirs indiscrets, in Souvenirs Indiscrets (1960)*. The
validator warns when a speaker's tail repeats its own work's title. The original stays the quotation — it is
what you verified at the page and what the connection is evidenced by — and the English is printed
beneath it, quieter, as the way in rather than the source. If a published English version exists and
differs from yours, say so in `translation_note` rather than silently preferring either: on the
Vivien card that difference is the whole reason the French is there.

**Anything you put in a source is searchable from its page.** The sources filter reads the quotation, the translation and its note, the context line, the speaker, the addressee, what it supports, the work title and author, the locator, the provenance and the turn labels. You do not have to register a new field anywhere for it to be findable - but a fact recorded ONLY in a relationship-level note (certainty_reasoning, a disputed block) is reachable from the map search and not from the source filter, because the filter is per quotation. The filter appears from four sources up; below that a page shows its sources plain. Matches are highlighted in place by walking text nodes - if you add markup to a card, do not introduce a text-node-splitting wrapper mid-phrase, or the highlight will stop finding phrases that cross it.

**The citation's byline links itself, on a match of the whole name.** Write `speaker` the way the
person's file writes their `name` and the link appears; write it any other way and the citation is
plain text, which is the safe failure. Case, accents and punctuation are folded, and `aka` and
`sort_name` are matched too, so *Renée Vivien* reaches a node spelled *Renee* — if a name you expect
to link does not, add the variant to `aka`.

**Do not loosen this to surnames or to partial matches.** Sarah Parker and Douglas Murray both cite
these pages, and neither is Charles Parker or Lord Alfred Douglas; a byline pointing at the wrong
person is a false claim about who said something. Where two people do fold to the same key the index
links neither, on purpose — treat that as correct behaviour and disambiguate the data, not the
matcher. Names with no node — historians, editors, collective bylines like *The Clerk of Arraigns
and the Foreman of the jury* — are meant to stay plain.

**A courtroom exchange is `voice: "exchange"`, not `period`.** `period` promises a single voice and is set in quotation marks accordingly; a cross-examination has counsel and witness in it. An exchange is drawn as a transcript from its `turns`, which you get by running `python tools/dump_turns.py`, **reading the split**, and storing it — the splitter is a heuristic and the corpus is small enough to check. The validator refuses an exchange with no turns, and refuses turns that do not reproduce the quotation word for word. Leave `who` empty where the record does not say whose turn it is.

**`voice` is per quotation, not per book.** `period` means the text is _entirely_ in the words of
someone alive at the time — a letter, a diary, sworn testimony. `modern` means a historian or
editor is writing _about_ them. An editor's footnote inside a volume of Wilde's letters is modern;
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
index is for _finding_; the rendered page is for _verifying_. Several sources in `works.json` carry
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

## Dates, and the field that exists so you never invent one

`evidence_date` is **the date of the thing evidenced** — the day the letter was written, the diary
entry made, the testimony sworn. It is a claim about the world. Add `"circa": true` when it is
approximate — approximate meaning **the value itself is in doubt**, not that a finer unit is
missing: Wilde and Douglas met in 1891, a year the editors state outright with only the month
uncertain, so that is not `circa`.

When the thing happened across a **span**, give the date a `to` rather than writing the range
into a `label`: `{"y": 1897, "m": 1, "to": {"y": 1897, "m": 3}}` displays as *January–March
1897*, and every range on the map is then spelled the same way. `label` is for what a date
object cannot say at all; the validator refuses a date carrying both.

Sources display in date order, so it is tempting, when a run reads out of sequence, to give an
undated source a plausible date and move on. Don't. Use **`order_hint`** instead:

```json
"evidence_date": null,
"order_hint": {"y": 1897, "m": 8, "why": "Sox says outright \"We do not know exactly when
   Fothergill appeared\". Wilde's letter of 21 September counts the six days as falling inside
   his last month at Berneval, so the visit sits in August or early September."}
```

It sorts exactly as a date would, and it is not a date. The card says so on its face — _"Undated —
placed here for reading order: …"_ — so a reader can tell a placement from a fact without opening
the JSON. The validator enforces both halves of the bargain: a source may not carry `evidence_date`
and `order_hint` together, and an `order_hint` without a `why` is an error, because an undated
placement with no reasoning attached is an invented date in disguise.

## Completeness protocol (set 2026-08-05, supersedes the change-control rule)

1. **Never park. Add everything to the map as you go.** Candidate lists were slowing the work and hiding evidenced people behind a decision that had already been made. If a person is evidenced, they become a node in the pass that found them.
2. **A person is not done until every letter ADDRESSED TO *or MENTIONING* them has been read at the page.** Do not move on before that. *Mentioning* is the half that keeps getting missed.
3. **Do not skip ahead.** The target is 100% of Wilde's correspondents and 100% of his letters.
4. **Lovelle verifies each node himself after the sweep completes.** The job here is completeness and honest provenance, not pre-filtering for quality — he is the filter.

**Why:** reading for the *addressee* loses everyone who appears inside someone else's letter. Charles Conder was described twice on pages already read — *"a sort of Corot of the sunlight"* (printed 911), *"Conder is now a* vineyard*"* (printed 928) — and logged from neither, because both times the letter was filed under its recipient. Harry Melvill, Arthur Howard Pickering and a second Rothenstein letter were all on folios already read, for the same reason. **The unit of reading is the PAGE, not the letter.**

**Three counting hazards, all hit at least once:**
- **Name forms.** `To Herbert Horne` vs `To Herbert P. Horne` — 1 letter vs 11. `G. H. Kersley`, not `George Kersley`. Match on surname *and* initials.
- **Page-count ≠ letter-count.** Letters are often printed two or three to a page; deduplicating hits by PDF page understated five nodes' letter counts.
- **The editors' index disambiguates what the text cannot.** It settled `Georges (boy), 1097, 1108, 1117` in one page — and carries its own errors, so verify entries at the page too.

### Superseding an existing quote (2026-08-05)

**When you read a page a node already cites, compare the logged quote against the full letter and extend or replace it.** The earlier passes trimmed to the phrase that matched; this one starts from the whole letter and elides only what does not characterise the relationship. **The fuller quote is the more accurate one — never assume a shorter existing quote was a deliberate editorial choice.**

Measured on 2026-08-05, across every quote in `data/`:

| verifier | quotes | median length |
|---|---|---|
| `agent-mechanical` | 382 | 276 chars |
| `claude-at-page` | 131 | **426 chars** |
| `Claude (Opus 5)` | 10 | 257 chars |

At-page quotes run about **55% longer at the median**, so **392 quotes are standing candidates for extension**. They are not a separate work item — they get fixed as a side effect of the page sweep, because the completeness protocol brings you back to every one of those pages anyway. When you extend one, keep its original `provenance` line and add yours; do not silently drop the earlier verification.

### The index lists FOLIOS, not letters (2026-08-06)

A printed folio carrying three letters appears in the Index of Recipients **once**. So an index
entry of 13 folios and a node claiming 16 letters are **not in conflict** — they are different
units, and both can be right.

This nearly caused nine correct nodes to be "corrected" into error. Before reconciling any count
against the index, check whether the node's own provenance already records multiple letters on one
folio (`harding`: "PDF 92 (three on one page)"; `graham-hill`: "three at printed 380"). **Check
before patching.**

The same distinction applies in reverse: `graham-robertson` has 6 index folios and 7 letters
because folio 347 carries two.

### Fix the map as you go — never log a debt (2026-08-06)

If something on a page belongs on the map, **write it in the same pass**. `READING_LOG.md` records
what was on each folio; it is **not a work queue**. Logging "read, not logged" and moving on was a
bad habit that accumulated across a session and had to be cleared retrospectively.

**The one legitimate exception** is a quote you cannot reproduce exactly without re-opening the
page. Never paraphrase a quotation into the data from memory — say plainly that the folio needs
re-reading, and re-read it.

That exception earned its keep immediately. Re-reading printed 973 rather than trusting a
remembered phrase showed that *"When I came out of prison / some met me with garments and with
spices, / and others with wise counsel. / **You met me with love**"* is **the suppressed dedication
of *The Ballad of Reading Gaol* to Robert Ross** — Wilde composed it deliberately without initials
or name, showed it to Smithers, and it was never printed. An earlier note of mine had filed the
phrase as a remark to Smithers about Smithers, because the line sits in a letter to Smithers and the
page-break hid the editors' footnote.

It is the **fourth documented suppression** on this map, beside Pater's withdrawn Conclusion,
Mahaffy's deleted chapter and Gide's torn-out journal — and the only one that is Wilde's own.

### One letter, one card — the duplicate-quote convention (2026-08-06)

Spotted by Lovelle on `alphonse`: the same letter appeared twice on his panel, once under a context
engagement with Wilde and again under his connection to Turner.

**Three cases, and only two of them are errors.**

**1. The same excerpt twice in one record — ERROR.** Quote it once. `fothergill--warren` carried an
identical Sox quotation twice in the same file.

**2. The same excerpt on a person's context engagement AND on a connection they are party to —
ERROR.** Keep it on the **connection**; that is the more specific claim and it already renders on
both endpoints' panels. A context engagement is for evidence with no connection to hang on. The
`alphonse` case was worse than cosmetic: the engagement named Wilde as the partner, implying a
Wilde–Alphonse pairing the source never makes. The letter is Wilde writing **to** Turner **about**
Turner's friend — Wilde is the witness, not a party.

Both are now hard errors in `tools/validate.py`.

**3. The same excerpt on two DIFFERENT connections — CORRECT, leave it.** One source often evidences
several claims: the letter naming Raphael and Fortuné is cited on both their connections; four of
Ives's household edges rest on one Cook paragraph; the Rolla letter is also the letter where Wilde
asks Smithers to come out to him. **Each connection genuinely needs its own citation.** The
duplication was only ever wrong on the *page*, where the shared person's panel printed the same
paragraph two, three or four times.

**That case is now collapsed at render time**, in `personSources()` and `withBar()`: identical
`(work, locator, text)` becomes one card that names every connection it belongs to, each keeping its
own certainty marker — *"with Edoardo Rolla `⋯▸` and Leonard Smithers `no connection line`"*.
Pointers (sources with no quote text) never collapse; several different pointers can share a
locator and are not the same evidence.

`tools/find_dupe_quotes.py` reports all three cases; after the fixes, 13 remain and all are case 3.

### Jealousy is an expression of attachment (2026-08-06)

**Jealousy counts.** A connection line needs some source asserting attraction, romance or sex — and
**possessive feeling about a third party is an assertion of attraction**, whether or not the word
appears. Wilde put out that a young man prefers another's company; a friend who talks *"a little too
much"* about an absent man, suspects him of *"treachery"*, and doubts he will return — these are the
same signal, and the map must read them the same way.

Caught by Lovelle asking *"Is that not jealousy?"* about `omero--ross`, which I had first declined
to draw on the ground that nothing in the passage "asserts attraction". That was inconsistent:
`boulton` is flagged as the strongest attraction candidate of its own batch on **exactly** this
signal — *"whom by the bye I believe you like* much better *than yours truly"*. Pique had been
treated as a tell there and as nothing here.

**How to read it:** "treachery" from an absent man means unfaithfulness, not commercial betrayal.
Wry commentary (*"a little too much"*) implies there is something to be wry about. Waiting, and
doubting a return, is attachment. Record the alternative reading in `certainty_reasoning` — Ross
handled Wilde's money, so "treachery" *could* be practical — but do not let the existence of a
duller reading suppress the natural one.

### Check BOTH indexes before deciding someone is too thin (2026-08-06)

Before concluding that a person does not warrant a node, look them up in **both** of the volume's
indexes — the Index of Recipients (letters *to* them) **and** the General Index (mentions *of*
them). A single reference is not evidence of a single reference.

Adolphe Retté was declined on the basis of one appearance, a name in a dinner invitation — *"Ask
Retté to come, if you think he would like it"* — which genuinely documents nothing. Lovelle asked
whether the index listed anything else. It does: **`Retté, Adolphe, 500, 506n`**, and 506n carries a
page of his own first-hand account, from *Le Symbolisme* (1903), of what he cut from *Salomé* —
corroborated by Stuart Merrill's memoir on the same page. He is a node now.

The same trap in reverse produced the `blacker` error: a claim that something was "not documented on
any page read here" was true of the pages read and false of the volume, and the General Index said
so. **The indexes are the check on our own judgement, not just a way to find pages.**
