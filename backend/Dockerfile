# Backend image for Render (free tier: 512 MB RAM, 0.1 CPU).
# Kept deliberately slim — no ML training deps, no dataset, no model weights.
FROM python:3.10-slim-bookworm

# Unbuffered logs so Render's log stream is live, and no .pyc clutter.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System libraries required by opencv-python-headless.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Requirements first so the dependency layer is cached across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads

# Render injects PORT at runtime; 10000 is its default and our local fallback.
ENV PORT=10000
EXPOSE 10000

# Single worker: the free instance has 512 MB, and OpenCV + sklearn are memory
# hungry. Scale with instance size, not workers, on this plan.
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
