# The World Wilde Web

A sourced map of documented romantic and sexual relationships in Oscar Wilde's circle,
1870s–1940s. **110 people, 106 connections, 389 quotations** — every claim carries the words it rests
on and the page they came from.

It began with Wilde because that is where the surviving paper is thickest. The intended scope is
wider: a map of queer relationships of the period, and contributions extending it — the Paris
salons, the women's networks, circles we have not touched — are welcome. See
[CONTRIBUTING.md](CONTRIBUTING.md).

## Running it

```bash
python tools/serve.py     # or: npm start
```

Rebuilds the data bundle, validates it, and serves at <http://localhost:8000>. Double-clicking
`index.html` will not work — the browser will not fetch the data from a `file://` page.

There is **no JavaScript toolchain and nothing to install** — `package.json` only wraps the Python
scripts so `npm start` works if that is the habit. Python 3.8+ is the only requirement.

| | |
|---|---|
| `npm start` / `python tools/serve.py` | rebuild, validate, serve |
| `npm run build` / `python tools/validate.py` | rebuild `data/circle.json` |
| `npm run check` / `python tools/validate.py --check` | validate only — use in CI |
| `npm run layout` / `python tools/layout_report.py` | measure the drawing |
| `python tools/test_navigation.py` | assert the pan/zoom gestures (needs the site served) |
| `python tools/test_solo.py` | assert the legend's solo filter (needs the site served) |
| `python tools/audit_dates.py` | list dates that disagree with their own context notes |
| `python tools/dump_turns.py` | print every exchange transcript, to read before storing it |

It is a plain static site: HTML, one stylesheet, one script, JSON and images. It can be published
to GitHub Pages or any static host with no build step beyond `python tools/validate.py`.

**The About panel's text is a markdown file**, `content/ABOUT.md`, compiled into the data bundle by
`tools/validate.py` — so the prose can be edited without going near markup. It is compiled rather
than parsed in the browser because the site's bargain is one script and no toolchain, and shipping a
markdown parser to every reader to render one static document would be a poor trade. Two
placeholders survive into the page: `{{line:<certainty>}}` becomes the real connection line, drawn
from the same definitions the legend uses, and `{{colophon}}` becomes the generated build line.
**The connection list draws each line instead of describing it.** It used to read "(dash-dot,
arrowed)", which is a caption of a picture the reader is looking at anyway, and which goes stale
silently the moment a dash pattern changes.

## What it does

**Line style records how we know**, not what happened. The reference deliberately makes no claim
about sexual acts in either direction — criminal law was designed to keep that evidence out of the
record, so treating its absence as a finding would mistake the effect of prosecution for a fact
about someone's life.

The lightest class is deliberately light. **Attraction expressed** covers everything from a written
declaration down to a single admiring line about a stranger — *"a very handsome young soldier of
twenty"* is enough. It was called *desire expressed* until August 2026, and the narrower word was
quietly excluding people: a man who survives in this record only because Wilde once called him
handsome has less paper than a man who survives because he wrote back, and that difference tracks
class almost exactly. Setting the bar where an approach or a declaration was needed kept the map's
poorest men off it. The bar is now attraction legible to an ordinary reader, and the arrow, the
`outcome` field and the quotation itself carry how much weight the connection can bear.

| | |
|---|---|
| **Married** (`married`) | a legal marriage |
| **Self-reported** | a participant's own words — letters, diaries, sworn testimony |
| **Second-hand** | someone else present, or a historian, attests it |
| **Uncorroborated** | asserted with very little supporting evidence; or actively contested |
| **Attraction expressed** | the record is one-sided — a declaration, an approach, or admiration noted in passing; the arrow shows which way |
| **No connection** | not a connection at all — the switch for people the map records but joins to no one |

**Married means a legal marriage, and that is a real limit — not a neutral one.** In August 2026 a
case arrived that the class cannot hold: Alfred Taylor and Charles Mason went through a marriage in
1893, Taylor in a wedding dress as the bride, rings exchanged, a wedding breakfast for friends
afterwards. Charles Parker gave it in evidence at the Old Bailey, Pierre Louÿs wrote to Gide about
it in the present tense as *"a marriage — a real marriage"*, Taylor retold it himself for years, and
Wilde wrote to Mason asking after his *"married life"*. That is better evidence than most things on
this map. It is filed as **Self-reported**, because two men in England in 1893 could not contract a
legal marriage — one of them was convicted of gross indecency two years later — and putting it in
the Married class would flatten the exact distinction the map exists to show. But the reverse
reading is just as available: a class defined by legality lets the law decide what the archive can
call a marriage, which is the thing this map is otherwise built to resist. **The edge carries the
ceremony in full** in its summary and sources either way. Whether the class itself should be widened
is open, and deliberately recorded here rather than settled quietly in a data file.

**No connection** is a switch, not a line style. Six people here have no recorded connection to
anyone, and without a control of their own they stayed at full strength while every real connection
was filtered away — so asking to see only *Attraction expressed* put the six most isolated people on
the map at the top of the visual hierarchy. They now dim with everything else.

