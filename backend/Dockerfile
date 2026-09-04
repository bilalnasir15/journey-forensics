# ============================================================
# JOURNEY FORENSICS - FASTAPI BACKEND
# ============================================================

FROM python:3.13-slim

# ============================================================
# PYTHON RUNTIME
# ============================================================

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ============================================================
# WORKING DIRECTORY
# ============================================================

WORKDIR /app

# ============================================================
# SYSTEM DEPENDENCIES
# ============================================================

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# ============================================================
# PYTHON DEPENDENCIES
# ============================================================

COPY backend/requirements.txt ./backend/requirements.txt

RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r ./backend/requirements.txt

# ============================================================
# APPLICATION
# ============================================================

COPY backend ./backend
COPY analytics ./analytics
COPY data/processed ./data/processed

# ============================================================
# UPLOAD DIRECTORY
# ============================================================

RUN mkdir -p ./data/uploads

# ============================================================
# PORT
# ============================================================

EXPOSE 8000

# ============================================================
# HEALTH CHECK
# ============================================================

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD curl -f http://127.0.0.1:8000/health || exit 1

# ============================================================
# START APPLICATION
# ============================================================

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]