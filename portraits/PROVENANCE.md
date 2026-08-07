# Portrait provenance

Every portrait here is the **lead image from that person's Wikipedia article**, taken under Wikipedia's own policy for lead images: each is either in the public domain or carries a Creative Commons licence permitting reuse. Each was checked before inclusion.

`credits.json` records, per portrait, the source and the licence.

Most were cropped to the sitter's face automatically. A few were done by hand and are marked as such in `credits.json` — the clearest case being Peter Doyle, whose Wikipedia lead image is the c.1869 M. P. Rice photograph of two people, Whitman on the left and Doyle on the right. Automatic detection has no way to know which face is wanted and would as readily have returned Whitman, putting the wrong man on Doyle's node. If that source is ever refetched, re-crop by hand and look at the result.

Not every person has an image. A portrait is only here when a free image exists. Contributions of appropriately-licensed photos are welcome to fill out our gaps.

The tool that fetched and cropped these lives in the private research repository. It depends on a third-party face-detection model.
