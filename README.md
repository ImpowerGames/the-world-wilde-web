# The World Wilde Web

A sourced map of documented romantic and sexual relationships in Oscar Wilde's circle, 1870s–1940s. **110 people, 106 connections, 389 quotations** — every claim carries the words it rests on and the page they came from.

It began with Wilde because that is where the surviving paper is thickest. The intended scope is wider: a map of queer relationships of the period, and contributions extending it — the Paris salons, the women's networks, circles we have not touched — are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Running it

```bash
python tools/serve.py
```

Rebuilds the data bundle, validates it, and serves at <http://localhost:8000>. Double-clicking `index.html` will not work — the browser will not fetch the data from a `file://` page.

There is **no JavaScript toolchain and nothing to install** Python 3.8+ is the only requirement.

|                                    |                                                         |
| ---------------------------------- | ------------------------------------------------------- |
| `python tools/serve.py`            | rebuild, validate, serve                                |
| `python tools/validate.py`         | rebuild `data/circle.json`                              |
| `python tools/validate.py --check` | validate only — use in CI                               |
| `python tools/layout_report.py`    | measure the drawing                                     |
| `python tools/test_navigation.py`  | assert the pan/zoom gestures (needs the site served)    |
| `python tools/test_solo.py`        | assert the legend's solo filter (needs the site served) |

It is a plain static site: HTML, one stylesheet, one script, JSON and images. It can be published to GitHub Pages or any static host with no build step beyond `python tools/validate.py`.

**The About panel's text is a markdown file**, `content/ABOUT.md`, compiled into the data bundle by `tools/validate.py`. `{{line:<certainty>}}` becomes the real connection line, drawn from the same definitions the legend uses, and `{{colophon}}` becomes the generated build line.

## What it does

**Line style records how we know**, not what happened. The reference deliberately makes no claim about sexual acts in either direction — criminal law was designed to keep that evidence out of the record, so treating its absence as a finding would mistake the effect of prosecution for a fact about someone's life.

The lightest class is deliberately light. **Attraction expressed** covers everything from a written declaration down to a single admiring line about a stranger — _"a very handsome young soldier of twenty"_ is enough.

|                          |                                                                                                                 |
| ------------------------ | --------------------------------------------------------------------------------------------------------------- |
| **Married** (`married`)  | a legal marriage                                                                                                |
| **Self-reported**        | a participant's own words — letters, diaries, sworn testimony                                                   |
| **Second-hand**          | someone else present, or a historian, attests it                                                                |
| **Uncorroborated**       | asserted with very little supporting evidence; or actively contested                                            |
| **Attraction expressed** | the record is one-sided — a declaration, an approach, or admiration noted in passing; the arrow shows which way |
| **No connection**        | not a connection at all — the switch for people the map records but joins to no one                             |

**Married means a legal marriage.** Alfred Taylor and Charles Mason went through a marriage in 1893, Taylor in a wedding dress as the bride, rings exchanged, a wedding breakfast for friends afterwards. Charles Parker gave it in evidence at the Old Bailey, Pierre Louÿs wrote to Gide about it in the present tense as _"a marriage — a real marriage"_, Taylor retold it himself for years, and Wilde wrote to Mason asking after his _"married life"_. It is filed as **Self-reported** instead of **Married**, because two men in England in 1893 could not contract a legal marriage. The edge carries the ceremony in full in its summary and sources either way.

