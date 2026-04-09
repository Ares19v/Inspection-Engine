import os
from roboflow import Roboflow
from ultralytics import YOLO

def train_model():
    # 1. Access the dataset
    rf = Roboflow(api_key="YOUR_ROBOFLOW_API_KEY")
    project = rf.workspace("tack-hwa-wong-zak5u").project("deeppcb-4dhir")
    dataset = project.version(5).download("yolov11")

    # 2. Use YOLO11s (Small)
    model = YOLO("yolo11s.pt") 

    # 3. High-Resolution GPU Training
    print("Inspection Engine: IGNITING RTX 5060 (Blackwell) FOR TRAINING...")
    model.train(
        data=os.path.join(dataset.location, "data.yaml"),
        epochs=50,
        imgsz=640,
        device=0,
        name="inspection_engine_final",
        patience=10,
        save=True,
        workers=4
    )

if __name__ == '__main__':
    train_model()
