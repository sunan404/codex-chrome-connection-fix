import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_plugin", ROOT / "scripts/build_plugin.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PluginPackageTests(unittest.TestCase):
    def test_bundle_and_repository_marketplace(self):
        self.assertEqual(builder.validate_bundle()["version"], "0.2.0")
        if (ROOT.parent / ".agents/plugins/marketplace.json").exists():
            self.assertEqual(builder.validate_marketplace(ROOT.parent / ".agents/plugins/marketplace.json", ROOT.parent)["name"], "sunzus")

    def test_archive_contains_complete_skill_without_cache_or_previous_archives(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "plugin.zip"
            count = builder.package(output)
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                self.assertEqual(count, len(names))
                self.assertIsNone(archive.testzip())
                for required in ("plugin.json", ".codex-plugin/plugin.json", "skills/academic-paper-reviewer/SKILL.md",
                                 "skills/academic-paper-reviewer/scripts/validate_review.py", "skills/academic-paper-reviewer/schemas/review.json"):
                    self.assertIn("academic-paper-reviewer/" + required, names)
                self.assertFalse(any("__pycache__" in n or "/dist/" in n or n.endswith(".pyc") for n in names))

    def test_presentations_cannot_drift_between_manifests(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plugin"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns("__pycache__", "dist"))
            path = root / ".codex-plugin/plugin.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            data["interface"]["displayName"] = "Different product"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "presentation"):
                builder.validate_bundle(root)

    def test_marketplace_cannot_escape_its_root(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "marketplace.json"
            path.write_text(json.dumps({"plugins": [{"name": "academic-paper-reviewer", "source": {"source": "local", "path": "./../outside"},
                 "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}}]}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "escapes"):
                builder.validate_marketplace(path, root)


if __name__ == "__main__":
    unittest.main()
