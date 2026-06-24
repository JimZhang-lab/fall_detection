# Agent Instructions

## Project Overview

This repository contains a fall-detection training and inference project. The active deliverable code is under `fall_detection/`.

Main entry points:

- `fall_detection/main.py`: PyQt5 GUI inference entry.
- `fall_detection/train.py`: YOLO training entry.
- `fall_detection/data.yaml`: YOLO dataset configuration.
- `fall_detection/requirements.txt`: Python dependency ranges.

## Important Rules

1. Do not delete or rewrite local datasets, model weights, historical outputs, or archived experiments unless the user explicitly asks.
2. Do not commit large data, model files, generated outputs, archived experiments, or local research documents. The `.gitignore` intentionally excludes `fall_detection/data/`, `fall_detection/assets/**/*.pt`, `fall_detection/outputs/`, `fall_detection/runs/`, `fall_detection/archive/`, and `fall_detection/docs/`.
3. Keep root-level documentation consolidated in `README.md`.
4. Local research and project notes may stay in `fall_detection/docs/`, but they should not be committed.
5. Prefer small, focused changes that preserve the current project layout.

## Common Commands

Install dependencies:

```bash
cd fall_detection
pip install -r requirements.txt
```

Run GUI inference:

```bash
cd fall_detection
python main.py
```

Train the current YOLO fall detector:

```bash
cd fall_detection
python train.py --epochs 50 --imgsz 640 --batch 16
```

Train with a smaller batch when VRAM is limited:

```bash
cd fall_detection
python train.py --epochs 50 --imgsz 640 --batch 8
```

Export a trained model into the GUI model directory:

```bash
cd fall_detection
python train.py --epochs 50 --batch 16 --export-name my-fall-model
```

## Dependency Notes

Use Python 3.11.x or 3.12.x for target test/deployment machines. For NVIDIA GPU use, install the CUDA-enabled PyTorch wheel from the official PyTorch selector before installing `requirements.txt`.

Use `README.md` as the tracked source of setup, hardware, and dependency guidance.

## Validation Checklist

Before committing:

1. Confirm `git status --ignored --short` does not include data/model/output files as tracked additions.
2. Confirm `README.md` still contains setup, inference, training, and hardware guidance.
3. If code changed, run at least a lightweight import or command check where feasible.
