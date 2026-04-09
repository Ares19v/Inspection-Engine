import cv2
import asyncio
import websockets
import json
import base64
import os
from ultralytics import YOLO

# Absolute path to your best-performing brain
weight_path = os.path.abspath(r"runs\detect\inspection_engine_final3\weights\best.pt")
model = YOLO(weight_path)

async def stream_camera():
    uri = "ws://127.0.0.1:8000/ws"
    try:
        async with websockets.connect(uri) as websocket:
            cap = cv2.VideoCapture(0)
            print("AI Eye Active. Streaming to Dashboard...")
            
            while cap.isOpened():
                success, frame = cap.read()
                if not success: break
                
                results = model(frame, conf=0.4) # Slightly lower conf for more detections
                annotated_frame = results[0].plot()
                
                _, buffer = cv2.imencode('.jpg', annotated_frame)
                jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                
                data = {
                    "image": jpg_as_text,
                    "defects": [model.names[int(c)] for c in results[0].boxes.cls]
                }
                
                await websocket.send(json.dumps(data))
                await asyncio.sleep(0.01)
            cap.release()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(stream_camera())
