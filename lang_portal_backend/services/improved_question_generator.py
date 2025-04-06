import boto3
import asyncio
import time
import json
import logging
from typing import List, Dict, Union, Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class ImprovedQuestionGenerator:
    def __init__(self):
        """Initialize Bedrock service with improved error handling and rate limiting."""
        self.client = boto3.client('bedrock-runtime')
        self.model_id = "anthropic.claude-v2"
        self.max_retries = 5
        self.base_delay = 2
        self.request_queue = asyncio.Queue()
        self.last_request_time = 0
        self.min_request_interval = 1.0

    async def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    async def _invoke_bedrock(self, prompt: str) -> Optional[str]:
        """Invoke Bedrock with retries and error handling."""
        await self._wait_for_rate_limit()
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps({
                        "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                        "max_tokens_to_sample": 2048,
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "stop_sequences": ["\n\nHuman:"]
                    })
                )
                response_body = json.loads(response['body'].read())
                return response_body.get('completion')
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'ThrottlingException':
                    delay = self.base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue
                logger.error(f"Bedrock API error: {str(e)}")
                return None
                
            except Exception as e:
                logger.error(f"Error invoking Bedrock: {str(e)}")
                return None
                
        logger.error("Max retries exceeded for Bedrock API call")
        return None

    async def generate_questions(
        self,
        text: str,
        num_questions: Optional[int] = None,
        language: str = 'ur'
    ) -> List[Dict[str, Union[str, List[str], int]]]:
        """
        Generate improved listening comprehension questions.
        
        Args:
            text: Text to generate questions from
            num_questions: Number of questions to generate
            language: Target language for questions
            
        Returns:
            List of questions with options and correct answers
        """
        try:
            # Construct a more detailed prompt
            prompt = f"""
            You are an expert language teacher creating listening comprehension questions.
            Create {num_questions} multiple-choice questions in {language} based on this text:

            {text}

            For each question:
            1. Make sure it tests comprehension, not just memory
            2. Include 4 options where only one is correct
            3. Provide a brief explanation for why the answer is correct
            4. Ensure questions progress from easier to more challenging
            5. Focus on key concepts and main ideas
            6. Include some questions about implied meanings or conclusions

            Format your response as a JSON array with objects containing:
            - question: The question text
            - options: Array of 4 possible answers
            - correct_answer: Index of correct answer (0-3)
            - explanation: Why this answer is correct

            Response format example:
            [
                {{
                    "question": "...",
                    "options": ["...", "...", "...", "..."],
                    "correct_answer": 0,
                    "explanation": "..."
                }}
            ]
            """

            # Generate questions using Bedrock
            response = await self._invoke_bedrock(prompt)
            if not response:
                raise ValueError("Failed to generate questions")

            # Extract JSON from response
            try:
                # Find the first [ and last ] to extract just the JSON array
                start = response.find('[')
                end = response.rfind(']') + 1
                if start == -1 or end == 0:
                    raise ValueError("No valid JSON array found in response")
                    
                questions = json.loads(response[start:end])
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse question generation response as JSON: {str(e)}")

            # Validate questions
            if not questions:
                raise ValueError("No questions generated")
                
            required_fields = {'question', 'options', 'correct_answer', 'explanation'}
            for i, q in enumerate(questions):
                # Check required fields
                if not all(field in q for field in required_fields):
                    raise ValueError(f"Question {i+1} missing required fields")
                    
                # Validate options
                if not isinstance(q['options'], list) or len(q['options']) != 4:
                    raise ValueError(f"Question {i+1} must have exactly 4 options")
                    
                # Validate correct_answer
                if not isinstance(q['correct_answer'], int) or not 0 <= q['correct_answer'] <= 3:
                    raise ValueError(f"Question {i+1} correct_answer must be between 0 and 3")

            return questions
            
        except Exception as e:
            logger.error(f"Question generation failed: {str(e)}")
            raise ValueError(f"Failed to generate questions: {str(e)}")
