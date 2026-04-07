# ── Stage 1: dependency builder ──────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS builder

# Pinned uv version for reproducible builds
COPY --from=ghcr.io/astral-sh/uv:0.5.29 /uv /uvx /bin/

WORKDIR /app

# Build-time system deps only (gcc for C-extension wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# ─── Layer-cache trick: copy lock files BEFORE any source code ───
# Docker only re-runs uv sync when pyproject.toml / uv.lock changes
COPY pyproject.toml uv.lock ./

ENV UV_NO_CACHE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# Install all Python deps — NO model downloads here (kept for volume mounting)
RUN uv sync --frozen --no-dev --no-install-project

# Strip test bloat from the venv to shrink the layer (leave .dist-info as it contains entry_points metadata)
RUN find /app/.venv -name "*.pyi" -delete && \
    find /app/.venv -name "test" -type d | xargs rm -rf && \
    find /app/.venv -name "tests" -type d | xargs rm -rf && \
    rm -rf /root/.cache/pip


# ── Stage 2: lean production runtime ─────────────────────────────────────────
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

# Runtime-only OS libraries
# libgomp1 → required by numpy/torch (OpenMP threading)
# curl     → used by the Docker healthcheck probe
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built venv from builder (no model cache — models go in a volume)
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY app/ ./app/
COPY run.py ./

# Only create the data directory that needs write access
RUN mkdir -p /app/.data/qdrant

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Point HuggingFace and Docling to the mounted volume path
    # Models are downloaded ONCE on first boot and persisted in a named volume
    HF_HOME=/app/.cache/huggingface \
    DOCLING_CACHE_DIR=/app/.cache/docling \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    # Avoid tokenizer parallelism warnings inside uvicorn workers
    TOKENIZERS_PARALLELISM=false

EXPOSE 8000

# 2 sync workers — optimal for CPU-bound ML inference without OOM risk
CMD ["uvicorn", "app.main:app", \
    "--host", "0.0.0.0", \
    "--port", "8000", \
    "--workers", "2", \
    "--timeout-keep-alive", "65", \
    "--access-log"]