# 跌倒检测项目交付说明

本项目将跌倒检测的训练代码、推理代码和配置统一整理到：

```text
fall_detection/
```

后续主要进入该目录即可完成推理、训练和模型管理。

## 1. 项目用途

本项目面向老人居家/养老场景的视频跌倒检测，当前可交付成果是一个基于 YOLO 的跌倒检测训练与本地推理系统。

当前已经支持：

1. 使用 YOLO 模型训练单类 `fall` 跌倒检测模型。
2. 使用 PyQt5 图形界面对图片或视频做跌倒检测。
3. 从 `assets/` 下自动读取多个历史模型权重。
4. 支持无人帧筛除、静态帧筛除、按帧间隔检测。
5. 输出带检测框的图片/视频和检测日志。

当前主目录：

```text
fall_detection/
├── main.py                    # 推理 GUI 入口
├── train.py                   # YOLO 训练入口
├── data.yaml                  # 训练数据配置
├── requirements.txt           # 依赖列表
├── gui/                       # PyQt5 推理界面
├── logic/                     # 推理逻辑
├── training/                  # 训练辅助脚本
├── assets/                    # 预训练模型和已训练模型
├── data/                      # 训练数据、标注数据和样例素材
└── outputs/                   # 推理输出结果
```

## 2. 环境依赖

建议使用虚拟环境安装依赖：

```bash
cd fall_detection
pip install -r requirements.txt
```

项目依赖版本范围：

```text
torch>=2.3.0,<3.0
torchvision>=0.18.0,<1.0
ultralytics>=8.4.76,<9.0
opencv-python>=4.10.0,<5.0
PyQt5>=5.15.10,<5.16
numpy>=1.26.0,<3.0
```

真实测试机/交付机推荐版本：

| 依赖 | 推荐版本 | 说明 |
| --- | --- | --- |
| Python | 3.11.x 或 3.12.x | 真实交付优先 3.11.x；新环境/YOLO26 实验可用 3.12.x。 |
| PyTorch | 2.3.0 及以上，低于 3.0 | YOLOv8 可用；YOLO26 实验建议 2.7+ CUDA 版。 |
| torchvision | 0.18.0 及以上，低于 1.0 | 与 PyTorch 匹配安装。 |
| ultralytics | 8.4.76 及以上，低于 9.0 | YOLOv8/YOLO26 训练推理框架，建议使用较新的 8.x。 |
| opencv-python | 4.10.0 及以上，低于 5.0 | 视频读写、图像处理、结果显示。 |
| PyQt5 | 5.15.10 及以上，低于 5.16 | GUI 界面依赖，保持在 PyQt5 5.15.x。 |
| numpy | 1.26.0 及以上，低于 3.0 | 图像/数组处理，兼容 OpenCV 和 Ultralytics。 |

如果使用 NVIDIA GPU，请先按 CUDA 版本安装支持 GPU 的 PyTorch，再安装项目依赖。例如 CUDA 12.8：

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
cd fall_detection
pip install -r requirements.txt
```

CUDA 12.6：

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
cd fall_detection
pip install -r requirements.txt
```

CPU 或无 GPU 临时测试可以直接：

```bash
cd fall_detection
pip install -r requirements.txt
```

检查命令：

```bash
python - <<'PY'
import torch
print("torch:", torch.__version__)
print("cuda available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu:", torch.cuda.get_device_name(0))
    print("vram GB:", round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2))
PY
```

如果 `cuda available` 是 `False`，项目会退回 CPU 推理，视频检测会明显变慢；训练也不建议使用 CPU。

## 3. 最低显卡配置

本项目推理可以不用显卡启动，因为代码会自动选择：

```python
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
```

但为了正常演示和训练，建议按下面配置准备。

| 用途 | 最低配置 | 推荐配置 | 说明 |
| --- | --- | --- | --- |
| 图片推理/短视频演示 | NVIDIA 4GB 显存，例如 GTX 1050 Ti 4GB、GTX 1650 4GB | RTX 3050 6GB/8GB、RTX 4060 8GB | CPU 也能启动，但视频检测会慢。 |
| 视频推理 + 无人帧筛除 | NVIDIA 4GB 显存可跑，6GB 更稳 | RTX 3050 6GB/8GB、RTX 3060 12GB、RTX 4060 8GB | 无人帧筛除会额外加载 `assets/yolov8n.pt`。 |
| YOLOv8n/YOLO26n 训练 | NVIDIA 6GB 显存，例如 GTX 1660 6GB、RTX 2060 6GB、RTX 3050 6GB | RTX 3060 12GB、RTX 4070 12GB、RTX 4060 Ti 16GB | 6GB 训练时建议 `batch=4` 或 `batch=8`。 |
| 默认 `batch=16` 训练 | NVIDIA 8GB 显存起步 | 12GB 显存更稳 | 当前默认训练命令使用 `--batch 16`。 |
| YOLO26s 或更大模型训练 | 8GB-12GB 起步 | 12GB-16GB 以上 | YOLO26s 比 YOLO26n 明显更大。 |
| 多路摄像头/长期部署 | 不建议 4GB | RTX 3060 12GB、RTX 4060 Ti 16GB、RTX 4070 12GB 或 Jetson Orin 系列 | 需要考虑多路视频、解码、日志和告警。 |

