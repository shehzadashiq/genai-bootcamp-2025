# Week 1

## Backend

I wrote the backend from scratch in both Python and GoLang. I used windsurf to analyse a modified specification for the backend and then implement it. I implemented the word vocabulary activity too and this works successfully. Getting it to work successfully though was a challenge.
Please describe your backend API implementation.

### Backend Prompt files

- [Prompt for Go](../lang_portal/backend_go/prompt_go.md)
- [Prompt for Python](../lang_portal/backend_python/prompt_python.md)
- [Backend Documentation](../lang_portal/backend_go/DEVELOPMENT.md)

## Frontend

The frontend was created in windsurf. I used windsurf to analyse both the prompts for the backend and frontend and then generate the implementation. I additionally asked Windsurf to implement themes such as Dark. This caused parts of the GUI to not appear correctly so the theme was modified. A lot of troubleshooting was required as it would go into react loops and not render if e.g. the DB had 0 events. There are further inconsistencies which I aim to address.

### Frontend Prompt File

[Prompt for Frontend](../lang_portal/frontend/prompt.md)

## Vocab Importer Implementation

I did not do this unfortunately as I focused on getting the backend and OPEA to work properly.

## OPEA

### OPEA Service Components

A container for the guardrails service needs to be added to the [Opea Comps Docker File](../opea-comps/docker-compose.yml)

N.B I have not modified the `OLLAMA Port` so it uses the default of `11434`

The OPEA mega-service consists of the following services.

- ollama-server
- guardrails-service
- tgi-server

Build the service using the command `docker-compose build mega-service`

### Troubleshooting

- `docker exec tgi-server env | grep -i hugging`
- `docker exec tgi-server env`

A [Text Generation Inference (TGI) Server](https://github.com/opea-project/GenAIComps/tree/main/comps/third_parties/tgi) is required to host the GuardRails model.

### Guardrails Services

The Guardrail Comp was added to the program. I also modified the port from `8000` to `8001` as it conflicted with the port for the docker service.

```yaml
  guardrails-service:
    image: opea/guardrails:latest
    container_name: guardrails-service
    ports:
      - ${GUARDRAILS_PORT:-7000}:7000
    environment:
      no_proxy: ${no_proxy}
      http_proxy: ${http_proxy}
      https_proxy: ${https_proxy}
      LLAMA_GUARD_MODEL: llama-guard
      OLLAMA_BASE_URL: http://ollama-server:11434
    depends_on:
      - ollama-server
```

This container requires a hugging-face token. If a token is not present the following error is shown when you run `docker compose up`

![image](https://github.com/user-attachments/assets/fd8c6979-5150-458c-8f31-c2ef47adc383)

To resolve this I generated an API Token on [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) and copied it.

I then installed the huggingface-cli by running `pip install -U "huggingface_hub[cli]"`

After this I ran `huggingface-cli login` and provided the token I had created previously

![image](https://github.com/user-attachments/assets/f4c94910-c8db-48fb-a1c2-59f3531add8e)

### GuardRails Endpoints

You can query the endpoints available on the Guardrails service by querying its [JSON endpoint]((http://localhost:9090/openapi.json))

- [opea_service@guardrails](http://localhost:9090/docs#/default/safety_guard_v1_guardrails_post)
- [GuardRail JSON](http://localhost:9090/openapi.json)
- [Health check](http://localhost:9090/v1/health_check)
- [Statistics](http://localhost:9090/v1/statistics)
- [Metrics](http://localhost:9090/metrics)

## References

- [Sharing SSH keys between Windows and WSL 2](https://devblogs.microsoft.com/commandline/sharing-ssh-keys-between-windows-and-wsl-2/)
- [Ollama Api Port Overview](https://www.restack.io/p/ollama-api-port-answer-cat-ai)
- [LLM Everywhere: Docker for Local and Hugging Face Hosting](https://www.docker.com/blog/llm-docker-for-local-and-hugging-face-hosting/)
- [OPEA Dev](https://opea.dev/)
- [meta-llama/LlamaGuard-7b](https://huggingface.co/meta-llama/LlamaGuard-7b)
- [https://www.reddit.com/r/huggingface/comments/1dgr0g2/where_do_i_get_the_affiliation_code/](https://www.reddit.com/r/huggingface/comments/1dgr0g2/where_do_i_get_the_affiliation_code/)
- [https://github.com/opea-project/GenAIComps/blob/main/comps/guardrails/src/guardrails/README.md](https://github.com/opea-project/GenAIComps/blob/main/comps/guardrails/src/guardrails/README.md)
- [Generative AI Components (GenAIComps)](https://github.com/opea-project/GenAIComps)
- [Trust and Safety with LLM](https://github.com/opea-project/GenAIComps/blob/main/comps/guardrails/README.md)
- [guardrails-usvc](https://artifacthub.io/packages/helm/test-opea/guardrails-usvc)
- [Generative AI Components (GenAIComps) Github Repo](https://github.com/opea-project/GenAIComps)
- [Guardrails Microservice](https://github.com/opea-project/GenAIComps/blob/main/comps/guardrails/src/guardrails/README.md)
- [TGI LLM Microservice](https://github.com/opea-project/GenAIComps/tree/main/comps/third_parties/tgi)
- [TGI Reference Docker Compose File](https://github.com/opea-project/GenAIComps/blob/main/comps/third_parties/tgi/deployment/docker_compose/compose.yaml)
- [Ollama Docker Compose Reference File](https://github.com/opea-project/GenAIComps/blob/main/comps/third_parties/ollama/deployment/docker_compose/compose.yaml)
- [GuardRails DockerFile](https://github.com/opea-project/GenAIComps/blob/main/comps/guardrails/src/guardrails/Dockerfile)
- [LVM Microservice](https://opea-project.github.io/latest/GenAIComps/comps/lvms/src/README.html)
- [OPEA GenAI Microservices](https://opea-project.github.io/latest/microservices/index.html#llms-microservice)
- [OPEA Generative AI Components (GenAIComps)](https://opea-project.github.io/latest/GenAIComps/README.html)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [OPEA GenAI Microservices](https://opea-project.github.io/latest/microservices/index.html)
- [OPEA Document Summary LLM Microservice](https://opea-project.github.io/latest/GenAIComps/comps/llms/src/doc-summarization/README.html)
- [OPEA Llms Microservice](https://opea-project.github.io/latest/microservices/index.html#lvms-microservice)
- [Returning "ValidationError: 1 validation error for LLMChain prompt value is not a valid dict (type=type_error.dict)" while trying to run the LLMChain](https://github.com/langchain-ai/langchain/issues/13681)
- [meta-llama/LlamaGuard-7b](https://huggingface.co/meta-llama/LlamaGuard-7b)
- [meta-llama/Meta-Llama-Guard-2-8B](https://huggingface.co/meta-llama/Meta-Llama-Guard-2-8B)
- [How To Use An .env File In Docker Compose](https://www.warp.dev/terminus/docker-compose-env-file)
- [Containerizing a Hugging Face Model with FastAPI and Docker for Efficient Deployment](https://dipankarmedh1.medium.com/containerize-a-hugging-face-model-using-docker-and-fastapi-9129248f7e12)
- [Hugging Face Command Line Interface (CLI)](https://huggingface.co/docs/huggingface_hub/main/en/guides/cli)
- [TTS](https://docs.coqui.ai/en/latest/tutorial_for_nervous_beginners.html)
