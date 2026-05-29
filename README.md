<div align="center">

<h1>🏭 Inspection Engine</h1>

<p><strong>Industrial-Grade Real-Time PCB Defect Detection System</strong></p>

<p>
  <a href="https://github.com/Ares19v/Inspection-Engine/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-22c55e.svg" alt="License: MIT">
  </a>
  <img src="https://img.shields.io/badge/Python-3.13+-3b82f6.svg" alt="Python 3.13+">
  <img src="https://img.shields.io/badge/PyTorch-Nightly-f97316.svg" alt="PyTorch Nightly">
  <img src="https://img.shields.io/badge/CUDA-12.8-76B900.svg" alt="CUDA 12.8">
  <img src="https://img.shields.io/badge/React-19-61DAFB.svg" alt="React 19">
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/mAP50-97.8%25-brightgreen.svg" alt="mAP50: 97.8%">
  <img src="https://img.shields.io/badge/Inference-~12ms-purple.svg" alt="Inference: ~12ms">
</p>

<p>A production-grade computer vision pipeline for high-speed Printed Circuit Board (PCB) quality control.<br>
Powered by a custom-trained <strong>YOLOv11s</strong> model, a <strong>FastAPI</strong> WebSocket backend, and a <strong>React 19</strong> industrial dashboard.<br>
Delivering real-time defect detection at <strong>80+ FPS</strong> on NVIDIA Blackwell hardware.</p>

</div>

---

## ✨ Features

| Feature | Description |
|:--|:--|
| 🎥 **Live Sensor Feed** | Real-time webcam streaming with zero-latency YOLO bounding box overlays |
| 🔍 **Static Analysis Mode** | Upload any PCB image — get back a fully annotated result from the model |
| ⚡ **TensorRT Acceleration** | GPU-compiled `.engine` file for maximum Blackwell SM 12.0 throughput |
| 📊 **Real-Time Anomaly Log** | Live defect feed with timestamps, auto-scrolling, and persistent session history |
| 📄 **PDF Report Generation** | One-click official inspection reports with timestamped anomaly timelog |
| 🎨 **Industrial Themes** | Four dark-mode color profiles: Carbon · Cobalt · Emerald · Crimson |
| 🔌 **Full-Duplex WebSockets** | Zero-copy frame streaming between the AI engine and the React dashboard |
| 🖱️ **One-Click Deployment** | Single `.bat` launch — backend + frontend + browser open, fully automated |
| 📦 **One-Click Install/Uninstall** | Save ~8 GB of disk space when not in use; restore the full stack in minutes |

---

## 📊 Performance

| Metric | Value |
|:--|:--|
| **Model Architecture** | YOLOv11s (Small) |
| **Training Dataset** | DeepPCB v5 · 3,000+ Annotated Images · CC BY 4.0 |
| **mAP50** | **97.8%** |
| **Inference Backend** | NVIDIA TensorRT (`.engine`) |
| **Inference Latency** | **~10–13 ms / frame** |
| **Live Throughput** | **80+ FPS** |
| **Target GPU** | NVIDIA RTX 5060 (Blackwell SM 12.0) |

---

## 🏗️ Architecture

The system is split into three fully asynchronous layers communicating over WebSockets:

```
┌─────────────────────────────────────────────────────────────┐
│  FACE — Vite + React 19  (localhost:5173)                   │
│  Industrial dark-mode dashboard                             │
│  Live feed · Anomaly log · Theme switcher · PDF export      │
└──────────────────────┬──────────────────────────────────────┘
                       │  ws://127.0.0.1:8000/ws
┌──────────────────────▼──────────────────────────────────────┐
│  HEART — FastAPI  (127.0.0.1:8000)                          │
│  /ws          → Frontend WebSocket (broadcaster)            │
│  /ws_internal → Internal AI pipe (receiver)                 │
│  POST /analyze → Static image analysis endpoint             │
│  GET  /health  → Liveness + model status check             │
└──────────────────────┬──────────────────────────────────────┘
                       │  ws://127.0.0.1:8000/ws_internal
┌──────────────────────▼──────────────────────────────────────┐
│  BRAIN — AI Inference Engine  (multiprocessing.Process)     │
│  DirectShow webcam capture → YOLO11s TensorRT               │
│  Annotated JPEG (Base64) → JSON {image, defects[]}          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔬 Defect Classes

Trained to detect **6 PCB defect categories** from the DeepPCB dataset:

| Class | Description |
|:--|:--|
| `copper` | Excess or missing copper on the PCB surface |
| `mousebite` | Partial break along the edge of the board |
| `open` | Broken trace causing an open circuit |
| `pin-hole` | Pinhole void drilled through the copper layer |
| `short` | Unintended conductive connection between traces |
| `spur` | Spurious copper protrusion from a trace |

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Minimum Version |
|:--|:--|
| OS | Windows 10 / 11 |
| Python | 3.13+ |
| Node.js | v18+ |
| GPU | NVIDIA RTX (Blackwell recommended) |
| CUDA Toolkit | 12.8+ |

### Step 1 — Clone

```bash
git clone https://github.com/Ares19v/Inspection-Engine.git
cd "Inspection Engine"
```

### Step 2 — One-Click Install

Double-click **`INSTALL.bat`** (or run from a terminal):

```bat
.\INSTALL.bat
```

This automatically:
- Creates a Python `venv`
- Installs **PyTorch Nightly** with CUDA 12.8 (Blackwell SM 12.0 support)
- Installs all backend dependencies from `backend/requirements.txt`
- Installs all frontend packages via `npm install`

> **Disk usage:** ~7–10 GB · **Time:** ~5–15 min depending on internet speed

### Step 3 — Launch

Double-click **`Run_Inspection_Engine.bat`**:

```bat
.\Run_Inspection_Engine.bat
```

The full stack starts automatically and your browser opens to `http://localhost:5173`.

