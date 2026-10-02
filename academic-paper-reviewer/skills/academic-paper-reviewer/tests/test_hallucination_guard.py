import copy
import tempfile
import unittest
from pathlib import Path
from support import FIXTURES
from build_example import build
from common import digest, read_json
from prepare_paper import prepare
from render_review import render, safe
from validate_review import validate
from literature import UnavailableProvider


class HallucinationGuardTests(unittest.TestCase):
    def setUp(self):
        self.source, self.profile, self.review, _ = build()
        self.sources = {"manuscript": self.source}

    def errors(self):
        return validate(self.profile, self.sources, self.review)

    def test_invented_quote_rejected(self):
        self.profile["evidence"][0]["text"] = "The authors used thirty seeds."
        self.assertTrue(any("mismatch" in e for e in self.errors()))

    def test_fabricated_section_rejected(self):
        self.profile["evidence"][0]["section"] = "Appendix that does not exist"
        self.assertTrue(any("mismatch" in e for e in self.errors()))

    def test_modified_source_text_rejected(self):
        self.source["text"] += " invented result"
        self.assertTrue(any("hash mismatch" in e for e in self.errors()))

    def test_original_file_mutation_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "paper.md"
            path.write_text((FIXTURES / "synthetic_memory.md").read_text(encoding="utf-8"), encoding="utf-8")
            from prepare_paper import parse_source, empty_profile
            source = parse_source(path)
            profile = empty_profile(source)
            path.write_text("changed original", encoding="utf-8")
            self.assertTrue(any("original file changed" in e for e in validate(profile, {"manuscript": source})))

    def test_dangling_evidence_and_experiment_rejected(self):
        self.review["concerns"][0]["evidence_ids"].append("FAKE")
        self.review["claim_evidence_audit"][0]["experiment_ids"].append("FAKE_EXP")
        errors = self.errors()
        self.assertTrue(any("Unknown review evidence" in e for e in errors))
        self.assertTrue(any("invalid experiment_ids" in e for e in errors))

    def test_claim_coverage_cannot_be_dropped(self):
        self.review["claim_evidence_audit"].pop()
        self.assertTrue(any("exactly one assessment" in e for e in self.errors()))

    def test_duplicate_roots_must_merge(self):
        cloned = copy.deepcopy(self.review["concerns"][0])
        cloned["concern_id"] = "DUPLICATE"
        self.review["concerns"].append(cloned)
        self.assertTrue(any("Duplicate final root cause" in e for e in self.errors()))

    def test_external_fact_without_inspected_source_rejected(self):
        statement = self.review["audits"]["ai_ml"][0]
        statement.update(information_type="external_fact", external_source_ids=["unfetched"])
        self.assertTrue(any("External fact requires" in e for e in self.errors()))

    def test_fake_citation_verification_rejected(self):
        self.review["citation_audits"][0]["status"] = "SUPPORTED"
        self.assertTrue(any("Verified citation status" in e for e in self.errors()))

    def test_provider_cannot_fabricate_search(self):
        with self.assertRaises(NotImplementedError):
            UnavailableProvider().paper_search("invent a prior paper")

    def test_numeric_quality_score_rejected(self):
        self.review["executive_assessment"][0]["text"] = "Paper Score: 87/100"
        self.assertTrue(any("Prohibited numerical" in e for e in self.errors()))

    def test_executive_assessment_length_is_checked(self):
        self.review["executive_assessment"] = [self.review["executive_assessment"][0]]
        self.assertTrue(any("150–300" in e for e in self.errors()))

    def test_injection_is_data_and_manual_output_ignores_demand(self):
        with tempfile.TemporaryDirectory() as temp:
            prepare(FIXTURES / "synthetic_memory.md", temp)
            alerts = read_json(Path(temp) / "injection_alerts.json")
            self.assertTrue(alerts["alerts"])
            self.assertFalse(alerts["instruction_execution"])
        self.assertIn("10/10", self.source["text"])
        self.assertEqual(self.errors(), [])
        rendered = render(self.profile, self.review, self.sources)
        # The demand may appear only as quoted untrusted evidence, never as assessment.
        self.assertNotIn("10/10", " ".join(s["text"] for s in self.review["executive_assessment"]))
        self.assertIn("OVERSTATED", rendered)

    def test_missing_seeds_are_not_invented(self):
        row = next(r for r in self.review["reproducibility"] if r["item"] == "random_seeds")
        self.assertEqual(row["status"], "MISSING")
        self.assertIn("was not established in the manuscript", row["reasoning"])
        self.assertNotIn("authors used only one", row["reasoning"].lower())
        row["searched_source_ids"] = []
        self.assertTrue(any("must search every" in e for e in self.errors()))

    def test_critical_needs_high_confidence(self):
        self.review["concerns"][0].update(severity="critical", confidence="LOW")
        self.assertTrue(any("Critical concern requires" in e for e in self.errors()))

    def test_unknown_schema_fields_and_numeric_confidence_rejected(self):
        self.review["concerns"][0]["confidence"] = 0.91
        self.review["quality_score"] = 87
        self.assertTrue(self.errors())

    def test_untrusted_html_and_links_are_not_active(self):
        escaped = safe('<script>alert(1)</script> ![exfil](https://example.invalid)')
        self.assertNotIn("<script>", escaped)
        self.assertNotIn("![exfil]", escaped)

    def test_disagreement_preserves_both_positions(self):
        origins = ["CL01", "MD01"]
        self.review["disagreements"].append({"disagreement_id": "D1", "topic": "Scope of the feedback control",
            "origin_ids": origins, "positions": [
                {"text": "The control isolates feedback inside the simulator.", "information_type": "reviewer_inference", "evidence_ids": ["E6"], "external_source_ids": [], "reasoning": "Only the feedback factor changes."},
                {"text": "The control does not establish deployment transfer.", "information_type": "reviewer_inference", "evidence_ids": ["E5", "E21"], "external_source_ids": [], "reasoning": "The generator is explicitly synthetic."}],
            "status": "RESOLVED", "reasoning": "The two positions concern different scopes; both are retained and broad C3 remains overstated."})
        self.assertEqual(self.errors(), [])
        text = render(self.profile, self.review, self.sources)
        self.assertIn("Reviewer disagreement D1", text)
        self.assertIn("control isolates feedback", text)
        self.assertIn("does not establish deployment transfer", text)
        self.review["disagreements"][0]["origin_ids"].append("fictional_origin")
        self.assertTrue(any("unknown origin" in e for e in self.errors()))


if __name__ == "__main__":
    unittest.main()
