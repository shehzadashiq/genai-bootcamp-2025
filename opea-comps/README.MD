# Running Ollama Third-Party Service

- [Running Ollama Third-Party Service](#running-ollama-third-party-service)
  - [Choosing a Model](#choosing-a-model)
  - [Getting the Host IP](#getting-the-host-ip)
    - [Windows](#windows)
    - [Linux](#linux)
  - [Ollama API](#ollama-api)
  - [Set Environment Variables](#set-environment-variables)
  - [Download (Pull) a model](#download-pull-a-model)
    - [Run Docker Compose](#run-docker-compose)
  - [Generate a Request](#generate-a-request)
  - [Technical Uncertainty](#technical-uncertainty)

## Choosing a Model

You can get the model_id that ollama will launch from the [Ollama Library](https://ollama.com/library).

[llama3.2](https://ollama.com/library/llama3.2)

eg. LLM_MODEL_ID="llama3.2:1b"

## Getting the Host IP

### Windows

```powershell
(Get-NetIPAddress -InterfaceAlias "Ethernet" | Where-Object AddressFamily -eq IPv4).IPAddress
```

### Linux

Get your IP address

```sh
sudo apt install net-tools
ifconfig
```

Or you can try this way `$(hostname -I | awk '{print $1}')`

## Ollama API

Once the Ollama server is running we can make API calls to the ollama API

[https://github.com/ollama/ollama/blob/main/docs/api.md](https://github.com/ollama/ollama/blob/main/docs/api.md)

## Set Environment Variables

```sh
export OLLAMA_PORT=11434
HOST_IP=$(hostname -I | awk '{print $1}') 
```

## Download (Pull) a model

Before running a LLM container you need to pull the image in Ollama

```sh
curl http://localhost:$OLLAMA_PORT/api/pull -d '{
  "model": "llama3.2:1b"
}'
```

### Run Docker Compose

Create the container

```sh
NO_PROXY=localhost LLM_ENDPOINT_PORT=$OLLAMA_PORT LLM_MODEL_ID="llama3.2:1b" docker compose up
```

## Generate a Request

```sh
curl http://localhost:$OLLAMA_PORT/api/generate -d '{
  "model": "llama3.2:1b",
  "prompt": "Why is the sky blue?"
}'
```

## Technical Uncertainty

Q Does bridge mode mean we can only access Ollama API with another model in the docker compose?

A No, the host machine will be able to access it

Q: Which port is being mapped 8008->11434

In this case 8008 is the port that host machine will access. the other other in the guest port (the port of the service inside container)

Q: If we pass the LLM_MODEL_Id to the ollama server will it download the model when on start?

It does not appear so. The ollama CLI might be running multiple APIs so you need to call the /pull api before trying to generat text

Q: Will the model be downloaded in the container? does that mean the ml model will be deleted when the container stops running?

A: The model will download into the container, and vanish when the container stop running. You need to mount a local drive and there is probably more work to be done.

Q: For LLM service which can text-generation it suggets it will only work with TGI/vLLM and all you have to do is have it running. Does TGI and vLLM have a stardarized API or is there code to detect which one is running? Do we have to really use Xeon or Guadi processor?

vLLM, TGI (Text Generation Inference), and Ollama all offer APIs with OpenAI compatibility, so in theory they should be interchangable.
