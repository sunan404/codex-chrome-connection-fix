"""Extract numeric tokens with units and original offsets; no semantic comparisons."""
import argparse
import re
from decimal import Decimal
from common import evidence_at, read_json, write_json

NUMBER = re.compile(r"(?<![\w.])[-+−]?(?:(?:\d{1,3}(?:,\d{3})+)|\d+)(?:\.\d+)?"
                    r"(?:[eE][-+]?\d+)?\s*(?:percentage points|百分点|\\?%|％|pp\b)?")


def normalize_number(token):
    raw = token.strip().replace("−", "-")
    unit = "number"
    if re.search(r"percentage points|百分点|pp$", raw):
        unit = "percentage_points"
    elif "%" in raw or "％" in raw:
        unit = "percent"
    raw = re.sub(r"percentage points|百分点|pp$|\\?%|％", "", raw).strip().replace(",", "")
    return str(Decimal(raw)), unit


def extract_numbers(source):
    result = []
    for seg in source["segments"]:
        text = source["text"][seg["start"]:seg["end"]]
        for m in NUMBER.finditer(text):
            token = m.group().rstrip()
            start = seg["start"] + m.start()
            value, unit = normalize_number(token)
            result.append({"number_id": f'N{len(result)+1}', "value": value, "unit": unit,
                           "evidence": evidence_at(source, start, start + len(token), f'NE{len(result)+1}'),
                           "context": text.strip(), "status": "UNMAPPED"})
    return {"numbers": result, "note": "Semantic identity, table layout and numeric role need reviewer confirmation."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    write_json(args.out, extract_numbers(read_json(args.source)))


if __name__ == "__main__":
    main()
