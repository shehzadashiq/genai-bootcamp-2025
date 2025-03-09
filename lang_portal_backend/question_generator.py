"""
Question generator for language listening exercises using Amazon Bedrock.
"""
from typing import Dict, List, Optional, Tuple, Union
import boto3
import json
from config import aws_config, app_config
from langchain_core.language_models import BaseLLM
from langchain_aws.chat_models import BedrockChat

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
        
        # Initialize Bedrock LLM
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
            
        # Prepare prompt for Bedrock
        prompt = f"""Generate {num_questions} multiple choice listening comprehension questions in {language} based on this text:

{text}

For each question:
1. Create a clear, focused question
2. Provide {app_config.OPTIONS_PER_QUESTION} possible answers
3. Mark the correct answer
4. Include an explanation

Format as JSON with this structure:
{{
    "questions": [
        {{
            "question": "Question text",
            "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
            "correct_answer": "Index of correct option (0-3)",
            "explanation": "Why this is the correct answer"
        }}
    ]
}}"""

        try:
            # Generate questions using LangChain Bedrock integration
            from langchain_core.messages import HumanMessage
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Parse response as JSON
            questions = json.loads(response.content)['questions']
            
            # Validate questions
            success, message = self.validate_questions(questions)
            if not success:
                raise ValueError(f"Question validation failed: {message}")
                
            return questions
            
        except json.JSONDecodeError:
            raise ValueError("Failed to parse question generation response as JSON")
        except KeyError:
            raise ValueError("Question generation response missing required fields")
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
                return False, f"Question {i+1} missing required fields"
                
            # Validate options
            if len(q['options']) != app_config.OPTIONS_PER_QUESTION:
                return False, f"Question {i+1} has wrong number of options"
                
            # Validate correct answer
            try:
                correct_idx = int(q['correct_answer'])
                if not 0 <= correct_idx < len(q['options']):
                    return False, f"Question {i+1} has invalid correct_answer index"
            except (ValueError, TypeError):
                return False, f"Question {i+1} has invalid correct_answer format"
                
        return True, "Questions validated successfully"
