# Celery Worker Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY 3rdparty/python/requirements-shared.txt /tmp/requirements-shared.txt
COPY 3rdparty/python/requirements-celery.txt /tmp/requirements-celery.txt

# Create requirements-celery.txt if it doesn't exist
RUN echo "celery[redis]>=5.3,<6" > /tmp/requirements-celery.txt && \
    echo "flower>=2.0,<3" >> /tmp/requirements-celery.txt && \
    echo "kombu>=5.3,<6" >> /tmp/requirements-celery.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements-shared.txt && \
    pip install --no-cache-dir -r /tmp/requirements-celery.txt

# Copy application code
COPY shared /app/shared
COPY services /app/services
COPY entry_points/celery_worker /app/entry_points/celery_worker

# Set Python path
ENV PYTHONPATH=/app:$PYTHONPATH

# Create non-root user
RUN useradd -m -u 1000 celeryuser && \
    chown -R celeryuser:celeryuser /app

# Switch to non-root user
USER celeryuser

# Default command: run Celery worker
CMD ["celery", "-A", "entry_points.celery_worker.app", "worker", "--loglevel=info"]

# Alternative commands (can be overridden):
# For beat scheduler: celery -A entry_points.celery_worker.app beat
# For flower: celery -A entry_points.celery_worker.app flower