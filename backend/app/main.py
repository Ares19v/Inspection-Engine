from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import multiprocessing
import cv2
import base64
import json
import struct
import time
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
    p = multiprocessing.Process(target=run_ai_eye, daemon=True)
    p.start()
    print("[BACKEND] AI Eye process started.")
    yield

app = FastAPI(title="Inspection Engine", version="1.3", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_bytes(self, data: bytes):
        dead: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_bytes(data)
            except Exception:
                dead.append(connection)
        for conn in dead:
            self.active_connections.remove(conn)

    async def broadcast_text(self, message: str):
        dead: list[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(connection)
        for conn in dead:
            self.active_connections.remove(conn)

manager = ConnectionManager()

class VideoStream:
    def __init__(self):
        import sys
        if sys.platform == "win32":
            self.cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(CAMERA_INDEX)
        else:
            self.cap = cv2.VideoCapture(CAMERA_INDEX)

        if not self.cap.isOpened():
            raise RuntimeError(
                f"Camera at index {CAMERA_INDEX} could not be opened. "
                "Check your USB/webcam connection and try again."
            )

        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

        self.ret, self.frame = self.cap.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            self.ret, self.frame = self.cap.read()
            if not self.ret:
                time.sleep(0.005)

    def read(self):
        return self.frame if self.ret else None

    def stop(self):
        self.stopped = True
        self.cap.release()

def run_ai_eye():
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
        print("[AI EYE] TensorRT engine not found - loaded PyTorch weights.")
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
        while True:
            try:
                async with websockets.connect("ws://127.0.0.1:8000/ws_internal") as ws:
                    print("[AI EYE] Connected to internal WebSocket. Streaming...")
                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, LIVE_JPEG_QUALITY, cv2.IMWRITE_JPEG_OPTIMIZE, 0]
                    
                    while True:
                        frame = stream.read()
                        if frame is None:
                            await asyncio.sleep(0.005)
                            continue

                        results = model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False, device=0)
                        annotated = results[0].plot()

                        _, buffer = cv2.imencode('.jpg', annotated, encode_params)
                        jpeg_bytes = buffer.tobytes()

                        detections = []
                        boxes = results[0].boxes
                        if boxes is not None and len(boxes) > 0:
                            for box in boxes:
                                coords = [round(float(x), 1) for x in box.xyxy[0].tolist()]
                                conf_val = round(float(box.conf[0]), 3)
                                cls_id = int(box.cls[0])
                                label = model.names[cls_id]
                                detections.append({
                                    "bbox": coords,
                                    "conf": conf_val,
                                    "label": label
                                })

                        metadata = {
                            "detections": detections,
                            "defects": [d["label"] for d in detections],
                            "count": len(detections),
                            "timestamp": time.time()
                        }
                        header_bytes = json.dumps(metadata).encode('utf-8')

                        packet = struct.pack('<HI', len(detections), len(header_bytes)) + header_bytes + jpeg_bytes
                        await ws.send(packet)
                        await asyncio.sleep(0.001)

            except Exception as e:
                print(f"[AI EYE] Stream error: {e}. Reconnecting in {AI_RECONNECT_DELAY}s...")
                await asyncio.sleep(AI_RECONNECT_DELAY)

    asyncio.run(stream_proc())

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

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_dir": str(WEIGHTS_DIR),
        "engine_ready": (WEIGHTS_DIR / "best.engine").exists(),
        "pt_ready":     (WEIGHTS_DIR / "best.pt").exists(),
    }

@app.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
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

    detections = []
    boxes = results[0].boxes
    if boxes is not None and len(boxes) > 0:
        for box in boxes:
            coords = [round(float(x), 1) for x in box.xyxy[0].tolist()]
            conf_val = round(float(box.conf[0]), 3)
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            detections.append({
                "bbox": coords,
                "conf": conf_val,
                "label": label
            })

    defects = [d["label"] for d in detections]

    return {
        "image": img_b64,
        "defects": defects,
        "detections": detections,
        "count": len(detections)
    }

@app.websocket("/ws")
async def websocket_frontend(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.websocket("/ws_internal")
async def websocket_internal(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            await manager.broadcast_bytes(data)
    except WebSocketDisconnect:
        pass
