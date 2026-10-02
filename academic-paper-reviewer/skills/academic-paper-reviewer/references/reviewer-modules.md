# Shared representation, seven logical modules

Read the profile once, use its common IDs, and return to original sections to
confirm uncertainty. Each module returns typed audit statements and zero or more
concerns using `concern.json`. Empty findings are allowed; absence of findings is
not evidence of flawlessness. Preserve all seven module records even if a module
is not applicable, explaining why in its audit. No multi-agent execution required.

1. **methodology**: research question, design alignment, controls, confounders,
   leakage, randomization, sampling, synthetic/real boundaries, baseline relevance,
   factor attribution and sanity comparisons. Use the general rubric.
2. **statistical**: independent unit, sample size, repeated observations,
   pseudoreplication, intervals/effect size/tests/bootstrap, multiplicity, variance,
   seeds and subgroups. Read statistical-review.md.
3. **ai_ml**: splits/contamination, prompts/models/API versions, sampling/seeds,
   hyperparameters, fair baselines/compute/evaluation, judges/human protocols,
   test reuse, ablation, robustness and sensitivity. Read ml-review-rubric.md.
4. **claim**: compare claim strength and scope across abstract/introduction/
   results/discussion/conclusion; create the graph after independent concerns.
5. **writing**: clarity, structure, flow/coherence, consistent terminology,
   redundancy, tone, vague adjectives, inflated language, abstract/body alignment,
   table/figure explanation. Keep these findings separate from scientific quality.
6. **reproducibility**: audit dataset and version, preprocessing, code, seeds,
   model and version, prompts, dependencies/environment/hyperparameters/hardware,
   evaluation/statistical procedures, raw results and analysis scripts. Label each
   AVAILABLE/PARTIAL/MISSING/NOT_APPLICABLE with exact evidence or searched coverage.
   AVAILABLE means reported in supplied material, not independently reproduced or
   downloaded. URLs alone do not establish working access.
7. **internal_consistency**: compare abstract/table/body/conclusion numbers,
   sample/seed/experiment counts, percentages/CI, table/figure/equation references,
   citation numbering and terminology. Use scripts for supported arithmetic and
   numbering; semantic consistency still requires reasoning.

Strength analysis follows claim verification. Meta-review follows all modules;
use severity-policy.md for merging, disagreements and prioritization. Every module
may acknowledge author-disclosed limitations or ask a question only when it affects
a judgment and cannot be answered from the supplied material.
