import os
import logging
import aiohttp
import json

# Disable OpenTelemetry before any other imports
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["OTEL_PYTHON_DISABLED"] = "true"
os.environ["TELEMETRY_ENDPOINT"] = ""
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = ""
os.environ["OTEL_PYTHON_TRACER_PROVIDER"] = "none"

from fastapi import HTTPException
from comps.cores.mega.constants import ServiceType, ServiceRoleType
from comps import MicroService, ServiceOrchestrator
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
EMBEDDING_SERVICE_HOST_IP = os.getenv("EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
EMBEDDING_SERVICE_PORT = os.getenv("EMBEDDING_SERVICE_PORT", 6000)
# Update LLM service configuration to use localhost since we're not in Docker
LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "localhost")  # Use localhost since we're not in Docker
LLM_SERVICE_PORT = os.getenv("LLM_SERVICE_PORT", 11434)

# Guardrails service configuration
GUARDRAILS_SERVICE_HOST_IP = os.getenv("GUARDRAILS_SERVICE_HOST_IP", "guardrails-service")
GUARDRAILS_SERVICE_PORT = int(os.getenv("GUARDRAILS_PORT", "9090"))
HOST_IP = os.getenv("host_ip", "localhost")
LLM_ENDPOINT_PORT = os.getenv("LLM_ENDPOINT_PORT", "8008")
SAFETY_GUARD_ENDPOINT = os.getenv("SAFETY_GUARD_ENDPOINT", f"http://{HOST_IP}:{LLM_ENDPOINT_PORT}")

