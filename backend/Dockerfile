# ─── Backend Dockerfile ───────────────────────────────────────────────────────
# Uses NVIDIA CUDA 12.8 base so the TensorRT engine and PyTorch can run on GPU.
# The live camera stream won't work inside Docker (no USB passthrough by default),
# but the full HTTP API (/health, /analyze) and WebSocket broadcast work perfectly.
#
# Requirements:
#   - NVIDIA Container Toolkit installed on the host
#   - docker-compose with `deploy.resources.reservations.devices` GPU support
# ─────────────────────────────────────────────────────────────────────────────

FROM nvidia/cuda:12.8.0-cudnn9-runtime-ubuntu22.04

# Prevent interactive prompts during apt installs
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.11 (stable, widely available on Ubuntu 22.04)
# and system-level OpenCV dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3-pip \
    python3.11-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Make python3.11 the default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

WORKDIR /app

# Install PyTorch nightly with CUDA 12.8 support first (cached layer)
RUN pip install --no-cache-dir --pre torch torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/nightly/cu128

# Install remaining backend dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY . .

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
