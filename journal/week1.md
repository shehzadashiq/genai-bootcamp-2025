# Week 1

# Backend

# Frontend

# OPEA

The Guardrail Comp was added to the program.

A container for the guardrails service needs to be added to the [Opea Comps Docker File](../opea-comps/docker-compose.yml)

N.B I have not modified the OLLAMA Port so it uses the default of `11434`

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

## References

- [Sharing SSH keys between Windows and WSL 2](https://devblogs.microsoft.com/commandline/sharing-ssh-keys-between-windows-and-wsl-2/)
