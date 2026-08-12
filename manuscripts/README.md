# manuscripts

The manuscripts folder records where the documents are located but does not include copies of the documents themselves. The copies are housed in a private repo outside of ths one.

**An archive with no `iiif_url` may be indexed here but cannot back a `facsimile`.** `tools/validate.py` refuses one, because the reader would draw a "View original" button that resolves to nothing, and such an archive is left out of `web.json` — there is nothing to browse into, and its page list would be weight for every visitor. `morgan` and `marland-blog` are in that position; a record that wants to point at them uses `manuscript` with a `url`.

The site draws manuscript pages from the **holding archive's IIIF image service**, live. A source record cites an archive, an item and page numbers; `tools/validate.py` resolves that against the manifest; the reader builds the image URL from the archive's `iiif_url` template and the page's pointer. Nothing is copied, so every scan is served by the institution that made it, under that institution's rights statement, and a reader always gets the archive's current copy.

## `manuscript`

Most quoted letters have no scan here: their originals are in other archives. Those records carry `manuscript.repository` instead, which the reader shows as an `MS …` chip.

**Every location is a _last known_ location.** Nothing here has been confirmed by going to an archive; each one is what an edition recorded, and editions have dates. The Complete Letters say so of private hands on p. xviii — its list "indicates the last known location" — and the Hyde Collection proves it of institutions, having become the British Library three years after the volume named it. The chip therefore names its authority and its year rather than a present tense nothing here can support. The single exception is a `facsimile`: that page draws the archive's own image service live, so the holding is proved by the picture on screen and the chip stays present tense.

**Every source says where it is.** For the great majority of the corpus the honest answer to "where is this" is not a building, so `tools/validate.py` derives one of three, and the reader's location filter carries them below the archives:

|               | when                                                                                         | what it tells a reader                                                  |
| ------------- | -------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **Published** | the document IS the work — a biography, a study, an editorial note, the printed trial record | there is no single original to see; any library with the edition has it |
| **Online**    | the work's `kind` ends `-web`                                                                | read where it is published; no library copy, and it can be taken down   |
| **Unknown**   | the document is a unique object (letter, diary, inscription…) and no archive is recorded     | nobody has traced it                                                    |

**Read the headnote with the tool, and distrust it twice.** `research-tools/source-volume/ms_locations.py` walks back from a quotation to its heading, and both of its blind spots produced the same wrong answer — a letter reported as having no manuscript when the volume names one. The OCR glues the headnote 92 times in 1408 (`MSClark`), and the volume has a second heading shape for letters between other people (`Reginald Turner to Robert Ross`), which the appendix on Wilde's last illness is almost entirely made of. Both are fixed; the lesson is that "print-only" is a claim to check at the page, not a result to write down.

A consequence worth knowing: `works.json` `kind` is now load-bearing rather than decorative, and the validator refuses one it does not recognise. A work with no publisher and no `ia_id` reads as unpublished, which is right for a lecture text or a personal communication and would be wrong for a book whose publisher nobody has filled in — the Internet Archive id is what rescues the 1924 _Art and Man_, whose publisher we have never confirmed.

**The repository names are the volume's own.** The Complete Letters prints a key to locations at pp. xxii–xxv, headed "Manuscript and Other Locations", which resolves the `MS Clark` / `MS Hyde` line above each letter and divides its abbreviations into three groups: INSTITUTIONS, INDIVIDUAL OWNERS, and FACSIMILES. Take the name from there rather than from memory, and note the one house deviation: the key writes Clark out as "…University of California, Los Angeles", and we use "William Andrews Clark Memorial Library, UCLA", which is what fits on a chip.

**No individual owner is named; the letter is located anyway.** The volume warns on p. xviii that its list "indicates the last known location of letters in private hands", because "private collectors often dispose of them discreetly; executors are understandably reluctant to disclose information; individuals become untraceable". So `MS Mason` resolves to a named living person, correct in 2000 and unverifiable now, and printing it on a public map would be both stale and an intrusion. Two entries in that list are exceptions, because what they name is a collection and not a person: the Hyde Collection (written as the British Library, below) and the Frederick R. Koch Collection.

The other 29 quoted letters — `MS Mason`, `MS Maguire`, `MS Secker`, the Hollands, Preston, Simpson, Dugdale, O'Donohue, Hughan, Rothenstein, Du Cann, Wilkinson, and `MS Private`, which names nobody at all — are written as **`Private collection`**. Take that list from the volume's own key rather than from a count of what a script reported: the first pass here built it from a frequency count and silently lost the tail, which is seven owners.

