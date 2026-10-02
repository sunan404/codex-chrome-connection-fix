# Extension contracts (not implemented providers)

`scripts/literature.py` declares a Protocol and an explicit unavailable adapter:

```python
paper_search(query) -> list[ExternalRecord]
paper_fetch(identifier) -> ExternalRecord
citation_lookup(reference) -> list[ExternalRecord]
related_papers(query) -> list[ExternalRecord]
```

An external record includes provider, identifier, URL, retrieval date, status,
metadata, source text and exact inspected quotes. Empty results must distinguish a
completed search with no matches from unavailable access. No fallback fabrication.

Future Semantic Scholar/OpenAlex/Crossref/arXiv/ACL Anthology adapters must manage
rate limits, attribution, stable IDs, source coverage, failed retrievals and
untrusted input. Bibliographic metadata can establish publication metadata only;
semantic citation judgments need the source passages. Claim support scoring and
acceptance prediction are deliberately excluded.

Other discipline packs add method/rubric instructions selected by field/paper type,
while retaining the common evidence ledger, graph assessments and meta-review.
Possible next work: OCR with uncertainty regions, reliable table layouts, included
LaTeX/BibTeX parsing, external source adapters and independently sampled live-model
evaluations. External-source and venue-rubric artifacts are present in the schema
so future integrations cannot silently bypass provenance.
