# Lord Alfred Douglas — Murray (2020) engagements dossier

**Person id:** `douglas` · **Status:** phase-a in progress
**Source:** Douglas Murray, _Bosie: The Tragic Life of Lord Alfred Douglas_ (Sceptre, 2020 reissue of the 2000 Hodder & Stoughton biography). Work key **`murray-2020`**.
**Repo PDF:** `docs/research/queer-history/victorian/douglas/sources/Murray_2020_Bosie--a-biography-of-Lord-Alfred-Douglas.pdf` — 375 PDF pages, text-layered.
**Read:** 2026-08-03, agent R14.

---

## ! PAGINATION FINDING — there is no printed↔PDF offset for this file

**The repo PDF is an ebook conversion. It carries no printed folios at all.** Established
2026-08-03 by rendering body pages as images and looking at them (PDF 30 and PDF 53, plus the
front matter and the tail of the book):

- No running heads, no page numbers, top or bottom, on any body page.
- The Contents (PDF 7) lists chapter titles **with no page numbers beside them** — the signature
  of a reflowed ebook, not a print scan.
- PDF 5 carries the publisher's ebook boilerplate: linked blue text, "double tap images to
  increase their size" — i.e. this file is a PDF rendering of the Sceptre e-edition.
- Mechanical check over the whole text layer: the only bare-number lines in the book are inline
  section markers inside chapters (e.g. the "4" mid-page on PDF 53, which is chapter section 4,
  not a folio) and note numbers. There is no folio stream.
- There is **no index** in this edition; the back matter runs Notes → Select Bibliography →
  Wilde's inscription → Picture Acknowledgements → Picture Section, and the last several PDF
  pages are blank/plates.

**Consequence for citation.** `offset = n/a`. Every locator in this dossier and in the JSON I
touch is written **`PDF p. NNN`** — deliberately not the bare `p. NNN` form, so that a Murray
locator can never be mistaken for a printed folio the way `letters-2000` locators are read.
Provenance strings say so explicitly and record "no printed folio on the page (ebook conversion)"
in place of the usual "printed folio confirmed".

**This should be recorded in `works.json` under `murray-2020` by the roster owner** (I am not
permitted to edit that file): the note there should warn that the 2020 file is unpaginated and
that pagination differs from both the 2000 Hodder and the 2001/2020 Sceptre print printings, so
`PDF p.` locators from this file cannot be converted to print pages without the print edition in
hand.

---

## Method

Text layer extracted with pypdfium2 to a scratch mirror for **finding only**; every quote below
was then read at the rendered page image (PDF page render at scale 2, viewed) before
transcription. Excerpts are kept short (≤3 sentences) — copyrighted trade biography.
Where a passage resisted short neutral transcription, a **pointer** stands in its place
(`quote: ""`, `supports:` the claim, `verification: unverified`), with the PDF page recorded so a
human can go straight to it.

---

## schwabe — Maurice Schwabe (roster node `schwabe`)

Murray places Schwabe as **Douglas's friend first**, brought by Douglas into Wilde's circle; the
2020 Foreword then adds letters unknown to the 2000 text.

**Passage S1 — the 1893 letters (Foreword to the 2020 Edition)**

> Since the publication of this book some missing letters from Bosie to Maurice Schwabe have
> surfaced in an Australian archive. Written in 1893, Bosie addresses Schwabe as 'My darling pretty
> boy', continuing, 'I really love you far more than any other boy in the world and shall always be
> your loving boy-wife, or your "little bitch" if you prefer it.'

— Douglas Murray, _Bosie_ (2020 edn), PDF p. 20.
**Provenance:** repo PDF p. 20; **no printed folio on the page (ebook conversion)**; read as page
image 2026-08-03 · verification: verified-exact
**Supports:** First-person primary evidence, quoted at page by a named biographer, of a sexual /
romantic relationship between Douglas and Schwabe in 1893.
**Context:** the sentence before it, in Murray's own voice, is "it does seem unlikely that there was
no gay feeling in Bosie in later life"; the sentences after it note that Schwabe, back from
Australia, stayed with Douglas several months after Douglas's wedding, and that on re-reading
Murray "wonder[s]".

**Passage S2 — Murray's 2000 text on the same pair**

> Douglas introduced some of his Oxford friends to Wilde's circle, and one in particular made an
> impact: Maurice Schwabe had been a friend of Douglas for some years though his introduction to
> Wilde was unfortunate. … It is fairly easy to guess what Douglas's relationship with Schwabe had
> been, and that Wilde and Douglas were in the habit of swapping their young men.

— Douglas Murray, _Bosie_ (2020 edn), PDF p. 53.
**Provenance:** repo PDF p. 53; no printed folio (ebook conversion); read as page image 2026-08-03 ·
verification: verified-elision (one elision, marked; the elided sentences concern Schwabe's later
role as "a millstone around Wilde's neck" at the trials)
**Supports:** Murray's own reading, in 2000, that the Douglas–Schwabe relationship was sexual — but
stated as inference ("it is fairly easy to guess"), not as documented fact. The 2020 letters are
what convert the inference into first-person evidence.