`MS Dickey` is not in this group and not in the key either — an abbreviation that appears above a letter to John Lane and is expanded in no footnote. The one record that would have inherited it quotes an inscription in a copy of _Salomé_, which the note places in the Sterling Library.

**One name is deliberately not the volume's.** The key expands `MS Hyde` to "The Hyde Collection", which in 2000 meant Mary Hyde Eccles's library at Four Oaks Farm, New Jersey. She died in 2003 and the collection was split: the Samuel Johnson material went to Harvard's Houghton Library, and **Wilde's archive went to the British Library**, where it is the Lady Eccles Oscar Wilde Collection, the manuscript portion cataloged as Add MS 81619–81884. The British Library says so itself, in [Researching manuscripts in the Lady Eccles Oscar Wilde Collection](https://www.bl.uk/stories/blogs/posts/researching-manuscripts-in-the-lady-eccles-oscar-wilde-collection) (22 January 2026). So the 48 quoted letters the volume places at "Hyde" are written here as `British Library, London (Lady Eccles Oscar Wilde Collection)`. Printing the 2000 name would send a reader looking for a private collection that no longer exists — which is exactly the staleness the volume warns about on p. xviii, only in this case the successor is public and citable.

Note this is a **different** provenance from the volume's own `MS British Library`, which is written here as `British Library, London` — 4 letters in the general manuscript collections rather than in the Eccles. The volume expands that abbreviation as "Department of Manuscripts, British Library, London", and the department is dropped for the same reason the shelfmark is: a department is an internal arrangement, not a location, and the Library has not used that name for years. The two entries stay separate because a **named collection** is a real place to be told to go; a defunct department is not.

**A second name is deliberately not the volume's, for the same reason.** The key calls it the "Pierpont Morgan Library"; the institution has been **The Morgan Library & Museum** since 2006. Written here as `The Morgan Library & Museum, New York`. Four records took the volume's name and a fifth, written by someone who had actually gone there, took the current one — so the same archive sat in the corpus under two spellings until they were reconciled. The rule that settles it is the Hyde rule: use the name a reader searching today will find.

**`archived_as` says what kind of object the archive holds** — `autograph` or `typescript` — and is written only where that contradicts the document type, so a letter needs it exactly when what survives is somebody's typed copy. It is the difference between a document that can settle emphasis and one that cannot: whoever typed the copy had already read the underlining and decided what it meant.

**A repository names an institution or a named collection, never a shelfmark.** `MA 7258` and `Add MS 81619` belong in `original_provenance`, which is the field for what you read and where. `tools/validate.py` refuses a repository containing a mark followed by digits; a parenthesised **collection** is fine and common, which is why the test is that specific.

A record may not carry both `facsimile` and `manuscript` — the facsimile already names the archive whose pages it shows — so letters at Texas take the facsimile and nothing else.

**Footnote quotations need a human read before either field is written.** A quotation lifted from a footnote inherits the heading of the letter that footnote annotates, which is right for a note _about_ that letter and wrong for a note quoting some other document. See the `de-lara` case in `research-tools/source-volume/ms_locations.py`.

## Adding an archive

Create `manuscripts/<key>/MANIFEST.json`. The `key` is what source records name in `facsimile.archive`.

```jsonc
{
  "collection": "…, Oscar Wilde Papers, 1851-1957",
  "collection_id": "p15878coll50",
  "archive": {
    "name": "Harry Ransom Center, The University of Texas at Austin",
    "short_name": "Harry Ransom Center",
    "collection": "Oscar Wilde Papers, 1851-1957",
    "collection_url": "https://hrc.contentdm.oclc.org/digital/collection/p15878coll50/search",
    // {pointer} is substituted with each page's own pointer, below.
    "record_url": "https://hrc.contentdm.oclc.org/digital/collection/p15878coll50/id/{pointer}",
    "iiif_url": "https://hrc.contentdm.oclc.org/digital/iiif/p15878coll50/{pointer}",
  },
  "items": [
    {
      "itemId": "2700", // what facsimile.item names
      "title": "Letters from Oscar Wilde to George Ives",
      "boxFolder": "Box 2, Folder 7",
      "pages": [
        {
          "page": 1, // what facsimile.pages names — stable, unlike filenames
          "pointer": "2677", // the archive's id for this image
          "shelfmark": "MSS_WildeO_2_7_001",
          "rights": "http://rightsstatements.org/vocab/NoC-US/1.0/",
        },
      ],
    },
  ],
}
```

`iiif_url` must address a IIIF Image API endpoint; the reader appends
`/full/<size>/0/default.jpg`. Check the service's `profile` in its `info.json` before assuming a
size form works — **level 1 has `240,` but not `!240,240`**, and CONTENTdm answers the
unsupported form with a broken image rather than an error, so it fails silently.

An archive with no IIIF service can still be indexed: pages will carry their shelfmark, rights
and record link, and the reader will show those without an image.

## Keeping a local copy

Fetch the images into the **private** tree, `../../manuscripts/<key>/`, and record their paths in
this manifest's per-page `file`. The site links so that provenance stays with the archive; the
private copy exists so the research outlives the archive's hosting. See
`../../manuscripts/README.md`.

## `letter_id` — how a manifest entry finds its citations

Every entry carries a `letter_id`, and so does every source record and transcription of the same
document.

```
letters-2000/1198#2      <work>/<folio>#<letter number>
letters-2000/649n3       <work>/<folio>n<note number>, for a document printed INSIDE a footnote
hrc/MSS_WildeO_2_10_004  <archive>/<shelfmark>
nypl/5936027             <archive>/<uuid>
morgan/MA7258#34         <archive>/<item>#<page number>
```

Each names the object by an identifier the object carries: a folio number, a shelfmark, an image
id.

**Which field holds it is declared per archive**, as `archive.page_id_field`: `shelfmark` for
`hrc`, `pointer` for `nypl` and `loc`, `null` for `morgan` and `marland-blog`, which publish no
page identifier. `mint_ids.py` refuses a declaration that yields a non-token or a duplicate.

```bash
python tools/manifest_links.py            # every document and what cites it
python tools/manifest_links.py --uncited  # only the ones nothing quotes yet
python tools/manifest_links.py --check    # malformed ids, and near-miss citations to look at
```

## Present

| key   | archive                                                   | items | pages |
| ----- | --------------------------------------------------------- | ----- | ----- |
| `hrc` | Harry Ransom Center, The University of Texas at Austin    | 13    | 572   |
| `loc` | Library of Congress — Whitman Papers, Feinberg Collection | 1     | 13    |

Three more archives are held **privately only**, because nothing cites them: `marland-blog`,
`morgan` and `nypl`. See `../../manuscripts/README.md`.

---

A `transcriptions/` folder sits beside each `MANIFEST.json`.
It holds one file per transcription, named `<archive>-<item>-<first image, 3 digits>.json`.
The filename is a local handle only. Each letter's identity is represented by the `letter_id` inside the file.

## Why this exists

The expensive part of a quotation is not finding the words — the Complete Letters already print
them — it is **having eyes on the document**. Marks are the one thing a printed edition cannot
settle: underlines, strikethroughs, the dashes the editors replaced with "normal punctuation as
the sense seems to demand". Those are only checkable against the manuscript, and Wilde's
underlines in particular can be carrying meaning rather than stress (see
`../CONTRIBUTING-CODE.md`).

So when a folder is being read to identify which images are which letter, the marks are read at
the same time and written down here. Doing it later would mean reading every letter again.

## Method

The volume's text is the base, because its **words** are accurate and already transcribed. What
is added here is what the volume destroys:

1. take the printed text as the starting point;
2. read the scan and restore every mark — `_underline_`, `__double__`, `~~struck through~~`,
   and the em-dashes that punctuate between words;
3. drop marks that are artefacts of the line ending, and say so;
4. record the **null findings** too — "nothing is underlined on either sheet" is a result.

### One printed italic, three different things

The Ives letters (HRC 2700) demonstrate this cleanly, because all four were read at the page in
one pass. The volume sets in italic:

| Printed as italic                                               | What the manuscript actually has                                                                    |
| --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| _Athenaeum_ (p. 1044)                                           | no mark — the editor's convention for a journal title                                               |
| _désaccord_, _rien n'est sacré à un cocher de fiacre_ (p. 1173) | no mark — the convention for French                                                                 |
| _Civilisation, Cause and Cure_ (p. 1197)                        | `'Civilization — Cause and Cure'` — **Wilde's own inverted commas**, plus his spelling and his dash |

Meanwhile the two marks Wilde _did_ make in those four letters are both lost: `_began_` at
p. 1173 is printed roman, and the underlined datelines `_Thursday_` and `_Saturday_` lose their
rule (p. 1196 loses the word as well, the volume heading the letter from its postmark instead).

So the printed italic is not evidence of a mark, and the absence of a printed italic is not
evidence there was none. Neither direction survives the edition. This is the whole reason the
transcriptions exist.

### Recognizing underlines

Not all long horizontal lines are underlines. There are often other marks that are easy to mistake for underlines:

- **Capital Ts.** Wilde draws the crossbar as a long sweep rising left to right, and it lands
  over or under the neighbouring word. `Talk`, `That` and `To` all unintentionally look like underlines
  this way. The test is whether the stroke is continuous with the letter.
- **the paper.** Ruled and squared stock, plus show-through from the verso, reads as a rule under
  a word at page size.

A real underline is the width of the word, at the writing weight, in the writing ink. Shape is
not part of the test — Wilde's underlines run from short and near-flat (`_began_`, p. 1173) to long,
rising and sweeping (`_Reading_`, p. 1029). Length against the word is what
discriminates, together with ink and weight.

When it is not clearly that, say so in `original_provenance` and leave `marks_verified` off until
a person corroborates it.

The printed volume often uses italics on an ordinary English words to signify underlines in the original text.
It is good evidence a mark exists — `_post-dated_` and `_not_` at pp. 1199–1201 were both
found that way — but the editors use italics for many other things and have sometimes transcribed marks incorrectly,
so it cannot break a tie about whether a given stroke is a mark. Say so when you lean on it for corroboration.

### How to transcribe

Transcription guidelines can be found in [`../CONTRIBUTING.md`](../CONTRIBUTING.md) and [`../CONTRIBUTING-CODE.md`](../CONTRIBUTING-CODE.md).

### The OCR text mirrors drop phrases, mis-decode them, and carry italics only partially

Two mirrors of the Complete Letters sit in `sources/_pdf-text-mirror/`: an older RapidOCR pass, and
a newer Marker pass (`*.marker.md`, with `*.pages.jsonl` and `_marker_pages/page-NNNN.md`). The
newer one is much better, but still cannot settle a quotation without consulting the pdf image directly.

**The newer pass fixed decoding errors.** Whole sentences the old pass dropped are back — the "sending notes in
a registered letter" clause at p. 1197, the 750-franc passage at p. 1200. A line the old pass
rendered as reversed gibberish at p. 1198 now reads correctly. And `pages.jsonl` carries a
`printed_folio` for every page, which replaces guessing the printed-to-PDF offset: it is **not**
constant across the volume — +20 around p. 535 and +46 around p. 1029 — so anything that assumes
one number will silently land on the wrong leaf.

**But it did not fully fix italics.** Marker emits italics, about 2,000 of them, but its recall is
poor. On printed p. 1173, which carries six (`intended`, `began`, `me`, `désaccord`, `cochers de
fiacre`, `Rien n'est sacré à un cocher de fiacre`), it found **two**. The two it missed, `began` and
`me`, are exactly the ordinary-English italics that turned out to record real underlines in the
manuscript.

So the asymmetry to work by: **an italic present in the mirror is good evidence there is one on the
page; an italic absent is no evidence at all.** And it cannot tell you a word is non-italic.

**The new OCR mirror also invents text on the facsimile plates.** The edition reproduces manuscript pages, and
Marker transcribes handwriting as though it were print, producing fluent and wholly wrong English —
`Dear Borie` for `Dear Bosie` on the _De Profundis_ opening. Confirmed handwriting pages are listed
in that folder's `README.md` and `VERIFICATION_REPORT.md`. Never quote them.

**Find with the mirror, read on the page.** `fitz`/PyMuPDF at ~320 dpi is enough to read the
type:

```python
import fitz
fitz.open(PDF)[printed_page_pdf_index].get_pixmap(dpi=320).save("page.png")
```

## Shape

Fields are named as `data/` names them, so an entry lifts without translation:

```jsonc
{
  "printed": { "work": "letters-2000", "locator": "p. 592" },
  "facsimile": { "archive": "hrc", "item": "2700", "pages": [19, 20] },
  "addressee": "George Ives",
  "context": "date, place, and what the letter is",
  "quote": "the text, with marks restored",
  "original_provenance": "which shelfmarks were read, and what was found there",
  "marks_verified": true,
  "transcribed_on": "2026-08-10",
}
```

`marks_verified` here means the same as in `web/data`: emphasis, accents and punctuation have
been collated against the document and match. It is absent, not false, when they have not.