The interface is **dark only** — one palette to maintain, and the ColorBrewer hues sit better on
a dark ground than on paper.

**Node shape marks gender** in the genogram convention — squares for men, circles for women, a
dashed outline where the record does not say. **Colour groups people by sphere**, on the
[ColorBrewer *Paired*](https://colorbrewer2.org/#type=qualitative&scheme=Paired&n=9) palette, whose
light/dark pairs are used deliberately: the men Outside the circle take the 1895 trials green a
shade lighter, because both are the same thing seen twice.

**Quotations in large quotation marks are period voices** — a letter, a diary, sworn testimony.
Those with a plain rule are a historian or editor writing *about* these people. The distinction is
drawn per quotation, not per book: an editor's footnote inside a volume of Wilde's letters is
modern, while a letter of Douglas's printed inside that same footnote is period.

**A third kind is an exchange**, and it is set **screenplay-style** — the speaker's name above the
line, behind a double rule. **Every quotation from the two trial transcripts is set this way, single
speaker or not**, so the court can be told from the post at a glance: a letter is one person's own
voice and looks like one; a transcript is a record of proceedings and should look like a record.
Fifty-six quotations, against thirty-four that have two or more speakers in them.

The setting took three tries, each measured on the same card. A rule beside a name COLUMN was too
much — *SOLICITOR-GENERAL* is 110px of a 490px panel, better than a fifth of the measure, charged to
every row including the ones that only say "Yes.", and the columns took eight wrapped lines where
name-above takes four. With the names above, the text runs full width and the rule costs 13px, so it
came back: it marks the whole block as proceedings before a word of it is read.

One quotation printed inside a trial volume is deliberately **not** set this way. `mavor--wilde` #2
is Lord Alfred Douglas's *Autobiography*, quoted by Hyde — narrative prose with dialogue in it, one
author's voice reporting speech, which is what `period` is for. Being printed inside a trial book
does not make a memoir a transcript.

**The turns are stored, not guessed at load time.** They are split from the quoted text by a
heuristic over the two printing conventions in these sources — Hyde's *"Did you ever kiss him?—Never
in my life"*, where the dash carries the change of speaker, and Holland's transcript, which labels
them outright — then read line by line and corrected where the splitter could not know better, and
written into the data. **The validator checks that the turns reproduce the quotation exactly**:
strip the markers that carry a change of speaker and what remains must match the verified text, so
a transcript can never quietly drop or reword its source. Where the record genuinely does not say
whose turn it is, the row is left unlabelled rather than attributed to a guess — the failure this
whole voice exists to prevent, committed one line lower, would be no better.

**A long run of sources can be filtered**, by text and by year. Wilde's page carries 178
quotations across 41 connections and the longest single connection carries fifteen; past a certain
length the run stops working as a reading order and becomes a haystack. The text box reads
everything the card contains and some of what it hides — the quotation, its translation, the
context line, the speaker and addressee, the work, the locator, the provenance, and an exchange's
speaker labels — so *ross* on Wilde's page cuts 178 down to 76, and *bosie* to 11. On a person's
page it also reads the partner's name, which is the fastest way to isolate one correspondence out
of forty-one.

**The match is highlighted where it sits.** Filtering to forty cards says which sources, not where
in them, and on a card carrying a long letter the matched word can be twelve lines down. The
highlight is painted by walking text nodes, never by rewriting markup — a string replace over a
card's HTML would rewrite `href` attributes and break the citation links — and because `<mark>`
inserts no characters, a highlighted quotation still copies out exactly as printed. That was worth
proving rather than assuming: across all 178 of Wilde's cards the selected text is identical
before marking, while marked, and after clearing. A phrase that straddles an element boundary
(`Wilde, in`, which crosses the `</a>` closing a linked byline) is not highlighted, which is the
safe direction to fail in. One-character terms filter but do not paint, since every card would
match.

**A hit inside the closed Provenance fold marks the fold**, rather than springing it open and
shoving the page around as you type. This turned out to matter more than expected: searching
`IIIF` returns 22 sources and *every one* of the 22 matches is inside a collapsed provenance note,
so without the hint all 22 would look like false positives. A few terms still match invisibly —
`Hyde` finds sources in his edition whose cards print the title rather than his name — which is
correct behaviour, if briefly puzzling.

**A year bound hides every undated source, and says so.** Eighty of the 389 quotations here carry
no year at all — a fifth of the evidence — so a range that silently dropped them would have the map
telling a reader it had shown them everything from 1895 when it had not. The count line reads
`47 of 178 · 10 undated hidden`. The year boxes take this list's own span as their placeholders
rather than a fixed 1865–1947, so the range on offer is the range that exists on the page in front
of you.

The bar appears from four sources up. Forty-one of the 106 connections rest on a single quotation
and fifty-eight on three or fewer, and a filter above one card is furniture pretending to be a
tool — it would be drawn most often on exactly the pages with nothing to filter.

**The name in a citation is a link when it belongs to somebody on the map** — 177 of the 389
citations, across 29 people. It goes in the citation rather than on the quotation itself, which
matters most to the exchanges: a screenplay-style block names its speakers in small capitals above
each turn, but *Parker* there is a turn marker, not a person, and the only place the card gives
Charles Parker his full name is the line beneath. Linking there also leaves the quotation clean —
nine hyperlinks threaded through a transcript would compete with the words for attention, and these
words are the point of the card.

**The match is on the whole name, and that is the whole safeguard.** A surname rule would read the
historian *Sarah Parker* as Charles Parker's and *Douglas Murray* as Lord Alfred Douglas's, and both
of them cite these pages; both stay plain. So do editors' bylines (*Merlin Holland and Rupert
Hart-Davis*), collective ones (*The Clerk of Arraigns and the Foreman of the jury*), titles the
roster does not carry under that form (*The Marquess of Queensberry*), and every modern historian —
212 citations in all, led by Matt Cook at 36 and David Sox at 30. A byline linking to the wrong
person would be a false claim about who said something, in a project whose entire premise is that
attribution is checkable; a byline that fails to link is merely a link that isn't there.

