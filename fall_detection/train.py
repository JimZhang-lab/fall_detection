import argparse
import os
import shutil

from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(description="Train YOLOv8 fall detection model.")
    parser.add_argument("--model", default="assets/yolov8n.pt", help="Base model or model config.")
    parser.add_argument("--data", default="data.yaml", help="YOLO dataset yaml.")
    parser.add_argument("--epochs", type=int, default=50, help="Training epochs.")
    parser.add_argument("--imgsz", type=int, default=640, help="Input image size.")
    parser.add_argument("--batch", type=int, default=16, help="Batch size.")
    parser.add_argument("--device", default=None, help="Device, e.g. 0, cpu, or mps.")
    parser.add_argument("--project", default="runs", help="Output project directory.")
    parser.add_argument("--name", default="fall_train", help="Run name.")
    parser.add_argument("--export-name", default="", help="Copy best.pt to assets/<export-name>/best.pt after training.")
    return parser.parse_args()


def main():
    args = parse_args()
    model = YOLO(args.model)

    train_kwargs = {
        "data": args.data,
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "project": args.project,
        "name": args.name,
        "exist_ok": True,
    }
    if args.device:
        train_kwargs["device"] = args.device

    model.train(**train_kwargs)

    best_path = os.path.join(args.project, args.name, "weights", "best.pt")
    print(f"训练完成，最佳模型位置：{best_path}")

    if args.export_name:
        target_dir = os.path.join("assets", args.export_name)
        os.makedirs(target_dir, exist_ok=True)
        shutil.copy2(best_path, os.path.join(target_dir, "best.pt"))
        print(f"已复制到推理模型目录：{target_dir}/best.pt")


if __name__ == "__main__":
    main()
