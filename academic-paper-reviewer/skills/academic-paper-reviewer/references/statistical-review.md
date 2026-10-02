# Statistical audit

First identify the independent sampling/randomization unit: participant, task,
episode, dataset, seed, cluster or deployment. Count independent units separately
from repeated observations. For paired treatments use the paired structure;
resampling query rows independently from clustered episodes may understate variance.

Inspect sample size rationale, repeated measurement, pseudoreplication, seed
variation, aggregation and subgroup analyses. Report what is described; do not
infer tests, bootstrap units, confidence intervals or variance from conventions.

Check effect magnitude and unit before significance: percentage point difference
is subtraction of percentages; relative percentage change divides by baseline.
Do not convert one into the other silently. Compare the same task, model, metric,
split and aggregation context. Confidence intervals must indicate confidence
level, sampling/resampling unit and estimator. Exact deterministic recalculation
needs sufficient operands and the specified formula.

Inspect assumptions of the reported test, bootstrap design, multiplicity, selective
reporting, heterogeneity and whether variability spans independent units. Large
query counts do not rescue a small number of independent simulations. Statistical
significance does not establish practical importance or causal attribution.

No reported CI/test is a reporting or inferential limitation, not proof of no
effect. A nonsignificant contrast is not evidence of equivalence without an
appropriate design and interval/margin. A useful, well-designed negative result is
a scientific strength; avoid equating unexpected results with poor methodology.