Whole-name does not mean literal. The index folds case, accents, and punctuation, and it carries
each person's `aka` and their `sort_name` in both directions, so *Renée Vivien* finds a node spelled
*Renee* and *Doyle, Peter* finds Peter Doyle. **Where two people fold together it links neither** —
an ambiguous key is stored as null rather than resolved to whichever was read first, which is the
same principle the unlabelled turn in a transcript is following.

**Everyone documented is a node.** Until August 2026 a person whose only connection was to somebody
already on the map lived inside that person's file, in a `context_engagements` slot, and never
appeared in the drawing. It was meant as a scope lock and worked as a holding pen: fourteen people
were in it, including a bookmaker who shared three years and three addresses with Fred Atkins, a boy
Harold Mellor's household bought from his father for 200 lire, and four legal wives. They are all on
the map now, along with every spouse the roster's people had — 110 people against 79. The scope
lock is now the **connection** rather than the person, which still keeps Natalie Barney's whole
Paris circle out. Two consequences worth stating: **the Spouse group is no longer just Constance
Wilde** but twenty-two husbands and wives, several of whom are the documented cost of the
relationships this map exists to record — Una Troubridge's marriage ended in 1919 *because of*
Radclyffe Hall, and the finding aid says so in those words. And the evidence under them is uneven in
a way the edges state out loud: Mary Bliss's marriage to John Marshall is verified at a printed page
in a book about that household, while all three of Richard Le Gallienne's marriages rest on an
uncited Wikipedia narrative that Wikidata does not independently corroborate. Both are on the map;
neither is presented as the other.

**Search has a scope.** The box searches **Names** by default, and the dropdown beside it widens
that to **Quotations** — every quotation attached to a person's connections, the context notes
around them, what each is said to evidence, and the person's own biography — or to **All**. Names
stays the default deliberately: searching *ross* across everything matches 52 of the 110 people,
because he is named throughout the evidence, while searching it by name matches one. A pill under
the box says which kind of hit you got, so a node lighting up for a word that appears only inside a
quotation is never unexplained; pressing Enter on a single name hit still goes to that person even
when dozens of quotations also mention them. Searching *handsome* in Quotations is the case this was
built for — it returns Elvin, the Egyptian at the Café d'Égypte, the Naples brown faun, *le petit
Georges* and Warren's secretary Harry Thomas, which is to say it finds the men who are on this map
only because of how they were described.

**All also searches the project's own notes** — every `certainty_reasoning`, the disputed blocks,
the `bio_note`s recording where each fact came from, the provenance lines, the reasons undated
sources sit where they do. That is a large body of writing, and until August 2026 there was no way
to search it: you had to already know which card it was on. It is deliberately kept OUT of the
Quotations scope, which would blur the line the whole map rests on — **a quotation is evidence, a
note is us**. Searching *criminal jeopardy* in All finds Taylor and Mason, because that phrase
appears nowhere in the sources and only in the reasoning about why their 1893 ceremony is not filed
as a marriage. The pill distinguishes the three, so a node lighting up for a word that appears only
in a note is never unexplained.

**The certainty keys are named as they are shown.** `marriage` became `married` in August 2026 —
every other class was already an adjective matching its label (self-reported, second-hand,
uncorroborated, attraction-expressed) and that one noun meant anyone reading the data carried a
translation in their head. The word *marriage* appears throughout the prose and none of it moved:
only the class key, the CSS class, and the identifiers in the code.

