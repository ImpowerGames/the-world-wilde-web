# The World Wilde Web

A sourced map of documented romantic and sexual relationships in Oscar Wilde's circle,
1870s–1940s. **71 people, 67 connections, 321 quotations** — every claim carries the words it rests
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

It is a plain static site: HTML, one stylesheet, one script, JSON and images. It can be published
to GitHub Pages or any static host with no build step beyond `python tools/validate.py`.

## What it does

**Line style records how we know**, not what happened. The reference deliberately makes no claim
about sexual acts in either direction — criminal law was designed to keep that evidence out of the
record, so treating its absence as a finding would mistake the effect of prosecution for a fact
about someone's life.

| | |
|---|---|
| **Married** | a legal marriage |
| **Self-reported** | a participant's own words — letters, diaries, sworn testimony |
| **Second-hand** | someone else present, or a historian, attests it |
| **Uncorroborated** | asserted, but nothing supports it; the dispute is shown |
| **Desire expressed** | the record is one-sided; the arrow shows which way |

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

**Verification chips.** ✓ means someone opened the source and read the passage on the page. ⧖
means not yet confirmed there — either located in a text layer but unchecked, or a pointer naming
where to look. Ten remain; they are marked, not hidden.

## Portraits

Thirty of the seventy-one have one, taken from **the photograph at the head of that person's
Wikipedia article**, so a reader who follows the link meets the same face. Prichard is the exception
and shows the rule's limit: he has a Wikidata entity but no article, so his comes from the entity.
All are public domain or released as such; provenance, licence and artist for each are in
[`portraits/credits.json`](portraits/credits.json).

Two separate things have to be right, and each has gone wrong once:

- **The person.** Entities are matched **by birth and death year**, never by name. Name alone
  returned a Robert Ross who was the Major-General that burned Washington in 1814, and a John Gray
  who is alive today.
- **The picture.** Wikidata's image property is a *different database* from the article, and the two
  often disagree — they did for six of these thirty. Worse, it can be wrong about a correctly
  identified person: Violet Hunt's entity is right, but the image hung on it is captioned, on
  Commons itself, "Violet Brooke Hunt" — another woman entirely. That one was on the map until
  August 2026. Taking the article's own image is the guard against it, because an article about a
  writer is watched by people who know what she looked like.

The forty-one gaps are not an oversight. They fall almost entirely on the trials witnesses and the
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

The graph is very nearly a forest — 71 people, 67 connections, 11 components, and only **7 edges
that close a cycle** — with one overwhelming hub. So it is drawn as a radial tree first and
relaxed second:

1. **Seed radially.** Ring = hop count from Wilde, which is also what the map means by
   connectedness. Each sibling group gets an angular wedge proportional to its subtree size.
2. **Order siblings by their chords.** Four of the seven cycle-closing edges belong to Douglas, and
   his partners are all Wilde's own children sitting in other wedges. A tree that ignores chords
   seats him in one place and then four springs tear him out of it. Sorting each sibling group by
   the mean angle of its chord partners — a barycentre pass, run twice — puts those wedges beside
   one another. **This one change took edge crossings from 27 to 4.**
3. **Then relax.** A short force pass lets the chords pull the rings into a web, followed by a
   final separation pass that pushes any node off a line it is not an endpoint of.

Two things were tried and measured *worse*, and are commented as such in the source so nobody
repeats them: holding nodes to their seeded position (crossings 27 → 37–54; the seating is a guess
and the springs carry real structure), and pushing the line-separation pass harder (worst-case
overlap 24% → 81%; nodes just shove each other onto other lines).

The four remaining crossings are structural — Douglas's chords to Ross and Schwabe against Wilde's
spokes to Ives and Ross. Straight lines between centres cannot avoid them; curved edges could.

## Method notes worth knowing

Each of these was learned the hard way, and is recorded per source in `data/works.json`:

- **Printed-to-PDF page offsets are frequently not constant.** Hyde's *Trials* steps from +22 to
  +46 across the volume as unfoliated plates are bound in; the *Complete Letters* offset *shrinks*
  from +51 to +46. Compute a folio and you will cite the wrong page. Read it off the rendered page.
- **A text layer is for finding; the page is for verifying.** OCR mirrors and search indexes locate
  a passage. Nothing is marked verified until someone has looked at the page it sits on.
- **Editions differ.** Locators inherited from another scholar's citation frequently do not match
  the printing you hold. Re-anchor before trusting them.
- **Null findings are recorded**, not discarded. Several entries note that a named biographer,
  searched in full, never makes a claim commonly attributed to them — useful for the next person.

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
