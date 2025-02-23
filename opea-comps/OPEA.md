# OPEA (Open Platform for Enterprise AI) Components

## Overview
OPEA is a microservices-based platform for deploying and managing AI services. The platform includes several key components:

1. **Mega Service**: A FastAPI-based service that orchestrates interactions between various components
2. **Guardrails Service**: A content filtering service using LLaMA Guard models
3. **Ollama Service**: Local LLM service for running open-source models

## Architecture

### Components

#### 1. Mega Service (Port 8001)
- Primary orchestration service
- Handles routing between components
- Implements safety checks and guardrails
- Built with FastAPI and Python

**Key Features:**
- Message routing and transformation
- Integration with Guardrails service
- Integration with Ollama LLM service
- Configurable through environment variables

#### 2. Guardrails Service (Port 9090)
- Content safety filtering
- Uses Meta's LlamaGuard models
- Runs on Text Generation Inference (TGI) server

**Configuration:**
- Model: meta-llama/Meta-Llama-Guard-2-8B
- Quantization: bitsandbytes for CPU efficiency
- Authentication: Requires Hugging Face token

#### 3. Ollama Service (Port 11434)
- Local LLM service
- Runs open-source models
- Built-in safety measures

## Setup

### Environment Variables
```sh
# Mega Service Configuration
MEGA_SERVICE_PORT=8000       # For Docker Service
MEGA_SERVICE_APP_PORT=8001   # For Python Application
HOST_IP=$(hostname -I | awk '{print $1}')

# Guardrails Configuration
GUARDRAILS_PORT=9090
SAFETY_GUARD_ENDPOINT="http://${HOST_IP}:8080"

# LLM Configuration
LLM_SERVICE_PORT=11434
```

### Dependencies
```
fastapi
uvicorn
python-multipart
aiohttp
python-dotenv
huggingface-hub<=0.24.0
langchain-community
langchain-huggingface
opentelemetry-api
opentelemetry-sdk
prometheus-fastapi-instrumentator
```

## API Examples

### 1. Basic Chat Query
```sh
curl -X POST http://localhost:8001/v1/example-service \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "messages": [
      {
        "role": "user",
        "content": "Hello, how are you?"
      }
    ]
  }'
```

### 2. Guardrails Health Check
```sh
curl http://localhost:9090/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

### 3. Guardrails Content Check
```sh
curl -X POST http://localhost:9090/v1/guardrails \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test message", "prompt": "Test prompt"}'
```

## Safety Features

The platform implements multiple layers of safety:

1. **Guardrails Service**
   - Uses LlamaGuard for content filtering
   - Checks both input prompts and responses
   - Categories include:
     - Violent Crimes
     - Non-Violent Crimes
     - Sex-Related Crimes
     - Child Sexual Exploitation
     - Privacy Violations
     - Hate Speech
     - Self-Harm Content
     - And more

2. **LLM Built-in Safety**
   - Ollama's built-in safety measures
   - Responds with warnings for inappropriate requests
   - Refuses to generate harmful content

## Current Limitations

1. **Guardrails Service**
   - Requires proper Hugging Face token configuration
   - CPU-based deployment may have performance implications
   - Currently using quantization for better CPU performance

2. **Response Filtering**
   - Some unsafe queries may not be properly blocked by Guardrails
   - Relying on LLM's built-in safety measures as backup

## Troubleshooting

### Common Issues
1. **TGI Server Connection**
   - Check if the TGI server is running
   - Verify Hugging Face token configuration
   - Ensure proper model loading

2. **Port Conflicts**
   - Default ports: 8001 (App), 9090 (Guardrails), 11434 (Ollama)
   - Check for port availability
   - Use environment variables to change ports if needed

### Debugging Commands
```sh
# Check TGI server environment
docker exec tgi-server env

# Check Guardrails logs
docker logs guardrail-service

# Pull LLM model
curl -X POST http://localhost:11434/api/pull -d '{"name": "llama3.2:1b"}'
```

## Linux Commands

### Environment Setup
```bash
# Set environment variables
export MEGA_SERVICE_PORT=8000
export MEGA_SERVICE_APP_PORT=8001
export HOST_IP=$(hostname -I | awk '{print $1}')
export GUARDRAILS_PORT=9090
export SAFETY_GUARD_ENDPOINT="http://${HOST_IP}:8080"

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Docker Commands
```bash
# Build and start services
docker-compose build
docker-compose up -d

# Check service status
docker ps
docker-compose ps

# View logs
docker logs -f tgi-server
docker logs -f guardrail-service
docker logs -f mega-service

# Check container environment
docker exec tgi-server env | grep -i hugging
docker exec guardrail-service env

# Stop services
docker-compose down

# Clean up
docker system prune -a  # Remove all unused containers, networks, and images
```

### Service Management
```bash
# Start Python application
uvicorn app:app --host 0.0.0.0 --port 8001 --reload

# Check service health
curl http://localhost:9090/v1/health_check
curl http://localhost:8001/health

# Monitor ports
netstat -tulpn | grep -E '8001|9090|11434'
lsof -i :8001  # Check what's using port 8001

# Process management
ps aux | grep -E 'tgi-server|guardrail|mega'
pkill -f uvicorn  # Stop the Python application
```

### File Operations
```bash
# Set permissions
chmod +x scripts/*.sh
chown -R user:user .venv/

# View logs
tail -f logs/mega-service.log
grep -r "error" logs/

# Disk usage
du -sh data/
df -h .
```

### Debugging
```bash
# Network debugging
nc -zv localhost 8001  # Test port connectivity
curl -v http://localhost:9090/v1/health_check  # Verbose API test
tcpdump -i any port 8001  # Monitor network traffic

# Log analysis
journalctl -u docker | grep -i tgi-server
grep -r "error" /var/log/
