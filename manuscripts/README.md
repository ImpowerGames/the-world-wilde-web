# manuscripts/ — where the documents are, not the documents

**No images live here, and none ever should.** Each subdirectory holds one file: a
`MANIFEST.json` describing the pages of one archive's holdings — page numbers, archival
shelfmarks, the archive's own image pointers, and the rights statement the archive attached to
each page.

The site draws manuscript pages from the **holding archive's IIIF image service**, live. A
source record cites an archive, an item and page numbers; `tools/validate.py` resolves that
against the manifest; the reader builds the image URL from the archive's `iiif_url` template and
the page's pointer. Nothing is copied, so every scan is served by the institution that made it,
under that institution's rights statement, and a reader always gets the archive's current copy.

## Adding an archive

Create `manuscripts/<key>/MANIFEST.json`. The `key` is what source records name in
`facsimile.archive`.

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
    "iiif_url": "https://hrc.contentdm.oclc.org/digital/iiif/p15878coll50/{pointer}"
  },
  "items": [
    {
      "itemId": "2700",                          // what facsimile.item names
      "title": "Letters from Oscar Wilde to George Ives",
      "boxFolder": "Box 2, Folder 7",
      "pages": [
        {
          "page": 1,                             // what facsimile.pages names — stable, unlike filenames
          "pointer": "2677",                     // the archive's id for this image
          "shelfmark": "MSS_WildeO_2_7_001",
          "rights": "http://rightsstatements.org/vocab/NoC-US/1.0/"
        }
      ]
    }
  ]
}
```

`iiif_url` must address a IIIF Image API endpoint; the reader appends
`/full/<size>/0/default.jpg`. Check the service's `profile` in its `info.json` before assuming a
size form works — **level 1 has `240,` but not `!240,240`**, and CONTENTdm answers the
unsupported form with a broken image rather than an error, so it fails silently.

An archive with no IIIF service can still be indexed: pages will carry their shelfmark, rights
and record link, and the reader will show those without an image.

## Keeping a local copy

Fetch the images into the **private** repository, outside `web/`, and keep this manifest in step
with the copy that sits beside them. The site links so that provenance stays with the archive;
the private copy exists so the research outlives the archive's hosting. See
`../../manuscripts/README.md` in the private tree.

## Present

| key | archive | items | pages |
| --- | --- | --- | --- |
| `hrc` | Harry Ransom Center, The University of Texas at Austin | 13 | 572 |
