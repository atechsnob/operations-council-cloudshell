FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Cloud Run expects PORT env var; default 8080
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Use uvicorn directly — gunicorn adds startup complexity without benefit for
# single-worker Cloud Run instances
CMD exec uvicorn chapter_07_deployment.main:app \
    --host 0.0.0.0 \
    --port ${PORT} \
    --workers 1 \
    --log-level info