**Also on Schwabe, not distilled into JSON:**
- PDF p. 60 — Schwabe introduced Wilde to Alfred Taylor.
- PDF p. 92 — Schwabe left England precipitately with Reginald Turner at the collapse of the first trial.
- PDF p. 96 — at the trials, Schwabe's name "had to be written down for the judge to see so that the courtroom did not know who it was. He was the nephew of the Solicitor-General's wife, Lady Lockwood."
- PDF p. 143 — a few months after his 1902 marriage Douglas told his wife by letter that Schwabe was staying with him. (This is the sentence the 2020 Foreword revisits.)

**Proposed class:** `documented-sexual`. First-person letters by a participant, quoted at page by a
scholarly work — the README's decision rule for the class. Fallback if the roster owner reads
"boy-wife" as insufficiently probative of sexual relations: `consensus`.

---

## Youth — Winchester and the Oxford years (PDF pp. 34-70)

Murray names four boys of the school years, plus one unnamed woman. Only Backhouse is a
sexual-relationship claim; the other three are named by Douglas himself, in the *Autobiography*
(1929) and *Without Apology* (1938), as friendships of specified kinds.

**Passage Y1 — Douglas's own three-way taxonomy of his school friendships**

> . . . I had many fine friendships, perfectly normal, wholesome, and not in the least sentimental.
> Such was my friendship with Encombe . . . I had other friendships which were sentimental and
> passionate, but perfectly pure and innocent. Such was my friendship with Wellington Stapleton
> Cotton. I had others again which were neither pure nor innocent.

