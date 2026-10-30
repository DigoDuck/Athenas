# Build context is the repository root.
FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 RUFF_CACHE_DIR=/tmp/ruff
WORKDIR /app

FROM base AS dev
COPY backend/requirements.txt backend/requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
# Source is bind-mounted at /repo by docker-compose.dev.yml.
WORKDIR /repo

FROM base AS use
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
# GUNICORN_BIND: set [::]:8000 only where the private network is IPv6-only (docs/hosting.md).
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py ensure_superuser && exec gunicorn config.wsgi -b \"${GUNICORN_BIND:-0.0.0.0:8000}\" --workers 2"]
