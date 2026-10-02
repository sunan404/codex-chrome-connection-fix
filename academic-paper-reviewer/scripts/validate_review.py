"""Fail closed on schema, source provenance and graph integrity; not semantic truth."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from common import ROOT, digest, evidence_at, load_sources, read_json
from build_schemas import MODULES, REPRO_ITEMS

PROHIBITED = re.compile(r"(?:paper\s*(?:quality\s*)?score|acceptance\s*probability|publication\s*probability|"
                        r"论文评分|录用概率|发表概率)\s*[:：=]?\s*\d", re.I)


def schema_errors(value, name):
    try:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
    except ImportError as exc:
        raise RuntimeError("Install requirements.txt for complete JSON Schema validation") from exc
    registry = Registry()
    schemas = {}
    for path in sorted((ROOT / "schemas").glob("*.json")):
        schema = read_json(path)
        Draft202012Validator.check_schema(schema)
        schemas[path.name] = schema
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return [f'{"/".join(str(p) for p in e.absolute_path)}: {e.message}'
            for e in Draft202012Validator(schemas[name], registry=registry).iter_errors(value)]


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def validate(profile, sources, review=None):
    errors = schema_errors(profile, "paper_representation.json")
    if review is not None:
        errors.extend(schema_errors(review, "review.json"))
    if errors:
        return errors
    descriptors = {s["source_id"]: s for s in profile["sources"]}
    if len(descriptors) != len(profile["sources"]):
        errors.append("Duplicate profile source IDs")
    if set(descriptors) != set(sources):
        errors.append("Profile source set must equal supplied source JSON set")
    for source_id, source in sources.items():
        descriptor = descriptors.get(source_id, {})
        for key in ("text_sha256", "file_sha256", "path"):
            if descriptor.get(key) != source.get(key):
                errors.append(f"Source {source_id}: descriptor {key} mismatch")
        if digest(source["text"]) != source["text_sha256"]:
            errors.append(f"Source {source_id}: text hash mismatch")
        if source.get("trust") != "untrusted_research_content":
            errors.append(f"Source {source_id}: untrusted classification required")
        cursor = 0
        for seg in source["segments"]:
            if seg["start"] != cursor or not cursor < seg["end"] <= len(source["text"]):
                errors.append(f"Source {source_id}: invalid segment coverage")
                break
            cursor = seg["end"]
        if cursor != len(source["text"]):
            errors.append(f"Source {source_id}: segment coverage incomplete")
        original = Path(source["path"])
        if original.is_file():
            import hashlib
            if hashlib.sha256(original.read_bytes()).hexdigest() != source["file_sha256"]:
                errors.append(f"Source {source_id}: original file changed since extraction")
    evidence = {}
    for item in profile["evidence"]:
        eid = item["evidence_id"]
        if eid in evidence:
            errors.append(f"Duplicate evidence ID: {eid}")
        evidence[eid] = item
        source = sources.get(item["source_id"])
        if source is None:
            errors.append(f"Evidence {eid}: unknown source")
            continue
        try:
            expected = evidence_at(source, item["start"], item["end"], eid)
        except ValueError as exc:
            errors.append(f"Evidence {eid}: {exc}")
            continue
        if item != expected:
            errors.append(f"Evidence {eid}: exact quote/hash/location mismatch")
    all_ids = {}
    for field in ("claims", "research_questions", "contributions", "methods", "datasets", "baselines", "metrics",
                  "experiments", "statistical_methods", "results", "limitations", "figures", "tables", "references"):
        for item in profile[field]:
            iid = item.get("id", item.get("claim_id"))
            if iid in all_ids:
                errors.append(f"Duplicate entity/claim ID: {iid}")
            all_ids[iid] = field
    for item in walk(profile):
        for eid in item.get("evidence_ids", []):
            if eid not in evidence:
                errors.append(f"Unknown profile evidence ID: {eid}")
    if review is None:
        return errors
    if profile["status"] != "extracted":
        errors.append("Final review requires a semantically extracted profile")
    executive_text = " ".join(s["text"] for s in review["executive_assessment"])
    if review["language"] == "zh":
        length = len(re.findall(r"[\u3400-\u9fff]", executive_text))
    else:
        length = len(re.findall(r"\b[\w]+(?:[-/][\w]+)*\b", executive_text))
    if not 150 <= length <= 300:
        errors.append("Executive assessment must contain 150–300 English words or Chinese characters (excluding evidence quotes)")
    claim_ids = {c["claim_id"] for c in profile["claims"]}
    if not claim_ids:
        errors.append("Final review requires at least one confirmed core claim")
    graph_ids = [a["claim_id"] for a in review["claim_evidence_audit"]]
    if set(graph_ids) != claim_ids or len(graph_ids) != len(set(graph_ids)):
        errors.append("Every profile claim must have exactly one assessment")
    graph_fields = {"experiment_ids": "experiments", "metric_ids": "metrics", "result_ids": "results",
                    "statistical_method_ids": "statistical_methods", "limitation_ids": "limitations"}
    for edge in review["claim_evidence_audit"]:
        for key, expected_field in graph_fields.items():
            for iid in edge[key]:
                if all_ids.get(iid) != expected_field:
                    errors.append(f"Claim {edge['claim_id']}: invalid {key} link {iid}")
        if edge["assessment"] in {"SUPPORTED", "PARTIALLY_SUPPORTED", "OVERSTATED"} and not edge["evidence_ids"]:
            errors.append("Evidence required for supported/partially-supported/overstated claim")
        if edge["assessment"] == "SUPPORTED":
            claim = next((c for c in profile["claims"] if c["claim_id"] == edge["claim_id"]), None)
            if claim and claim["claim_type"] == "empirical" and not (edge["experiment_ids"] and edge["result_ids"]):
                errors.append("SUPPORTED empirical claims require experiment and result links")
    external = {}
    for source in review["external_sources"]:
        sid = source["source_id"]
        if sid in external:
            errors.append(f"Duplicate external source ID: {sid}")
        external[sid] = source
        if digest(source["text"]) != source["text_sha256"]:
            errors.append(f"External source {sid}: text hash mismatch")
        if source["status"] == "INSPECTED" and not source["quotes"]:
            errors.append(f"External source {sid}: inspected quotes required")
        for quote in source["quotes"]:
            if not (0 <= quote["start"] < quote["end"] <= len(source["text"])) or source["text"][quote["start"]:quote["end"]] != quote["text"]:
                errors.append(f"External source {sid}: quote mismatch")
    for item in walk(review):
        for eid in item.get("evidence_ids", []):
            if eid not in evidence:
                errors.append(f"Unknown review evidence ID: {eid}")
        for sid in item.get("external_source_ids", []):
            if sid not in external:
                errors.append(f"Unknown external source ID: {sid}")
        if "information_type" in item and "text" in item:
            kind = item["information_type"]
            if kind in {"manuscript_fact", "reviewer_inference"} and not item.get("evidence_ids"):
                errors.append(f"{kind} statement requires manuscript evidence: {item['text'][:60]}")
            if kind == "external_fact" and (not item.get("external_source_ids") or any(
                    external.get(s, {}).get("status") != "INSPECTED" for s in item["external_source_ids"])):
                errors.append("External fact requires inspected external sources")
            if kind in {"reviewer_inference", "recommendation"} and not (item.get("reasoning", "").strip() or item.get("why_it_matters", "").strip()):
                errors.append(f"{kind} requires reasoning")
        # Scan reviewer prose only; untrusted quoted source may legitimately contain score demands.
        for key in ("text", "claim", "reasoning", "impact", "suggested_fix", "why_it_matters"):
            if key in item and isinstance(item[key], str) and item not in review["external_sources"] and "start" not in item:
                if PROHIBITED.search(item[key]):
                    errors.append("Prohibited numerical quality/acceptance prediction in reviewer output")
    origins = {}
    for module in MODULES:
        for concern in review["module_findings"][module]:
            cid = concern["concern_id"]
            if cid in origins:
                errors.append(f"Duplicate module concern ID: {cid}")
            origins[cid] = concern
            if concern["category"] != module:
                errors.append("Module finding category must match its module")
            if concern["origin_ids"]:
                errors.append("Raw module findings must not claim other origins")
    roots, final_ids, used_origins = set(), set(), set()
    for concern in review["concerns"]:
        cid = concern["concern_id"]
        if cid in final_ids:
            errors.append(f"Duplicate final concern ID: {cid}")
        final_ids.add(cid)
        key = (concern["root_cause"].casefold().strip(), concern["affected_scope"].casefold().strip())
        if key in roots:
            errors.append("Duplicate final root cause and scope; merge concerns")
        roots.add(key)
        if not concern["origin_ids"]:
            errors.append("Final concern must preserve module origin IDs")
        for origin in concern["origin_ids"]:
            if origin not in origins:
                errors.append(f"Unknown module origin: {origin}")
            if origin in used_origins:
                errors.append("An origin cannot be duplicated across final concerns")
            used_origins.add(origin)
        if concern["severity"] == "critical" and concern["confidence"] != "HIGH":
            errors.append("Critical concern requires HIGH evidence confidence")
    for concern in list(origins.values()) + review["concerns"]:
        if not set(concern["claim_ids"]) <= claim_ids:
            errors.append("Concern references unknown claim")
    dispute_origins = set()
    for dispute in review["disagreements"]:
        for oid in dispute["origin_ids"]:
            if oid not in origins:
                errors.append("Disagreement has unknown origin")
            dispute_origins.add(oid)
    if set(origins) - used_origins - dispute_origins:
        errors.append("Raw concerns must be preserved in final concerns or disagreements")
    repro = review["reproducibility"]
    if {r["item"] for r in repro} != set(REPRO_ITEMS) or len(repro) != len(REPRO_ITEMS):
        errors.append("Reproducibility must cover each required item exactly once")
    for row in repro:
        if not set(row["searched_source_ids"]) <= set(sources):
            errors.append("Reproducibility search references unknown source")
        if row["status"] in {"AVAILABLE", "PARTIAL"} and not row["evidence_ids"]:
            errors.append("Reported reproducibility information requires evidence")
        if row["status"] == "MISSING" and set(row["searched_source_ids"]) != set(sources):
            errors.append("Missing-information assertion must search every supplied source")
    for question in review["author_questions"]:
        if question["information_type"] != "recommendation":
            errors.append("Author questions must be recommendations")
    limits = review["review_limits"]
    covered = [c["source_id"] for c in limits["coverage"]]
    if set(covered) != set(sources) or len(covered) != len(set(covered)):
        errors.append("Review coverage must identify every supplied source exactly once")
    if limits["supplemental_material_read"] and len(sources) < 2:
        errors.append("Supplement read declared without a supplied supplement source")
    if limits["external_literature_checked"] and not any(s["status"] == "COMPLETED" for s in review["literature_searches"]):
        errors.append("External literature check requires an actual completed search record")
    for search in review["literature_searches"]:
        if not set(search["source_ids"]) <= set(external):
            errors.append("Literature search references unknown external sources")
    for audit in review["citation_audits"]:
        if all_ids.get(audit["reference_id"]) != "references":
            errors.append("Citation audit must link a manuscript reference entity")
        if audit["status"] in {"SUPPORTED", "PARTIALLY_SUPPORTED", "MISREPRESENTED"}:
            if not audit["external_source_ids"] or any(external.get(s, {}).get("status") != "INSPECTED" for s in audit["external_source_ids"]):
                errors.append("Verified citation status requires inspected external evidence")
        if audit["status"] == "SOURCE_UNAVAILABLE" and not any(
                external.get(s, {}).get("status") == "SOURCE_UNAVAILABLE" for s in audit["external_source_ids"]):
            errors.append("SOURCE_UNAVAILABLE requires a recorded failed retrieval")
    completed = [a for a in review["citation_audits"] if a["status"] in {"SUPPORTED", "PARTIALLY_SUPPORTED", "MISREPRESENTED"}]
    if limits["citation_verification"] == "NOT_VERIFIED" and completed:
        errors.append("Citation verification declaration contradicts verified audits")
    if limits["citation_verification"] == "PARTIAL" and not completed:
        errors.append("Partial citation verification requires at least one inspected audit")
    if limits["citation_verification"] == "COMPLETED":
        references = {r["id"] for r in profile["references"]}
        if not references or {a["reference_id"] for a in completed} != references:
            errors.append("Completed citation verification requires all manuscript references inspected")
    if review["venue_rubric"] is not None and any(
            external.get(s, {}).get("status") != "INSPECTED" for s in review["venue_rubric"]["external_source_ids"]):
        errors.append("Venue rubric requires inspected official source evidence")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--review")
    parser.add_argument("--sources", nargs="+", required=True)
    args = parser.parse_args()
    try:
        errors = validate(read_json(args.profile), load_sources(args.sources), read_json(args.review) if args.review else None)
    except (ValueError, KeyError, OSError, RuntimeError) as exc:
        parser.exit(2, f"Validation failed: {exc}\n")
    if errors:
        parser.exit(1, "Validation failed:\n" + "\n".join(f"- {e}" for e in errors) + "\n")
    print("PASS: schema, exact provenance and graph invariants. Semantic support still requires review.")


if __name__ == "__main__":
    main()