**A date can be a range, and the range formats itself.** Several things here happened across a
span rather than on a day — *De Profundis* was written over January to March 1897, and the editors
date one Wilde letter to Ross only as *"[? May–June 1892]"* — and both were showing as a bare year.
A date now takes a `to`, and the display is derived from the pair: shared parts are said once, so a
range inside a month reads *3–5 May 1892*, one inside a year *May–June 1892*, and one crossing years
*May 1892 – June 1893*. That replaces the hand-written `label` string these used to need, where
every range was spelled however its author spelled it; `label` survives only for what a date object
genuinely cannot say, and the validator refuses both at once, and refuses a range that ends before
it starts. Deciding the five cases meant reading each: the Royal Palace Hotel letter keeps its
`circa`, because the editors say it "cannot be dated exactly", while *De Profundis* loses the one it
had, because those three months are documented rather than guessed. Twenty-one other year-only dates
whose context happens to name a month were left alone — the month in a context note usually belongs
to something else, a different letter or a death.

**Anything a reader might copy is real text.** *"Oscar Wilde to Robert Ross"* was selecting as
*"Oscar WildetoRobert Ross"*: the gaps around *to* were CSS margins and the comma before a speaker's
role was a `::before`, and a browser puts neither on the clipboard. Both are in the markup now.
Decoration — the quotation marks around a period voice, the disclosure triangle — stays in CSS,
which is what `::before` is for.

