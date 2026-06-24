# Claude Project Notes

## Active Project

The active project is `fall_detection/`, a YOLO-based fall-detection training and PyQt5 inference application.

Use these files first:

- `fall_detection/main.py`
- `fall_detection/train.py`
- `fall_detection/gui/main_window.py`
- `fall_detection/logic/detector.py`
- `fall_detection/logic/utils.py`
- `fall_detection/data.yaml`
- `fall_detection/requirements.txt`

## Repository Hygiene

- Root documentation should remain consolidated in `README.md`.
- Local research notes may stay in `fall_detection/docs/`, but they should not be committed.
- Do not commit local datasets, trained weights, inference outputs, training runs, archived experiments, or local research documents.
- The `.gitignore` intentionally excludes data, model weights, outputs, runs, archive directories, and docs.
- Do not delete datasets or model assets from disk unless the user explicitly asks.
- Keep task-boundary and repository-hygiene notes here or in `AGENTS.md`; do not put "do not delete", "do not commit", or similar agent instructions in `README.md`.
- Keep `README.md` focused on user-facing setup, inference, training, hardware, and troubleshooting.

## Standard Commands

Install:

```bash
cd fall_detection
pip install -r requirements.txt
```

Inference:

```bash
cd fall_detection
python main.py
```

Training:

```bash
cd fall_detection
python train.py --epochs 50 --imgsz 640 --batch 16
```

Low-VRAM training:

```bash
cd fall_detection
python train.py --epochs 50 --imgsz 640 --batch 8
```

## Environment Guidance

Target test/deployment environments should use Python 3.11.x or 3.12.x. For NVIDIA GPU machines, install the CUDA-enabled PyTorch wheel first, then install `fall_detection/requirements.txt`.

Use the root `README.md` as the tracked dependency and hardware reference.
