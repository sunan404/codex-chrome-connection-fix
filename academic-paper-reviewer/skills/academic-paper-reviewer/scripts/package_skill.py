"""Package only this skill's maintained files in an inspectable ordinary ZIP."""
import argparse
from pathlib import Path
import zipfile
from common import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    target = Path(args.out).resolve()
    if target.suffix.lower() != ".zip":
        parser.error("Output must be an ordinary .zip archive")
    target.parent.mkdir(parents=True, exist_ok=True)
    files = [p for p in ROOT.rglob("*") if p.is_file() and p.resolve() != target and
             not any(part in {"__pycache__", ".git", ".venv", "dist", "runs"} for part in p.relative_to(ROOT).parts) and
             p.suffix != ".pyc"]
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, Path(ROOT.name) / path.relative_to(ROOT))
    print(f"Packaged {len(files)} files: {target}")


if __name__ == "__main__":
    main()
