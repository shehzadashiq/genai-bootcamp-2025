FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install local package
COPY . /app/opea-comps/
WORKDIR /app/opea-comps
RUN pip install -e .

# Copy and install mega-service requirements
WORKDIR /app/mega-service
COPY mega-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy mega-service code
COPY mega-service/app.py .

EXPOSE 8000

# Run the service using module:app syntax
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
