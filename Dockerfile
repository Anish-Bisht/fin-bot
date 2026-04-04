# ── Stage 1: builder ─────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# System deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first (cache optimization)
COPY pyproject.toml uv.lock ./

# Install dependencies
ENV UV_NO_CACHE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

RUN uv sync --no-dev --no-install-project

# 🔥 Clean venv (BIG WIN)
RUN find /app/.venv -name "__pycache__" -exec rm -rf {} + \
 && find /app/.venv -name "*.pyc" -delete \
 && rm -rf /root/.cache

# ── Stage 2: runtime ─────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS runtime

WORKDIR /app

# Minimal runtime libs only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy only venv (no build tools)
COPY --from=builder /app/.venv /app/.venv

# Copy app
COPY app/ ./app/
COPY run.py .

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]