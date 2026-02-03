# ==========================================
# High-Speed Camera Testing - Docker Image
# ==========================================
# Supports: MindVision cameras (USB/GigE) + Webcam fallback
# Platforms: linux/amd64 (x86_64)
#
# Usage:
#   docker build -t high-speed-camera .
#   docker run --privileged -v /dev/video0:/dev/video0 -p 7860:7860 high-speed-camera
#
# For GigE cameras:
#   docker run --network host -p 7860:7860 high-speed-camera --camera-ip 169.254.22.149
# ==========================================

# ------------------------------------------
# Stage 1: Builder
# ------------------------------------------
FROM python:3.13-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies
RUN uv venv /opt/venv && \
    uv pip install --no-cache --python /opt/venv/bin/python -e "."

# ------------------------------------------
# Stage 2: Runtime
# ------------------------------------------
FROM python:3.13-slim-bookworm AS runtime

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    v4l-utils \
    # Network tools for GigE camera support
    iputils-ping \
    net-tools \
    iproute2 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r camera && useradd -r -g camera -m -s /bin/bash camerauser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
WORKDIR /app
COPY --chown=camerauser:camera . .

# Ensure Linux SDK library is accessible
# The SDK is bundled in spec/Linux_sdk_x64/lib/x64/libMVSDK.so
# mvsdk.py will detect and load it automatically
RUN if [ -f /app/spec/Linux_sdk_x64/lib/x64/libMVSDK.so ]; then \
        echo "Linux SDK found"; \
        chmod +x /app/spec/Linux_sdk_x64/lib/x64/libMVSDK.so; \
    else \
        echo "WARNING: Linux SDK not found!"; \
    fi

# Create clips directory with proper permissions
RUN mkdir -p /app/clips && chown -R camerauser:camera /app/clips

# Switch to non-root user
USER camerauser

# Expose Gradio port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/')" || exit 1

# Default command
ENTRYPOINT ["python", "main.py"]
CMD ["--port", "7860"]
