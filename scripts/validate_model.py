import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate a custom marine-sonar YOLO model"); parser.add_argument("--model", default="backend/models/best.pt"); parser.add_argument("--data", default="dataset/data.yaml"); args = parser.parse_args()
    try:
        from ultralytics import YOLO
        metrics = YOLO(args.model).val(data=args.data)
        print({"precision": metrics.box.mp, "recall": metrics.box.mr, "mAP50": metrics.box.map50, "mAP50_95": metrics.box.map})
    except ImportError as exc: raise SystemExit("Install ultralytics to validate the custom model.") from exc
