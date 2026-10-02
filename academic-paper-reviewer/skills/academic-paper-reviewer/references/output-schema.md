# Output contract v1.0

Schemas use JSON Schema draft 2020-12. `schemas/common.json` defines evidence,
entities and typed statements; the three product schemas reference it locally.
`validate_review.py` registers only bundled schemas (no remote schema retrieval),
then checks source hashes, exact quote spans, source locations, all entity links,
claim coverage, module coverage, missing-info coverage, provenance, explicit root
deduplication, conflict origins and external-verification preconditions.

## Paper Representation

`metadata`, `sources`, `evidence`, `claims`, `research_questions`, `contributions`,
`methods`, `datasets`, `baselines`, `metrics`, `experiments`, `statistical_methods`,
`results`, `limitations`, `figures`, `tables`, `references` and extraction warnings.
Every entity has `id`, `text`, `evidence_ids`; a claim additionally has `claim_id`,
`claim_type`, `strength`, `scope`. Set status=`extracted` only after semantic review.
Unreported entities stay empty, not fabricated. Source descriptors match every
supplied source JSON exactly. `prepare_paper.py` produces an explicitly incomplete
but structurally valid profile.

## Concern

Required: concern_id, severity, category, title, claim, evidence_ids, reasoning,
impact, suggested_fix, confidence, information_type, root_cause, affected_scope,
claim_ids, origin_ids, priority. Evidence IDs resolve to the ledger's exact section,
page, line, location and text. Only manuscript_fact/reviewer_inference can label the
concern assertion; external facts appear in typed audit statements instead.
`suggested_fix` is always Recommendation, not an established obligation.

## Review

All prose-bearing assessments use typed statements. A statement has `text`,
`information_type`, `evidence_ids`, `external_source_ids`, `reasoning`. The graph has
claim_id, assessment, reasoning, evidence_ids, experiment_ids, metric_ids,
result_ids, statistical_method_ids, limitation_ids. Empty graph links must be
explained in reasoning. Every manuscript claim has exactly one assessment.

`module_findings` and `audits` contain all seven modules. `concerns` is the merged
final list; raw findings remain in module_findings. `strengths` includes grounded
text, why_it_matters and confidence. `reproducibility` audits all 16 items with
status, evidence_ids, searched_source_ids and reasoning. `disagreements` retain both
positions, origins, status and rationale. `author_questions` are recommendations.

`review_limits` explicitly records external_literature_checked, citation_verification,
supplemental_material_read (true/false), coverage (source IDs, all/partial),
unconfirmed_information and limitations (typed statements). These are declarations
of actual operations, not automatic promises. `external_sources` records retained
text/quotes; `literature_searches` records actual searches; `citation_audits`
contains individual statuses. `venue_rubric` defaults to null.

Default output: Executive Assessment (150–300 English words or Chinese characters),
Strengths, Major Concerns (including moderate), Minor Concerns, Claim–Evidence Audit,
Methodology Audit, Statistical Audit, AI/ML Experiment Audit, Internal Consistency,
Reproducibility, Writing & Presentation, Questions for Authors, Meta Review /
Reviewer disagreement, Review Limitations. Do not add an overall score. Evidence
quotes show Manuscript Fact; inference and recommendations are explicitly labeled.
The renderer supports Chinese/English headings and never replaces original quotes.

Validation proves structural and provenance invariants; it cannot prove semantic
entailment, detect every hallucinated paraphrase, or guarantee injection resistance.
Finish with a manual source-aware review. Freeform chat can use the same headings,
but artifact workflows must save and validate review.json before rendering.
