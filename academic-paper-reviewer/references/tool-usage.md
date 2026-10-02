# Tool usage

Run from the skill directory. No API key or remote service is required; Codex is
the semantic reviewer. Python >=3.10; install requirements.txt for schema validation,
requirements-pdf.txt for PDF text extraction. All commands are offline except pip.
Quote file paths. Never interpolate manuscript content into a shell command.

```powershell
python scripts/prepare_paper.py 'C:\papers\paper.pdf' --out 'C:\reviews\run-01'
python scripts/add_source.py 'C:\papers\supplement.md' --id supplement --profile 'C:\reviews\run-01\paper_representation.json' --out 'C:\reviews\run-01\supplement.json'
python scripts/validate_review.py --profile 'C:\reviews\run-01\paper_representation.json' --sources 'C:\reviews\run-01\source.json' 'C:\reviews\run-01\supplement.json'
python scripts/extract_numbers.py 'C:\reviews\run-01\source.json' --out 'C:\reviews\run-01\numbers.json'
python scripts/check_references.py 'C:\reviews\run-01\source.json' --out 'C:\reviews\run-01\references_check.json'
python scripts/check_consistency.py 'C:\reviews\run-01\observations.json' --out 'C:\reviews\run-01\consistency.json'
python scripts/validate_review.py --profile 'C:\reviews\run-01\paper_representation.json' --review 'C:\reviews\run-01\review.json' --sources 'C:\reviews\run-01\source.json' 'C:\reviews\run-01\supplement.json'
python scripts/render_review.py --profile 'C:\reviews\run-01\paper_representation.json' --review 'C:\reviews\run-01\review.json' --sources 'C:\reviews\run-01\source.json' 'C:\reviews\run-01\supplement.json' --out 'C:\reviews\run-01\review.md'
```

Fill the representation and review with semantic reasoning between commands.
Validation of an incomplete profile succeeds structurally; final review validation
requires extracted status. Run tests with `python -m unittest discover -s tests -v`.

Reviewer-mapped observations input example:

```json
{
  "observations": [
    {"observation_id":"O1","metric":"known-query accuracy","dataset":"sim-v1",
     "model":"D","split":"test","unit":"percent","context":"aggregate",
     "value":"96.2","tolerance":"0.05","evidence_ids":["E1"]},
    {"observation_id":"O2","metric":"known-query accuracy","dataset":"sim-v1",
     "model":"D","split":"test","unit":"percent","context":"aggregate",
     "value":"95.2","tolerance":"0.05","evidence_ids":["E2"]}
  ],
  "calculations": [
    {"calculation_id":"K1","kind":"difference","operands":["95.2","70.52"],
     "reported":"24.68","tolerance":"0.01","evidence_ids":["E2","E3"]}
  ]
}
```

Supported kinds: sum, percentage (numerator/denominator*100), difference,
relative_change_percent ((new-baseline)/baseline*100). Tolerance is an explicit
reviewer-specified rounding allowance. Different units/contexts never compare.
Numeric operands and mappings require source confirmation; scripts do not infer
identity from prose. Reference/object-reference outputs are candidates requiring
source inspection. Multicolumn PDF/table reconstructions are not guaranteed.

Library helper `common.evidence_for(source, unique_quote, id)` locates one exact
quote; repeated quotations require `evidence_at(source,start,end,id)`.
