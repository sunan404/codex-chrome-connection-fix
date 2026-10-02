"""Check reviewer-mapped numeric identities and explicit arithmetic with Decimal."""
import argparse
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from common import read_json, write_json

IDENTITY = ("metric", "dataset", "model", "split", "unit", "context")


def check_consistency(data):
    observations = data.get("observations", [])
    groups = defaultdict(list)
    ids = set()
    for observation in observations:
        if observation["observation_id"] in ids:
            raise ValueError("Duplicate observation id")
        ids.add(observation["observation_id"])
        if not all(str(observation.get(k, "")).strip() for k in IDENTITY):
            raise ValueError("Every observation needs all six explicit identity fields")
        if not observation.get("evidence_ids"):
            raise ValueError("Every observation needs evidence_ids")
        if not Decimal(observation["value"]).is_finite():
            raise ValueError("Numbers must be finite")
        tolerance = Decimal(observation.get("tolerance", "0"))
        if not tolerance.is_finite() or tolerance < 0:
            raise ValueError("Tolerance must be finite and nonnegative")
        groups[tuple(observation[k] for k in IDENTITY)].append(observation)
    conflicts = []
    for key, group in groups.items():
        for i, left in enumerate(group):
            for right in group[i+1:]:
                tolerance = max(Decimal(left.get("tolerance", "0")), Decimal(right.get("tolerance", "0")))
                if abs(Decimal(left["value"]) - Decimal(right["value"])) > tolerance:
                    conflicts.append({"kind": "NUMERICAL_CONFLICT", "identity": dict(zip(IDENTITY, key)),
                                      "left": left, "right": right,
                                      "reasoning": "Same reviewer-confirmed quantity differs beyond specified rounding tolerance."})
    arithmetic = []
    for operation in data.get("calculations", []):
        operands = [Decimal(v) for v in operation["operands"]]
        kind = operation["kind"]
        if not all(v.is_finite() for v in operands) or not operation.get("evidence_ids"):
            raise ValueError("Calculations require finite operands and evidence")
        if kind == "sum":
            computed = sum(operands, Decimal(0))
        elif len(operands) != 2:
            raise ValueError("Ratio/difference operations require exactly two operands")
        elif kind in {"percentage", "relative_change_percent"} and operands[1] == 0:
            arithmetic.append({"calculation_id": operation["calculation_id"], "status": "UNDEFINED_ZERO_DENOMINATOR"})
            continue
        elif kind == "percentage":
            computed = operands[0] / operands[1] * 100
        elif kind == "difference":
            computed = operands[0] - operands[1]
        elif kind == "relative_change_percent":
            computed = (operands[0] - operands[1]) / operands[1] * 100
        else:
            raise ValueError(f"Unknown calculation kind: {kind}")
        reported = Decimal(operation["reported"])
        tolerance = Decimal(operation.get("tolerance", "0"))
        if not reported.is_finite() or not tolerance.is_finite() or tolerance < 0:
            raise ValueError("Reported number and nonnegative tolerance must be finite")
        arithmetic.append({"calculation_id": operation["calculation_id"], "computed": str(computed),
                           "reported": str(reported), "evidence_ids": operation["evidence_ids"],
                           "status": "MATCH" if abs(computed - reported) <= tolerance else "ARITHMETIC_MISMATCH"})
    return {"conflicts": conflicts, "arithmetic": arithmetic,
            "scope": "Only explicitly mapped quantities and specified calculations; no semantic contradiction detector."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Reviewer-mapped observations JSON")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        result = check_consistency(read_json(args.input))
    except (ValueError, KeyError, InvalidOperation) as exc:
        parser.exit(2, f"consistency check failed: {exc}\n")
    write_json(args.out, result)


if __name__ == "__main__":
    main()
