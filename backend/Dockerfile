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

# ---- Install System Dependencies & Node.js for MongoDB MCP Server ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ---- Dependency layer (cached unless requirements.txt changes) ----
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Application code ----
COPY app/ ./app/

EXPOSE 8080

# Start the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
