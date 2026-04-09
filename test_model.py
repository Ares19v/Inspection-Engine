import os
import random
from ultralytics import YOLO

# Load the model
model_path = os.path.abspath(r"runs\detect\inspection_engine_final3\weights\best.pt")
model = YOLO(model_path)

# Path to validation images
test_path = r"DeepPCB-5\valid\images"
images = [os.path.join(test_path, f) for f in os.listdir(test_path) if f.endswith('.jpg')]

# Select 25 random images
test_batch = random.sample(images, 25)

print("\n" + "="*60)
print(f"{'IMAGE NAME':<30} | {'DEFECT':<15} | {'CONFIDENCE'}")
print("-" * 60)

# Run prediction without saving files
results = model.predict(source=test_batch, conf=0.5, save=False, verbose=False)

for i, r in enumerate(results):
    img_name = os.path.basename(test_batch[i])
    
    # Check if any defects were found
    if len(r.boxes) == 0:
        print(f"{img_name:<30} | {'CLEAN':<15} | {'N/A'}")
    else:
        for box in r.boxes:
            label = model.names[int(box.cls)]
            conf = float(box.conf)
            print(f"{img_name:<30} | {label:<15} | {conf:.2%}")

print("="*60)
print(f"TEST COMPLETE: Processed 25 images on RTX 5060.")
