# SMRTBuddy — Cloud Run image.
# Serves the API, the built frontend at /ui, and the fallback dashboard at
# /app. Fixture and replay data must be inside the image: the engine loads
# them at import time and the demo scenarios read them at runtime.
FROM python:3.11-slim

WORKDIR /srv/smrtbuddy

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY dist ./dist
COPY dashboard ./dashboard
COPY data ./data

ENV PYTHONUNBUFFERED=1

# Cloud Run injects PORT; bind all interfaces, never localhost.
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
