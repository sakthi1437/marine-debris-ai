import argparse


def main():
    parser = argparse.ArgumentParser(description="Train a custom YOLO model on labeled marine-sonar data")
    parser.add_argument("--data", default="dataset/data.yaml"); parser.add_argument("--model", default="yolo11n.pt"); parser.add_argument("--epochs", type=int, default=50); parser.add_argument("--imgsz", type=int, default=640); parser.add_argument("--batch", type=int, default=16); parser.add_argument("--device", default="auto"); args = parser.parse_args()
    try:
        from ultralytics import YOLO
    except ImportError as exc: raise SystemExit("Install ultralytics to train; no dataset is downloaded automatically.") from exc
    print("Training requires an appropriately labeled marine-sonar dataset; generic pretrained weights are initialization only.")
    YOLO(args.model).train(data=args.data, epochs=args.epochs, imgsz=args.imgsz, batch=args.batch, device=args.device)


if __name__ == "__main__": main()