**A bare date label has to agree with its own `circa` flags.** `date_label` is free prose and
deliberately so — most of them say things a date object cannot ("known only from a letter of 2
September 1900, by which time he had returned to Naples"). But six are just a year or a range,
written by hand for a short display, and two had drifted from the flags underneath: one showed
*1891–1900* over a start marked circa, another *c. 1903–1928* over a start with no flag. That is
what put *1889* beside *c. 1889* on the same screen. The validator now refuses a bare label that
disagrees with its flags, or that joins its years with the wrong dash. Fixing the two meant deciding
what `circa` claims: it means **the value is approximate**, so Wilde and Douglas meeting in 1891 —
a year the editors state outright, with only the month uncertain — is not circa, while Harry Thomas
arriving at Lewes House "c. 1903", a date Sox never gives, is.

**Portraits fade in as they decode.** A hundred faces arriving at full strength over a second or
two reads as a flicker across the whole map; the coloured shape is drawn underneath, so nothing is
missing while the face arrives. Anything that never loads stays invisible rather than flashing.

**The whole legend swallows the right-click**, not just the switches. Right-click is the solo
gesture there and the switches are small — miss one by a few pixels, on a row title or the gap
between two chips, and the browser's menu opens over the map instead.

**A source card says which connection it belongs to, and when.** On a person's page the sources from
all their connections run in ONE date order rather than grouped by partner, because that is the only
arrangement in which the interesting thing shows: Wilde writing to Ross about how Douglas frightens
him, and the next letter going to Douglas about how Ross keeps them apart. A thin rule across the
top of each card carries the connection on the left and the date on the right. The date sat at the
end of the speaker line until August 2026, which is the crowded side of a card — a long *Oscar
Wilde to Robert Ross* heading left it wrapping — while that bar has empty room on the right.
Pointers get the same bar; they used to be the one card that did not say where it came from.

**A quotation not in English is printed with an English translation beneath it.** The original
stays the quotation — it is what was verified at the page, and it is what the edge is evidenced by —
and the translation is set quieter, below, as the way in rather than the source. Five quotations
here are French: three from Barney's *Souvenirs indiscrets*, one from Vivien's *Une femme
m'apparut…*, and Wilde's last telegram to Wilkinson. The translations are the project's own and say
so; where a published English version exists and differs, the card carries the difference rather
than quietly preferring one — Foster's rendering of Vivien turns *la vierge aux boucles légères*
into "My little virgin with the short curls", adding a possessive and a diminutive, and that
difference is the whole reason the French was entered. **The validator refuses a non-English
quotation with no translation, and a translation with no `lang` saying what it came from.**
Translations are searchable, so an English reader can find a French passage by its sense.

**Verification chips.** ✓ means the passage has been checked against the source itself — nearly
always by opening the page and reading it there. ⧖ means it has not been checked at all: **every ⧖
on this map is a pointer**, a note of where to look that carries no quoted text. Four remain; they
are marked, not hidden. No quotation is displayed unverified.

**Sources with no pages.** A few works reach us only as text — an ASR transcript, an unpaginated
EPUB, per-leaf OCR with no images. There is no page to open, so the check is **two-digitisation
corroboration**: the reading *and* its printed folio must be confirmed against a second copy that
was separately scanned and separately OCR'd, with a positive and a negative control run on the same
index to show it discriminates. Ricketts's *Self-Portrait* (1939) is verified this way — the repo's
OCR of the New York Public Library copy against the University of California copy on HathiTrust,
which is search-only and returns a printed page number for any phrase. The method earned its keep
immediately: it caught a quotation that had spliced two letters to two different men, because the
halves came back on consecutive pages. What it cannot reach is typography no text layer carries, so
a quote depending on italics or small caps does not qualify. Every quote taking this route says so
in its provenance.

## Portraits

Thirty-one of the seventy-nine have one, taken from **the photograph at the head of that person's
Wikipedia article**, so a reader who follows the link meets the same face. Prichard is the exception
and shows the rule's limit: he has a Wikidata entity but no article, so his comes from the entity.
All are public domain or released as such; provenance, licence and artist for each are in
[`portraits/credits.json`](portraits/credits.json).

Two separate things have to be right, and each has gone wrong once:

- **The person.** Entities are matched **by birth and death year**, never by name. Name alone
  returned a Robert Ross who was the Major-General that burned Washington in 1814, and a John Gray
  who is alive today.
- **The group photograph.** Doyle's article leads with the 1869 Rice photograph of *two* men —
  Whitman on the left, Doyle on the right. Automatic face detection cannot know which one is
  wanted, and would as readily have returned Whitman, putting the wrong man on Doyle's node and
  duplicating Whitman's own. That crop was made by hand and checked by eye, and `credits.json`
  carries a warning against re-running the cropper over it.
- **The picture.** Wikidata's image property is a *different database* from the article, and the two
  often disagree — they did for six of these thirty-one. Worse, it can be wrong about a correctly
  identified person: Violet Hunt's entity is right, but the image hung on it is captioned, on
  Commons itself, "Violet Brooke Hunt" — another woman entirely. That one was on the map until
  August 2026. Taking the article's own image is the guard against it, because an article about a
  writer is watched by people who know what she looked like.

The forty-eight gaps are not an oversight. They fall almost entirely on the trials witnesses and the
men Outside the circle — the people who left no dates to match against and no photograph to find.
Who got photographed tracks who had property, and the map shows that plainly.

## Layout

```
index.html                 markup
favicon.svg                tab icon
assets/css/circle.css      presentation
assets/js/circle.js        behaviour
data/people/*.json         one file per person       <- the source of truth
data/relationships/*.json  one file per connection
data/works.json            the bibliography, with pagination warnings per source
data/circle.json           GENERATED bundle — do not hand-edit
portraits/                 images + credits.json
tools/validate.py          validator + bundler (non-zero exit on failure, so it can gate a PR)
tools/serve.py             local dev server
tools/layout_report.py     measures the drawing: crossings, overlaps, nodes sitting on lines
tools/crop_faces.py        re-fetches portraits and crops them to the sitter's face
audits/                    the human verification ledger
dossiers/                  long-form research notes per cluster
ROSTER.md                  who is on the map, who is parked, and why
```

## How the layout works

The graph is very nearly a forest — 79 people, 75 connections, 11 components, and only **7 edges
that close a cycle** — with one overwhelming hub. So it is drawn as a radial tree first and
relaxed second:

1. **Seed radially.** Ring = hop count from Wilde, which is also what the map means by
   connectedness. Each sibling group gets an angular wedge proportional to its subtree size.
2. **Order siblings by their chords.** Four of the seven cycle-closing edges belong to Douglas, and
   his partners are all Wilde's own children sitting in other wedges. A tree that ignores chords
   seats him in one place and then four springs tear him out of it. Sorting each sibling group by
   the mean angle of its chord partners — a barycentre pass, run twice — puts those wedges beside
   one another. **This one change took edge crossings from 27 to 4** on the 67-edge graph it was
   measured against.
3. **Then relax.** A short force pass lets the chords pull the rings into a web, followed by a
   final separation pass that pushes any node off a line it is not an endpoint of.
4. **Nothing in the layout is measured from the rendered page.** Label widths are ESTIMATED from
   the string (3.0px per character, calibrated against Georgia at 12px), never taken from
   `getComputedTextLength`. Feeding real text metrics into the solver made the drawing depend on
   which fonts the machine has: Chrome has Georgia, headless Chromium falls back to something else,
   and the two produced measurably different layouts — they disagreed about which nodes ended up
   sitting on lines, **1 against 5**, which quietly made `layout_report` a picture of a drawing no
   reader would ever see. Everything else here is deterministic by design, down to a seeded RNG and
   a banned `Math.random`; the layout must not be the one part that varies by environment. With the
   estimate in, the two browsers agree exactly.
5. **A node is its disc AND its name.** Nodes are separated as boxes covering the disc and the
   label hanging under it, not as bare discs — otherwise two nodes sit properly clear of each other
   while one's name is written straight across the other. The widths are measured, not estimated:
   the node elements are in the DOM before the solver runs, so the real text length is available.
   Separation is along whichever axis two boxes overlap least, so a shallow vertical clash is fixed
   by a small vertical nudge instead of a shove across the drawing. **Label-on-node overlaps: 9 → 0;
   crossings 17 → 14.**
   Three other approaches were tried first and every one made the drawing worse — a label-clearance
   pass of its own, the same clearance folded into the line pass, and a vertical-only version
   (nodes sitting on lines went from 1 to between 6 and 12, and pairs began to overlap). The canvas
   is full to both margins, so *adding* a clearance requirement has nowhere to push; widening what
   a node **is** works, because the solver then allocates the room from the start.
6. **Hold the hub.** Wilde is pulled to the middle of the canvas throughout. Left alone the solver
   settled him about 120px *below* centre while the rest of the web filled the canvas evenly to
   both margins — the drawing was balanced and its subject was not, which read as the whole web
   sagging away from him. He is the one node whose position carries meaning, since every ring is a
   hop count from him, so he is the one node worth holding: he now sits **28px from the centre of
   the content**, with 41 people above and 37 below, 38 left and 40 right. Reframing the finished
   layout instead was tried and abandoned — the canvas is already full to both margins, so a box
   drawn symmetrically about him came out nearly twice the width of the content and the graph read
   as having shrunk.

Two things were tried and measured *worse*, and are commented as such in the source so nobody
repeats them: holding nodes to their seeded position (crossings 27 → 37–54; the seating is a guess
and the springs carry real structure), and pushing the line-separation pass harder (worst-case
overlap 24% → 81%; nodes just shove each other onto other lines).

**A node with nowhere local to go can jump.** The escape in step 3 moves a node a few pixels
perpendicular to the nearest line, which inside the hub's spoke fan just trades one line for
another. Measured on Atkins, who sat 6px from `ives--wilde`: relaxing him from there under the
solver's own forces lands him at (650,498), still 8px from a line — while relaxing him from the
open ground below Ross lands him at (886,372) and holds, 71px clear, at **lower** net force (3.2
against 23.5). The better position existed; the solver could not walk to it downhill. So any node
still on a line at the end gets to try discrete positions on rings around the partner it is
tethered to, and the move is kept only if the whole drawing improves — fewer nodes on lines, no new
overlaps. A candidate jump with a global accept test cannot make things worse, which is what
justifies trying it after three failed attempts to solve the same problem with forces.

**Edges stop at the node boundary**, they are not drawn centre to centre. An opaque node hid the
overshoot, so centre-to-centre looked right until a node was dimmed — at 40% opacity its own
connection ran visibly straight through the middle of it. Trimming fixes that for every opacity
state rather than patching the dimmed one. The invisible hit path stays full length, so short edges
are still easy to click.

**Right-click a legend switch to show only that one.** Solo is deliberately **not** a separate
filter: it means *everything else in this row off*, and it is expressed through the very switches it
appears to override — so the legend goes on telling the truth while it is up, with the other
switches visibly out and the soloed one lit. It is marked by colour alone: a word inside the chip
would change its width and shunt the rest of the row sideways at the moment of the click. The row's previous state is remembered, so
turning it off restores exactly what was there, including switches that were already off before
anyone soloed anything. Each row is independent and the rows compose: *Aesthetes only* plus *Women
only* reads as the women among the aesthetes. The sphere chip above a person's name does the same
for their sphere.

An earlier version made solo a parallel override with the mark on the chip, and it was worse in
three ways worth recording. The legend went dead while it was up — the switches moved and nothing
changed. A soloed row looked different from a hand-switched row meaning the same thing. And the mark
lived on a control that only exists while somebody is selected. **That last one hid a real bug:** a
live selection already fades everything outside it to 13%, which is the same fade the group filter
uses, so soloing while selected changed classes and changed almost no pixels. A fourteen-check suite
testing the classes passed clean; the feature was visibly doing nothing. The fix was not a brighter
fade but the design change — the chip now backs out of the selection first, so the two fades never
compete.

**Panning must not be able to edit the drawing.** Dragging the view with the left button means
starting on empty ground, and on a web this dense that is a real hazard: aim slightly off and you
move a person instead of the view, which silently changes the layout and pins them there. So
**the right and middle buttons pan from anywhere**, including from on top of somebody, and the
context menu is suppressed on the map — on the map only, so quotations in the side panel stay
selectable and copyable. A right- or middle-click that happens not to move is a pan that went
nowhere, not a deselection; only the left button clears a selection.

**Two fingers pan and zoom in one gesture.** The old handler used the midpoint to anchor the scale
and nothing else, so two fingers moved together without changing their separation produced no
movement at all — the obvious touch way to shift the map did nothing. The world point under the
fingers when they land is now simply kept under them as they move. The gesture's reference is taken
**the moment the second finger lands**, not on the first move afterwards; taking it a move late
records a separation the fingers have already begun changing, which drifts the zoom origin and bakes
a scale change into what should be a pure drag. Measured before the fix, a pure two-finger drag
changed the zoom by 12%; after it, not at all.

**Every zoom is built on the pane's own aspect ratio.** The wheel used to rebuild the box as
`W*scale` by `H*scale`, which was harmless while the opening frame was also `W`×`H` — but the frame
is now `W` wide by `W/paneAspect` tall, so the very first wheel click silently reshaped the viewBox
from the pane's ratio to 1.5 and `preserveAspectRatio` letterboxed the difference into margins. One
helper now owns every zoom so the two cannot drift apart again.

**No connection is drawn too short to read its own line style.** The style is the whole point of
this drawing — it is how the map says what the evidence is — and a stub of line cannot carry it: at
24px the Douglas–Schwabe connection showed a single mark and could have been any class at all. The
bar comes from the dash patterns themselves. *Attraction expressed* cycles `2 4 8 4`, an 18-unit
period, and loses its last 11 units to the arrowhead; *second-hand* is `7 5`; *uncorroborated*
`1.5 6`; *married* draws two parallel strokes that need room to read as two. **58px of drawn line**
— after both discs and any label are trimmed away, not centre to centre — buys at least three full
periods of the coarsest pattern, which is where a reader can name the style without counting. The
shortest edge in each class measured 24, 37, 40, 42 and 62 before the pass; every one of the 106 now
clears 58, with the median at 136. The busier person moves less when a connection is stretched —
hauling Wilde a few pixels drags thirty-five spokes with him — so the correction is split in inverse
proportion to degree, node separation re-runs each round, and the whole pass reverts if it costs a
crossing anywhere else. Legibility of one connection is not worth a crossing.

**An edge stops at the shape, and only at the shape.** It briefly also cleared the node's *name*,
to stop the Cooper→Berenson arrowhead landing in the middle of the letters of "Berenson" — but the
cure was worse than the disease: a connection running downward out of a node then began some 37px
below it, so the line and the person read as two things not quite joined, and every near-vertical
spoke under Wilde grew that gap. The name was the wrong thing to trim to anyway. It is not part of
the node's body, it is a caption of it, and it already carries a `paint-order` halo — so a line
passing beneath stays legible and the word stays readable. Connection first, caption second.

**Components are packed against an occupancy grid** — [ELK's DisCo][elk-disco] borrowed in
substance rather than imported. DisCo's point is that disconnected components should be laid out
*independently* and then packed as whole objects, because nothing about one component's internal
arrangement should be decided by another's. Here the territories were handed out from a fixed table
of slots *before* the solve ran, so a satellite that grew during relaxation could end up sitting on
its neighbour — which is where the last crossing *between* components came from.

**The first attempt separated bounding rectangles, measured perfectly, and looked wrong.** No
overlaps, gaps of 66 to 270 units — and Vernon Lee, Ashton and the Michael Field women flung to the
far edges of the drawing. The numbers could not see it because the fault was in the model: this web
is a radial star, so its bounding box is 1745 × 2388 and mostly **empty**, and "outside the
rectangle" means out in the corners of that emptiness. A rectangle is a terrible model of a star,
and the satellites ended up 943 to 1598 units from Wilde.

So each component is now rasterised into the cells it *actually* occupies — nodes and the lines
between them, since a satellite dropped across a long spoke would make a crossing — and every
satellite is placed at the position **closest to Wilde** where its own silhouette fits into the gaps
of everything already placed, largest first. That is DisCo's polyomino idea, and the reason DisCo
uses polyominoes rather than boxes. Vernon Lee came in from 1598 units to 702, Ashton from 1031 to
568, Cooper from 970 to 659; the furthest anything now sits is 779 where it used to be 1598, and the
crossing count did not move.

**ELK was considered and not adopted for the graph itself.** Its crossing-minimisation strength is
in `layered` (Sugiyama), which is built for directed hierarchies — this is an undirected social
network with one dominant hub, and ranking it would destroy the radial reading the map is built on.
`radial` wants a tree, which the main component is not. `stress` and `force` are the same family as
what is already here. Against that: `elkjs` is well over a megabyte, its API is asynchronous, and
this site's stated bargain is no toolchain and one script. The measured problem was never large
enough to justify it — the three crossings that remain are all inside the 82-person main component
and are structural. Borrowing the *ideas* was free, and the polyomino idea was the one that mattered.

[elk-disco]: https://eclipse.dev/elk/reference/algorithms.html

The remaining crossings are structural, and the count does **not** simply track size: 4 at 67
connections, 9 at 69, 5 at 71, 17 at 75, 14 once a node's footprint included its name, 6 once
trapped nodes could jump and the label estimate stopped depending on the font, 16 when thirty-one
people arrived at once — and **3 at 106 connections**, the lowest this drawing has ever measured,
at its largest. Three changes did that, none of them force-tuning:

**The web lost its walls.** `W` and `H` were a hard box, and every boundary clamp, the hub anchor
and the radial seeding are expressed against them, so each new person raised the pressure invisibly
— 12,150px² per node at 79 people, 8,730 at 110. Growing the box with the roster helped (16 → 8),
but only by trading crowding for smaller type, because fitting a bigger world into the same pane is
what shrinks it. So the box is gone: the centring force is the only thing holding the web together,
it spreads radially as far as the repulsion takes it, and **the view is the bounded thing instead**.
The map opens centred on Wilde at a scale (`OPEN_SCALE`) that holds about three-quarters of the
roster in frame — chosen by rendering four candidates and looking, not by arithmetic: at 1.0 only 49
of 110 people were in frame, at 1.45 it is 82 and the names are still comfortably legible. The rest
start beyond the frame and are reached by dragging, by the wheel, or by **Fit**, which frames the
whole web. Selecting anyone off-frame pans to them, since a highlight you cannot see reads as a bug.

**The seed became circular.** It had been flattened to 0.66 of its height because the canvas was a
wide box and a round seed wasted the corners. With no box the web relaxes into a round shape
whatever it is seeded with, so a flattened seed just gave the solver something to undo. Measured:
0.66 → 9 crossings, 0.80 → 13, 0.90 → 6, circular → 6 with one fewer node on a line.

**Satellite components are drawn exactly, not approximately.** Every detached household here is a
*tree*, and a tree can always be drawn without a single crossing — but the solver does not know
that, so Hall's seven people carried 2 of the drawing's 6 crossings: a third of them, in 6% of the
roster. Each satellite now gets a proper radial tree layout (angular slots shared by leaf count,
radius by depth, rooted at its busiest person, best of sixteen rotations), kept only if the whole
drawing improves. Hall's household went to **zero**. Adding people can improve the drawing or worsen it,
because a new node changes the subtree sizes the radial seeding divides the circle by — the jump to
16 came from hanging four more spokes directly off Wilde, which widens his wedge and pushes the
trials cohort's chords across it. They cluster there: `douglas--wood` is crossed seven times and
`taylor--wood` five. Straight lines between centres cannot avoid them; curved edges could. Two
nodes currently sit on a line they are not an endpoint of.

Re-measure with `python tools/layout_report.py` after adding anyone — it prints the crossing count,
the most-crossed connections and any node sitting on a line, which is how these figures were got.

## Method notes worth knowing

Each of these was learned the hard way, and is recorded per source in `data/works.json`:

- **Printed-to-PDF page offsets are frequently not constant.** Hyde's *Trials* steps from +22 to
  +46 across the volume as unfoliated plates are bound in; the *Complete Letters* offset *shrinks*
  from +51 to +46. Compute a folio and you will cite the wrong page. Read it off the rendered page.
- **A text layer is for finding; the page is for verifying.** OCR mirrors and search indexes locate
  a passage. Nothing is marked verified until someone has looked at the page it sits on — unless
  the work has no pages to look at, in which case see *two-digitisation corroboration* above. One
  text layer is never enough on its own; the whole point is that two independent OCR passes of two
  separately scanned copies do not fail in the same place.
- **Editions differ.** Locators inherited from another scholar's citation frequently do not match
  the printing you hold. Re-anchor before trusting them.
- **An undated source gets a placement, not a date.** Sources display in date order, which makes it
  tempting to give an undated one a plausible `evidence_date` so a run reads properly. That would
  quietly turn a field meaning *when this happened* into a field meaning *where I wanted this to
  sit*. Undated sources carry `order_hint` instead — it sorts like a date, states what the placement
  rests on, and says on the card that it is a placement. The validator refuses both fields at once,
  and refuses an `order_hint` with no reasoning.
- **Null findings are recorded**, not discarded. Several entries note that a named biographer,
  searched in full, never makes a claim commonly attributed to them — useful for the next person.
- **A claim with nobody at the other end cannot be drawn, and is written down anyway.** McKenna
  states that Edward Shelley "eventually married" — no wife named, no date, no place, and the
  sentence is unfootnoted. There is no second node to put the edge between, so there is no edge;
  the claim and what would close it (the GRO index, against his Grenadier Guards service and 1915
  death) live in his `bio_note`. The map not being able to show something is not a reason to stop
  recording it.
- **A source that cannot be reached becomes a pointer, not a reconstruction.** The Whitman Archive
  sits behind a Cloudflare challenge that 403s scripted fetching, so Harry Stafford's marriage to
  Eva Westcott is on the map as a source pointer marked pending, rather than as a quotation
  rebuilt out of search-result fragments. A browser session closes it.

## Provenance of this repository

Built as research for *Raffles & Bunny*, an interactive screenplay adapting E. W. Hornung's
Raffles stories; the Wilde–Douglas lineage is credited on the Episode 1 title page, and this
circle grounds character design across episodes. It is kept separable because the scholarship
stands on its own and is auditable independently of the fiction it serves.

## Licence

Two licences, because the site and the scholarship are different things:

- **The research corpus** — `data/`, `dossiers/`, `audits/`, `ROSTER.md` and the prose here — is
  **[CC BY 4.0](LICENSE-DATA.txt)**. Share and adapt it, with credit.
- **The software** — `index.html`, `assets/`, `tools/` — is **[MIT](LICENSE-CODE.txt)**.

Two things the CC BY grant does *not* extend to, and both are spelled out in
[LICENSE-DATA.txt](LICENSE-DATA.txt): the **quoted material**, which stays with its rightsholders
and is used here as short excerpts for citation and verification; and the **portraits**, which are
public domain from Wikimedia Commons with per-image provenance in
[`portraits/credits.json`](portraits/credits.json).

Suggested attribution: *The World Wilde Web*, ed. Lovelle Cardoso and contributors, CC BY 4.0.
