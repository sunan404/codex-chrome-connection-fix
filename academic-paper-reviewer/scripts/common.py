"""Local JSON I/O and exact provenance helpers. Never execute manuscript text."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def evidence_at(source, start, end, evidence_id):
    if not 0 <= start < end <= len(source["text"]):
        raise ValueError("Evidence span must be nonempty and in source bounds")
    segment = next((s for s in source["segments"] if s["start"] <= start < s["end"]), None)
    if segment is None or end > segment["end"]:
        raise ValueError("Evidence must stay inside one source segment")
    line = source["text"].count("\n", 0, start) + 1
    return {
        "evidence_id": evidence_id, "source_id": source["source_id"],
        "source_hash": source["text_sha256"], "start": start, "end": end,
        "text": source["text"][start:end], "section": segment["section"],
        "page": segment["page"], "line": line,
        "location": f'{source["path"]}:line {line}' + (f', page {segment["page"]}' if segment["page"] else ""),
    }


def evidence_for(source, quote, evidence_id):
    """Convenience for unique quotes; ambiguous repeats require explicit spans."""
    start = source["text"].find(quote)
    if start < 0 or source["text"].find(quote, start + 1) >= 0:
        raise ValueError("Quote must occur exactly once; use explicit offsets otherwise")
    return evidence_at(source, start, start + len(quote), evidence_id)


def load_sources(paths):
    result = {}
    for path in paths:
        source = read_json(path)
        if source["source_id"] in result:
            raise ValueError("Duplicate source_id")
        if digest(source["text"]) != source["text_sha256"]:
            raise ValueError("Source text hash mismatch")
        result[source["source_id"]] = source
    return result
