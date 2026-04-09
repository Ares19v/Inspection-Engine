from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import multiprocessing
import cv2
import base64
import json
import asyncio
from ultralytics import YOLO
import os

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

# --- INTERNAL CAMERA ENGINE ---
def run_ai_eye():
    # Absolute path to model
    path = os.path.abspath(r"..\runs\detect\inspection_engine_final3\weights\best.pt")
    model = YOLO(path)
    cap = cv2.VideoCapture(0)
    
    # We use a separate sync loop to talk to the local websocket
    import websockets
    import json
    
    async def stream():
        async with websockets.connect("ws://127.0.0.1:8000/ws_internal") as ws:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                
                results = model(frame, conf=0.4, verbose=False)
                annotated = results[0].plot()
                
                _, buffer = cv2.imencode('.jpg', annotated)
                img_str = base64.b64encode(buffer).decode('utf-8')
                
                payload = {
                    "image": img_str,
                    "defects": [model.names[int(c)] for c in results[0].boxes.cls]
                }
                await ws.send(json.dumps(payload))
                await asyncio.sleep(0.01)
                
    asyncio.run(stream())

# WebSocket for the Frontend
@app.websocket("/ws")
async def websocket_frontend(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# WebSocket for the Internal AI Eye
@app.websocket("/ws_internal")
async def websocket_internal(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data) # Forward AI data to Frontend
    except WebSocketDisconnect:
        pass

# Boot up the AI Eye on start
@app.on_event("startup")
async def startup_event():
    p = multiprocessing.Process(target=run_ai_eye, daemon=True)
    p.start()
    print("RTX 5060 AI Eye Initialized and Tied to Backend.")

