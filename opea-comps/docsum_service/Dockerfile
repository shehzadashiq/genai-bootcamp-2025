# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

# Create a non-root user
RUN useradd -m -u 1000 appuser

# Set working directory and create necessary directories
WORKDIR /app
RUN mkdir -p data/chroma audio_cache && \
    chown -R appuser:appuser /app && \
    chmod 755 /app/audio_cache

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    tesseract-ocr \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY --chown=appuser:appuser . .

# Ensure volume mount point has correct permissions
RUN mkdir -p /app/audio_cache && \
    chown -R appuser:appuser /app/audio_cache && \
    chmod 755 /app/audio_cache

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8002

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
