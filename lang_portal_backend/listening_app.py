"""
Example implementation of the Language Listening Application with guardrails.
Demonstrates integration with YouTube transcripts, AWS services, and vector storage.
"""
import boto3
import chromadb
from youtube_transcript_api import YouTubeTranscriptApi
from typing import Dict, List, Optional, Tuple
from guardrails import with_guardrails, LanguageGuardrails
import streamlit as st
from langchain.embeddings import BedrockEmbeddings
import json
from config import aws_config, vector_store_config, app_config
from config_validation import validate_all_configs, ConfigValidationError
from hindi_urdu_converter import HindiUrduConverter
from vector_store import VectorStore

class LanguageListeningApp:
    def __init__(self):
        # Validate all configurations before initializing
        self._validate_configuration()
        
        # Initialize AWS clients with config
        self.bedrock = boto3.client(
            'bedrock-runtime',
            region_name=aws_config.AWS_REGION
        )
        self.polly = boto3.client(
            'polly',
            region_name=aws_config.AWS_REGION
        )
        self.translate = boto3.client(
            'translate',
            region_name=aws_config.AWS_REGION
        )
        
        # Initialize vector store
        self.vector_store = VectorStore()
        
        # Initialize Bedrock embeddings with config
        self.embeddings = BedrockEmbeddings(
            client=self.bedrock,
            model_id=aws_config.BEDROCK_EMBEDDING_MODEL
        )
        
        # Initialize Hindi-Urdu converter
        self.hindi_urdu_converter = HindiUrduConverter()

    def _validate_configuration(self):
        """Validate all configurations before starting the application."""
        results = validate_all_configs()
        invalid_configs = [r for r in results if r['status'] == 'invalid']
        
        if invalid_configs:
            error_msg = "\n".join([
                f"- {r['component']}: {r['message']}"
                for r in invalid_configs
            ])
            raise ConfigValidationError(
                f"Configuration validation failed:\n{error_msg}"
            )

    @with_guardrails
    def fetch_youtube_transcript(
        self, 
        video_id: str, 
        language: str = 'ur',
        user_id: str = 'default'
    ) -> List[Dict]:
        """
        Fetch and validate transcript from YouTube.
        """
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id, 
            languages=[language]
        )
        
        # Combine transcript segments and validate
        full_text = ' '.join(segment['text'] for segment in transcript)
        
        # Check transcript length
        if len(full_text) > app_config.MAX_TRANSCRIPT_LENGTH:
            raise ValueError(f"Transcript too long (maximum {app_config.MAX_TRANSCRIPT_LENGTH} characters)")
            
        return transcript, full_text

    @with_guardrails
    def generate_listening_exercise(
        self,
        text: str,
        language: str = 'ur',
        user_id: str = 'default'
    ) -> Dict:
        """
        Generate a listening exercise with questions.
        """
        # Use Bedrock to generate questions
        prompt = f"""
        Generate {app_config.QUESTIONS_PER_EXERCISE} listening comprehension questions in {language} for the following text:
        {text}
        
        Each question should have {app_config.OPTIONS_PER_QUESTION} options.
        
        Format as JSON with the following structure:
        {{
            "questions": [
                {{
                    "question": "question text",
                    "options": ["option1", "option2", "option3", "option4"],
                    "correct_answer": "correct option"
                }}
            ]
        }}
        """
        
        response = self.bedrock.invoke_model(
            modelId=aws_config.BEDROCK_MODEL_ID,
            body=json.dumps({
                "prompt": prompt,
                "max_tokens": 1000,
                "temperature": 0.7
            })
        )
        
        exercise = json.loads(response['body'].read())
        return exercise

    @with_guardrails
    def generate_audio(
        self,
        text: str,
        language: str = 'ur',
        user_id: str = 'default'
    ) -> bytes:
        """
        Generate audio for the text using Amazon Polly.
        For Urdu, first convert Hindi script to Urdu if needed.
        """
        # If text is in Hindi script, convert to Urdu
        if language == 'ur':
            try:
                # Try AWS Translate first (primary method)
                response = self.translate.translate_text(
                    Text=text,
                    SourceLanguageCode='hi',
                    TargetLanguageCode='ur'
                )
                text = response['TranslatedText']
            except Exception as e:
                if aws_config.TRANSLATION_FALLBACK:
                    # Use character mapping fallback system
                    text = self.hindi_urdu_converter.convert(text)
                else:
                    raise e
        
        response = self.polly.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=aws_config.POLLY_VOICE_ID
        )
        
        return response['AudioStream'].read()

    def _convert_hindi_to_urdu(self, text: str) -> str:
        """
        Convert Hindi text to Urdu script using our robust conversion system.
        Uses AWS Translate as primary method with character mapping fallback.
        """
        try:
            # Try AWS Translate first (primary method)
            response = self.translate.translate_text(
                Text=text,
                SourceLanguageCode='hi',
                TargetLanguageCode='ur'
            )
            return response['TranslatedText']
        except Exception as e:
            if aws_config.TRANSLATION_FALLBACK:
                # Use character mapping fallback system
                return self.hindi_urdu_converter.convert(text)
            else:
                raise e

    @with_guardrails
    def store_exercise(
        self,
        exercise: Dict,
        metadata: Optional[Dict] = None,
        user_id: str = 'default'
    ) -> str:
        """
        Store a language exercise in the vector store.
        
        Args:
            exercise: Exercise content including transcript, questions, etc.
            metadata: Optional metadata like language, difficulty, etc.
            user_id: User ID for rate limiting
            
        Returns:
            ID of the stored exercise
        """
        # Add user_id to metadata
        if metadata is None:
            metadata = {}
        metadata['user_id'] = user_id
        
        # Store in vector store
        exercise_id = self.vector_store.add_exercise(
            content=exercise,
            metadata=metadata
        )
        
        return exercise_id

    @with_guardrails
    def find_similar_exercises(
        self,
        query: str,
        language: str = 'ur',
        limit: Optional[int] = None,
        user_id: str = 'default'
    ) -> List[Dict]:
        """
        Find similar exercises using semantic search.
        
        Args:
            query: Search query
            language: Target language
            limit: Maximum number of results
            user_id: User ID for rate limiting
            
        Returns:
            List of similar exercises
        """
        # Set up metadata filter for language
        where = {'language': language} if language else None
        
        # Search vector store
        exercises = self.vector_store.search_similar(
            query=query,
            n_results=limit,
            where=where
        )
        
        return exercises

    @with_guardrails
    def get_exercise_by_id(
        self,
        exercise_id: str,
        user_id: str = 'default'
    ) -> Optional[Dict]:
        """
        Retrieve a specific exercise by ID.
        
        Args:
            exercise_id: ID of the exercise
            user_id: User ID for rate limiting
            
        Returns:
            Exercise content if found, None otherwise
        """
        return self.vector_store.get_exercise(exercise_id)

    @with_guardrails
    def list_user_exercises(
        self,
        user_id: str = 'default',
        language: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        List exercises for a specific user.
        
        Args:
            user_id: User ID
            language: Optional language filter
            limit: Maximum number of exercises to return
            
        Returns:
            List of exercises
        """
        # Set up metadata filter
        where = {'user_id': user_id}
        if language:
            where['language'] = language
            
        return self.vector_store.list_exercises(
            where=where,
            limit=limit
        )

    @with_guardrails
    def update_exercise(
        self,
        exercise_id: str,
        exercise: Dict,
        metadata: Optional[Dict] = None,
        user_id: str = 'default'
    ) -> None:
        """
        Update an existing exercise.
        
        Args:
            exercise_id: ID of the exercise to update
            exercise: New exercise content
            metadata: Optional new metadata
            user_id: User ID for rate limiting
        """
        # Update in vector store
        self.vector_store.update_exercise(
            exercise_id=exercise_id,
            content=exercise,
            metadata=metadata
        )

    @with_guardrails
    def delete_exercise(
        self,
        exercise_id: str,
        user_id: str = 'default'
    ) -> None:
        """
        Delete an exercise.
        
        Args:
            exercise_id: ID of the exercise to delete
            user_id: User ID for rate limiting
        """
        self.vector_store.delete_exercise(exercise_id)

def main():
    st.set_page_config(
        page_title=app_config.APP_TITLE,
        page_icon="🎧",
        layout="wide"
    )
    
    st.title(app_config.APP_TITLE)
    
    try:
        app = LanguageListeningApp()
        
        if app_config.DEBUG:
            st.warning("Running in DEBUG mode")
            
            # Display configuration validation results in debug mode
            with st.expander("Configuration Validation Results"):
                results = validate_all_configs()
                for result in results:
                    status_color = "green" if result['status'] == 'valid' else "red"
                    st.markdown(
                        f"**{result['component']}**: "
                        f":{status_color}[circle]: {result['message']}"
                    )
        
        # YouTube URL input
        youtube_url = st.text_input("Enter YouTube URL:")
        if youtube_url and st.button("Generate Exercise"):
            try:
                # Extract video ID from URL
                video_id = youtube_url.split("v=")[1]
                
                with st.spinner("Fetching transcript..."):
                    transcript, full_text = app.fetch_youtube_transcript(
                        video_id=video_id,
                        language='ur',
                        user_id='default'
                    )
                
                with st.spinner("Generating exercise..."):
                    exercise = app.generate_listening_exercise(
                        text=full_text,
                        language='ur',
                        user_id='default'
                    )
                
                with st.spinner("Generating audio..."):
                    audio = app.generate_audio(
                        text=full_text,
                        language='ur',
                        user_id='default'
                    )
                
                # Store exercise
                exercise_id = app.store_exercise(
                    exercise=exercise,
                    metadata={'language': 'ur'},
                    user_id='default'
                )
                
                # Display exercise
                st.audio(audio)
                for q in exercise['questions']:
                    st.write(q['question'])
                    answer = st.radio(
                        "Choose your answer:",
                        q['options'],
                        key=hash(q['question'])
                    )
                    if st.button("Check", key=f"check_{hash(q['question'])}"):
                        if answer == q['correct_answer']:
                            st.success("Correct!")
                        else:
                            st.error(f"Incorrect. The answer is: {q['correct_answer']}")
                            
            except Exception as e:
                st.error(f"Error: {str(e)}")
                if app_config.DEBUG:
                    st.exception(e)
        
        # Search similar exercises
        st.header("Search Similar Exercises")
        query = st.text_input("Enter topic to search for:")
        if query and st.button("Search"):
            with st.spinner("Searching..."):
                similar = app.find_similar_exercises(
                    query=query,
                    language='ur',
                    user_id='default'
                )
                
            if not similar:
                st.info("No similar exercises found")
            else:
                for ex in similar:
                    st.write("---")
                    st.write(f"Text: {ex['text']}")
                    st.write("Questions:")
                    for q in ex['exercise']['questions']:
                        st.write(f"- {q['question']}")
                        
    except ConfigValidationError as e:
        st.error("Configuration Error")
        st.error(str(e))
        if app_config.DEBUG:
            st.exception(e)
    except Exception as e:
        st.error("Application Error")
        st.error(str(e))
        if app_config.DEBUG:
            st.exception(e)

if __name__ == "__main__":
    main()
