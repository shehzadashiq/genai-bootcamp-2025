"""
Question generator for language listening exercises using Amazon Bedrock.
"""
from typing import Dict, List, Optional, Tuple, Union
import boto3
import json
import re
from config import aws_config, app_config
from langchain_core.language_models import BaseLLM
from langchain_aws.chat_models import BedrockChat
from langchain_core.messages import HumanMessage, SystemMessage

class QuestionGenerator:
    def __init__(self):
        """Initialize Bedrock client for question generation."""
        # Initialize Bedrock clients
        self.bedrock = boto3.client(
            'bedrock',
            region_name=aws_config.AWS_REGION
        )
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=aws_config.AWS_REGION
        )
        
        # Initialize Bedrock LLM with specific parameters for question generation
        self.llm = BedrockChat(
            client=self.bedrock_runtime,  # Use runtime client for inference
            model_id=aws_config.BEDROCK_MODEL_ID,
            model_kwargs={
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2000,
                "stop_sequences": []
            }
        )

    def generate_questions(
        self,
        text: str,
        num_questions: Optional[int] = None,
        language: str = 'ur'
    ) -> List[Dict[str, Union[str, List[str], int]]]:
        """
        Generate listening comprehension questions using Bedrock.
        
        Args:
            text: Text to generate questions from
            num_questions: Number of questions to generate
            language: Target language for questions
            
        Returns:
            List of questions with options and correct answers
        """
        if num_questions is None:
            num_questions = app_config.QUESTIONS_PER_EXERCISE
            
        # System message to enforce JSON format
        system_message = SystemMessage(content="""You are a language learning question generator. 
Always respond with valid JSON containing multiple choice questions.
Each question must have exactly 4 options labeled A) through D).
The correct_answer must be a number 0-3 corresponding to the index of the correct option.
Include a clear explanation for each correct answer.""")
            
        # Prepare prompt for Bedrock
        prompt = f"""Create {num_questions} multiple choice questions in {language} based on this text:

{text}

Return ONLY a JSON object with this EXACT structure:
{{
    "questions": [
        {{
            "question": "Question text here",
            "options": [
                "A) First option",
                "B) Second option",
                "C) Third option",
                "D) Fourth option"
            ],
            "correct_answer": 0,
            "explanation": "Explanation for why the first option (index 0) is correct"
        }}
    ]
}}

Requirements:
1. MUST be valid JSON
2. Each question MUST have exactly 4 options
3. Options MUST be labeled A) through D)
4. correct_answer MUST be a number 0-3
5. All text MUST be in {language}
6. DO NOT include any text outside the JSON"""

        try:
            # Generate questions using LangChain Bedrock integration
            response = self.llm.invoke([
                system_message,
                HumanMessage(content=prompt)
            ])
            
            # Clean the response to ensure it's valid JSON
            content = response.content.strip()
            # Remove any text before the first {
            content = content[content.find('{'):]
            # Remove any text after the last }
            content = content[:content.rfind('}')+1]
            
            try:
                # Parse response as JSON
                questions = json.loads(content)['questions']
            except (json.JSONDecodeError, KeyError) as e:
                # If JSON parsing fails, try to extract JSON using regex
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    questions = json.loads(json_match.group(0))['questions']
                else:
                    raise ValueError("Could not extract valid JSON from response")
            
            # Validate questions
            success, message = self.validate_questions(questions)
            if not success:
                raise ValueError(f"Question validation failed: {message}")
                
            return questions
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse question generation response as JSON: {str(e)}")
        except KeyError as e:
            raise ValueError(f"Question generation response missing required fields: {str(e)}")
        except Exception as e:
            raise ValueError(f"Question generation failed: {str(e)}")

    def validate_questions(
        self,
        questions: List[Dict[str, Union[str, List[str], int]]]
    ) -> Tuple[bool, str]:
        """
        Validate generated questions for format and completeness.
        
        Args:
            questions: List of generated questions
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not questions:
            return False, "No questions generated"
            
        required_fields = {'question', 'options', 'correct_answer', 'explanation'}
        
        for i, q in enumerate(questions):
            # Check required fields
            if not all(field in q for field in required_fields):
                missing = required_fields - set(q.keys())
                return False, f"Question {i+1} missing fields: {', '.join(missing)}"
                
            # Validate options
            if not isinstance(q['options'], list):
                return False, f"Question {i+1} options must be a list"
                
            if len(q['options']) != app_config.OPTIONS_PER_QUESTION:
                return False, f"Question {i+1} must have exactly {app_config.OPTIONS_PER_QUESTION} options"
                
            # Validate option format
            for j, opt in enumerate(q['options']):
                if not opt.startswith(f"{chr(65+j)}) "):  # A), B), C), D)
                    return False, f"Question {i+1} option {j+1} must start with '{chr(65+j)}) '"
                
            # Validate correct answer
            try:
                correct_idx = int(q['correct_answer'])
                if not 0 <= correct_idx < len(q['options']):
                    return False, f"Question {i+1} correct_answer must be between 0 and {len(q['options'])-1}"
            except (ValueError, TypeError):
                return False, f"Question {i+1} correct_answer must be a number"
                
            # Validate text fields
            if not q['question'].strip():
                return False, f"Question {i+1} has empty question text"
            if not q['explanation'].strip():
                return False, f"Question {i+1} has empty explanation"
                
        return True, "Questions validated successfully"
