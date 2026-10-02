"""Add an explicitly supplied supplement without fetching or executing it."""
import argparse
from pathlib import Path
from common import read_json, write_json
from prepare_paper import parse_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input")
    parser.add_argument("--id", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--out", required=True, help="New source JSON path")
    args = parser.parse_args()
    profile = read_json(args.profile)
    if any(s["source_id"] == args.id for s in profile["sources"]):
        parser.error("source id already exists")
    if Path(args.out).resolve() in {Path(args.profile).resolve(), Path(args.input).resolve()}:
        parser.error("output must differ from profile and original supplement")
    source = parse_source(args.input, args.id)
    write_json(args.out, source)
    profile["sources"].append({k: source[k] for k in ("source_id", "path", "text_sha256", "file_sha256")})
    profile["extraction_warnings"].extend(source["warnings"])
    write_json(args.profile, profile)


if __name__ == "__main__":
    main()
