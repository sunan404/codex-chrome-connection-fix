# AI / ML / NLP / LLM / Agent empirical layer

Inspect training/validation/test split provenance, duplicates, prompt examples,
retrieval indexes, model selection and test reuse. A risk of contamination is an
inference; alleging demonstrated contamination requires direct evidence.

Record dataset/version/license or access, preprocessing, model/checkpoint/API
version and access date, prompt/system prompt/template, temperature/sampling,
context window, retrieval settings, seeds, dependencies, hyperparameters and tuning
budget. Report unavailable information without guessing default API behavior.

Check baseline fairness: same data access, information, tuning budget and evaluation
budget; include compute where central to the contribution. For agents, distinguish
episode/task independence, tool affordances, memory initialization, retries,
feedback generation, failure handling and environment constraints. Synthetic
retrieval geometry does not automatically establish behavior of real embeddings.

For LLM-as-a-judge, inspect rubric and prompt disclosure, judge version, blinding,
position/style bias, repeated judgments and human agreement. For human evaluation,
inspect participant selection, task protocol, blinding and inter-rater reliability.
Judge observations nested within tasks are not automatically independent units.

Inspect factor-specific ablations, robustness, sensitivity to workload/seed/model,
and subgroup reporting only insofar as they inform the paper's actual claims.
Suggested experiments must explain the uncertainty they resolve. Do not demand
real-world deployment if the claim is explicitly limited to a synthetic mechanism.
