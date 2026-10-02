# Evidence and claim discipline

The source ledger is authoritative for provenance. Preserve original text as decoded
UTF-8 (PDF text extraction is a distinct artifact), SHA-256, source ID, half-open
Unicode character offsets [start,end), line, section and optional PDF page. Offsets
are characters, not bytes. Evidence must remain inside a source segment. Short
exact quotations plus the surrounding original paragraph establish context.
Never silently repair a quote, merge distant spans or treat a source's assertion as
independently verified. For multi-line support, use several evidence entries.

The ledger proves that a passage exists. Codex must still assess whether the passage
entails the interpretation, whether the design supports attribution, and whether
the passage is contradicted elsewhere. Preserve negative evidence and limitations.

## Information types

| Type | Required grounding | Meaning |
|---|---|---|
| manuscript_fact | evidence_ids | What this manuscript states/reports; not independent truth |
| external_fact | external_source_ids with inspected source passages | Facts actually checked outside the manuscript |
| reviewer_inference | evidence_ids + reasoning | Interpretation derived from documented evidence |
| recommendation | reasoning, normally evidence_ids | Proposed author action; not a venue requirement |

Every scientific finding, strength, audit item, executive assertion and author
question is a typed statement. Concern `claim` is classified by `information_type`;
`reasoning` and `impact` are reviewer inference; `suggested_fix` is a recommendation.
Author questions use recommendation and explain what judgment depends on the answer.
Source quotes are manuscript facts regardless of the parent concern's type.

Record missing information as not established, with `searched_source_ids` on a
reproducibility item and reasoning explaining coverage. Do not infer one seed from
no reported seeds, no controls from no described controls, or no effect from p>0.05.
External absence claims require an adequately scoped search, not a title search.

## Claim extraction

After evidence extraction, identify major assertions across abstract, introduction,
results, discussion and conclusion. Each claim has an exact anchoring passage, type
(empirical/method/theoretical/scope), strength (bounded/qualified/universal), and
scope such as datasets, tasks, configurations and deployment setting. Paraphrase
faithfully; do not synthesize stronger claims than the paper states. Keep a result
claim separate from its broader interpretation. `claim_candidates.json` is a lexical
index only: patterns cannot identify all claims or evaluate scope.

## Claim–evidence graph

Each review assessment links a claim ID to experiments, metrics, result entities,
statistical-method entities, limitations, and the exact evidence IDs supporting
each edge. Record absent links as empty arrays and explain what is unestablished.
No claim may disappear just because its support is weak.

| Assessment | Use when |
|---|---|
| SUPPORTED | Stated scope and strength fit the documented design and evidence |
| PARTIALLY_SUPPORTED | Evidence supports a meaningful subset; remaining boundary is explicit |
| OVERSTATED | A narrower result exists but the claim expands scope/strength beyond it |
| UNSUPPORTED | An assessable assertion lacks adequate support or is contradicted by available evidence |
| NOT_TESTABLE_FROM_MANUSCRIPT | Available material cannot adjudicate the assertion; distinguish access/extraction gaps |

Every assessment is reviewer inference with reasoning. Missing reported procedures
can limit confidence without making every empirical claim UNSUPPORTED. Assess
causal language against interventions/control design, synthetic→real-world scope,
retrieval→intelligence, observed configuration→universal conclusions, and evidence
absence→proof of absence. A disclosed limitation is a strength and an evidential
boundary; it does not immunize a conflicting conclusion.

## Calibration

HIGH: direct, unambiguous passages with adequate context and verified arithmetic.
MEDIUM: grounded but relies on an interpretation or incomplete reporting.
LOW: indirect, ambiguous, extraction-limited or unresolved contradictory evidence.
These are evidence-sufficiency judgments, not statistical or calibrated probabilities.
Severity measures impact; confidence measures evidential strength. They are independent.
