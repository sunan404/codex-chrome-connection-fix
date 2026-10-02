import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from support import ROOT, FIXTURES
from build_example import build
from common import read_json, write_json
from prepare_paper import parse_source, prepare
from validate_review import validate
from render_review import render


class EndToEndTests(unittest.TestCase):
    def test_complete_cli_flow_and_render(self):
        source, profile, review, observations = build()
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            def run(script, *args):
                result = subprocess.run([sys.executable, str(ROOT / "scripts" / script), *map(str, args)],
                                        capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                return result
            run("prepare_paper.py", FIXTURES / "synthetic_memory.md", "--out", out)
            parsed = read_json(out / "source.json")
            self.assertEqual(parsed["text_sha256"], source["text_sha256"])
            write_json(out / "profile.json", profile)
            write_json(out / "review.json", review)
            write_json(out / "observations.json", observations)
            run("check_consistency.py", out / "observations.json", "--out", out / "consistency.json")
            common = ["--profile", out / "profile.json", "--review", out / "review.json", "--sources", out / "source.json"]
            run("validate_review.py", *common)
            run("render_review.py", *common, "--out", out / "review.md")
            text = (out / "review.md").read_text(encoding="utf-8")
            self.assertIn("Claim–Evidence Audit", text)
            self.assertIn("24.68", text)
            self.assertIn("OVERSTATED", text)
            self.assertEqual(len(read_json(out / "consistency.json")["conflicts"]), 1)

    def test_supplement_added_and_missing_search_coverage_invalidated(self):
        source, profile, review, _ = build()
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            supplement = out / "supplement.md"
            supplement.write_text("# Supplement\nThe random seeds are 4 and 9.\n", encoding="utf-8")
            write_json(out / "profile.json", profile)
            result = subprocess.run([sys.executable, str(ROOT / "scripts/add_source.py"), str(supplement),
                "--id", "supplement", "--profile", str(out / "profile.json"), "--out", str(out / "supplement.json")],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            new_profile = read_json(out / "profile.json")
            sources = {"manuscript": source, "supplement": read_json(out / "supplement.json")}
            self.assertEqual(validate(new_profile, sources), [])
            errors = validate(new_profile, sources, review)
            self.assertTrue(any("must search every" in e for e in errors))
            self.assertTrue(any("coverage must identify every" in e for e in errors))

    def test_chinese_render_keeps_original_evidence(self):
        source, profile, review, _ = build()
        review["language"] = "zh"
        review["title"] = "合成检索论文审查示例"
        review["executive_assessment"] = [{
            "text": "论文在十二个独立生成的合成场景中研究使用反馈对记忆检索的影响。反馈组与对照组仅改变反馈项，提供了范围明确的机制实验；预先指定的负对照也具有方法价值。主要不确定性在于查询共享场景状态，而区间按查询独立重采样，尚不能确认场景层面的精度。此外，摘要与表格准确率不一致，真实世界助手结论超过证据范围。作者已经披露外部有效性和重采样局限，应保留这一透明性优点。当前审查信心为中等，原始结果与可执行代码缺失限制了独立复现。",
            "information_type": "reviewer_inference", "evidence_ids": ["E4", "E6", "E11", "E18", "E21", "E22", "E23", "E24"],
            "external_source_ids": [], "reasoning": "结论范围和统计单位依据原文及实验对照核查。"}]
        text = render(profile, review, {"manuscript": source})
        self.assertIn("## 主张—证据审计", text)
        self.assertIn("审稿人推断", text)
        self.assertIn("Results cannot be generalized", text)

    def test_prepare_does_not_overwrite_manuscript(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "source.txt"
            path.write_text("Original manuscript", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must not overwrite"):
                prepare(path, temp)
            self.assertEqual(path.read_text(encoding="utf-8"), "Original manuscript")

    def test_pdf_text_and_unreadable_page_warning(self):
        try:
            import pymupdf
        except ImportError:
            self.skipTest("Optional PDF dependency not installed")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "paper.pdf"
            doc = pymupdf.open()
            page = doc.new_page()
            page.insert_text((72, 72), "Abstract\nWe show a bounded effect of 95.2%.")
            doc.new_page()
            doc.save(path)
            doc.close()
            source = parse_source(path)
            self.assertIn("95.2%", source["text"])
            self.assertEqual(source["segments"][0]["page"], 1)
            self.assertTrue(any("Page 2" in w for w in source["warnings"]))

    def test_scanned_pdf_fails_explicitly(self):
        try:
            import pymupdf
        except ImportError:
            self.skipTest("Optional PDF dependency not installed")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "blank.pdf"
            doc = pymupdf.open()
            doc.new_page()
            doc.save(path)
            doc.close()
            with self.assertRaisesRegex(ValueError, "no extractable text"):
                parse_source(path)


if __name__ == "__main__":
    unittest.main()
