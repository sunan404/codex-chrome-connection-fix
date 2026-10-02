"""Maintain the bundled draft-2020-12 contracts without remote schema dependencies."""
from common import ROOT, write_json

BASE = "https://academic-paper-reviewer.invalid/schemas/"
MODULES = ["methodology", "statistical", "ai_ml", "claim", "writing", "reproducibility", "internal_consistency"]
REPRO_ITEMS = ["dataset", "dataset_version", "preprocessing", "code", "random_seeds", "model",
               "model_version", "prompt", "dependencies", "environment", "hyperparameters", "hardware",
               "evaluation_procedure", "statistical_procedure", "raw_results", "analysis_scripts"]


def obj(properties, required=None):
    return {"type": "object", "properties": properties, "required": list(properties) if required is None else required,
            "additionalProperties": False}


def array(items, minimum=0):
    return {"type": "array", "items": items, "minItems": minimum}


def enum(values):
    return {"type": "string", "enum": values}


S = {"type": "string", "minLength": 1}
IDS = {"type": "array", "items": S, "uniqueItems": True}
HASH = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
INT = {"type": "integer", "minimum": 0}
CONF = enum(["HIGH", "MEDIUM", "LOW"])


def ref(name):
    return {"$ref": f"{BASE}common.json#/$defs/{name}"}


def schema(name, properties):
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": BASE + name, **obj(properties)}


def build():
    statement = obj({"text": S, "information_type": enum(["manuscript_fact", "external_fact", "reviewer_inference", "recommendation"]),
                     "evidence_ids": IDS, "external_source_ids": IDS, "reasoning": {"type": "string"}})
    evidence = obj({"evidence_id": S, "source_id": S, "source_hash": HASH, "start": INT, "end": INT,
                    "text": S, "section": S, "page": {"type": ["integer", "null"], "minimum": 1},
                    "line": {"type": "integer", "minimum": 1}, "location": S})
    entity = obj({"id": S, "text": S, "evidence_ids": {**IDS, "minItems": 1}})
    claim = obj({"claim_id": S, "text": S, "evidence_ids": {**IDS, "minItems": 1},
                 "claim_type": enum(["empirical", "method", "theoretical", "scope"]),
                 "strength": enum(["bounded", "qualified", "universal"]), "scope": S})
    common = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": BASE + "common.json",
              "$defs": {"statement": statement, "evidence": evidence, "entity": entity, "claim": claim}}
    profile = schema("paper_representation.json", {
        "schema_version": {"const": "1.0"},
        "metadata": obj({"title": S, "language": enum(["en", "zh", "mixed", "unknown"]), "field": S,
                         "paper_type": S, "target_venue": {"type": ["string", "null"]}}),
        "status": enum(["needs_semantic_extraction", "extracted"]),
        "sources": array(obj({"source_id": S, "path": S, "text_sha256": HASH, "file_sha256": HASH}), 1),
        "evidence": array(ref("evidence")), "claims": array(ref("claim")),
        "extraction_warnings": array(S),
        **{field: array(ref("entity")) for field in ["research_questions", "contributions", "methods", "datasets",
           "baselines", "metrics", "experiments", "statistical_methods", "results", "limitations", "figures", "tables", "references"]}})
    concern = schema("concern.json", {
        "concern_id": S, "severity": enum(["critical", "major", "moderate", "minor"]),
        "category": enum(MODULES), "title": S, "claim": S, "evidence_ids": {**IDS, "minItems": 1},
        "reasoning": S, "impact": S, "suggested_fix": S, "confidence": CONF,
        "information_type": enum(["manuscript_fact", "reviewer_inference"]),
        "root_cause": S, "affected_scope": S, "claim_ids": IDS, "origin_ids": IDS,
        "priority": {"type": "integer", "minimum": 1, "maximum": 4}})
    external = obj({"source_id": S, "url": S, "identifier": S, "retrieved_at": S,
                    "status": enum(["INSPECTED", "SOURCE_UNAVAILABLE"]), "text": {"type": "string"},
                    "text_sha256": HASH, "retrieval_note": S,
                    "quotes": array(obj({"start": INT, "end": INT, "text": S}))})
    graph = obj({"claim_id": S, "assessment": enum(["SUPPORTED", "PARTIALLY_SUPPORTED", "OVERSTATED", "UNSUPPORTED", "NOT_TESTABLE_FROM_MANUSCRIPT"]),
                 "reasoning": S, "information_type": {"const": "reviewer_inference"},
                 **{key: IDS for key in ["evidence_ids", "experiment_ids", "metric_ids", "result_ids", "statistical_method_ids", "limitation_ids"]}})
    strength = obj({"strength_id": S, "text": S, "evidence_ids": {**IDS, "minItems": 1},
                    "why_it_matters": S, "confidence": CONF,
                    "information_type": enum(["manuscript_fact", "reviewer_inference"])})
    review = schema("review.json", {
        "schema_version": {"const": "1.0"}, "language": enum(["en", "zh"]), "title": S,
        "review_confidence": CONF, "executive_assessment": array(ref("statement"), 1),
        "strengths": array(strength), "concerns": array({"$ref": BASE + "concern.json"}),
        "claim_evidence_audit": array(graph),
        "module_findings": obj({module: array({"$ref": BASE + "concern.json"}) for module in MODULES}),
        "audits": obj({module: array(ref("statement"), 1) for module in MODULES}),
        "reproducibility": array(obj({"item": enum(REPRO_ITEMS), "status": enum(["AVAILABLE", "PARTIAL", "MISSING", "NOT_APPLICABLE"]),
            "evidence_ids": IDS, "searched_source_ids": IDS, "reasoning": S}), len(REPRO_ITEMS)),
        "author_questions": array(ref("statement")),
        "disagreements": array(obj({"disagreement_id": S, "topic": S, "origin_ids": {**IDS, "minItems": 2},
            "positions": array(ref("statement"), 2), "status": enum(["UNRESOLVED", "RESOLVED"]), "reasoning": S})),
        "external_sources": array(external),
        "literature_searches": array(obj({"query": S, "provider": S, "searched_at": S,
            "status": enum(["COMPLETED", "UNAVAILABLE"]), "source_ids": IDS, "note": S})),
        "citation_audits": array(obj({"reference_id": S, "evidence_ids": {**IDS, "minItems": 1}, "external_source_ids": IDS,
            "status": enum(["SUPPORTED", "PARTIALLY_SUPPORTED", "MISREPRESENTED", "NOT_VERIFIED", "SOURCE_UNAVAILABLE"]), "reasoning": S})),
        "venue_rubric": {"anyOf": [{"type": "null"}, obj({"venue": S, "year": {"type": "integer"}, "external_source_ids": {**IDS, "minItems": 1},
            "applied_dimensions": array(S, 1), "reasoning": S})]},
        "review_limits": obj({"external_literature_checked": {"type": "boolean"},
            "citation_verification": enum(["NOT_VERIFIED", "PARTIAL", "COMPLETED"]), "supplemental_material_read": {"type": "boolean"},
            "coverage": array(obj({"source_id": S, "status": enum(["ALL_EXTRACTED_TEXT", "PARTIAL"]), "note": S}), 1),
            "unconfirmed_information": array(S), "limitations": array(ref("statement"), 1)})})
    for name, value in [("common.json", common), ("paper_representation.json", profile), ("concern.json", concern), ("review.json", review)]:
        write_json(ROOT / "schemas" / name, value)


if __name__ == "__main__":
    build()
