from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import multiprocessing
import cv2
import base64
import json
import asyncio
from ultralytics import YOLO
import os
import threading
import time

app = FastAPI()

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
        self.active_connections.remove(websocket)
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# --- MULTI-THREADED CAMERA CLASS ---
class VideoStream:
    def __init__(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) # DirectShow for Windows speed
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FPS, 60)
        self.ret, self.frame = self.cap.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            self.ret, self.frame = self.cap.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.cap.release()

# --- INTERNAL AI ENGINE ---
def run_ai_eye():
    # Use the new .engine file for RTX 5060 TensorRT speed
    path = os.path.abspath(r"..\runs\detect\inspection_engine_final3\weights\best.engine")
    model = YOLO(path, task='detect')
    
    stream = VideoStream().start()
    
    import websockets
    
    async def stream_proc():
        async with websockets.connect("ws://127.0.0.1:8000/ws_internal") as ws:
            while True:
                frame = stream.read()
                if frame is None: continue
                
                # Inference on Blackwell TensorRT
                results = model(frame, conf=0.4, verbose=False, device=0)
                annotated = results[0].plot()
                
                _, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
                img_str = base64.b64encode(buffer).decode('utf-8')
                
                payload = {
                    "image": img_str,
                    "defects": [model.names[int(c)] for c in results[0].boxes.cls]
                }
                await ws.send(json.dumps(payload))
                await asyncio.sleep(0.001) # Near-zero sleep for max FPS
                
    asyncio.run(stream_proc())

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
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        pass

@app.on_event("startup")
async def startup_event():
    p = multiprocessing.Process(target=run_ai_eye, daemon=True)
    p.start()
    print("RTX 5060 HYPER-SPEED AI Eye Initialized.")

