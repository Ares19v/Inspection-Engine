# EVAL — Inspection Engine

> **Evaluation Date:** 2026-05-29  
> **Evaluator:** Automated Portfolio Review  
> **Maturity Level:** Production-Ready / Advanced MVP

---

## 1. Project Purpose & Problem Statement

Inspection Engine addresses a highly demanding industrial automation problem: real-time, automated optical inspection (AOI) of Printed Circuit Boards (PCBs) during manufacturing. Traditional visual inspections are slow, prone to human fatigue, and expensive. General object-detection setups suffer from high latency and fail to register tiny structural anomalies.

This platform bridges the gap by leveraging a custom-trained **YOLOv11s** object detector trained on the **DeepPCB v5** dataset (3,000+ images) to detect 6 micro-defect categories (`copper`, `mousebite`, `open`, `pin-hole`, `short`, and `spur`). By combining full-duplex WebSockets with TensorRT compilation, the system achieves sub-13ms inference latency and throughput exceeding 80 FPS on target GPU hardware, satisfying high-speed conveyor line requirements.

---

## 2. Technical Architecture

The Inspection Engine uses a three-tier, fully asynchronous decoupled architectural pattern communicating via local WebSockets:

1.  **Industrial Frontend (FACE):** A high-performance SPA built with **Vite + React 19**. It features a zero-latency canvas layer with real-time bounding box overlays, dynamic dark-mode industrial themes (Carbon, Cobalt, Emerald, Crimson), persistent session logs, and client-side PDF inspection report generation.
2.  **FastAPI Core (HEART):** Acts as the asynchronous orchestration hub. It maintains two WebSocket endpoints:
    *   `/ws` to broadcast processed video frames (as Base64 JPEGs) and JSON metadata to the frontend.
    *   `/ws_internal` to receive high-speed inference streams from the decoupled AI process.
    *   It also exposes standard HTTP routes `/health` and `/analyze` (for static image evaluation).
3.  **Decoupled AI Brain (BRAIN):** Runs as an independent OS-level process using Python's `multiprocessing.Process`. This prevents python's Global Interpreter Lock (GIL) from blocking network I/O or frame ingestion. It captures raw frames from the DirectShow camera feed, pushes them through the YOLOv11 TensorRT engine (`best.engine` or falls back to `.pt`), and feeds the results back to FastAPI.

---

## 3. Model & Weights Details

*   **Core Architecture:** Ultralytics YOLOv11s (Small).
*   **Training Dataset:** DeepPCB v5 (3,000+ annotated industrial macro-photography images).
*   **Model Weights on Hugging Face:** Available under the repository [devanshty/Inspection-Engine](https://huggingface.co/devanshty/Inspection-Engine).
*   **Download Code Snippet:**
    ```python
    from huggingface_hub import hf_hub_download
    # Download PyTorch weights
    model_path = hf_hub_download(repo_id='devanshty/Inspection-Engine', filename='best.pt')
    ```
*   **Performance Metrics:**
    *   **mAP50:** **97.8%** across all defect classes.
    *   **Inference Latency:** **~10–13 ms** per frame.
    *   **Throughput:** **80+ FPS** using NVIDIA TensorRT on RTX 5060 (Blackwell SM 12.0).
*   **TensorRT Acceleration:** The `.engine` file must be compiled locally using:
    ```python
    from ultralytics import YOLO
    model = YOLO("runs/detect/inspection_engine_final3/weights/best.pt")
    model.export(format="engine", device=0)
    ```

---

## 4. Strengths

*   **Process Isolation:** Decoupling the camera grab/inference loop into an isolated `multiprocessing.Process` completely bypasses python GIL limitations, guaranteeing maximum frame rate stability.
*   **Dual Inference Modes:** Seamless automatic fallback to PyTorch `.pt` if the hardware-specific compiled `.engine` is missing.
*   **Industrial Front-End UX:** Exceedingly clean, responsive industrial dashboards using React 19 with instant PDF reports and live session history.
*   **Zero-Dependency Setup Scripts:** The project includes highly robust, disk-space-conscious scripts:
    *   `INSTALL.bat` which installs PyTorch Nightly with CUDA 12.8 support.
    *   `UNINSTALL.bat` which clears `venv` and `node_modules` instantly, recovering ~8 GB of space.

---

## 5. Limitations & Gaps

*   **Single-Camera Limit:** The backend only supports a single DirectShow camera index capture (`cv2.VideoCapture`). Real factory floors demand multi-camera synchronizations.
*   **No Central DB Persistence:** session anomaly logs exist entirely in-memory on the frontend or backend process during execution. There is no historical database (PostgreSQL/TimescaleDB) for long-term audit trail tracking.
*   **Limited Dynamic Zoom/Calibration:** Pixels are not calibrated to real-world millimeters. The tool lacks spatial grid calibrations to calculate the exact physical dimensions of anomalies.

---

## 6. Code Quality Assessment

*   **Structure:** Exceptionally organized. Modular backend (`backend/app/services/` and `backend/app/api/`) coupled with clear training entry-points (`model_training/`).
*   **Reliability:** The inclusion of automated validation CLI (`test_model.py`) makes validating fresh weights fast and painless.
*   **Cleanliness:** Pinned backend dependency files, clear configuration maps, and consistent logging protocols.

---

## 7. Maturity Breakdown

| Dimension | Score | Notes |
|-----------|-------|-------|
| Functionality | 9/10 | Flawless real-time & static detection, automated reports, multiple dark themes. |
| Code Quality | 9/10 | isolated multiprocessing AI worker, clean react architecture. |
| Documentation | 8/10 | Clear system diagram, math formulas, api refs, training guides. |
| Scalability | 6/10 | Lacks multi-channel camera switching, database logging, or REST integration. |
| Security | 8/10 | Pinned supply chain, zero credentials exposed, completely local operation. |
| **Overall** | **8.0/10** | High-performance industrial AOI application. Highly viable for production with a database layer. |

---

## 8. Suggested Next Steps

1.  **Introduce Multi-Channel Camera Streams:** Expand FastAPI WebSocket orchestration to switch between multiple DirectShow and RTSP IP camera endpoints.
2.  **Add TimescaleDB / PostgreSQL Audit Persistence:** Build a historical analytics dashboard to display defect distributions, yields, and throughput metrics over weeks/months.
3.  **Implement Spatial Calibration:** Enable users to define physical dimensions (e.g., DPI or active viewport boundaries) to report defect sizes in actual millimeters.

---
<p align="center">Made by Devansh Tyagi @ 2026</p>
