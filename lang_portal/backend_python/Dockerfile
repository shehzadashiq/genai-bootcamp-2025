FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE config.settings_prod

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create necessary directories
RUN mkdir -p /var/log/django /app/logs

# Create non-root user
RUN useradd -m django
RUN chown -R django:django /app /var/log/django
USER django

# Run gunicorn
CMD ["gunicorn", "--config", "gunicorn.conf.py", "config.wsgi:application"] 