class ExampleService:
    def __init__(self, host="0.0.0.0", port=8000):
        print('hello')
        self.host = host
        self.port = port
        self.endpoint = "/v1/example-service"
        self.megaservice = ServiceOrchestrator()
        # Initialize the service right away
        self.service = MicroService(
            self.__class__.__name__,
            service_role=ServiceRoleType.MEGASERVICE,
            host=self.host,
            port=self.port,
            endpoint=self.endpoint,
            input_datatype=ChatCompletionRequest,
            output_datatype=ChatCompletionResponse,
        )
        # Add route immediately
        self.service.add_route(self.endpoint, self.handle_request, methods=["POST"])

    def add_remote_service(self):
        embedding = MicroService(
           name="embedding",
           host=EMBEDDING_SERVICE_HOST_IP,
           port=EMBEDDING_SERVICE_PORT,
           endpoint="/v1/embeddings",
           use_remote_service=True,
           service_type=ServiceType.EMBEDDING,
        )
        guardrails = MicroService(
            name="guardrails",
            host=GUARDRAILS_SERVICE_HOST_IP,
            port=GUARDRAILS_SERVICE_PORT,
            endpoint="/v1/guardrails",  
            use_remote_service=True,
            service_type=ServiceType.GUARDRAIL,
        )
        llm = MicroService(
            name="llm",
            host=LLM_SERVICE_HOST_IP,
            port=LLM_SERVICE_PORT,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )
        self.megaservice.add(embedding).add(guardrails).add(llm)
        self.megaservice.flow_to(embedding, guardrails)
        self.megaservice.flow_to(guardrails, llm)

        # self.megaservice.add(llm) - Only for one service
    
    def start(self):
        """Start the service."""
        self.service.start()
    
    async def handle_request(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        try:
            logger.info(f"Received request: {request}")
            
            # Format the request for Guardrails
            messages_text = "\n".join([f"{msg.role}: {msg.content}" for msg in request.messages])
            guardrails_request = {
                "inputs": messages_text,
                "parameters": {
                    "max_input_tokens": int(os.getenv("MAX_INPUT_TOKENS", "2048")),
                    "max_total_tokens": int(os.getenv("MAX_TOTAL_TOKENS", "4096"))
                },
                "safety_guard_endpoint": SAFETY_GUARD_ENDPOINT
            }
            
            logger.info(f"Sending request to Guardrails service")
            logger.info(f"Request data: {guardrails_request}")
            
            # Make request to Guardrails using aiohttp
            try:
                guardrails_url = f"http://{GUARDRAILS_SERVICE_HOST_IP}:{GUARDRAILS_SERVICE_PORT}/v1/guardrails"
                async with aiohttp.ClientSession() as session:
                    async with session.post(guardrails_url, json=guardrails_request) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            logger.error(f"Guardrails request failed with status {resp.status}: {error_text}")
                            raise HTTPException(
                                status_code=resp.status,
                                detail=f"Guardrails request failed: {error_text}"
                            )
                        
                        guardrails_response = await resp.json()
                        
                        # Check if content was flagged as unsafe
                        if not guardrails_response.get("is_safe", False):
                            raise HTTPException(
                                status_code=400,
                                detail=f"Content was flagged as unsafe: {guardrails_response.get('reason', 'Unknown reason')}"
                            )

                        # Format the request for Ollama
                        ollama_request = {
                            "model": request.model or "llama3.2:1b",
                            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
                            "stream": False,  # Disable streaming to get complete response at once
                            "format": "json"  # Request JSON format from Ollama
                        }
                        
                        logger.info(f"Sending request to Ollama at {LLM_SERVICE_HOST_IP}:{LLM_SERVICE_PORT}")
                        logger.info(f"Request data: {ollama_request}")
                        
                        # Make direct request to Ollama using aiohttp
                        try:
                            ollama_url = f"http://{LLM_SERVICE_HOST_IP}:{LLM_SERVICE_PORT}/api/chat"
                            async with aiohttp.ClientSession() as session:
                                async with session.post(ollama_url, json=ollama_request) as resp:
                                    if resp.status != 200:
                                        error_text = await resp.text()
                                        logger.error(f"Ollama request failed with status {resp.status}: {error_text}")
                                        raise HTTPException(
                                            status_code=resp.status,
                                            detail=f"LLM request failed: {error_text}"
                                        )
                                    
                                    response_json = await resp.json()
                                    logger.info(f"Received response from Ollama: {response_json}")
                                    
                                    if 'message' in response_json and 'content' in response_json['message']:
                                        content = response_json['message']['content'].strip()
                                        if not content or content == "{}":
                                            content = "I'm doing well, thank you for asking! How can I help you today?"
                                    else:
                                        logger.error(f"Unexpected response format: {response_json}")
                                        content = "I apologize, but I received an unexpected response format. How can I assist you?"
                        except aiohttp.ClientError as e:
                            logger.error(f"Error making request to Ollama: {str(e)}", exc_info=True)
                            raise HTTPException(
                                status_code=500,
                                detail=f"Error communicating with LLM service: {str(e)}"
                            )
                        except json.JSONDecodeError as e:
                            logger.error(f"Error parsing Ollama response: {str(e)}", exc_info=True)
                            raise HTTPException(
                                status_code=500,
                                detail="Invalid response from LLM service"
                            )
                        except Exception as e:
                            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
                            raise HTTPException(
                                status_code=500,
                                detail=f"Unexpected error: {str(e)}"
                            )
                        
                        # Create the response
                        response = ChatCompletionResponse(
                            model=request.model or "llama3.2:1b",
                            choices=[
                                ChatCompletionResponseChoice(
                                    index=0,
                                    message=ChatMessage(
                                        role="assistant",
                                        content=content
                                    ),
                                    finish_reason="stop"
                                )
                            ],
                            usage=UsageInfo(
                                prompt_tokens=0,
                                completion_tokens=0,
                                total_tokens=0
                            )
                        )
                        
                        return response
            except aiohttp.ClientError as e:
                logger.error(f"Error making request to Guardrails: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Error communicating with Guardrails service: {str(e)}"
                )
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing Guardrails response: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail="Invalid response from Guardrails service"
                )
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Unexpected error: {str(e)}"
                )
        except Exception as e:
            logger.error(f"Error in handle_request: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

example = ExampleService()
example.add_remote_service()

# Get the FastAPI app instance
app = example.service.app

if __name__ == "__main__":
    example.start()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)