— Lord Alfred Douglas, _Autobiography_ (1929), quoted by Murray, _Bosie_ (2020 edn), PDF p. 35.
**Provenance:** repo PDF p. 35; no printed folio (ebook conversion); read as page image 2026-08-03 ·
verification: verified-elision (Douglas's own ellipses preserved as printed by Murray)
**Supports:** Two named, self-classified relationships — **Viscount Encombe** (explicitly
non-sentimental) and **Wellington Stapleton Cotton** ("sentimental and passionate, but perfectly
pure and innocent"). The third category is unnamed, by design.
**Also at PDF p. 34:** "He only named one boy with whom he had been to bed during his time at
Winchester and this was certainly not a sexual encounter" — the mumps episode, in which Stapleton
Cotton climbed through Douglas's bedroom window and got into bed with him for half an hour, trying
to catch mumps so that the two would be quarantined together (PDF p. 35).

**Passage Y2 — Backhouse's claim**

> The most famous among Douglas's contemporaries who recorded in detail his sexual activity at
> school, and afterwards, was Sir Edmund Trelawny Backhouse. His scabrous, unpublished,
> _Autobiography_, written in Peking in 1943, should be treated with caution: he wrote that his six
> years at Winchester were 'a carnival of unbridled lust', and claimed to have had sexual
> relationships with more than thirty boys during his time there, including Alfred Douglas.

— Douglas Murray, _Bosie_ (2020 edn), PDF p. 36.
**Provenance:** repo PDF p. 36; no printed folio (ebook conversion); read as page image 2026-08-03 ·
verification: verified-exact
**Supports:** A named claimant of sexual relations with Douglas at Winchester, together with the
biographer's own caution about him ("There is proof that some of his claims were not true").
**Backhouse's own sentence, at the same page:** he claimed in 1943 that Douglas "would probably not
thank me for recalling numerous love episodes at Winchester in which he was usually the ascendant
and I the pathic, although positions were sometimes reversed."
**Murray's frame at the same page:** "buggery almost certainly did not take place between the
Winchester boys and it seems that when they had 'immoral relationships' with other boys they
probably went no further than mutual masturbation."

**Maurice Turner** — PDF p. 287. In _Without Apology_ (1938) Douglas "told the world about his
schoolboy love affairs, including the one with Maurice Turner. He did not know that Turner had been
dead for almost thirty years, killed in 1910 in a hunting accident." Murray's phrase is "love
affairs"; he gives Turner no other appearance in the book, and no first name beyond "Maurice".
**Not to be confused with Reginald Turner** (roster node `turner`).

**The unnamed woman, winter 1888-89** — PDF p. 44. Between leaving Winchester and going up to
Magdalen, Douglas travelled in France with his tutor Gerald Campbell; "while staying in a hotel in
the South of France he met a woman, whose identity is unknown, with whom he had his first
heterosexual affair." Douglas described her as "a lady of celebrated beauty, at least twelve years
older than myself"; she was the divorced wife of an earl and a cousin of Campbell's. The affair
ended when the tutor knocked at the bedroom door demanding the return of his "ravished ewe-lamb".
**No edge possible: the partner is unnamed in the source.**

**Edward Francis Shepherd** — PDF p. 34. An American boy at Douglas's preparatory school, "slightly
older"; "the two became close" and "parted with sadness when Shepherd left for Eton in 1883".
Murray makes no romantic or sexual claim. Recorded here as a named early attachment; **not an
edge**.

**Charlie Hickey — NULL FINDING.** Roster node `hickey` does **not** appear in Murray at all.
Mechanical check of the full text layer for "Hickey", "Hicke", "Charlie" and "Charley": **zero
matches** in 375 pages. No `douglas--hickey` edge can be built from this source.

---

## wood — Alfred Wood (roster node `wood`)

**Passage W1**

> Wilde and Douglas were treading a dangerous path. Douglas had befriended a young and unemployed
> clerk from Oxford called Alfred Wood, who proved to be less than honest, and when letters from
> Wilde to Douglas turned up in the hands of blackmailers like Wood with whom they had slept, the
> two sides of Wilde's homosexual life came together: the romantic love for Douglas and the sexual
> encounters with rent boys.

— Douglas Murray, _Bosie_ (2020 edn), PDF p. 60.
**Provenance:** repo PDF p. 60; no printed folio (ebook conversion); read as page image 2026-08-03 ·
verification: verified-exact
**Supports:** Murray's assertion that Douglas as well as Wilde had slept with Wood. "they" in "with
whom they had slept" takes Wilde and Douglas as its antecedent — the subject of the sentence's first
clause.
**Note on the strength of the claim:** the sentence is Murray's own, unfootnoted at this point, and
the plural "blackmailers like Wood" makes it a class statement rather than an itemised one.
**At PDF p. 95** Murray adds only what the trial record already carries: "Douglas had given the
unemployed clerk several of his old suits, and Wood claimed that he had found the letters in the
pockets."

**Proposed class:** `alleged` — a single secondary source, asserting in passing and in the plural,
with no first-person evidence offered for the Douglas half of the claim. (Contrast `wilde--wood`,
which rests on Wood's sworn testimony and a jury conviction.)

---

## Philip Danney — autumn 1893 (NOT on the roster; new-node candidate)

Register note per README: ages are given exactly as Murray gives them.

**Passage D1 — how the boy came into it**

> Robert Ross had stayed in Bruges with the Reverend Biscale Hale Wortham, who kept a boys' school
> there and was also the brother-in-law of Ross's tutor at King's, Oscar Browning. Ross had known a
> pupil there, Philip Danney, since the lad was fourteen. Danney was now sixteen and Ross invited
> him to 'stay' with him in London.

— Douglas Murray, _Bosie_ (2020 edn), PDF p. 68.
**Provenance:** repo PDF p. 68; no printed folio (ebook conversion); read as page image 2026-08-03 ·
verification: verified-exact
**Supports:** The identity, age and route of the boy at the centre of the incident; Murray's source
is a letter from Max Beerbohm to Reginald Turner.
**Murray's framing sentence just before it:** "Douglas had a strong reason of his own for going
abroad at this time. As usual, it had to do with a boy."

**Passage D2 — what Murray says happened**

> response was to rush to London, seduce the boy and take him back to Goring where, according to
> Oscar Browning's summary of events, 'On Saturday the boy slept with Douglas, on Sunday he slept
> with Oscar. On Monday he returned to London and slept with a woman at Douglas' expense.'

— Douglas Murray, _Bosie_ (2020 edn), PDF p. 69 (sentence continues from p. 68, "Douglas's").
**Provenance:** repo PDF p. 69; no printed folio (ebook conversion); read as page image 2026-08-03 ·
verification: verified-exact
**Supports:** A documented sexual relation between Douglas and Danney, contemporaneously summarised
by a third party (Oscar Browning). Also the aftermath: Danney returned to Bruges three days late,
told his headmaster, and his father went to the police but dropped the prosecution "when he realised
that although Ross and Douglas would be sentenced to two years each, his own son would spend six
months in prison"; "Wilde's name was kept out of it" and "Ross hid in Davos."

**NEW-NODE CANDIDATE.** If the roster owner creates `danney`, this supports a `douglas--danney`
edge at `documented-sexual` (contemporary third-party summary, not participant testimony — could
also be argued at `alleged`), and separately a `danney--ross` and a `danney--wilde` edge. **Not
created: creating person files is the roster owner's call.** This is also the single strongest piece
of Douglas–Ross *joint* evidence in the book — see the Ross section below.

---

## 'Florifer' — 1897-98 (nickname only; no node possible)

**Passage F1**

> Douglas claimed that, at this period, he was getting away from the crimes with which Wilde was
> associated, but this is not true: a letter from Wilde to Turner mentions that Douglas was in love
> with a boy nicknamed 'Florifer', who was only fourteen.

— Douglas Murray, _Bosie_ (2020 edn), PDF p. 121.
**Provenance:** repo PDF p. 121; no printed folio (ebook conversion); read as page image 2026-08-03 ·
verification: verified-exact
**Supports:** A named (nicknamed) attachment of Douglas's in the post-Naples period, evidenced by
Wilde's correspondence. Murray adds: "Although, as we have seen, Wilde cannot always be believed,
his reference to this relationship has been substantiated by others."
**No edge is possible:** the person exists in the record only under a nickname. Recorded here as a
lead. Murray's note 107 at PDF p. 333 is the citation to chase.

---

## Doris Edwards — 1913 (NOT on the roster; new-node candidate)

**Passage E1**

> Shortly after Olive left him, a woman appeared providentially during the Custance libel case and
> offered him money. … Her name was Doris Edwards and she helped Douglas through a trying period but
> also lured him into 'immorality'.

— Douglas Murray, _Bosie_ (2020 edn), PDF p. 195.
**Provenance:** repo PDF p. 195; no printed folio (ebook conversion); read as page image 2026-08-03 ·
verification: verified-elision (the elided clause records that Douglas turned down the money but
began to see her regularly, and that she "filled the void in his life created by Olive's departure")
**Supports:** The identity and the occasion.

**Passage E2 — the sexual claim**

> For some weeks he took her everywhere with him in innocent friendship, explaining to her that as a
> Catholic he could not have an affair with her. In the end, though, he succumbed to temptation and
> slept with her.

— Douglas Murray, _Bosie_ (2020 edn), PDF p. 195.
**Provenance:** as above · verification: verified-exact
**Supports:** Sexual relations, asserted flatly by the biographer, with a footnote (n. 7) to
Douglas's own *Autobiography*, pp. 259-60 (per the notes at PDF p. 339).
**Corroborating first-person material at PDF pp. 195-196:** Douglas's own letter to his wife, which
in the same breath denies and concedes — "although I had met and known Doris for some time I utterly
refused to do wrong with her", then "Now I have fallen into living in sin and I am utterly
miserable." He signed himself "Your loving Boy".
**Identification, at PDF p. 339 (Notes, ch. 6 n. 6):** "The identity of the woman named D.E. in the
Autobiography can be deduced from the letters of Lord Alfred Douglas to Nathalie Barney in the
Doucet Library, Paris. Doris Edwards subsequently became Doris Carlyle." (Read in the text layer
only; not verified at page image — see the pointer list.)

**NEW-NODE CANDIDATE `edwards-doris`.** If created, supports a `douglas--edwards-doris` edge,
proposed `documented-sexual` (biographer's flat assertion resting on Douglas's own memoir, plus
Douglas's letters), dated 1913, ending with the reconciliation with Olive during the bankruptcy
examination. Gender f. **Not created.**

---

## Ivor Goring — 1926-27 (NOT on the roster; new-node candidate)

Register note: Murray states Goring's age. Transcribed as stated.

**Passage G1**

> Late in 1926 a young man by the name of Ivor Goring turned up on Douglas's doorstep and asked for
> his help. He said he had no one else and that he was penniless. Ivor Goring was then eighteen.

— Douglas Murray, _Bosie_ (2020 edn), PDF p. 261.
**Provenance:** repo PDF p. 261; no printed folio (ebook conversion); read from the extracted text
layer, **page image not yet consulted** · verification: unverified ⧖
**Supports:** The start date and Goring's age. Murray's framing sentence: "Douglas struck up one of
the most enigmatic relationships of these years."

**Passage G2 — what Murray concludes about it**

> There was no doubt that the relationship was platonic, but it was then open to misconstruction. …
> Douglas let slip the iron façade he had kept in place for twenty years and admitted to Herbert
> Moore Pim, 'In the end I got very fond of him; he is very good-looking and attractive.' There is
> no doubt that Douglas was physically attracted to Ivor, but it was not for this reason that he
> took him under his wing.

— Douglas Murray, _Bosie_ (2020 edn), PDF p. 262.
**Provenance:** repo PDF p. 262; no printed folio (ebook conversion); read as page image 2026-08-03 ·
verification: verified-elision (the elided sentences concern Goring's mother, their poverty, and
Douglas's charity)
**Supports:** Both halves of the finding at once — Murray asserts one-directional physical
attraction on Douglas's side **and** asserts that nothing sexual took place. That is the exact shape
of the README's `attraction-expressed` class.
**Also at PDF pp. 261, 263:** Goring told Beverley Nichols "I am the reincarnation of Dorian Gray";
Murray reads him as "infatuated, if not with Douglas as an older man, then with the ideal of him as
a young one", wanting "to recreate with Douglas the Wilde-Bosie relationship, with Douglas taking on
the role of Wilde". It ended in April 1927 when Goring took a film job with Ivor Novello and sailed
on the *Aquitania* to America; Douglas wrote at least two poems about him, of which one survives —
"To — With an Ivory Hand Mirror", his last lyric poem, titled so as to preserve the young man's
anonymity.
**The 2020 Foreword, PDF p. 20, revisits this too:** Murray, listing what he would now hold less
firmly, names "that strange, brief, later friendship with Ivor Goring."

**NEW-NODE CANDIDATE `goring-ivor`.** If created, supports a `douglas--goring-ivor` edge, proposed
`attraction-expressed`, `direction: douglas`, `outcome: unknown` (Murray says platonic in 2000 and
"I wonder" in 2020 — the outcome is exactly what the source leaves open), 1926-1927. Gender m.
**Not created.** Note the id must not collide with the place-name Goring-on-Thames, which appears
throughout the same book.

---

## Later attachments Murray records but does not name

- **PDF p. 44** — the unnamed woman in the South of France, winter 1888-89 (see Youth section).
- **PDF p. 104** — Le Havre, July 1895. Left there by More Adey, Douglas "decided to do some sailing
  and hired two young sailors as crew. The local paper discovered this and published an article
  accusing the young English lord of trying to corrupt the youth of the town." He gave up the boat
  and was hounded; the police watched him. Douglas's reply to the paper is quoted: his crime is
  being Wilde's friend. **No names given; no romantic or sexual claim made by Murray** — the
  accusation is the newspaper's. Recorded because the task asked specifically about Le Havre.
- **PDF p. 229** — "At one point Douglas claimed that he had been having an affair with a woman
  during the last years of Wilde's life, but whether this was true or not (and there is no other
  evidence to support such a claim)…" — Douglas's own unsupported claim, unnamed partner. Read in
  the text layer only ⧖.
- **PDF p. 20** — Murray records that he "did ignore one lurid claim of a sexual encounter with
  Bosie very late in his life from someone who seemed to me a fantasist." Claimant unnamed, claim
  rejected by the biographer. Not an edge; recorded so the record shows it was considered.

---

## ross — Robert Ross (roster node `ross`): what Murray actually says

**The task question was whether Murray, a named biographer readable at page, supports the
early-1890s Douglas–Ross affair that our `alleged` edge carries as a McKenna-only pointer.
He does not. He does not assert it, hint at it, or mention it to reject it.**

Mechanical basis for that statement: "Ross" occurs 388 times across 103 PDF pages of the book. Every
occurrence in the pre-1900 chapters (PDF pp. 51, 53, 64, 66, 68, 69, 87, 91, 92) was read in
context; PDF 53, 68, 69 and 170 were read at page image. Nothing in any of them describes a sexual
or romantic relationship between Douglas and Ross. Targeted regex sweeps over the whole text
(`Ross … Douglas … (bed|affair|lover|sex|slept|intimac|relations)` and its mirror) return only the
Wilde-copyright quarrel, the 1921 *Evening News* death-hoax, and Douglas's charge that Ross
corrupted young boys.

**Passage R1 — Murray's account of how they met**

> Friendship with Wilde meant that Douglas began to move in a new circle of people. … Of them,
> perhaps the most important was Robert Ross. … Whether or not he was 'the first boy Oscar ever
> had', he was certainly devoted to Wilde, and when he was ousted as Wilde's lover by a series of
> attractive young men, he grew bitter. When Douglas first got to know him, though, Ross was an
> amusing and appealing personality. The two quickly became friends, as did More Adey who shared
> rooms with Ross.

— Douglas Murray, _Bosie_ (2020 edn), PDF p. 53.
**Provenance:** repo PDF p. 53; no printed folio (ebook conversion); read as page image 2026-08-03 ·
verification: verified-elision
**Supports:** This is exactly where a Douglas–Ross affair would sit if Murray held one. What Murray
puts there instead is friendship — with the rivalry running *through* Wilde ("ousted as Wilde's
lover"), not between the two men.

**Passage R2 — the closest thing to intimacy, and it runs through a third person**

The Philip Danney affair of autumn 1893 (full transcription in the Danney section above): Ross, whom
Murray calls "smitten", tells Douglas that the sixteen-year-old is in London; Douglas goes and takes
him to Goring; Danney's father drops the prosecution on realising "that although Ross and Douglas
would be sentenced to two years each, his own son would spend six months in prison". Shared sexual
milieu and shared legal jeopardy — **not** a relationship between the two men.

**Passage R3 — Douglas's own dating of the break, 1909, four years before Ransome**

> I agree with you that it is better that we should keep apart. I don't consider that you have ever
> been a real friend of mine, in the sense that More and others have been my friends. And I may tell
> you frankly that I don't think your character has improved with age.

— Douglas to Ross, c. early 1909, quoted by Murray, _Bosie_ (2020 edn), PDF p. 170.
**Provenance:** repo PDF p. 170; no printed folio (ebook conversion); read as page image 2026-08-03 ·
verification: verified-exact
**Supports:** The break located in 1909 and in Douglas's post-conversion turn, not in the 1913
Ransome trial. Murray's frame: Douglas's preceding paragraph, refusing "those who are engaged in
active propaganda of every kind of wickedness from anarchy to sodomy", was "actionable in itself",
and Ross was advised against proceeding by Sir George Lewis.

**Murray's chronology of the feud, for the record (not distilled to JSON):** the 1905 *De Profundis*
publication; the December 1908 Ritz dinner in Ross's honour, which Douglas declined and then
resented (PDF p. 168); Crosland's campaign through the *Academy* (PDF pp. 168-169); Ross's evidence
against Crosland in the Manners-Sutton case (PDF p. 170); Ross's deposit of the *De Profundis* MS in
the British Museum, late 1909, sealed (PDF pp. 170-171); the Ransome trial, 1913 (PDF p. 193); Ross's
criminal prosecution of Douglas, 1914 (PDF pp. 199-210); and Douglas's masses for Ross after Ross's
death — "I felt that as he was my greatest enemy and spent 10 years of his life trying to ruin me
and my reputation I ought to try to help him, as of course I've forgiven him" (Douglas to Marie
Stopes, 1939; PDF p. 316, text layer only ⧖).

### Class I would now propose for `douglas--ross`

**Keep `alleged`, but rewrite the `disputed` block.** The certainty label should not move on my say-so
— but the *grounds* have changed materially. Before, the disputed block said the McKenna claim was
"Not directly rebutted in any source read this session" and listed Murray as "likewise unconsulted".
Murray has now been consulted, in full, at page. He is the standard modern biography of the
*other* party to the claim, he is candid about Douglas's sex life to the point of saying "no such
defence can be made for Bosie" over ages (PDF p. 20), and he had every reason to record a
Douglas–Ross affair if he believed in one. His silence is therefore **informative** silence, not
absence of coverage.

Concretely, I would propose:
- `disputed.asserted_by` — keep McKenna, but **strike the parenthetical "with echoes in later
  biography (e.g. Murray, Bosie (2000), likewise unconsulted)"**. That clause is now falsified:
  Murray does not echo the claim. This is the one thing in our existing records that Murray
  contradicts.
- `disputed.disputed_by` — add Murray as a **named biographer whose full account of the pair,
  read at page, contains no such relationship**, with PDF p. 53 as the locus.
- `disputed.grounds` — add that the non-corroboration is now positive, not merely unchecked.
- `date_label` / `summary` — Murray dates the estrangement to 1908-09 (Ritz dinner, Crosland,
  Douglas's break-off letter), earlier than our "friendly until c. 1912". Douglas's own 1929 memoir
  said he "declined to go on associating with him", which now reads as consistent with 1909.

If the roster owner would rather the edge carry only what is documented, the alternative is to
**delete the edge** and record the pair's association on the person records instead — the two men
were fellow intimates of Wilde and later enemies, but on the evidence actually readable at page
they were never a couple. I do not think that call is mine.

---

## Maurice Turner — summer 1887, Winchester (NOT on the roster; strongest new-node candidate)

**Not Reginald Turner.** Roster node `turner` is Reginald Turner, of Wilde's exile circle. Maurice
Turner was a Winchester boy, the son of a housemaster, and appears nowhere near Wilde. Murray gives
him a sustained treatment at PDF pp. 39-40 and returns to him twice (PDF pp. 56, 287); Douglas gave
him a whole chapter of *Without Apology* (1938).

**Passage T1 — how it began**

> It was during the summer of 1887 that Douglas had what was perhaps his most intense emotional
> relationship during his time at school. It is unlikely that it had a sexual side since he was
> confident enough of its purity to devote a whole chapter to it in his 1938 book of memoirs
> _Without Apology_.

— Douglas Murray, _Bosie_ (2020 edn), PDF p. 39.
**Provenance:** repo PDF p. 39; no printed folio (ebook conversion); read as page image 2026-08-03 ·
verification: verified-exact
**Supports:** The date, the intensity, and Murray's judgement on the sexual question.

**Passage T2 — the meeting, with ages as Murray states them**

> German measles lasted only a few days but the boys were quarantined for three weeks, and it was
> during the first days of his illness that Douglas set eyes on Maurice Turner, who was two years
> younger and the son of a housemaster: 'a violent mutual attraction sprang up'.

— Douglas Murray, _Bosie_ (2020 edn), PDF p. 39 (the inner quotation is Douglas's own).
**Provenance:** as above · verification: verified-exact
**Supports:** Mutuality, stated in Douglas's own words. Douglas was sixteen in the summer of 1887
(b. 22 October 1870); Murray states only "two years younger" for Turner and gives him no birth date.
The rest of the page: the boys became inseparable, walking the empty school fields; at the parting
in the matron's room "they kissed each other and wept openly" in front of her, and "She saw nothing
reprehensible in this."

**Passage T3 — Douglas's own insistence on its nature**

> 'Our relationship,' he wrote, '(perhaps I ought to make it clear in this day, when any great
> friendship between persons of the same sex is generally labelled homosexual as a matter of course)
> was entirely innocent and idyllic, but it was certainly sentimental to the last degree, which was
> very far from being the case with most friendships between older and younger boys in my day at
> Winchester. Immorality there might be, but sentiment no!'

— Lord Alfred Douglas, _Without Apology_ (1938), quoted by Murray, _Bosie_ (2020 edn), PDF p. 40.
**Provenance:** repo PDF p. 40; no printed folio (ebook conversion); read as page image 2026-08-03 ·
verification: verified-exact
**Supports:** The participant's own statement, made in 1938 and unprompted, that the relationship was
sentimental and not sexual — the textbook shape of `romantic-nonsexual`, where the record makes no
sexual claim and the parties say so themselves.
**Murray's own weighting, same page:** "In old age he would never have written in such detail of his
time with Maurice Turner had their friendship been in any way 'immoral'. It is fascinating, though:
not only did it signal the high point in the succession of his encounters with other boys at
Winchester, it set a precedent for his future relationships, with both men and women." And at PDF p.
56: "it seems, his relationship with Maurice Turner was the ideal."

**The one wrinkle.** At PDF p. 287, describing *Without Apology*, Murray writes that Douglas "told
the world about his schoolboy love affairs, including the one with Maurice Turner", and notes
Turner "had been dead for almost thirty years, killed in 1910 in a hunting accident". "Love affairs"
there sits against "entirely innocent" at PDF p. 40. Both readings are Murray's, thirty pages
apart. Flagged rather than resolved.

**NEW-NODE CANDIDATE `turner-maurice`.** If created, supports a `douglas--turner-maurice` edge,
proposed `romantic-nonsexual` — display label "Romantic", which is exactly the case the README
describes: documented mutual attachment where the record makes no sexual claim, and here the
participant explicitly denies one. Dates 1887, effectively ended the same summer; last recorded
contact when Douglas visited Winchester from Oxford. Turner died 1910. Gender m. **Not created —
new nodes are the roster owner's call.** The id must be distinct from `turner`.

---

## George Montagu — 1888 (weak lead; reported, not proposed)

At PDF pp. 40-41 Murray describes Douglas's last Winchester year: George Montagu, Encombe's fag and
four years Douglas's junior, later 9th Earl of Sandwich, described by Douglas as "a fair-haired,
blue-eyed pretty boy with engaging manners". Murray: "He fell for the boy's charm during his last
term, and since their mothers were great friends often stayed at the family's home, which doubtless
fired his adoration. Montagu was a boy in whom Douglas could take an almost fatherly interest and he
made a beeline for him whenever he visited Winchester after he had gone up to Oxford." (PDF p. 41,
text layer only ⧖; PDF p. 40 read at page image.)

Murray's own hedge — "almost fatherly interest" — puts this below the README's bar for
`attraction-expressed`, which asks that the desire be legible as desire to a reader not already holding
the coding hypothesis. **Reported as a lead; no edge proposed.** Montagu matters to the record
anyway: he is the fiancé Olive Custance jilted in 1902 (PDF pp. 139-141), which the
`custance--douglas` record already carries.

---

## NULL FINDINGS in Murray (2020) — roster names checked and not supported

Mechanical sweep of the full text layer (375 pages), then context reading of every hit.

| roster id | occurrences in Murray | finding |
|---|---|---|
| `hickey` (Charlie Hickey) | **0** — also 0 for "Hicke", "Charlie", "Charley" | Absent from the book entirely. **No edge possible from this source.** |
| `ives` (George Ives) | 4, all in the endnotes | Citations only — Stokes's article on the Ives diaries (PDF pp. 322, 323) and two Wilde-to-Ives letters (PDF pp. 327, 333). Murray's main text never discusses Ives. **Nothing to append to `douglas--ives`.** |
| `adey` (More Adey) | present throughout | Confirms the settled null. Murray has Adey as Ross's flatmate (PDF p. 53), as the man who left Douglas at Le Havre in 1895 (PDF p. 104), and as the friend Douglas named against Ross in 1909 — "I don't consider that you have ever been a real friend of mine, in the sense that More and others have been my friends" (PDF p. 170). **No contrary evidence. Do not create an edge.** |
| `grainger` (Walter Grainger) | 2 (PDF pp. 65, 90) | Grainger was **Douglas's** Oxford servant, brought by Douglas to Goring in the "Salomé Summer" of 1893; Murray's only other mention is the libel-trial question to Wilde. **No romantic or sexual claim about Douglas and Grainger.** |
| `turner` (Reginald Turner) | 16 | Companion, correspondent and Egypt travelling party; the Wilde-to-Turner letter is Murray's source for 'Florifer'. **No romantic or sexual claim about Douglas and Reginald Turner.** |
| `gray`, `raffalovich`, `taylor`, `shelley`, `atkins`, `mavor`, `parker-charles`, `parker-william`, `conway`, `scarfe`, `pollitt`, `marillier`, `miles`, `whitman`, `fothergill`, `warren`, `prichard`, `wilkinson`, `didaco`, `rolla`, `bloodworth`, `saunders`, `goddard`, `holt`, `langtry`, `balcombe` | 0 or Wilde-only | No Douglas pair supported. John Gray appears twice, both times as the man Douglas *displaced* in Wilde's affections (PDF pp. 52, 272) — a fact about `gray--wilde`, not about Douglas. |
| `barney` (Natalie Clifford Barney) | 7 | Murray's Barney material is Barney's pursuit of **Olive Custance** (PDF p. 133) and Barney's later friendship with Douglas in America (PDF pp. 135, 137). Douglas's own letter to Olive: "please don't think for an instant that I shall fall in love with her" (PDF p. 135). **No `barney--douglas` edge.** Note that Murray's endnote at PDF p. 339 makes Douglas's letters to Barney, in the Doucet Library, the source that identifies Doris Edwards. |

---

## Pointers ⧖ — read in the text layer only, page image not consulted

These are recorded so the roster owner (or a later pass) can go straight to them. Nothing below is
carried into JSON as a verified quote.

| PDF p. | what is there |
|---|---|
| 41 | George Montagu: "He fell for the boy's charm during his last term … an almost fatherly interest" |
| 44 | The unnamed woman, South of France, winter 1888-89 — Douglas's first heterosexual affair |
| 104 | Le Havre, July 1895: the two young sailors hired as crew, the newspaper accusation, the police watch |
| 108 | Walter Spindler, the *Poems* frontispiece portrait, and the inscribed presentation copy ("from his friend") |
| 183 | Bankruptcy, 14 January 1913, on a money-lender's petition |
| 229 | Douglas's own unsupported claim of an affair with a woman during Wilde's last years |
| 240 | Mr Justice Avory's sentence in full, including the surety "particularly to Mr Winston Churchill" |
| 244 | *In Excelsis*: first sonnet 20 February 1924, sequence finished Good Friday 18 April; MS confiscated |
| 249-250 | Release 12 May 1924; publication in the *London Mercury*, October 1924, and by Martin Secker that December |
| 261 | Raymond certified to St Andrew's Hospital, Northampton, 26 August 1927; Ivor Goring's arrival, aged eighteen |
| 263 | The end of the Goring episode, April 1927; the last lyric poem, "To — With an Ivory Hand Mirror" |
| 315, 317 | The Colmans' farm at Lancing; "Old Monk's Farm" named |
| 316 | Douglas to Marie Stopes, 1939, on having masses said for Ross |
| 339 | Notes, ch. 6 n. 6 — the Doucet Library letters that identify Doris Edwards, later Doris Carlyle |

---

## Summary of what this dossier proposes

**Edges created (both parties already on the roster):**

| file | proposed class | one line |
|---|---|---|
| `douglas--schwabe.json` | `documented-sexual` | Douglas's own 1893 letters, quoted at page in the 2020 Foreword — "My darling pretty boy", "your loving boy-wife" |
| `douglas--wood.json` | `alleged` (+`disputed`) | Murray's single unfootnoted clause that the blackmailers were men "with whom they had slept"; Wood was Douglas's Oxford valet |

**Sources appended to existing edges:** `douglas--ross.json` (3), `douglas--wilde.json` (2),
`custance--douglas.json` (2). No certainty, reasoning or disputed block was altered on any existing
edge.

**New-person candidates, in descending order of evidential strength — for the roster owner:**

1. **Maurice Turner** — Winchester, summer 1887. `romantic-nonsexual`. Murray pp. 39-40, 56, 287.
2. **Philip Danney** — autumn 1893. Sixteen at the time; Ross had known him since he was fourteen.
   Third-party contemporary summary of the acts. Murray pp. 68-69. Would also give `danney--ross`
   and `danney--wilde`.
3. **Doris Edwards** (later Doris Carlyle) — 1913. `documented-sexual`. Murray p. 195, note at p. 339.
4. **Ivor Goring** — 1926-27. `attraction-expressed`, direction `douglas`, outcome `unknown`.
   Murray pp. 20, 261-263.
5. **Sir Edmund Trelawny Backhouse** — Winchester, mid-1880s. `alleged`, with a `disputed` block
   written from Murray's own caution ("There is proof that some of his claims were not true").
   Murray p. 36.
6. **George Montagu**, later 9th Earl of Sandwich — 1888. Below the bar; reported only. Murray pp. 40-41.
7. **Edward Francis Shepherd** — prep school, to 1883. Friendship only; no claim. Murray p. 34.
8. **Wellington Stapleton Cotton** and **Viscount Encombe** — self-classified by Douglas as
   "sentimental and passionate, but perfectly pure and innocent" and as "not in the least
   sentimental" respectively. Encombe is a clear non-edge. Stapleton Cotton is arguable at
   `romantic-nonsexual` on Douglas's own words. Murray p. 35.

Not proposable at all, for want of a name: the unnamed divorced countess of 1888-89 (p. 44), the two
Le Havre sailors (p. 104), the boy known only as "Florifer", who Murray states was fourteen (p. 121),
the unnamed woman of Douglas's 1920s claim (p. 229), and the unnamed late-life claimant Murray
dismissed as a fantasist (p. 20).
