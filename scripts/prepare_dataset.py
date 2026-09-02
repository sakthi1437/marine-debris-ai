from pathlib import Path
import argparse


def validate(root: Path) -> int:
    errors = 0
    for split in ("train", "val", "test"):
        images, labels = root / "images" / split, root / "labels" / split
        image_files = {p.stem for p in images.glob("*") if p.is_file()} if images.exists() else set()
        label_files = {p.stem for p in labels.glob("*.txt")} if labels.exists() else set()
        missing = image_files - label_files
        if missing: print(f"{split}: {len(missing)} images have no labels"); errors += len(missing)
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--dataset", type=Path, default=Path("dataset")); args = parser.parse_args()
    raise SystemExit(1 if validate(args.dataset) else 0)