**Node shape marks legal gender** in the genogram convention — squares for men, circles for women, a dashed outline where the record does not say. **Color groups people by sphere**, using a [ColorBrewer](https://colorbrewer2.org/#type=qualitative&scheme=Paired&n=9) palette

**Verification chips.** ✓ means the passage has been checked against the source itself — nearly always by opening the page and reading it there. ⧖ means the source has not been read yet: **every ⧖ on this map is a pointer**, a note of where to look that carries no quoted text.

## Portraits

Thirty-one of the seventy-nine have one, taken from **the photograph at the head of that person's Wikipedia article where available and from other public domain sources when not**.

All are public domain or released as such; provenance, licence and artist for each are in [`portraits/credits.json`](portraits/credits.json).

## Layout

```
index.html                 markup
favicon.svg                tab icon
assets/css/circle.css      presentation
assets/js/circle.js        behaviour
data/people/*.json         one file per person
data/relationships/*.json  one file per connection
data/works.json            the bibliography, with pagination warnings per source
data/circle.json           GENERATED bundle — do not hand-edit
portraits/                 images + credits.json
tools/validate.py          validator + bundler (non-zero exit on failure, so it can gate a PR)
tools/serve.py             local dev server
tools/layout_report.py     measures the drawing: crossings, overlaps, nodes sitting on lines
```

## How the layout works

The graph is very nearly a forest with one overwhelming hub (Wilde). So it is drawn as a radial tree first and relaxed second:

1. **Seed radially.** Ring = hop count from Wilde, which is also what the map means by connectedness. Each sibling group gets an angular wedge proportional to its subtree size.
2. **Order siblings by their chords.** Four of the seven cycle-closing edges belong to Douglas, and his partners are all Wilde's own children sitting in other wedges. A tree that ignores chords seats him in one place and then four springs tear him out of it. Sorting each sibling group by the mean angle of its chord partners — a barycentre pass, run twice — puts those wedges beside one another.
3. **Then relax.** A short force pass lets the chords pull the rings into a web, followed by a final separation pass that pushes any node off a line it is not an endpoint of.

**Components are packed against an occupancy grid** — [ELK's DisCo][elk-disco] was used for inspiration. DisCo's point is that disconnected components should be laid out _independently_ and then packed as whole objects, because nothing about one component's internal arrangement should be decided by another's. Here the territories were handed out from a fixed table of slots _before_ the solve ran, so a satellite that grew during relaxation could end up sitting on its neighbour.

Re-measure with `python tools/layout_report.py` after adding anyone — it prints the crossing count, the most-crossed connections and any node sitting on a line.

## Controls

To **pan**, _click-and-drag_.

To **zoom**, _scroll_ or _pinch-and-zoom_.

To **move a node**, _press-and-hold the node until it turns gold_, then _drag it_.

To **reset a node**, _press, hold, and release the node without moving_.

To **solo a filter**, _right-click the switch for the filter in the legend_, and it will toggle on that filter and toggle off all the others in the same category.

**Right-click a legend switch to show only that one.** Solo means _everything else in this row off_. The row's previous state is remembered, so
turning it off restores exactly what was there, including switches that were already off before soloing. Each row is independent and the rows compose: _Aesthetes only_ plus _Women only_ reads as the women among the aesthetes. The sphere chip above a person's name does the same for their sphere.

## Method notes worth knowing

Each of these was learned the hard way, and is recorded per source in `data/works.json`:

- **Printed-to-PDF page offsets are frequently not constant.** Hyde's _Trials_ steps from +22 to +46 across the volume as unfoliated plates are bound in; the _Complete Letters_ offset _shrinks_
  from +51 to +46. Compute a folio and you will cite the wrong page. Read it off the rendered page.
- **A text layer is for finding; the page is for verifying.** Automated OCR mirrors and search indexes locate a passage. Nothing is marked verified until someone has looked at the page it sits on.
- **Editions differ.** Locators inherited from another scholar's citation frequently will not match the printing you hold. Re-anchor before citing them.
- **Undated sources can specify an order hint.** Sources display in date order. Undated sources carry `order_hint` instead — it sorts like a date, states what the placement rests on, and says on the card that it is a placement. The validator refuses both fields at once, and refuses an `order_hint` with no reasoning.
- **Null findings are recorded**, not discarded.
- **A source that cannot be reached becomes a pointer.**

## Provenance of this repository

Built as research for _Raffles & Bunny_, an interactive adaptation of E. W. Hornung's Raffles stories. It is published separately because the scholarship stands on its own and is auditable independently of the fiction it serves.

## Licence

- **The research corpus** — `data/` and the prose here — is **[CC BY 4.0](LICENSE-DATA.txt)**. Share and adapt it, with credit.
- **The software** — `index.html`, `assets/`, `tools/` — is **[MIT](LICENSE-CODE.txt)**.

Two things the CC BY grant does _not_ extend to, and both are spelled out in [LICENSE-DATA.txt](LICENSE-DATA.txt): the non-public-domain **quoted material**, which stays with its rightsholders and is used here as short excerpts for citation and verification; and the **portraits**, which are public domain from Wikimedia Commons with per-image provenance in [`portraits/credits.json`](portraits/credits.json).

Suggested attribution: _The World Wilde Web_, ed. Lovelle Cardoso and contributors, CC BY 4.0.
