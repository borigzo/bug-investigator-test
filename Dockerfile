# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8080

RUN useradd --create-home --uid 10001 appuser
WORKDIR /app
COPY --chown=appuser:appuser app.py ./
USER appuser

EXPOSE 8080

# app.py ловит KeyboardInterrupt, поэтому SIGINT даёт чистую остановку (python как PID 1 игнорирует SIGTERM)
STOPSIGNAL SIGINT

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/', timeout=2)"]

CMD ["python", "app.py"]