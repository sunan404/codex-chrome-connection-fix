"""Check simple numeric citations and LaTeX labels; never verify citation meaning."""
import argparse
import re
from common import read_json, write_json


def expand_numbers(value):
    numbers = set()
    for part in re.split(r"[,，]", value):
        bounds = re.split(r"[-–—]", part.strip())
        if len(bounds) == 1:
            numbers.add(int(bounds[0]))
        elif len(bounds) == 2:
            low, high = map(int, bounds)
            if high < low or high - low > 500:
                raise ValueError("Unordered or excessive citation range")
            numbers.update(range(low, high + 1))
    return numbers


def check_references(source):
    definitions, citations, latex_labels, latex_refs, bib_keys, cite_keys = set(), set(), set(), set(), set(), set()
    warnings = []
    definition_counts = {}
    for seg in source["segments"]:
        text = source["text"][seg["start"]:seg["end"]]
        in_references = bool(re.search(r"references|bibliography|参考文献", seg["section"], re.I))
        numeric_definitions = re.finditer(r"(?m)^\s*\[(\d+)\]\s+", text) if in_references else []
        for numeric_definition in numeric_definitions:
            number = int(numeric_definition.group(1))
            definitions.add(number)
            definition_counts[number] = definition_counts.get(number, 0) + 1
        if not in_references:
            for m in re.finditer(r"\[([\d\s,，–—-]+)\](?!\s*\()", text):
                try:
                    citations.update(expand_numbers(m.group(1)))
                except ValueError:
                    warnings.append(f"Unparsed numeric bracket on line containing: {text.strip()}")
        latex_labels.update(re.findall(r"\\label\{([^}]+)\}", text))
        latex_refs.update(re.findall(r"\\(?:ref|eqref|autoref)\{([^}]+)\}", text))
        bib_keys.update(re.findall(r"\\bibitem(?:\[[^]]*\])?\{([^}]+)\}", text))
        for block in re.findall(r"\\cite\w*\*?(?:\[[^]]*\])*\{([^}]+)\}", text):
            cite_keys.update(k.strip() for k in block.split(","))
    object_definitions = {"table": set(), "figure": set(), "equation": set()}
    object_uses = {kind: set() for kind in object_definitions}
    names = {"table": "Table|表", "figure": "Figure|Fig\\.|图", "equation": "Equation|Eq\\.|公式"}
    for line in source["text"].splitlines():
        for kind, pattern in names.items():
            for m in re.finditer(rf"(?:{pattern})\s*(\d+)", line, re.I):
                object_uses[kind].add(int(m.group(1)))
            caption = re.match(rf"\s*(?:{pattern})\s*(\d+)\s*[:：.]", line, re.I)
            if caption:
                object_definitions[kind].add(int(caption.group(1)))
    return {"numeric_citations": sorted(citations), "numeric_definitions": sorted(definitions),
            "missing_numeric_references": sorted(citations - definitions) if definitions else [],
            "duplicate_numeric_definitions": sorted(k for k, count in definition_counts.items() if count > 1),
            "numeric_status": "CHECKED_SIMPLE_NUMBERING" if definitions else "NOT_ESTABLISHED",
            "undefined_latex_labels": sorted(latex_refs - latex_labels),
            "undefined_cite_keys": sorted(cite_keys - bib_keys) if bib_keys else [],
            "latex_citation_status": "CHECKED_INLINE_BIBITEM" if bib_keys else "NOT_ESTABLISHED",
            "object_reference_candidates": {k: sorted(object_uses[k] - object_definitions[k]) for k in names},
            "citation_verification": "NOT_VERIFIED", "warnings": warnings,
            "scope": "Simple patterns only. Numeric brackets may be intervals/arrays; captions may be missed. Confirm candidates manually. External .bib and includes are not followed."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    write_json(args.out, check_references(read_json(args.source)))


if __name__ == "__main__":
    main()
