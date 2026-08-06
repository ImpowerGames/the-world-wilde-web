# Portrait provenance

Every portrait here is the **lead image from that person's Wikipedia article**, taken under
Wikipedia's own policy for lead images: each is either in the public domain or carries a Creative
Commons licence permitting reuse. Each was checked before inclusion.

`credits.json` records, per portrait, the source and the licence.

**Crops.** Most were cropped to the sitter's face automatically. A few were done by hand and are
marked as such in `credits.json` — the clearest case being Peter Doyle, whose Wikipedia lead image
is the c.1869 M. P. Rice photograph of **two** people, Whitman on the left and Doyle on the right.
Automatic detection has no way to know which face is wanted and would as readily have returned
Whitman, putting the wrong man on Doyle's node and duplicating Whitman's own portrait. If that
source is ever refetched, re-crop by hand and **look at the result**.

**Not everyone has one.** A portrait is only here when a free image exists. Most of the people on
the *outside the circle* tier have none, and that absence is itself part of what the map records:
the men who survive under a first name or no name at all were not photographed for posterity.

The tool that fetched and cropped these lives in the private research repository, not here — it
depends on a third-party face-detection model. See `research-tools/portraits/` there.
