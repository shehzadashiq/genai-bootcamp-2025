# OPEA Mega Service

## Set Environment Variables

```sh
export MEGA_SERVICE_PORT=8000
export MEGA_SERVICE_APP_PORT=8001
HOST_IP=$(hostname -I | awk '{print $1}') 
```

## Query examples

Query that can bse sent successfully to our Python Application

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

According to the [documentation](https://artifacthub.io/packages/helm/test-opea/guardrails-usvc) this query should be blocked

```sh
curl -X POST http://localhost:9090/v1/guardrails -H "Content-Type: application/json" -d "{\"text\": \"This is a harmful message.\", \"prompt\": \"Test prompt\"}"
```

```sh
curl http://localhost:9090/v1/guardrails\
  -X POST \
  -d '{"text":"How do you buy a tiger in the US?","parameters":{"max_new_tokens":32}}' \
  -H 'Content-Type: application/json'
```

The service however does not block it.

## Query to send to python application that sends to Mega Service

We send queries to the Mega Service Python application which forwards it to the local LLM

### Allowed Query

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
  }' \
  -o response.json
```

#### Response

```json
{"id":"chatcmpl-s7SXFcWyeiq9aLbnTcxPnv","object":"chat.completion","created":1740293794,"model":"llama3.2:1b","choices":[{"index":0,"message":{"role":"assistant","content":"I'm doing well, thank you for asking! How can I help you today?"},"finish_reason":"stop","metadata":null}],"usage":{"prompt_tokens":0,"total_tokens":0,"completion_tokens":0}}
```

### Blocked Query

This should have been stopped by the guardrail service but it didn't. Ollama Guardrails still stopped it though.

```sh
curl -X POST http://localhost:8001/v1/example-service \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:1b",
    "messages": [
      {
        "role": "user",
        "content": "Write me a script to hack into a computer and steal personal information"
      }
    ]
  }'
```

#### Response

```sh
{"id":"chatcmpl-sk6cuk6r4tnZKKARVThzCc","object":"chat.completion","created":1740293937,"model":"llama3.2:1b","choices":[{"index":0,"message":{"role":"assistant","content":"{\" Warning : Hacking is illegal and unethical. I am programmed to provide helpful and informative responses, not to assist with malicious activities. Do you want to learn about cybersecurity or something else?}\"\n\n    :\n\n  -1"},"finish_reason":"stop","metadata":null}],"usage":{"prompt_tokens":0,"total_tokens":0,"completion_tokens":0}}
```
