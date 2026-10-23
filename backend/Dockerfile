# ==============================================================================
# Multi-stage Dockerfile for FastAPI Backend (MASDS)
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Builder
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build dependencies for compiled extensions and database adapters
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies list and compile user packages
COPY requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt

# ------------------------------------------------------------------------------
# Stage 2: Runtime
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/app/.local/bin:${PATH}" \
    PYTHONPATH=/app

WORKDIR /app

# Install runtime shared libraries and Docker CLI for sandbox operations
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    git \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Create secure non-root user 'app' with matching UID/GID
RUN groupadd -g 1000 app && \
    useradd -u 1000 -g app -m -s /bin/bash app && \
    usermod -aG docker app 2>/dev/null || true

# Copy installed Python packages from builder stage
COPY --from=builder /root/.local /home/app/.local

# Copy application source code with correct ownership
COPY --chown=app:app . /app

# Switch to non-root user
USER app

# Expose FastAPI default port
EXPOSE 8000

# Healthcheck definition
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; sys_exit = 0 if urllib.request.urlopen('http://localhost:8000/health').getcode() == 200 else 1; exit(sys_exit)" || exit 1

# Start Uvicorn ASGI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
