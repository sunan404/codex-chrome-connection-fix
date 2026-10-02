# Severity and meta-review

- critical: direct, high-confidence evidence of a central validity failure that
  undermines the main result (for example documented test labels entering training).
  Explain why ordinary clarification cannot resolve it. Do not label suspicion,
  missing reporting, modest novelty, language errors or lack of one baseline critical.
- major: materially affects a core claim, experimental interpretation or ability to
  reproduce the main finding; fixing it may require analysis/design changes.
- moderate: meaningful local uncertainty or reporting gap with bounded impact.
- minor: presentation, terminology, local arithmetic typo or clarity issue whose
  correction does not substantially change the main scientific interpretation.

Map critical/major/moderate to Major Concerns, minor to Minor Concerns, retaining
the original label. Prioritize by core claim (priority=1), experimental validity
(2), reproducibility (3), and writing repair (4); add impact reasoning within ties.
Never count reviewer votes. A negative result is not a reason to lower assessment.

Retain original findings from methodology, statistical, ai_ml, claim, writing,
reproducibility and internal_consistency in `module_findings`. Each final concern
lists `origin_ids`, `root_cause`, `affected_scope`, and `priority`.
Merge equivalent root cause, scope and remedy into one final concern and list all
origins. The validator detects duplicate explicit root-cause/scope labels, not
semantic paraphrases; Codex must perform semantic deduplication.

Before merging, reread evidence and scan whether two modules take opposing
positions on the same question. Record a `Reviewer disagreement` with a topic,
both typed positions and evidence, origins, and a reasoned resolution or an
explicit unresolved status. Do not silently prefer the majority. A resolved
disagreement remains visible with its resolution rationale.
