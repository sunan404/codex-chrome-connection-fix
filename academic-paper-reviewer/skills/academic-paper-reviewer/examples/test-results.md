# Validation results — 2026-10-02

Environment: Windows / PowerShell, Python 3.14.3. JSON Schema dependency installed;
optional PyMuPDF is available. No API calls or external manuscript upload were used.

## Automated run

```text
python -m unittest discover -s tests -v
Ran 41 tests in 12.807s
OK
```

- 6 structure/claim/provenance and manually authored semantic regression tests.
- 11 numeric identity, arithmetic, rounding, finite-input and reference checks.
- 6 end-to-end/format tests including CLI flow, Chinese rendering, supplements,
  PDF text/blank pages, scanned PDF explicit failure and original-file preservation.
- 18 artifact hallucination/provenance/coverage, injection-data, external-source,
  disagreement, score exclusion and summary-length checks.

Additional checks:

```text
python -X utf8 <bundled skill-creator>/scripts/quick_validate.py <skill>
Skill is valid!

python scripts/validate_review.py --profile examples/example_paper_profile.json --review examples/example_review.json --sources examples/example_source.json
PASS: schema, exact provenance and graph invariants. Semantic support still requires review.

python -m compileall -q scripts examples tests
PASS
```

## Required behavior cases

| Case | Retained evidence / result | Validation type |
|---|---|---|
| Synthetic-only evidence with broad real-world conclusion | E5/E21/E24; C3=OVERSTATED | Codex-authored semantic fixture + regression |
| Authors already disclose external-validity limitations | E21/E22; explicitly acknowledged, CL01/MD01 merged | Codex-authored semantic fixture + origin/dedup validation |
| Abstract 96.2% vs table 95.2% | E1/E15; one mapped NUMERICAL_CONFLICT | Deterministic calculation + end-to-end CLI |
| Embedded reviewer score instruction | E25 retained as untrusted data; no instructed score emitted | Parser non-execution + manual-output regression |
| Missing seeds | MISSING, not established; no invented one-seed assertion | Codex-authored audit + searched-coverage enforcement |
| Strong negative result | E9/E12/E18; C2=SUPPORTED; S2 strength | Codex-authored semantic fixture + regression |

The example includes three audited claims, three strengths, five raw module
concerns merged to four final concerns, all seven reviewer audits, and all sixteen
reproducibility fields. Table arithmetic: 95.2 − 70.52 = 24.68 percentage points.
All evidence quotes resolve to exact locations in the fictional input.

## Interpretation limits

The combined fixture is plausible academic material created for this test; it is
not a real publication. Semantic conclusions were authored by the creating Codex
against the full manuscript and saved in examples/build_example.py. Regression
tests preserve those judgments; they do not independently generate fresh reviews.
No independent agent, fresh-run model sampling, broad real-paper benchmark,
calibrated hallucination rate, external novelty verification or semantic citation
retrieval was performed. Injection pattern detection is not a complete security
filter. Structural provenance validation is not a semantic entailment proof.
