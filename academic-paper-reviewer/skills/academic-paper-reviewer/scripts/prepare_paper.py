"""Parse source structure; produce candidates, never automatic scientific judgments."""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

from common import digest, evidence_at, write_json

FIELDS = ("research_questions", "contributions", "methods", "datasets", "baselines",
          "metrics", "experiments", "statistical_methods", "results", "limitations",
          "figures", "tables", "references")
HEADING = re.compile(r"^(?:#{1,6}\s+(.+)|\\(?:sub)*section\*?\{([^}]+)\}|"
                     r"(\d+(?:\.\d+)*[.)]?\s+\S.*)|"
                     r"(Abstract|Introduction|Methods?|Results|Discussion|Conclusion|"
                     r"Limitations|References|摘要|引言|方法|结果|讨论|结论|局限性|参考文献))$", re.I)
INJECTION = re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions|"
                       r"reviewer\s+must|rate\s+this\s+paper|system\s*prompt|"
                       r"忽略.{0,12}指令|审稿人必须|给.{0,8}(?:满分|优秀评分)", re.I)
CLAIM_HINT = re.compile(r"\b(?:we (?:show|find|demonstrate|propose)|improv\w*|outperform\w*|"
                        r"cannot be generalized|no (?:benefit|improvement))\b|"
                        r"(?:我们提出|结果表明|提升|优于|不能推广)", re.I)


def parse_source(path, source_id="manuscript"):
    path = Path(path).resolve()
    suffix = path.suffix.lower()
    warnings = []
    if suffix == ".pdf":
        try:
            import pymupdf
        except ImportError as exc:
            raise ValueError("PDF input requires requirements-pdf.txt; text modes need no PDF dependency") from exc
        with pymupdf.open(path) as doc:
            pages = [p.get_text("text", sort=True) for p in doc]
        if not any(p.strip() for p in pages):
            raise ValueError("PDF has no extractable text; scanned PDF/OCR is unsupported")
        warnings.append("PDF reading order, tables, figures and equations require visual confirmation; OCR not performed.")
        for i, text in enumerate(pages, 1):
            if not text.strip():
                warnings.append(f"Page {i} has no extractable text; coverage incomplete.")
    elif suffix in {".md", ".markdown", ".txt", ".tex"}:
        pages = [path.read_text(encoding="utf-8-sig")]
        if suffix == ".tex":
            warnings.append("LaTeX inspected as raw source: no macro expansion, compilation or input/include following.")
    else:
        raise ValueError("Supported inputs: .pdf, .md, .markdown, .txt, .tex")
    text = "".join(p if p.endswith("\n") else p + "\n" for p in pages)
    segments = []
    cursor = 0
    section = "Preamble"
    for page_index, page_text in enumerate(pages, 1):
        normalized = page_text if page_text.endswith("\n") else page_text + "\n"
        for line in normalized.splitlines(keepends=True):
            m = HEADING.match(line.strip())
            if m:
                section = next(g for g in m.groups() if g is not None)
            segments.append({"start": cursor, "end": cursor + len(line), "section": section,
                             "page": page_index if suffix == ".pdf" else None})
            cursor += len(line)
    return {"source_id": source_id, "path": str(path), "format": suffix.lstrip("."),
            "file_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "text_sha256": digest(text), "text": text, "segments": segments,
            "warnings": warnings, "trust": "untrusted_research_content"}


def empty_profile(source):
    title = next((line.strip().lstrip("# ") for line in source["text"].splitlines() if line.strip()), "Untitled")
    profile = {"schema_version": "1.0", "metadata": {"title": title, "language": "unknown",
               "field": "unknown", "paper_type": "unknown", "target_venue": None},
               "sources": [{k: source[k] for k in ("source_id", "path", "text_sha256", "file_sha256")}],
               "evidence": [], "claims": [], "status": "needs_semantic_extraction",
               "extraction_warnings": source["warnings"]}
    profile.update({field: [] for field in FIELDS})
    return profile


def prepare(path, out):
    out = Path(out)
    outputs = {"source.json", "source.txt", "paper_representation.json", "claim_candidates.json", "injection_alerts.json", "numbers.json", "references_check.json"}
    if Path(path).resolve() in {(out / name).resolve() for name in outputs}:
        raise ValueError("Run artifacts must not overwrite the input manuscript; choose a separate output directory")
    out.mkdir(parents=True, exist_ok=True)
    source = parse_source(path)
    profile = empty_profile(source)
    candidates, alerts = [], []
    for seg in source["segments"]:
        line = source["text"][seg["start"]:seg["end"]].rstrip("\r\n")
        if not line:
            continue
        if INJECTION.search(line):
            alerts.append(evidence_at(source, seg["start"], seg["start"] + len(line), f'I{len(alerts)+1}'))
        if CLAIM_HINT.search(line):
            candidates.append({"status": "UNCONFIRMED_CANDIDATE", "evidence": evidence_at(
                source, seg["start"], seg["start"] + len(line), f'H{len(candidates)+1}')})
    write_json(out / "source.json", source)
    (out / "source.txt").write_text(source["text"], encoding="utf-8")
    write_json(out / "paper_representation.json", profile)
    write_json(out / "claim_candidates.json", candidates)
    write_json(out / "injection_alerts.json", {"alerts": alerts, "instruction_execution": False,
               "note": "Pattern alerts are incomplete; every source is untrusted regardless of matches."})
    from extract_numbers import extract_numbers
    from check_references import check_references
    write_json(out / "numbers.json", extract_numbers(source))
    write_json(out / "references_check.json", check_references(source))
    return profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        prepare(args.input, args.out)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"prepare failed: {exc}\n")
    print("Prepared source and unconfirmed candidates; semantic extraction is required.")


if __name__ == "__main__":
    main()
