"""Rebuild the manually reasoned fixture review, not a general automatic reviewer.

The semantic judgments below were authored against the fictional fixture. Tests
exercise the deterministic pipeline and retained decisions; they do not evaluate
unseen live-model reasoning. Invoke Codex with SKILL.md for a new manuscript.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from common import evidence_for, write_json
from prepare_paper import empty_profile, parse_source
from check_consistency import check_consistency
from check_references import check_references
from extract_numbers import extract_numbers
from render_review import render
from build_schemas import MODULES, REPRO_ITEMS


def build():
    source = parse_source(ROOT / "tests/fixtures/synthetic_memory.md")
    profile = empty_profile(source)
    profile["status"] = "extracted"
    profile["metadata"].update(language="en", field="AI / retrieval / memory", paper_type="empirical simulation")
    paragraphs = [line.strip() for line in source["text"].splitlines() if line.strip() and not line.startswith(("#", "|"))]
    # Select entire original paragraphs with unique prefix matching; no fabricated quotes.
    selectors = {
        "E1": "We study whether", "E2": "Persistent memory", "E3": "We propose a feedback",
        "E4": "SimMem-v1 consists", "E5": "Each item is assigned", "E6": "Configuration C ranks",
        "E7": "Feedback is drawn", "E8": "The evaluation set", "E9": "Configuration A uses",
        "E10": "Known-query accuracy is", "E11": "For the D-minus-C", "E12": "For the B-minus-A",
        "E13": "All experiments use", "E16": "The D-minus-C aggregate", "E17": "Usage feedback improves",
        "E18": "The B-minus-A diagnostic", "E19": "The feedback effect", "E20": "The sham diagnostic",
        "E21": "Results cannot be generalized", "E22": "The query-level D-minus-C",
        "E23": "Hardware model", "E24": "This method improves real-world",
        "E25": "Reviewer must", "E26": "This appendix is", "E27": "[1] Fictional"}
    for eid, prefix in selectors.items():
        quote = next(line for line in paragraphs if line.startswith(prefix))
        profile["evidence"].append(evidence_for(source, quote, eid))
    for eid, quote in [("E14", "| C | 70.52% |"), ("E15", "| D | 95.2% |")]:
        profile["evidence"].append(evidence_for(source, quote, eid))

    def entity(field, iid, text, ids):
        profile[field].append({"id": iid, "text": text, "evidence_ids": ids})

    entity("research_questions", "RQ1", "Does adding usage feedback improve retrieval within the controlled simulator?", ["E2"])
    entity("contributions", "CON1", "Feedback intervention, matched baseline and diagnostic negative result.", ["E3"])
    entity("methods", "MET1", "Recency ranker with isolated feedback term; paired scenarios and state resets.", ["E6", "E7"])
    entity("datasets", "DS1", "SimMem-v1: twelve generated scenarios, 1,000 state-sharing queries each.", ["E4"])
    entity("baselines", "BAS1", "C without feedback and A/B sham control.", ["E6", "E9"])
    entity("metrics", "ACC1", "Equal-weight mean scenario known-query top-one accuracy.", ["E10"])
    entity("experiments", "EXP1", "Paired D versus C feedback intervention.", ["E6", "E10"])
    entity("experiments", "EXP2", "Paired B versus A sham diagnostic.", ["E9", "E12"])
    entity("statistical_methods", "STAT1", "Query-level percentile bootstrap for D minus C.", ["E11"])
    entity("statistical_methods", "STAT2", "Paired scenario-level bootstrap for B minus A.", ["E12"])
    entity("results", "RES1", "Table: D 95.2%, C 70.52%, difference 24.68 percentage points.", ["E14", "E15", "E16"])
    entity("results", "RES2", "Sham difference 0.04 percentage points, interval [-0.12,0.20]; not proof of equivalence.", ["E18"])
    entity("limitations", "LIM1", "Synthetic vectors and feedback do not establish real-world transfer.", ["E5", "E19", "E21"])
    entity("limitations", "LIM2", "Author-disclosed uncertainty underestimation from shared query state.", ["E4", "E22"])
    entity("tables", "TAB1", "Configuration C/D known-query accuracy table.", ["E14", "E15"])
    entity("references", "REF1", "Fictional SimMem-v1 specification; no actual publication asserted.", ["E27"])
    profile["claims"] = [
        {"claim_id": "C1", "text": "Feedback improves known-query retrieval in the specified SimMem-v1 configuration.", "evidence_ids": ["E17"], "claim_type": "empirical", "strength": "bounded", "scope": "SimMem-v1 D versus C"},
        {"claim_id": "C2", "text": "The sham diagnostic does not establish a practically relevant gain or equivalence.", "evidence_ids": ["E18"], "claim_type": "empirical", "strength": "qualified", "scope": "SimMem-v1 B versus A"},
        {"claim_id": "C3", "text": "This method improves real-world AI assistants.", "evidence_ids": ["E24"], "claim_type": "scope", "strength": "universal", "scope": "real-world AI assistants"}]

    def statement(text, ids, kind="reviewer_inference", reasoning=None):
        return {"text": text, "information_type": kind, "evidence_ids": ids, "external_source_ids": [],
                "reasoning": reasoning or ("Interpretation is confined to the cited manuscript passages." if kind != "manuscript_fact" else "")}

    def concern(cid, category, title, claim, ids, reasoning, impact, fix, root, scope, claims, priority, severity="major", confidence="HIGH"):
        return {"concern_id": cid, "severity": severity, "category": category, "title": title, "claim": claim,
                "evidence_ids": ids, "reasoning": reasoning, "impact": impact, "suggested_fix": fix, "confidence": confidence,
                "information_type": "reviewer_inference", "root_cause": root, "affected_scope": scope,
                "claim_ids": claims, "origin_ids": [], "priority": priority}

    overclaim = concern("CL01", "claim", "Conclusion exceeds the simulator evidence",
        "The broad assistant-improvement statement is not established by this synthetic retrieval experiment.", ["E5", "E21", "E24"],
        "The conclusion's first sentence claims real-world transfer while the limitations explicitly rule out such generalization. The later qualification does not resolve the unconditional sentence.",
        "Readers may attribute end-to-end deployment benefits to a study that measures generated known-query retrieval only.",
        "Limit the first conclusion sentence to SimMem-v1, or provide evidence testing the broader claim.", "unsupported_transfer", "C3", ["C3"], 1)
    methodology = concern("MD01", "methodology", "External-validity boundary is explicitly disclosed",
        "The synthetic-vector and manually specified feedback design supports a controlled mechanism, with limited deployment scope.", ["E5", "E6", "E7", "E19", "E21"],
        "The C/D contrast isolates the feedback factor, but no natural-language task or learned feedback mechanism is tested. Authors already disclose this boundary; this is not a failure to recognize limitations.",
        "This boundary matters for the broad C3 conclusion, not for invalidating all controlled results.",
        "Align the conclusion with the stated scope; real-embedding tests would be an optional route to broader support.", "unsupported_transfer", "C3", ["C3"], 1)
    statistical = concern("ST01", "statistical", "Query bootstrap does not preserve scenario dependence",
        "The reported D-minus-C interval does not establish uncertainty across independent generated scenarios.", ["E4", "E11", "E22"],
        "Queries share state within twelve scenarios but are resampled as 12,000 independent outcomes. The authors disclose possible underestimation; the actual amount cannot be calculated without scenario-level data.",
        "The effect magnitude is documented, but precision and inference beyond these scenarios remain uncertain.",
        "Report paired scenario-level contrasts and an interval that preserves the independent scenario units.", "bootstrap_unit", "C1_interval", ["C1"], 2)
    numeric = concern("IN01", "internal_consistency", "Abstract and table report different aggregate accuracy",
        "D accuracy is 96.2% in the abstract and 95.2% in Table 1 for the same SimMem-v1 aggregate quantity.", ["E1", "E10", "E15"],
        "Reviewer-confirmed metric/dataset/model/split/aggregation identities match, and the 1.0 percentage point difference exceeds rounding. The correct value cannot be adjudicated from these passages alone.",
        "The discrepancy changes the reported gain if the abstract value is used. Table-based arithmetic is internally consistent.",
        "Reconcile the source of the abstract number with Table 1 and update the affected summary.", "accuracy_mismatch", "D_aggregate", ["C1"], 2, "moderate")
    reproducibility = concern("RP01", "reproducibility", "Core simulation artifacts are not supplied",
        "Exact seeds, code, per-scenario measurements and analysis scripts are not established in this supplied draft.", ["E13", "E23"],
        "The draft describes generator parameters and software versions but explicitly omits execution and analysis artifacts. This does not establish that the authors used only one seed or lacked these artifacts internally.",
        "Independent reruns and corrected scenario-level intervals cannot be checked from the supplied material.",
        "Provide a versioned generator, seed schedule, raw scenario-level results and analysis scripts.", "simulation_artifacts", "main_results", ["C1", "C2"], 3, "moderate")
    raw = {module: [] for module in MODULES}
    for finding in [overclaim, methodology, statistical, numeric, reproducibility]:
        raw[finding["category"]].append(finding)
    final = []
    for i, (finding, origin_ids) in enumerate([(overclaim, ["CL01", "MD01"]), (statistical, ["ST01"]), (numeric, ["IN01"]), (reproducibility, ["RP01"])], 1):
        final.append({**finding, "concern_id": f"M{i}", "origin_ids": origin_ids})
    final[0]["evidence_ids"] = ["E5", "E6", "E7", "E19", "E21", "E24"]
    final[0]["reasoning"] += " Authors explicitly acknowledge the external-validity boundary; the concern is the conflicting conclusion."

    def edge(cid, status, ids, reasoning, experiments, metrics, results, stats, limitations):
        return {"claim_id": cid, "assessment": status, "reasoning": reasoning, "information_type": "reviewer_inference",
                "evidence_ids": ids, "experiment_ids": experiments, "metric_ids": metrics, "result_ids": results,
                "statistical_method_ids": stats, "limitation_ids": limitations}

    availability = {
        "dataset": ("AVAILABLE", ["E4", "E5"], "The generated scenario structure is reported; AVAILABLE denotes reporting, not execution."),
        "dataset_version": ("PARTIAL", ["E4"], "SimMem-v1 is named, but no released artifact hash is supplied."),
        "preprocessing": ("PARTIAL", ["E5", "E7"], "Vector/feedback generation is described; executable generator is not supplied."),
        "code": ("MISSING", ["E13"], "Not established in the manuscript; the draft explicitly omits executable code."),
        "random_seeds": ("MISSING", ["E23"], "Random seed information was not established in the manuscript. No seed count is inferred."),
        "model": ("AVAILABLE", ["E6"], "The ranking equations are described in prose; no pretrained model is involved."),
        "model_version": ("NOT_APPLICABLE", ["E5", "E6"], "No pretrained/API model is used; code version remains an artifact gap."),
        "prompt": ("NOT_APPLICABLE", ["E5"], "No linguistic input, LLM prompt or judge is used in this simulator."),
        "dependencies": ("PARTIAL", ["E13"], "Python/NumPy versions are reported, but no full dependency lock is supplied."),
        "environment": ("PARTIAL", ["E10", "E13"], "Software and single-worker CPU context are reported; full environment is incomplete."),
        "hyperparameters": ("AVAILABLE", ["E6", "E7", "E8"], "Ranking weights and feedback probability are explicitly reported."),
        "hardware": ("PARTIAL", ["E10", "E23"], "CPU worker count is provided; hardware model is not established."),
        "evaluation_procedure": ("AVAILABLE", ["E8", "E10"], "Held-out generation, top-one metric and equal scenario weighting are reported."),
        "statistical_procedure": ("AVAILABLE", ["E11", "E12"], "Both resampling procedures are described; availability does not imply statistical validity."),
        "raw_results": ("MISSING", ["E13", "E23"], "Not established in the manuscript; raw scenario-level measurements are explicitly omitted."),
        "analysis_scripts": ("MISSING", ["E13"], "Not established in the manuscript; analysis scripts are explicitly omitted.")}
    review = {
        "schema_version": "1.0", "language": "en", "title": "Evidence-grounded review: Feedback-Guided Retrieval (fictional fixture)", "review_confidence": "MEDIUM",
        "executive_assessment": [
            statement("The manuscript evaluates usage feedback in a controlled memory simulator with twelve generated scenarios and paired ranking configurations. It reports a large D-versus-C difference in known-query retrieval, alongside a sham diagnostic whose scenario-level interval does not establish a practically relevant gain. These are measurements of a specified synthetic mechanism, and no natural-language interaction or pretrained embedding model is evaluated.", ["E4", "E5", "E6", "E16", "E18"], "manuscript_fact"),
            statement("The strongest contribution is the interpretable feedback-only comparison, complemented by a pre-specified negative diagnostic and explicit disclosure of external-validity and bootstrap limitations. The negative result contributes useful information about measurement stability; its direction does not reduce the quality of that diagnostic design.", ["E6", "E9", "E12", "E18", "E21", "E22"]),
            statement("The biggest uncertainty is how much of the apparent precision survives scenario-level resampling and how the synthetic effect transfers beyond this generator. The first conclusion sentence claims real-world assistant improvements despite the explicit generalization boundary. An abstract/table discrepancy additionally prevents confirmation of the intended aggregate accuracy. Review confidence is medium because the design and reporting issues are directly grounded, while raw results and executable artifacts are unavailable for independent reproduction.", ["E1", "E11", "E15", "E21", "E23", "E24"])],
        "strengths": [
            {"strength_id": "S1", "text": "C/D isolates the feedback term within paired generated scenarios.", "evidence_ids": ["E6", "E7"], "why_it_matters": "This directly targets the simulator-level contribution with an interpretable control, within the specified mechanism.", "confidence": "HIGH", "information_type": "reviewer_inference"},
            {"strength_id": "S2", "text": "The pre-specified sham diagnostic reports its uncertain negative result with paired scenario-level resampling.", "evidence_ids": ["E9", "E12", "E18"], "why_it_matters": "A negative diagnostic can reveal measurement artifacts; the paper avoids claiming equivalence from an interval spanning zero.", "confidence": "HIGH", "information_type": "reviewer_inference"},
            {"strength_id": "S3", "text": "The manuscript explicitly discloses external-validity and resampling-unit limitations.", "evidence_ids": ["E21", "E22"], "why_it_matters": "Transparency makes the evidential boundary inspectable, even though the conclusion needs alignment.", "confidence": "HIGH", "information_type": "manuscript_fact"}],
        "concerns": final, "module_findings": raw,
        "claim_evidence_audit": [
            edge("C1", "PARTIALLY_SUPPORTED", ["E6", "E14", "E15", "E16", "E22"], "The paired control and table support a simulator-level mean difference; the uncertainty interval and abstract value remain unresolved. No real-world transfer is implied by this bounded claim.", ["EXP1"], ["ACC1"], ["RES1"], ["STAT1"], ["LIM1", "LIM2"]),
            edge("C2", "SUPPORTED", ["E9", "E12", "E18"], "The stated interval and paired scenario analysis support the carefully bounded lack of established practically relevant gain; this is not proof of equivalence.", ["EXP2"], ["ACC1"], ["RES2"], ["STAT2"], ["LIM1"]),
            edge("C3", "OVERSTATED", ["E5", "E19", "E21", "E24"], "Only synthetic retrieval is evaluated; the unconditional deployment claim exceeds that scope. No experiment, metric, result or statistical support for real-world assistant behavior is established. Authors already disclose the limitation.", [], [], [], [], ["LIM1"])],
        "audits": {
            "methodology": [statement("The feedback-only C/D control is appropriate to the bounded mechanism question; Gaussian vectors and manually specified feedback restrict deployment interpretation. Authors already disclose this boundary.", ["E2", "E5", "E6", "E7", "E21"])],
            "statistical": [statement("The twelve scenarios are independent units while 12,000 queries share within-scenario state. The D/C query bootstrap does not preserve that dependence. The sham diagnostic uses the more appropriate scenario-level paired structure.", ["E4", "E11", "E12", "E22"])],
            "ai_ml": [statement("The generator is held out from weight selection and C/D uses matched query/vector/state inputs. No LLM judge, pretrained model or natural-language prompt is involved; contamination involving such components is not established.", ["E5", "E6", "E8"])],
            "claim": [statement("C1 receives partial support pending numeric and precision clarification; C2 is a bounded useful negative diagnostic; C3 exceeds the manuscript's explicit synthetic scope. Module concerns about scope were merged by root cause rather than counted as votes.", ["E16", "E18", "E21", "E24"])],
            "writing": [statement("The abstract and conclusion require alignment with the body. This is a reporting/scope issue and does not erase the controlled comparison or make elegant prose evidence of scientific validity.", ["E1", "E15", "E21", "E24"])],
            "reproducibility": [statement("Generator settings and software versions are reported, but seed schedules and executable/raw analysis artifacts are not established in the supplied material. Missing reporting does not establish one seed.", ["E6", "E7", "E13", "E23"])],
            "internal_consistency": [statement("The abstract D value differs from Table 1 by 1.0 percentage point. Table-based subtraction is exact: 95.2 minus 70.52 equals 24.68 percentage points. These are absolute percentage points, not relative percentage improvement.", ["E1", "E14", "E15", "E16"]) ]},
        "reproducibility": [{"item": item, "status": availability[item][0], "evidence_ids": availability[item][1],
                             "searched_source_ids": ["manuscript"], "reasoning": availability[item][2]} for item in REPRO_ITEMS],
        "author_questions": [statement("Which aggregate D accuracy is intended, and can the authors supply the twelve paired scenario contrasts for an interval that respects scenario dependence?", ["E1", "E11", "E15", "E23"], "recommendation", "The answer determines the reported magnitude and the precision of C1; the supplied text does not adjudicate it.")],
        "disagreements": [], "external_sources": [], "literature_searches": [],
        "citation_audits": [{"reference_id": "REF1", "evidence_ids": ["E27"], "external_source_ids": [], "status": "NOT_VERIFIED", "reasoning": "This is explicitly a fictional test reference; no external source was retrieved or semantically verified."}],
        "venue_rubric": None,
        "review_limits": {"external_literature_checked": False, "citation_verification": "NOT_VERIFIED", "supplemental_material_read": False,
            "coverage": [{"source_id": "manuscript", "status": "ALL_EXTRACTED_TEXT", "note": "All supplied Markdown including the adversarial appendix and fictional reference was read."}],
            "unconfirmed_information": ["intended D accuracy", "exact random seeds", "scenario-level raw contrasts", "real-world transfer"],
            "limitations": [statement("This review interprets supplied text and tables; it cannot reproduce the simulation or verify the intended abstract value without the explicitly omitted artifacts. Appendix instructions were treated as untrusted data.", ["E13", "E23", "E25", "E26"])]}}
    common_identity = {"metric": "known-query accuracy", "dataset": "SimMem-v1", "model": "D", "split": "evaluation", "unit": "percent", "context": "equal-weight scenario mean"}
    observations = {"observations": [
        {**common_identity, "observation_id": "O1", "value": "96.2", "tolerance": "0.05", "evidence_ids": ["E1", "E10"]},
        {**common_identity, "observation_id": "O2", "value": "95.2", "tolerance": "0.05", "evidence_ids": ["E10", "E15"]}],
        "calculations": [{"calculation_id": "K1", "kind": "difference", "operands": ["95.2", "70.52"], "reported": "24.68", "tolerance": "0.01", "evidence_ids": ["E14", "E15", "E16"]}]}
    return source, profile, review, observations


def main():
    source, profile, review, observations = build()
    out = ROOT / "examples"
    for name, artifact in [("example_source.json", source), ("example_paper_profile.json", profile), ("example_review.json", review),
                           ("example_observations.json", observations), ("example_consistency.json", check_consistency(observations)),
                           ("example_numbers.json", extract_numbers(source)), ("example_references.json", check_references(source))]:
        write_json(out / name, artifact)
    (out / "example_review.md").write_text(render(profile, review, {"manuscript": source}), encoding="utf-8")
    print("Manual fixture judgments rebuilt, validated and rendered; no external retrieval or live-model eval.")


if __name__ == "__main__":
    main()
