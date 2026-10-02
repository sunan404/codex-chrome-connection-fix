"""Validate bundled paths and build a Codex-compatible plugin ZIP, offline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {"__pycache__", ".git", ".venv", "dist", "runs"}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def validate_bundle(root=ROOT):
    root = Path(root).resolve()
    portable = load(root / "plugin.json")
    legacy = load(root / ".codex-plugin/plugin.json")
    if portable.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        raise ValueError("Portable Agent Plugins schema declaration required")
    for key in ("name", "version", "description", "author", "homepage", "repository"):
        if portable.get(key) != legacy.get(key):
            raise ValueError(f"Portable and Codex compatibility manifests disagree on {key}")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", portable["name"]):
        raise ValueError("Plugin name must be kebab-case")
    if not re.fullmatch(r"\d+\.\d+\.\d+", portable["version"]):
        raise ValueError("Release version must be a semantic version")
    settings = portable["extensions"]["com.openai"]
    if settings["interface"] != legacy["interface"]:
        raise ValueError("Portable and compatibility presentation metadata differ")
    if legacy.get("skills") != "./skills/":
        raise ValueError("Canonical skill directory must be ./skills/")
    if any(key in legacy or key in settings for key in ("mcpServers", "apps", "hooks")):
        raise ValueError("This skills-only plugin must not declare unimplemented servers/apps/hooks")
    for key in ("displayName", "shortDescription", "longDescription", "developerName", "category", "defaultPrompt"):
        if not settings["interface"].get(key):
            raise ValueError(f"Missing install-surface field: {key}")
    skills = list((root / "skills").glob("*/SKILL.md"))
    if len(skills) != 1:
        raise ValueError("This version must package exactly one complete review skill")
    skill = skills[0].parent
    for item in ("scripts/prepare_paper.py", "scripts/validate_review.py", "scripts/render_review.py",
                 "schemas/review.json", "references/reviewer-modules.md", "requirements-pdf.txt"):
        if not (skill / item).is_file():
            raise ValueError(f"Skill dependency missing: {item}")
    for markdown in [root / "README.md", skill / "SKILL.md", skill / "README.md", *skill.glob("references/*.md")]:
        for target in re.findall(r"\]\(([^)]+)\)", markdown.read_text(encoding="utf-8")):
            if "://" not in target and not target.startswith("#"):
                resolved = (markdown.parent / target.split("#")[0]).resolve()
                if not resolved.is_relative_to(root) or not resolved.exists():
                    raise ValueError(f"Broken or escaping reference in {markdown.name}: {target}")
    return portable


def validate_marketplace(path, root):
    marketplace = load(path)
    root = Path(root).resolve()
    entries = [p for p in marketplace["plugins"] if p["name"] == "academic-paper-reviewer"]
    if len(entries) != 1:
        raise ValueError("Marketplace must contain exactly one reviewer plugin entry")
    entry = entries[0]
    source = entry["source"]
    if source.get("source") != "local" or not source["path"].startswith("./"):
        raise ValueError("Repository marketplace source must be relative and local")
    target = (root / source["path"]).resolve()
    if not target.is_relative_to(root):
        raise ValueError("Marketplace plugin source escapes its root")
    if entry["policy"]["installation"] != "AVAILABLE" or entry["policy"]["authentication"] != "ON_INSTALL":
        raise ValueError("Marketplace policies do not match this package")
    validate_bundle(target)
    return marketplace


def package(out, root=ROOT):
    root = Path(root).resolve()
    metadata = validate_bundle(root)
    target = Path(out).resolve()
    if target.suffix.lower() != ".zip":
        raise ValueError("Output must be .zip")
    target.parent.mkdir(parents=True, exist_ok=True)
    files = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in EXCLUDED for part in relative.parts) or path.suffix == ".pyc":
            continue
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise ValueError(f"Do not ship external/symlinked assets: {relative}")
        if path.is_file() and path.resolve() != target:
            files.append(path)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, Path(metadata["name"]) / path.relative_to(root))
    return len(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out")
    parser.add_argument("--marketplace")
    parser.add_argument("--marketplace-root")
    args = parser.parse_args()
    try:
        metadata = validate_bundle()
        if args.marketplace:
            if not args.marketplace_root:
                parser.error("--marketplace-root is required with --marketplace")
            validate_marketplace(args.marketplace, args.marketplace_root)
        if args.out:
            count = package(args.out)
            print(f'Packaged {metadata["name"]} {metadata["version"]}: {count} files → {args.out}')
        else:
            print(f'PASS: plugin manifests, paths and skill resources ({metadata["version"]}).')
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f"Plugin validation failed: {exc}\n")


if __name__ == "__main__":
    main()
