import os
import random
from pathlib import Path
from ultralytics import YOLO

# ---------------------------------------------------------------------------
# Paths — anchored to this file's location, not the shell's CWD
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
WEIGHTS_DIR  = PROJECT_ROOT / "runs" / "detect" / "inspection_engine_final3" / "weights"

model_path = WEIGHTS_DIR / "best.pt"
model = YOLO(str(model_path))

# Path to validation images
test_path = PROJECT_ROOT / "DeepPCB-5" / "valid" / "images"
images = [str(p) for p in test_path.glob("*.jpg")]

if len(images) < 25:
    print(f"Warning: only {len(images)} images found in {test_path}. Using all of them.")
    test_batch = images
else:
    test_batch = random.sample(images, 25)

print("\n" + "=" * 60)
print(f"{'IMAGE NAME':<30} | {'DEFECT':<15} | {'CONFIDENCE'}")
print("-" * 60)

# Run prediction without saving files
results = model.predict(source=test_batch, conf=0.5, save=False, verbose=False)

for i, r in enumerate(results):
    img_name = os.path.basename(test_batch[i])

    if len(r.boxes) == 0:
        print(f"{img_name:<30} | {'CLEAN':<15} | {'N/A'}")
    else:
        for box in r.boxes:
            label = model.names[int(box.cls)]
            conf  = float(box.conf)
            print(f"{img_name:<30} | {label:<15} | {conf:.2%}")

print("=" * 60)
print(f"TEST COMPLETE: Processed {len(test_batch)} images.")
