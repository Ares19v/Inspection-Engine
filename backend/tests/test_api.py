"""
API test suite for Inspection Engine backend.

All heavy GPU/camera dependencies (cv2, ultralytics, torch, multiprocessing)
are patched out using sys.modules stubs BEFORE importing the FastAPI app.
This lets the full test suite run in any CPU-only CI environment (GitHub Actions,
local dev machines without a GPU, etc.) without needing real hardware.
"""

import sys
import base64
from io import BytesIO
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# ─── Stub out every heavy/GPU dependency ─────────────────────────────────────
# These must be set before `from app.main import app` is evaluated.

# cv2 stub
_cv2 = MagicMock()
_cv2.VideoCapture = MagicMock()
_cv2.IMREAD_COLOR = 1
_cv2.CAP_DSHOW = 700
_cv2.CAP_PROP_FRAME_WIDTH = 3
_cv2.CAP_PROP_FRAME_HEIGHT = 4
_cv2.IMWRITE_JPEG_QUALITY = 1
# imencode returns (success_bool, numpy_buffer)
_cv2.imencode = MagicMock(
    return_value=(True, np.frombuffer(b"\xff\xd8\xff\xd9", dtype=np.uint8))
)
# imdecode returns a fake 480x640 BGR frame
_cv2.imdecode = MagicMock(
    return_value=np.zeros((480, 640, 3), dtype=np.uint8)
)
sys.modules["cv2"] = _cv2

# ultralytics stub
_yolo_instance = MagicMock()
_yolo_instance.names = {0: "open", 1: "short", 2: "copper"}
_fake_result = MagicMock()
_fake_result.boxes.cls = []
_fake_result.plot = MagicMock(return_value=np.zeros((480, 640, 3), dtype=np.uint8))
_yolo_instance.return_value = [_fake_result]          # model(frame) → [result]
_yolo_instance.predict = MagicMock(return_value=[_fake_result])

_ultralytics = MagicMock()
_ultralytics.YOLO = MagicMock(return_value=_yolo_instance)
sys.modules["ultralytics"] = _ultralytics

# torch / tensorrt stubs (not used directly by the endpoints, but imported transitively)
sys.modules["torch"] = MagicMock()
sys.modules["tensorrt"] = MagicMock()

# websockets stub (used inside run_ai_eye subprocess — never called in tests)
sys.modules["websockets"] = MagicMock()

# ─── Now it's safe to import the FastAPI app ─────────────────────────────────
with patch("multiprocessing.Process"):          # prevent the AI subprocess from spawning
    from app.main import app, get_static_model  # noqa: E402

from starlette.testclient import TestClient      # noqa: E402


# ─── Shared fixture ──────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def client():
    """Provides a synchronous ASGI TestClient for all tests in this module."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ─── /health ─────────────────────────────────────────────────────────────────
class TestHealthEndpoint:
    def test_returns_200(self, client: TestClient):
        """Health endpoint must always return HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_response_is_json(self, client: TestClient):
        response = client.get("/health")
        assert response.headers["content-type"].startswith("application/json")

    def test_required_fields_present(self, client: TestClient):
        """Response must contain status, engine_ready, and pt_ready keys."""
        data = client.get("/health").json()
        assert "status" in data,        "Missing 'status' field"
        assert "engine_ready" in data,  "Missing 'engine_ready' field"
        assert "pt_ready" in data,      "Missing 'pt_ready' field"

    def test_status_value_is_ok(self, client: TestClient):
        data = client.get("/health").json()
        assert data["status"] == "ok", f"Expected 'ok', got {data['status']!r}"

    def test_engine_ready_is_boolean(self, client: TestClient):
        data = client.get("/health").json()
        assert isinstance(data["engine_ready"], bool)

    def test_pt_ready_is_boolean(self, client: TestClient):
        data = client.get("/health").json()
        assert isinstance(data["pt_ready"], bool)


