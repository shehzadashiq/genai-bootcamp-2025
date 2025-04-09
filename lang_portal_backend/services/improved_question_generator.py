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
            if not text.strip():
                raise ValueError("Empty text provided")

            # Prepare prompt for question generation
            prompt = f"""Human: Generate multiple choice questions based on the following text. Return ONLY a JSON array of questions.

Each question object must have:
- "question": The question text
- "options": Array of 4 answer choices
- "correct_answer": Index (0-3) of the correct option
- "explanation": Brief explanation of why the answer is correct

Example format:
[
  {{
    "question": "What is being discussed?",
    "options": [
      "Option 1",
      "Option 2", 
      "Option 3",
      "Option 4"
    ],
    "correct_answer": 0,
    "explanation": "Option 1 is correct because..."
  }}
]

Text to generate questions from:
{text}

Requirements:
1. Return ONLY the JSON array, no other text
2. Each question MUST have exactly 4 options
3. correct_answer MUST be 0-3 (index of correct option)
4. Include brief explanations
5. Use {language} script for all text
6. Focus on key points from the text
7. Make questions clear and unambiguous
"""

            # Get response from Bedrock
            response = await self._invoke_bedrock(prompt)
            if not response:
                raise ValueError("Failed to get response from Bedrock")

            logger.debug(f"Raw response from Bedrock: {response}")
            
            # Clean up the response to find JSON
            try:
                # Remove any non-JSON text
                response = response.strip()
                # Find the first [ and last ]
                start = response.find('[')
                end = response.rfind(']') + 1
                
                if start == -1 or end == 0:
                    logger.error("No JSON array found in response")
                    logger.error(f"Response content: {response}")
                    
                    # If response looks like formatted questions, try to convert to JSON
                    if "1." in response and "a)" in response:
                        logger.info("Attempting to convert formatted questions to JSON")
                        questions = []
                        current_question = None
                        
                        for line in response.split('\n'):
                            line = line.strip()
                            if not line:
                                continue
                                
                            # New question starts with number
                            if line[0].isdigit() and "." in line:
                                if current_question:
                                    questions.append(current_question)
                                current_question = {
                                    "question": line.split(".", 1)[1].strip(),
                                    "options": [],
                                    "correct_answer": 0,  # Default to first option
                                    "explanation": "Based on the context from the audio"
                                }
                            # Option line starts with a letter and )
                            elif line[0].isalpha() and ")" in line:
                                if current_question:
                                    current_question["options"].append(line.split(")", 1)[1].strip())
                                    
                        # Add last question
                        if current_question and len(current_question["options"]) == 4:
                            questions.append(current_question)
                            
                        if questions:
                            return questions
                            
                    raise ValueError("No valid JSON array found in response")
                    
                json_str = response[start:end]
                logger.debug(f"Extracted JSON string: {json_str}")
                
                try:
                    # Clean up JSON string
                    json_str = json_str.replace('\n', ' ').replace('\r', '')
                    json_str = re.sub(r',(\s*})', r'\1', json_str)  # Remove trailing commas
                    json_str = re.sub(r',(\s*])', r'\1', json_str)
                    questions = json.loads(json_str)
                    
                    # Validate questions
                    valid_questions = []
                    for q in questions:
                        try:
                            # Check required fields
                            if not all(k in q for k in ['question', 'options', 'correct_answer', 'explanation']):
                                logger.error(f"Question missing required fields: {q}")
                                continue
                                
                            # Validate options array
                            if not isinstance(q['options'], list) or len(q['options']) != 4:
                                logger.error(f"Question has invalid options array: {q}")
                                continue
                                
                            # Validate correct_answer
                            if not isinstance(q['correct_answer'], int) or q['correct_answer'] not in range(4):
                                logger.error(f"Question has invalid correct_answer: {q}")
                                continue
                                
                            # All validation passed
                            valid_questions.append(q)
                            logger.info(f"Valid question: {json.dumps(q, ensure_ascii=False)}")
                            
                        except Exception as e:
                            logger.error(f"Error validating question: {str(e)}")
                            continue
                            
                    if not valid_questions:
                        logger.error("No valid questions after validation")
                        return []
                        
                    return valid_questions
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON: {str(e)}")
                    logger.error(f"Response content: {response}")
                    return []
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {str(e)}")
                logger.error(f"Response content: {response}")
                raise ValueError(f"Failed to parse question generation response as JSON: {str(e)}")

        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return []
