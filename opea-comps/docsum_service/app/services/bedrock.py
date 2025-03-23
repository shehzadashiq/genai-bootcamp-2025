import boto3
import json
import logging
import time
import asyncio
from typing import Optional, List
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class BedrockService:
    def __init__(self):
        self.client = boto3.client('bedrock-runtime')
        self.model_id = "anthropic.claude-v2"  # Reverting to Claude v2 for now
        self.max_retries = 5
        self.base_delay = 2  # Increased base delay
        self.request_queue = asyncio.Queue()
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests

    async def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits by waiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    async def summarize(self, text: str) -> Optional[str]:
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                await self._wait_for_rate_limit()

                prompt = f"""Human: Please provide a concise summary of the following text:

{text}
\n\nAssistant:"""

                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps({
                        "prompt": prompt,
                        "max_tokens_to_sample": 1000,
                        "temperature": 0.7,
                        "top_p": 0.9,
                    })
                )

                response_body = json.loads(response['body'].read())
                summary = response_body.get('completion', '').strip()
                return summary

            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ThrottlingException' and retry_count < self.max_retries - 1:
                    delay = self.base_delay * (2 ** retry_count)  # Exponential backoff
                    logger.warning(f"Rate limited by Bedrock, retrying in {delay} seconds...")
                    await asyncio.sleep(delay)  # Use asyncio.sleep instead of time.sleep
                    retry_count += 1
                    continue
                logger.error(f"Error calling Bedrock: {str(e)}")
                return None
            except Exception as e:
                logger.error(f"Error calling Bedrock: {str(e)}")
                return None

        logger.error("Max retries exceeded for Bedrock API call")
        return None

    async def list_available_models(self) -> List[str]:
        """List all available Bedrock models."""
        try:
            bedrock = boto3.client('bedrock')
            response = bedrock.list_foundation_models()
            models = [model['modelId'] for model in response['modelSummaries']]
            logger.info(f"Available Bedrock models: {models}")
            return models
        except Exception as e:
            logger.error(f"Error listing models: {str(e)}")
            return []
