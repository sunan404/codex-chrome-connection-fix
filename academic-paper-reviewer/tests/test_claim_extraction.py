"""Parser/provenance tests plus regression assertions on manually authored judgments."""
import tempfile
import unittest
from pathlib import Path
from support import FIXTURES
from common import read_json
from prepare_paper import parse_source, prepare
from build_example import build
from validate_review import validate


class ClaimExtractionTests(unittest.TestCase):
    def test_candidates_do_not_become_confirmed_claims(self):
        with tempfile.TemporaryDirectory() as temp:
            prepare(FIXTURES / "synthetic_memory.md", temp)
            profile = read_json(Path(temp) / "paper_representation.json")
            candidates = read_json(Path(temp) / "claim_candidates.json")
            self.assertTrue(candidates)
            self.assertEqual(profile["claims"], [])
            self.assertEqual(profile["status"], "needs_semantic_extraction")
            self.assertTrue(all(c["status"] == "UNCONFIRMED_CANDIDATE" for c in candidates))

    def test_chinese_structure_and_offsets(self):
        source = parse_source(FIXTURES / "chinese.md")
        self.assertIn("结果", {s["section"] for s in source["segments"]})
        self.assertEqual(source["segments"][-1]["end"], len(source["text"]))

    def test_latex_is_read_without_include_execution(self):
        source = parse_source(FIXTURES / "paper.tex")
        self.assertIn("\\input{never-execute-this}", source["text"])
        self.assertIn("Methods", {s["section"] for s in source["segments"]})
        self.assertTrue(source["warnings"])

    def test_manually_reasoned_overclaim_regression(self):
        source, profile, review, _ = build()
        self.assertEqual(validate(profile, {"manuscript": source}, review), [])
        graph = {a["claim_id"]: a for a in review["claim_evidence_audit"]}
        self.assertEqual(graph["C3"]["assessment"], "OVERSTATED")
        self.assertEqual(graph["C3"]["experiment_ids"], [])

    def test_disclosed_limitation_acknowledged_in_manual_review(self):
        _, _, review, _ = build()
        self.assertIn("already disclose", review["claim_evidence_audit"][2]["reasoning"])
        scopes = [c for c in review["concerns"] if c["root_cause"] == "unsupported_transfer"]
        self.assertEqual(len(scopes), 1)
        self.assertEqual(set(scopes[0]["origin_ids"]), {"CL01", "MD01"})
        self.assertIn("explicitly acknowledge", scopes[0]["reasoning"])

    def test_negative_diagnostic_is_strength_in_manual_review(self):
        _, _, review, _ = build()
        audit = next(a for a in review["claim_evidence_audit"] if a["claim_id"] == "C2")
        self.assertEqual(audit["assessment"], "SUPPORTED")
        self.assertTrue(any("E18" in s["evidence_ids"] for s in review["strengths"]))
        self.assertFalse(any(c["root_cause"] == "negative_result" for c in review["concerns"]))


if __name__ == "__main__":
    unittest.main()
