"""Render a validated review to bilingual Markdown with visible information types."""
import argparse
from pathlib import Path
from common import load_sources, read_json
from validate_review import validate

LABELS = {"en": {"manuscript_fact": "Manuscript Fact", "external_fact": "External Fact",
                   "reviewer_inference": "Reviewer Inference", "recommendation": "Recommendation"},
          "zh": {"manuscript_fact": "论文事实", "external_fact": "外部事实",
                   "reviewer_inference": "审稿人推断", "recommendation": "建议"}}


def safe(text):
    # Quotes are data: no embedded HTML, active links/images, or formatting directives.
    result = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    for char in ("\\", "`", "*", "_", "[", "]", "|", "#"):
        result = result.replace(char, "\\" + char)
    return result.replace("\r", "").replace("\n", " ")


def render(profile, review, sources):
    errors = validate(profile, sources, review)
    if errors:
        raise ValueError("Cannot render invalid review:\n" + "\n".join(errors))
    lang = review["language"]
    zh = lang == "zh"
    labels = LABELS[lang]
    evidence = {e["evidence_id"]: e for e in profile["evidence"]}
    external = {s["source_id"]: s for s in review["external_sources"]}
    claims = {c["claim_id"]: c for c in profile["claims"]}
    lines = [f'# {safe(review["title"])}', ""]

    def heading(en, cn):
        lines.extend([f"## {cn if zh else en}", ""])

    def evidence_lines(ids):
        for eid in ids:
            e = evidence[eid]
            lines.extend([f'- **{eid} · {labels["manuscript_fact"]}** — {safe(e["section"])}; {safe(e["location"])}',
                          f'  > {safe(e["text"])}', ""])

    def statement(item, compact=False):
        lines.extend([f'**{labels[item["information_type"]]}:** {safe(item["text"])}', ""])
        if compact:
            refs = [f'{eid} ({safe(evidence[eid]["section"])}, line {evidence[eid]["line"]})' for eid in item["evidence_ids"]]
            lines.extend([f'**Evidence:** {"; ".join(refs)}', ""])
            return
        if item["reasoning"]:
            lines.extend([f'**{labels["reviewer_inference"]}:** {safe(item["reasoning"])}', ""])
        evidence_lines(item["evidence_ids"])
        for sid in item["external_source_ids"]:
            src = external[sid]
            lines.extend([f'**{labels["external_fact"]} source {sid}:** {safe(src["url"])}; {safe(src["retrieved_at"])}', ""])
            for q in src["quotes"]:
                lines.extend([f'> {safe(q["text"])}', ""])

    heading("Executive Assessment", "执行摘要")
    lines.extend([f'**{"审查信心" if zh else "Review confidence"}: {review["review_confidence"]}**', ""])
    for item in review["executive_assessment"]:
        statement(item, compact=True)
    heading("Strengths", "优点")
    for item in review["strengths"]:
        lines.extend([f'### {item["strength_id"]}', "", f'**{labels[item["information_type"]]}:** {safe(item["text"])}', "",
                      f'**{labels["reviewer_inference"]} — {"意义" if zh else "Why it matters"}:** {safe(item["why_it_matters"])}', "",
                      f'**Confidence:** {item["confidence"]}', ""])
        evidence_lines(item["evidence_ids"])
    for major in (True, False):
        heading("Major Concerns" if major else "Minor Concerns", "主要问题" if major else "次要问题")
        selected = sorted([c for c in review["concerns"] if (c["severity"] != "minor") == major], key=lambda c: c["priority"])
        if not selected:
            lines.extend(["未识别到有充分证据的问题。" if zh else "No evidence-grounded concerns identified in this category.", ""])
        for c in selected:
            lines.extend([f'### {c["concern_id"]}: {safe(c["title"])}', "",
                          f'**Severity:** {c["severity"]} · **Confidence:** {c["confidence"]} · **Priority:** {c["priority"]}', "",
                          f'**{labels[c["information_type"]]}:** {safe(c["claim"])}', ""])
            evidence_lines(c["evidence_ids"])
            lines.extend([f'**{labels["reviewer_inference"]} — Reasoning:** {safe(c["reasoning"])}', "",
                          f'**{labels["reviewer_inference"]} — Why it matters:** {safe(c["impact"])}', "",
                          f'**{labels["recommendation"]}:** {safe(c["suggested_fix"])}', "",
                          f'**Module origins:** {", ".join(c["origin_ids"])}', ""])
    heading("Claim–Evidence Audit", "主张—证据审计")
    lines.extend(["| Claim | Evidence | Assessment | Main limitation / Reasoning |", "|---|---|---|---|"])
    for edge in review["claim_evidence_audit"]:
        lines.append(f'| {edge["claim_id"]}: {safe(claims[edge["claim_id"]]["text"])} | {", ".join(edge["evidence_ids"]) or "Not established"} | {edge["assessment"]} | Reviewer Inference: {safe(edge["reasoning"])} |')
    lines.append("")
    for edge in review["claim_evidence_audit"]:
        lines.extend([f'**{edge["claim_id"]} graph:** experiments={", ".join(edge["experiment_ids"]) or "none established"}; '
                      f'metrics={", ".join(edge["metric_ids"]) or "none established"}; results={", ".join(edge["result_ids"]) or "none established"}; '
                      f'statistics={", ".join(edge["statistical_method_ids"]) or "none established"}; limitations={", ".join(edge["limitation_ids"]) or "none established"}', ""])
        evidence_lines(edge["evidence_ids"])
    for module, en, cn in [("methodology", "Methodology Audit", "方法审计"), ("statistical", "Statistical Audit", "统计审计"),
                            ("ai_ml", "AI / ML Experiment Audit", "AI / ML 实验审计"),
                            ("internal_consistency", "Internal Consistency", "内部一致性")]:
        heading(en, cn)
        for item in review["audits"][module]:
            statement(item)
    heading("Reproducibility", "可复现性")
    lines.extend(["| Item | Status | Evidence / Search coverage | Reasoning |", "|---|---|---|---|"])
    for r in review["reproducibility"]:
        lines.append(f'| {r["item"]} | {r["status"]} | {", ".join(r["evidence_ids"])}; searched: {", ".join(r["searched_source_ids"])} | Reviewer Inference: {safe(r["reasoning"])} |')
    lines.append("")
    for item in review["audits"]["reproducibility"]:
        statement(item)
    heading("Writing & Presentation", "写作与呈现")
    for item in review["audits"]["writing"]:
        statement(item)
    heading("Questions for Authors", "致作者的问题")
    for item in review["author_questions"]:
        statement(item)
    heading("Meta Review", "综合审查")
    lines.extend(["排序依据为核心主张、实验有效性、可复现性和文字修正；不按 reviewer 数量投票。" if zh else
                  "Concerns are prioritized by core claims, experimental validity, reproducibility and prose repair; reviewer counts are not votes.", ""])
    for item in review["audits"]["claim"]:
        statement(item)
    if not review["disagreements"]:
        lines.extend(["No unresolved reviewer disagreement recorded in this run.", ""])
    for d in review["disagreements"]:
        lines.extend([f'### Reviewer disagreement {d["disagreement_id"]}: {safe(d["topic"])}', "", f'**{d["status"]}**', ""])
        for item in d["positions"]:
            statement(item)
        lines.extend([f'**{labels["reviewer_inference"]}:** {safe(d["reasoning"])}', "", f'**Origins:** {", ".join(d["origin_ids"])}', ""])
    heading("Review Limitations", "审查局限")
    limits = review["review_limits"]
    lines.extend([f'External literature checked: {limits["external_literature_checked"]}; citation verification: {limits["citation_verification"]}; '
                  f'supplemental material read: {limits["supplemental_material_read"]}.', ""])
    for c in limits["coverage"]:
        lines.extend([f'- Coverage {safe(c["source_id"])}: {c["status"]}. {safe(c["note"])}', ""])
    for value in limits["unconfirmed_information"]:
        lines.extend([f'- Not established in the manuscript: {safe(value)}', ""])
    for item in limits["limitations"]:
        statement(item)
    if review["venue_rubric"] is None:
        lines.extend(["General academic review rubric applied; no verified venue-specific rubric was used.", ""])
    else:
        lines.extend([f'Venue rubric: {safe(review["venue_rubric"]["venue"])} {review["venue_rubric"]["year"]}; '
                      f'sources: {", ".join(review["venue_rubric"]["external_source_ids"])}', ""])
    for audit in review["citation_audits"]:
        lines.extend([f'- Citation {audit["reference_id"]}: {audit["status"]}. {safe(audit["reasoning"])}', ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--review", required=True)
    parser.add_argument("--sources", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if Path(args.out).resolve() in {Path(p).resolve() for p in [args.profile, args.review, *args.sources]}:
        parser.error("render output must not overwrite input artifacts")
    try:
        text = render(read_json(args.profile), read_json(args.review), load_sources(args.sources))
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(1, f"Render failed: {exc}\n")
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print("Validated review rendered.")


if __name__ == "__main__":
    main()
