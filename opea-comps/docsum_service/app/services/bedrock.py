import boto3
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class BedrockService:
    def __init__(self):
        self.client = boto3.client('bedrock-runtime')
        self.model_id = "anthropic.claude-v2"  # or another suitable model

    async def summarize(self, text: str) -> Optional[str]:
        try:
            prompt = f"""Human: Please provide a concise summary of the following text:

{text}
\n\nAssistant:
            """

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

        except Exception as e:
            logger.error(f"Error calling Bedrock: {str(e)}")
            return None
