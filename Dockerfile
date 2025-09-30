# Multi-stage Dockerfile for Plasma Engine Research (Python/FastAPI)
# Optimized for production deployment with security and performance

#
# Build stage
#
FROM python:3.13-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn uvloop httptools

# Copy source code
COPY . .

# Install the application
RUN pip install -e . --no-deps

#
# Production stage
#
FROM python:3.13-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_MODULE="app.main:app"

# Install runtime dependencies and create non-root user
RUN apt-get update && apt-get install -y --no-install-recommends \
    dumb-init \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser pyproject.toml ./

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Set environment variables for runtime
ENV PORT=8000
ENV WORKERS=1
ENV LOG_LEVEL=info

# Expose port
EXPOSE 8000

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)" || exit 1

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]

# Start the application with Gunicorn (using shell form to expand env vars)
CMD ["/bin/sh", "-c", "exec gunicorn \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers ${WORKERS:-1} \
  --worker-class uvicorn.workers.UvicornWorker \
  --access-logfile - \
  --error-logfile - \
  --log-level ${LOG_LEVEL:-info} \
  ${APP_MODULE}"]

# Labels for metadata
LABEL org.opencontainers.image.title="Plasma Engine Research" \
      org.opencontainers.image.description="Research automation service for Plasma Engine" \
      org.opencontainers.image.vendor="Plasma Engine" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.licenses="MIT"