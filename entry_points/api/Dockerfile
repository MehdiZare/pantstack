# API Service Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY 3rdparty/python/requirements-shared.txt /tmp/requirements-shared.txt
COPY 3rdparty/python/requirements-web-api.txt /tmp/requirements-api.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements-shared.txt && \
    pip install --no-cache-dir -r /tmp/requirements-api.txt

# Copy application code
COPY shared /app/shared
COPY services /app/services
COPY entry_points/api /app/entry_points/api

# Set Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Create non-root user
RUN useradd -m -u 1000 apiuser && \
    chown -R apiuser:apiuser /app

# Switch to non-root user
USER apiuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: run API server
CMD ["python", "-m", "entry_points.api.run"]

# Alternative with uvicorn directly:
# CMD ["uvicorn", "entry_points.api.main:app", "--host", "0.0.0.0", "--port", "8000"]