简洁结论：

```text
只做推理演示：最低 4GB NVIDIA 显卡，推荐 6GB-8GB。
要自己训练：最低 6GB NVIDIA 显卡，推荐 12GB。
要训练 YOLO26 或后续部署：推荐 12GB 起步。
如果只能选一张卡：优先推荐 RTX 3060 12GB。
```

## 4. Web UI 推理（推荐）

项目提供了现代化的 Web 界面，使用 React + Ant Design + Tailwind CSS 构建。

### 快速启动

**步骤 1**：进入项目目录并安装依赖

```bash
cd fall_detection
pip install -r requirements.txt
```

**步骤 2**：启动后端 API

在一个终端窗口运行：

```bash
cd fall_detection
python api.py
```

后端 API 将在 `http://127.0.0.1:5000` 运行

**步骤 3**：启动前端应用

在另一个终端窗口运行：

```bash
cd web
npm install    # 首次运行时安装依赖
npm run dev
```

前端应用将在 `http://localhost:3000` 运行

**步骤 4**：打开浏览器

访问 [http://localhost:3000](http://localhost:3000) 开始使用 Web UI。

### Web UI 功能

- ✨ 现代化响应式界面
- 📁 文件拖拽上传（图像和视频）
- 🤖 多模型支持
- 🎯 检测选项配置（无人帧筛除、静态帧筛除、帧间隔）
- 📊 实时检测日志显示
- 📥 结果文件下载

详见 [web/README.md](web/README.md)

## 4.1 启动推理（PyQt5 GUI - 已弃用）

如需使用旧的 PyQt5 图形界面：

```bash
cd fall_detection
python main.py
```

界面中可以选择：

```text
data/samples/images/
data/samples/videos/
```

也可以选择其他图片或视频。

推理输出保存到：

```text
outputs/<模型名称>/
```

例如：

```text
outputs/mixdata-two-70-augment/0001.mp4
outputs/mixdata-two-70-augment/0001.txt
```

## 5. 启动训练

当前训练集配置在：

```text
fall_detection/data.yaml
```

训练数据结构：

```text
fall_detection/data/fall_dataset/
├── images/train/
├── images/val/
├── labels/train/
└── labels/val/
```

基础训练命令：

```bash
cd fall_detection
python train.py --epochs 50 --imgsz 640 --batch 16
```

显存不足时降低 batch：

```bash
python train.py --epochs 50 --imgsz 640 --batch 8
python train.py --epochs 50 --imgsz 640 --batch 4
```

指定设备：

```bash
python train.py --device 0      # NVIDIA GPU
python train.py --device cpu    # CPU，不推荐训练使用
python train.py --device mps    # Apple Silicon 可尝试
```

训练完成后默认结果位置：

```text
fall_detection/runs/fall_train/weights/best.pt
```

训练完成并导出到推理模型目录：

```bash
python train.py --epochs 50 --batch 16 --export-name my-fall-model
```

导出后会生成：

```text
fall_detection/assets/my-fall-model/best.pt
```

重新运行 `python main.py`，模型下拉框会自动出现：

```text
my-fall-model/best.pt
```

## 6. YOLO26 训练说明

如果后续要尝试 YOLO26，建议先训练轻量版 `YOLO26n`，再根据验证结果考虑更大模型。

训练 YOLO26n：

```bash
cd fall_detection
python train.py --model yolo26n.pt --epochs 50 --imgsz 640 --batch 16 --device 0 --name fall_yolo26n --export-name fall-yolo26n
```

如果显存不足：

```bash
python train.py --model yolo26n.pt --epochs 50 --imgsz 640 --batch 8 --device 0 --name fall_yolo26n_b8 --export-name fall-yolo26n-b8
```

训练 YOLO26s 时建议从 `batch=8` 开始：

```bash
python train.py --model yolo26s.pt --epochs 50 --imgsz 640 --batch 8 --device 0 --name fall_yolo26s --export-name fall-yolo26s
```

迁移到 YOLO26 前建议完成：

1. YOLO26 需要目标测试机/训练机安装的 `ultralytics` 版本支持对应模型。
2. YOLO26 不能直接复用旧 YOLOv8 权重，需要重新训练。
3. 是否替换现有最佳模型，需要用验证集和样例视频重新比较。

## 7. 数据和模型说明

```text
fall_detection/assets/
```

模型目录。推理界面会自动读取 `assets/*/best.pt`。

```text
fall_detection/data/fall_dataset/
```

当前主训练集。

```text
fall_detection/data/transform/
```

原始视频、抽帧、人工标注和混合数据，保留用于后续补充训练集。

```text
fall_detection/data/yolo_dataset/
```

早期 YOLO 数据集，作为历史数据资产保留。

```text
fall_detection/data/samples/
```

推理测试图片和视频。

```text
fall_detection/outputs/
```

推理输出结果。

## 8. 常见问题

如果界面模型列表为空，请确认模型文件位于：

```text
fall_detection/assets/<模型名称>/best.pt
```

如果训练时显存不足，优先降低 `--batch`，其次降低 `--imgsz`。

如果 `torch.cuda.is_available()` 为 `False`，请重新安装与显卡 CUDA 版本匹配的 PyTorch。
