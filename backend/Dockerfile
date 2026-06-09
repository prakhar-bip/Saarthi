# ============================================================
# Sarthi Backend - Production Dockerfile
# Python FastAPI application served via Uvicorn
# ============================================================

FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr (useful for Cloud Run logs)
ENV PYTHONUNBUFFERED=1
# Cloud Run injects PORT; default to 8080
ENV PORT=8080

WORKDIR /app

# ---- Dependency layer (cached unless requirements.txt changes) ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Application code ----
COPY app/ ./app/

EXPOSE 8080

# Start the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
