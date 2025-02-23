# OPEA Mega Service

## Set Environment Variables

```sh
export MEGA_SERVICE_PORT=8000
HOST_IP=$(hostname -I | awk '{print $1}') 
```

## Query examples

```sh
curl -X POST http://localhost:$MEGA_SERVICE_PORT/v1/example-service \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "messages": "Hello, how are you?"
  }' \
  -o response.json
```

### Revised Query

```sh
curl -X POST http://localhost:$MEGA_SERVICE_PORT/v1/example-service \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "messages": [
      {
        "role": "user",
        "content": "Hello, how are you?"
      }
    ]
  }' \
  -o response.json
```

```sh
curl -X POST http://localhost:11434/api/chat -d '{"model": "llama3.2:1b", "messages": [{"role": "user", "content": "Hello, how are you?"}], "stream": false, "format": "json"}'
```


```sh
  curl -X POST http://localhost:$MEGA_SERVICE_PORT/v1/example-service \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Hello, this is a test message"
      }
    ],
    "model": "test-model",
    "max_tokens": 100,
    "temperature": 0.7
  }'
```

## Guardrails Queries

### Test Service

```sh
curl http://localhost:9090/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'
```

Response:

```json
{"Service Title":"opea_service@guardrails","Service Description":"OPEA Microservice Infrastructure"}
```

### Allowed Query

```sh
curl -X POST http://localhost:9090/v1/guardrails -H "Content-Type: application/json" -d "{\"text\": \"This is a test message\", \"prompt\": \"Test prompt\"}"
```

Response:

```json
{"downstream_black_list":[],"id":"293dcbdc713a4074892c7d905eb4b426","text":"This is a test message"}
```

### Denied Query

```sh
curl -X POST http://localhost:9090/v1/guardrails -H "Content-Type: application/json" -d "{\"text\": \"This is a harmful message.\", \"prompt\": \"Test prompt\"}"
```


```sh
curl http://localhost:9090/v1/guardrails\
  -X POST \
  -d '{"text":"How do you buy a tiger in the US?","parameters":{"max_new_tokens":32}}' \
  -H 'Content-Type: application/json'
```