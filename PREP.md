# 🏭 Inspection Engine Study Guide (From-Scratch)

Welcome to the beginner's learning guide for **Inspection Engine**, an industrial-grade real-time PCB defect detection platform! This guide will take you step-by-step through how computer vision, multiprocessing, WebSockets, and modern web frameworks work together.

---

## 🗺️ Architectural Map

Inspection Engine consists of three main components communicating with low latency:
```
┌──────────────────────────────────────┐
│  Vite + React 19 Frontend            │
│  - Displays live camera feeds        │
│  - Logs defects and exports PDFs     │
└──────────────────┬───────────────────┘
                   │ WebSocket (ws://)
┌──────────────────▼───────────────────┐
│  FastAPI Backend Core                │
│  - Routes image/JSON payloads        │
│  - Directs raw streams               │
└──────────────────┬───────────────────┘
                   │ Internal WebSocket
┌──────────────────▼───────────────────┐
│  AI Inference Engine (Multiprocessing)│
│  - Captures video frames             │
│  - Performs YOLOv11s inference       │
└──────────────────────────────────────┘
```

### Why Multiprocessing?
In Python, the **Global Interpreter Lock (GIL)** restricts execution to a single thread at a time. If the backend server had to capture video frames, run machine learning models, and handle client network connections in a single thread, the frame rate would drop significantly.
By using `multiprocessing.Process`, we run the AI Inference Engine in a **completely separate OS process** that communicates with the main FastAPI server over a fast local WebSocket (`/ws_internal`). This ensures a solid **80+ FPS** performance!

---

## 🔍 The AI Model: YOLOv11s

*   **Architecture:** YOLOv11s (Small variant). YOLO stands for "You Only Look Once" — it predicts bounding boxes and class probabilities in a single pass through the neural network.
*   **Dataset:** DeepPCB v5, containing over 3,000 annotated images of PCBs with micro-defects.
*   **Defect Categories:**
    1.  `copper` — Missing or extra copper.
    2.  `mousebite` — Small edge bites on the board.
    3.  `open` — Traces that are broken, resulting in an open circuit.
    4.  `pin-hole` — Voids drilled through the copper paths.
    5.  `short` — Traces that touch where they shouldn't, forming short circuits.
    6.  `spur` — Small unwanted copper spikes extending from traces.

### Compilation to TensorRT
To speed up execution on NVIDIA GPUs, we compile PyTorch models (`best.pt`) to a TensorRT `.engine` file. TensorRT optimizes layers, merges kernels, and compiles the model specifically to your GPU chip's architecture, speeding up processing to **10-13ms per frame**!

---

## 🛠️ Step-by-Step Local Deployment

Let's get the application up and running on your local machine:

### 1. One-Click Setup (Windows)
*   **Install:** Double-click `INSTALL.bat`. This creates a Python `venv` using PyTorch Nightly with CUDA 12.8, and installs all packages for React and FastAPI.
*   **Run:** Double-click `Run_Inspection_Engine.bat`. It starts both the frontend and backend servers and automatically opens `http://localhost:5173`.
*   **Clean Up:** Run `UNINSTALL.bat` to clear the environment folders (`venv/` and `node_modules/`), freeing up ~8 GB of space.

### 2. Manual Commands
If you want to run the parts individually:

**Backend Setup:**
```bash
cd backend
python -m venv venv
# Activate the venv
.\venv\Scripts\activate
# Install requirements
pip install -r requirements.txt
# Run FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Frontend Setup:**
```bash
cd frontend
npm install
npm run dev
```
Open your browser to `http://localhost:5173` to explore the industrial dashboard!
