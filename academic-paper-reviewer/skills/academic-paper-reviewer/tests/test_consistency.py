import copy
import unittest
from support import FIXTURES
from build_example import build
from check_consistency import check_consistency
from check_references import check_references
from extract_numbers import extract_numbers
from prepare_paper import parse_source


class ConsistencyTests(unittest.TestCase):
    def setUp(self):
        self.source, _, _, self.input = build()

    def test_abstract_table_conflict_and_difference(self):
        output = check_consistency(self.input)
        self.assertEqual(len(output["conflicts"]), 1)
        self.assertEqual(output["conflicts"][0]["left"]["value"], "96.2")
        self.assertEqual(output["conflicts"][0]["right"]["value"], "95.2")
        self.assertEqual(output["arithmetic"][0]["computed"], "24.68")
        self.assertEqual(output["arithmetic"][0]["status"], "MATCH")

    def test_distinct_context_and_unit_never_compare(self):
        for key in ["metric", "dataset", "model", "split", "unit", "context"]:
            with self.subTest(key=key):
                data = copy.deepcopy(self.input)
                data["observations"][1][key] = "different"
                self.assertEqual(check_consistency(data)["conflicts"], [])

    def test_rounding_tolerance(self):
        data = copy.deepcopy(self.input)
        data["observations"][0].update(value="95.23", tolerance="0.05")
        self.assertEqual(check_consistency(data)["conflicts"], [])

    def test_relative_percent_is_not_percentage_point_difference(self):
        data = copy.deepcopy(self.input)
        data["calculations"][0]["kind"] = "relative_change_percent"
        result = check_consistency(data)["arithmetic"][0]
        self.assertEqual(result["status"], "ARITHMETIC_MISMATCH")
        self.assertGreater(float(result["computed"]), 34)

    def test_zero_denominator_is_unestablished(self):
        data = copy.deepcopy(self.input)
        data["calculations"][0].update(kind="percentage", operands=["1", "0"])
        self.assertEqual(check_consistency(data)["arithmetic"][0]["status"], "UNDEFINED_ZERO_DENOMINATOR")

    def test_mapping_requires_full_identity(self):
        data = copy.deepcopy(self.input)
        del data["observations"][0]["dataset"]
        with self.assertRaises(ValueError):
            check_consistency(data)

    def test_nonfinite_tolerance_cannot_hide_conflicts(self):
        for value in ("Infinity", "NaN", "-1"):
            with self.subTest(value=value):
                data = copy.deepcopy(self.input)
                data["observations"][0]["tolerance"] = value
                with self.assertRaises(ValueError):
                    check_consistency(data)

    def test_numbers_retain_exact_offsets_and_units(self):
        result = extract_numbers(self.source)
        selected = [n for n in result["numbers"] if n["value"] in {"96.2", "95.2", "24.68"}]
        self.assertGreaterEqual(len(selected), 3)
        for number in selected:
            e = number["evidence"]
            self.assertEqual(self.source["text"][e["start"]:e["end"]], e["text"])
        self.assertTrue(any(n["unit"] == "percentage_points" for n in selected))

    def test_internal_reference_check_does_not_verify_semantics(self):
        result = check_references(self.source)
        self.assertEqual(result["citation_verification"], "NOT_VERIFIED")
        self.assertEqual(result["missing_numeric_references"], [])

    def test_latex_unknown_labels_and_bib_keys(self):
        result = check_references(parse_source(FIXTURES / "paper.tex"))
        self.assertEqual(result["undefined_latex_labels"], ["eq:missing"])
        self.assertEqual(result["undefined_cite_keys"], ["beta"])

    def test_numeric_ranges_and_markdown_links(self):
        source = parse_source(FIXTURES / "synthetic_memory.md")
        # Isolated pattern input: source spans need no file mutation.
        source["text"] = "Text [1, 3–4]. [2](https://example.invalid)\nReferences\n[1] One\n[3] Three\n"
        source["segments"] = [{"start": 0, "end": 58, "section": "Body", "page": None},
                              {"start": 58, "end": len(source["text"]), "section": "References", "page": None}]
        boundary = source["text"].index("References")
        source["segments"][0]["end"] = boundary
        source["segments"][1]["start"] = boundary
        result = check_references(source)
        self.assertEqual(result["numeric_citations"], [1, 3, 4])
        self.assertEqual(result["missing_numeric_references"], [4])


if __name__ == "__main__":
    unittest.main()