# ─── /analyze ────────────────────────────────────────────────────────────────
# A minimal valid 1×1 JPEG (avoids depending on Pillow in CI)
_MINIMAL_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n"
    b"\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d"
    b"\x1a\x1c\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.342\x1e64"
    b"2\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f"
    b"\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01"
    b"\x00\x00?\x00\xfb\xd2\x8a(\x03\xff\xd9"
)


class TestAnalyzeEndpoint:
    def test_missing_file_returns_422(self, client: TestClient):
        """Calling /analyze with no file must return 422 Unprocessable Entity."""
        response = client.post("/analyze")
        assert response.status_code == 422

    def test_valid_image_returns_200(self, client: TestClient):
        """A valid JPEG upload must return HTTP 200."""
        with patch("app.main.get_static_model", return_value=_yolo_instance):
            response = client.post(
                "/analyze",
                files={"file": ("test_pcb.jpg", _MINIMAL_JPEG, "image/jpeg")},
            )
        assert response.status_code == 200

    def test_response_contains_image_field(self, client: TestClient):
        """Response JSON must include an 'image' field (Base64 JPEG)."""
        with patch("app.main.get_static_model", return_value=_yolo_instance):
            data = client.post(
                "/analyze",
                files={"file": ("test_pcb.jpg", _MINIMAL_JPEG, "image/jpeg")},
            ).json()
        assert "image" in data, "Response missing 'image' field"

    def test_response_contains_defects_field(self, client: TestClient):
        """Response JSON must include a 'defects' list."""
        with patch("app.main.get_static_model", return_value=_yolo_instance):
            data = client.post(
                "/analyze",
                files={"file": ("test_pcb.jpg", _MINIMAL_JPEG, "image/jpeg")},
            ).json()
        assert "defects" in data,             "Response missing 'defects' field"
        assert isinstance(data["defects"], list), "'defects' must be a list"

    def test_image_field_is_valid_base64(self, client: TestClient):
        """The 'image' field must be a valid Base64-encoded string."""
        with patch("app.main.get_static_model", return_value=_yolo_instance):
            data = client.post(
                "/analyze",
                files={"file": ("test_pcb.jpg", _MINIMAL_JPEG, "image/jpeg")},
            ).json()
        try:
            base64.b64decode(data["image"])
        except Exception as exc:
            pytest.fail(f"'image' field is not valid Base64: {exc}")

    def test_clean_board_returns_empty_defects(self, client: TestClient):
        """When YOLO detects nothing, defects list must be empty."""
        clean_result = MagicMock()
        clean_result.boxes.cls = []
        clean_result.plot = MagicMock(
            return_value=np.zeros((480, 640, 3), dtype=np.uint8)
        )
        clean_model = MagicMock()
        clean_model.return_value = [clean_result]
        clean_model.names = {0: "open"}

        with patch("app.main.get_static_model", return_value=clean_model):
            data = client.post(
                "/analyze",
                files={"file": ("clean.jpg", _MINIMAL_JPEG, "image/jpeg")},
            ).json()
        assert data["defects"] == [], f"Expected empty defects, got {data['defects']}"

    def test_defective_board_returns_defect_names(self, client: TestClient):
        """When YOLO detects defects, their class names must appear in the response."""
        import torch
        defective_result = MagicMock()
        defective_result.boxes.cls = [0, 1]   # open, short
        defective_result.plot = MagicMock(
            return_value=np.zeros((480, 640, 3), dtype=np.uint8)
        )
        defective_model = MagicMock()
        defective_model.return_value = [defective_result]
        defective_model.names = {0: "open", 1: "short"}

        with patch("app.main.get_static_model", return_value=defective_model):
            data = client.post(
                "/analyze",
                files={"file": ("defective.jpg", _MINIMAL_JPEG, "image/jpeg")},
            ).json()
        assert "open" in data["defects"],  "Expected 'open' in defects"
        assert "short" in data["defects"], "Expected 'short' in defects"
