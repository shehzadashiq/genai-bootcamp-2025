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

Revised Query

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