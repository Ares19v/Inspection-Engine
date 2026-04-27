"""
Inspection Engine — Centralized Configuration
All hardcoded values live here. Change once, reflected everywhere.
"""
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# This file lives at: backend/app/config.py
# Parents: [0] app/  [1] backend/  [2] project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
WEIGHTS_DIR  = PROJECT_ROOT / "runs" / "detect" / "inspection_engine_final3" / "weights"

# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------
CONFIDENCE_THRESHOLD  = 0.4   # Minimum confidence to report a detection
LIVE_JPEG_QUALITY     = 80    # JPEG quality for live-stream frames (speed)
STATIC_JPEG_QUALITY   = 88    # JPEG quality for static-analysis frames (clarity)

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
CAMERA_INDEX = 0     # OpenCV device index (0 = default/first webcam)
CAMERA_FPS   = 60    # Target capture FPS

# ---------------------------------------------------------------------------
# AI Subprocess
# ---------------------------------------------------------------------------
AI_RECONNECT_DELAY = 3   # Seconds to wait before retrying a dropped WS connection

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000
