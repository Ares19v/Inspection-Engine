# 🏭 Inspection Engine v1.2
**Real-Time PCB Defect Detection System**

An industrial-grade computer vision pipeline designed for high-speed Printed Circuit Board (PCB) quality control. This system leverages state-of-the-art YOLOv11 object detection, communicating over full-duplex WebSockets to a React-based industrial dashboard.

It is heavily optimized for **NVIDIA Blackwell (SM 12.0)** architecture, enabling sub-15ms inference latency at the edge.

---

## 📊 Performance Metrics
- **Core Model:** YOLO11s (Custom Trained)
- **Dataset:** DeepPCB (3,000+ Annotated Images)
- **Mean Average Precision (mAP50):** 97.8%
- **Inference Latency:** ~10-13ms per frame
- **Live Throughput:** 80+ FPS capability

## 🏗️ System Architecture
The project is divided into three asynchronous layers:

1. **The Brain (AI Engine):** Runs on PyTorch Nightly (CUDA 12.8). Uses Python multiprocessing to bypass the GIL and dedicate maximum CPU threads to feeding the RTX 5060 GPU.
2. **The Heart (FastAPI Backend):** Acts as a high-speed router. It accepts raw Base64 image streams and defect tensors from the AI Engine, broadcasting them via WebSockets (ws://127.0.0.1:8000/ws).
3. **The Face (Vite + React UI):** A minimalist, dark-mode terminal tailored for factory floors. Features real-time anomaly logging, dynamic theme switching, and native PDF report generation.

---

## 🚀 Features
- **Live Sensor Feed:** Real-time webcam integration with zero-lag bounding box overlays.
- **Static Analysis Mode:** Upload high-res images for deep scanning.
- **Automated PDF Reporting:** Generate official timestamped inspection logs with a single click.
- **Micro-Theming:** Seamless UI transitions between Carbon, Cobalt, Emerald, and Crimson industrial themes.
- **One-Click Deployment:** Automated batch script (.bat) deployment for zero-touch initialization.

---

## 💻 Local Setup & Installation

### Prerequisites
- Python 3.13+
- Node.js v18+
- NVIDIA GPU (RTX 50-Series / Blackwell recommended)
- CUDA Toolkit 12.8+

### 1. Clone the Repository
\\\ash
git clone https://github.com/YOUR_USERNAME/Inspection-Engine.git
cd "Inspection Engine"
\\\

### 2. Backend Initialization
\\\ash
# Create and activate virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows

# Install Nightly PyTorch for SM_12.0 support
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128

# Install dependencies
pip install fastapi uvicorn ultralytics opencv-python websockets
\\\

### 3. Frontend Initialization
\\\ash
cd frontend
npm install
\\\

### 4. Execution
To launch the entire stack simultaneously, run the included batch file from the project root:
\\\ash
./Run_Inspection_Engine.bat
\\\
Alternatively, navigate to \http://localhost:5173\ once the Vite server is live.

---
*Developed as a Final Year B.Tech Computer Science Project by Devansh Tyagi.*