---

## 🗑️ Uninstall / Free Disk Space

When you don't need the project running, free up ~8 GB instantly:

```bat
.\UNINSTALL.bat
```

This removes `venv/` and `frontend/node_modules/` — **your code, model weights, and configs are completely safe.**  
Run `INSTALL.bat` again to restore the full environment in minutes.

---

## 📡 API Reference

### WebSocket Endpoints

| Endpoint | Direction | Payload |
|:--|:--|:--|
| `ws://127.0.0.1:8000/ws` | Server → Client | `{ image: string (base64 JPEG), defects: string[] }` |
| `ws://127.0.0.1:8000/ws_internal` | AI Engine → Server | Same as above (internal pipe) |

### HTTP Endpoints

| Method | Endpoint | Description |
|:--|:--|:--|
| `GET` | `/health` | Liveness check + model file status |
| `POST` | `/analyze` | Static PCB image analysis |

#### `GET /health` — Response

```json
{
  "status": "ok",
  "model_dir": "...\\runs\\detect\\inspection_engine_final3\\weights",
  "engine_ready": true,
  "pt_ready": true
}
```

#### `POST /analyze` — Request

`multipart/form-data` with field `file` (JPEG or PNG image of a PCB)

#### `POST /analyze` — Response

```json
{
  "image": "<base64-encoded annotated JPEG>",
  "defects": ["open", "short"]
}
```

---

## 🧪 Running Model Tests

```bash
# Activate the virtual environment
.\venv\Scripts\activate

# Run batch inference on 25 random validation images
python test_model.py
```

Sample output:

```
============================================================
IMAGE NAME                     | DEFECT          | CONFIDENCE
------------------------------------------------------------
00041003_test.jpg              | open            | 94.21%
00041015_test.jpg              | CLEAN           | N/A
00041028_test.jpg              | short           | 89.47%
00041044_test.jpg              | mousebite       | 96.83%
============================================================
TEST COMPLETE: Processed 25 images.
```

---

## 🧠 Training Your Own Model

The full training pipeline is included in `model_training/`:

```bash
.\venv\Scripts\activate
cd model_training
python train.py
```

This downloads the DeepPCB v5 dataset from Roboflow and fine-tunes `yolo11s.pt` for 50 epochs with early stopping. Results are saved to `runs/detect/`.

### Exporting to TensorRT

The `.engine` file is machine-specific (compiled for your exact GPU) and is **not** included in this repository. After training, export it from the `.pt` weights:

```python
from ultralytics import YOLO
model = YOLO("runs/detect/inspection_engine_final3/weights/best.pt")
model.export(format="engine", device=0)
```

> The backend automatically falls back to the `.pt` file if no `.engine` is present — no extra configuration needed.

---

## 📁 Project Structure

```
Inspection Engine/
│
├── 📂 backend/
│   ├── requirements.txt         # Pinned Python dependencies
│   └── 📂 app/
│       ├── main.py              # FastAPI server, WebSocket routing, AI spawn
│       ├── config.py            # Centralized config (ports, paths, thresholds)
│       ├── 📂 api/              # Route handlers (extensible)
│       └── 📂 services/         # Business logic layer (extensible)
│
├── 📂 frontend/
│   └── 📂 src/
│       └── App.jsx              # Full React 19 industrial dashboard
│
├── 📂 model_training/
│   ├── train.py                 # YOLO fine-tuning script (Roboflow + GPU)
│   └── download_data.py         # Dataset download helper
│
├── 📂 runs/detect/
│   └── inspection_engine_final3/
│       └── weights/
│           ├── best.pt          # ✅ Trained PyTorch weights (in repo)
│           └── best.engine      # ⚡ TensorRT engine (gitignored, generate locally)
│
├── test_model.py                # Batch validation CLI
│
├── INSTALL.bat                  # ⬇️  One-click full installation
├── UNINSTALL.bat                # 🗑️  One-click dependency cleanup
├── Run_Inspection_Engine.bat    # 🚀  One-click launcher (full stack)
│
├── LICENSE
└── README.md
```

---

## 🗺️ Roadmap

- [x] Real-time live webcam inference
- [x] Static image upload + analysis
- [x] TensorRT acceleration (Blackwell SM 12.0)
- [x] WebSocket full-duplex streaming
- [x] PDF inspection report generation
- [x] Multi-theme industrial dashboard
- [x] One-click install / uninstall
- [ ] Multi-camera channel switching
- [ ] Historical analytics with trend graphs
- [ ] Docker containerization
- [ ] REST API for programmatic batch submission
- [ ] ONNX export for cross-platform deployment

---

## 📜 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

<div align="center">
  <sub>Developed as a Final Year B.Tech Computer Science Project by <a href="https://github.com/Ares19v">Devansh Tyagi</a></sub>
</div>

---
<p align="center">
  Made by Devansh Tyagi @ 2026
</p>

## 🤗 Model on Hugging Face

The trained model is available on Hugging Face: [devanshty/Inspection-Engine](https://huggingface.co/devanshty/Inspection-Engine)

### Download

```python
from huggingface_hub import hf_hub_download
model_path = hf_hub_download(repo_id='devanshty/Inspection-Engine', filename='best.pt')
```
