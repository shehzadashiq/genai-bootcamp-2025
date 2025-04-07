import boto3
import asyncio
import time
import json
import logging
import re
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
        self.min_request_interval = 2.0  # Increase minimum interval between requests
        self.max_concurrent_requests = 3
        self._semaphore = asyncio.Semaphore(self.max_concurrent_requests)

    async def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    async def _invoke_bedrock(self, prompt: str) -> Optional[str]:
        """Invoke Bedrock with retries and error handling."""
        async with self._semaphore:  # Limit concurrent requests
            await self._wait_for_rate_limit()
            
            for attempt in range(self.max_retries):
                try:
                    # Split long text into chunks if needed
                    if len(prompt) > 10000:
                        prompt = prompt[:10000] + "..."  # Truncate if too long
                        
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
                    completion = response_body.get('completion')
                    if completion:
                        return completion.strip()
                    else:
                        logger.error("Empty completion from Bedrock")
                        
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code in ['ThrottlingException', 'TooManyRequestsException', 'ServiceUnavailable']:
                        delay = self.base_delay * (2 ** attempt)
                        logger.warning(f"Rate limit hit, retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                        continue
                    logger.error(f"Bedrock API error: {error_code} - {str(e)}")
                    return None
                    
                except Exception as e:
                    logger.error(f"Error invoking Bedrock: {str(e)}")
                    if attempt < self.max_retries - 1:
                        delay = self.base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
                        continue
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
            prompt = f"""You are an expert language teacher creating listening comprehension questions. I need you to create {num_questions or 5} multiple-choice questions in {language} based on this text. Format your entire response as a valid JSON array.

Input text:
{text}

Instructions:
1. Make sure each question tests comprehension, not just memory
2. Include 4 options where only one is correct
3. Provide a brief explanation for why the answer is correct
4. Ensure questions progress from easier to more challenging
5. Focus on key concepts and main ideas
6. Include some questions about implied meanings or conclusions

You must respond with ONLY a JSON array in this exact format, no other text:
[
    {{
        "question": "Question text here",
        "options": [
            "Option 1 (correct answer)",
            "Option 2",
            "Option 3",
            "Option 4"
        ],
        "correct_answer": 0,
        "explanation": "Why this is the correct answer"
    }}
]

Important:
- ONLY output the JSON array, no other text
- Ensure the JSON is valid and properly formatted
- The correct_answer must be the index (0-3) of the correct option
- All text must be in {language} script
"""

            # Generate questions using Bedrock
            response = await self._invoke_bedrock(prompt)
            if not response:
                raise ValueError("Failed to generate questions")

            # Extract JSON from response
            try:
                # Clean the response to find JSON array
                cleaned_response = response.strip()
                start = cleaned_response.find('[')
                end = cleaned_response.rfind(']') + 1
                
                if start == -1 or end == 0:
                    logger.error(f"No JSON array found in response: {cleaned_response}")
                    raise ValueError("No valid JSON array found in response")
                    
                json_str = cleaned_response[start:end]
                logger.debug(f"Extracted JSON string: {json_str}")
                
                try:
                    questions = json.loads(json_str)
                except json.JSONDecodeError as e:
                    # Try to clean up common JSON issues
                    json_str = json_str.replace('\n', ' ').replace('\r', '')
                    json_str = re.sub(r',(\s*})', r'\1', json_str)  # Remove trailing commas
                    json_str = re.sub(r',(\s*])', r'\1', json_str)
                    questions = json.loads(json_str)
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {str(e)}")
                logger.error(f"Response content: {response}")
                raise ValueError(f"Failed to parse question generation response as JSON: {str(e)}")

            # Validate and clean up questions
            if not isinstance(questions, list):
                raise ValueError("Response is not a list of questions")
                
            if not questions:
                raise ValueError("No questions generated")
                
            cleaned_questions = []
            for i, q in enumerate(questions, 1):
                try:
                    # Validate required fields
                    if not isinstance(q, dict):
                        raise ValueError(f"Question {i} is not a dictionary")
                    
                    required_fields = {'question', 'options', 'correct_answer', 'explanation'}
                    missing_fields = required_fields - set(q.keys())
                    if missing_fields:
                        raise ValueError(f"Question {i} missing fields: {', '.join(missing_fields)}")
                    
                    # Validate question text
                    if not isinstance(q['question'], str) or not q['question'].strip():
                        raise ValueError(f"Question {i} has invalid question text")
                    
                    # Validate options
                    if not isinstance(q['options'], list):
                        raise ValueError(f"Question {i} options is not a list")
                    if len(q['options']) != 4:
                        raise ValueError(f"Question {i} must have exactly 4 options")
                    if not all(isinstance(opt, str) and opt.strip() for opt in q['options']):
                        raise ValueError(f"Question {i} has invalid option text")
                    
                    # Validate correct_answer
                    if not isinstance(q['correct_answer'], int):
                        raise ValueError(f"Question {i} correct_answer must be an integer")
                    if not 0 <= q['correct_answer'] <= 3:
                        raise ValueError(f"Question {i} correct_answer must be between 0 and 3")
                    
                    # Clean up the question
                    cleaned_question = {
                        'question': q['question'].strip(),
                        'options': [opt.strip() for opt in q['options']],
                        'correct_answer': q['options'][q['correct_answer']],  # Convert index to text
                        'explanation': q['explanation'].strip() if q['explanation'] else None
                    }
                    cleaned_questions.append(cleaned_question)
                    
                except Exception as e:
                    logger.error(f"Error validating question {i}: {str(e)}")
                    continue
            
            if not cleaned_questions:
                raise ValueError("No valid questions after validation")
                
            return cleaned_questions
            
        except Exception as e:
            logger.error(f"Question generation failed: {str(e)}")
            raise ValueError(f"Failed to generate questions: {str(e)}")
