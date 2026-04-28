from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import multiprocessing
import cv2
import base64
import json
import asyncio
import numpy as np
from ultralytics import YOLO
import threading

from app.config import (
    WEIGHTS_DIR,
    CONFIDENCE_THRESHOLD,
    LIVE_JPEG_QUALITY,
    STATIC_JPEG_QUALITY,
    CAMERA_INDEX,
    CAMERA_FPS,
    AI_RECONNECT_DELAY,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Spawn the AI Eye subprocess on startup; it is daemon=True so it dies with the server."""
    p = multiprocessing.Process(target=run_ai_eye, daemon=True)
    p.start()
    print("[BACKEND] AI Eye process started.")
    yield
    # Nothing explicit to clean up — daemon process exits automatically

app = FastAPI(title="Inspection Engine", version="1.2", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# CONNECTION MANAGER  (auto-prunes dead connections on every broadcast)
# ---------------------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        dead: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(connection)
        for conn in dead:
            self.active_connections.remove(conn)

manager = ConnectionManager()

# ---------------------------------------------------------------------------
# MULTI-THREADED CAMERA CLASS
# ---------------------------------------------------------------------------
class VideoStream:
    def __init__(self):
        import sys
        if sys.platform == "win32":
            # On Windows, DSHOW is far more stable than the default MSMF backend
            # which can throw -1072875772 (MF_E_INVALIDMEDIATYPE) on some cameras.
            self.cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(CAMERA_INDEX)
        else:
            # On Linux/macOS (including Docker), use the default backend (V4L2/AVFoundation)
            self.cap = cv2.VideoCapture(CAMERA_INDEX)

        if not self.cap.isOpened():
            raise RuntimeError(
                f"Camera at index {CAMERA_INDEX} could not be opened. "
                "Check your USB/webcam connection and try again."
            )

        # Explicitly request 640x480 — universally supported, prevents invalid
        # media type crashes or black screens on unsupported hardware.
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.ret, self.frame = self.cap.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            self.ret, self.frame = self.cap.read()
            # If the frame failed to read, sleep briefly to avoid pegging the CPU
            if not self.ret:
                import time
                time.sleep(0.01)

    def read(self):
        return self.frame if self.ret else None

    def stop(self):
        self.stopped = True
        self.cap.release()

# ---------------------------------------------------------------------------
# LIVE AI ENGINE  (runs as a separate multiprocessing.Process)
# ---------------------------------------------------------------------------
def run_ai_eye():
    """
    Spawned on FastAPI startup. Reads the webcam, runs YOLO inference,
    and streams annotated frames to /ws_internal with full reconnect recovery.
    """
    # Re-import config inside the subprocess (multiprocessing needs it)
    from app.config import (
        WEIGHTS_DIR, CONFIDENCE_THRESHOLD, LIVE_JPEG_QUALITY, AI_RECONNECT_DELAY
    )

    engine_path = WEIGHTS_DIR / "best.engine"
    pt_path     = WEIGHTS_DIR / "best.pt"

    if engine_path.exists():
        model = YOLO(str(engine_path), task='detect')
        print("[AI EYE] Loaded TensorRT engine.")
    elif pt_path.exists():
        model = YOLO(str(pt_path))
        print("[AI EYE] TensorRT engine not found — loaded PyTorch weights.")
    else:
        print(f"[AI EYE] FATAL: No model weights found in {WEIGHTS_DIR}")
        return

    try:
        stream = VideoStream().start()
    except RuntimeError as e:
        print(f"[AI EYE] FATAL: {e}")
        return

    import websockets

    async def stream_proc():
        while True:                                          # Outer reconnect loop
            try:
                async with websockets.connect("ws://127.0.0.1:8000/ws_internal") as ws:
                    print("[AI EYE] Connected to internal WebSocket. Streaming...")
                    while True:
                        frame = stream.read()
                        if frame is None:
                            await asyncio.sleep(0.01)
                            continue

                        results   = model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False, device=0)
                        annotated = results[0].plot()

                        _, buffer = cv2.imencode(
                            '.jpg', annotated,
                            [cv2.IMWRITE_JPEG_QUALITY, LIVE_JPEG_QUALITY]
                        )
                        img_str = base64.b64encode(buffer).decode('utf-8')

                        payload = {
                            "image":   img_str,
                            "defects": [model.names[int(c)] for c in results[0].boxes.cls]
                        }
                        await ws.send(json.dumps(payload))
                        await asyncio.sleep(0.001)

            except Exception as e:
                print(f"[AI EYE] Stream error: {e}. Reconnecting in {AI_RECONNECT_DELAY}s...")
                await asyncio.sleep(AI_RECONNECT_DELAY)

    asyncio.run(stream_proc())

# ---------------------------------------------------------------------------
# STATIC ANALYSIS — lazy-loaded model for one-shot HTTP requests
# ---------------------------------------------------------------------------
_static_model: YOLO | None = None

def get_static_model() -> YOLO:
    global _static_model
    if _static_model is None:
        engine_path = WEIGHTS_DIR / "best.engine"
        pt_path     = WEIGHTS_DIR / "best.pt"
        if engine_path.exists():
            _static_model = YOLO(str(engine_path), task='detect')
        elif pt_path.exists():
            _static_model = YOLO(str(pt_path))
        else:
            raise FileNotFoundError(f"No model weights found in {WEIGHTS_DIR}")
    return _static_model

# ---------------------------------------------------------------------------
# HTTP ENDPOINTS
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    """Quick liveness check used by the frontend before opening a WebSocket."""
    return {
        "status": "ok",
        "model_dir": str(WEIGHTS_DIR),
        "engine_ready": (WEIGHTS_DIR / "best.engine").exists(),
        "pt_ready":     (WEIGHTS_DIR / "best.pt").exists(),
    }

@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """
    Static analysis endpoint.
    Accepts a PCB image, runs YOLO inference, and returns an annotated
    JPEG (Base64) together with a list of detected defect class names.
    """
    model = get_static_model()

    contents = await file.read()
    nparr    = np.frombuffer(contents, np.uint8)
    frame    = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        return {"error": "Could not decode image. Please upload a valid JPEG or PNG."}

    results   = model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)
    annotated = results[0].plot()

    _, buffer = cv2.imencode(
        '.jpg', annotated,
        [cv2.IMWRITE_JPEG_QUALITY, STATIC_JPEG_QUALITY]
    )
    img_b64 = base64.b64encode(buffer).decode('utf-8')
    defects = [model.names[int(c)] for c in results[0].boxes.cls]

    return {"image": img_b64, "defects": defects}

# ---------------------------------------------------------------------------
# WEBSOCKET ENDPOINTS
# ---------------------------------------------------------------------------
@app.websocket("/ws")
async def websocket_frontend(websocket: WebSocket):
    """Frontend-facing WebSocket. Receives frames broadcast from ws_internal."""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.websocket("/ws_internal")
async def websocket_internal(websocket: WebSocket):
    """Internal WebSocket. AI subprocess pushes frames here; they are broadcast to all frontends."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        pass

