"""
Language Listening Application with guardrails.
Integrates YouTube transcripts, AWS services, and vector storage.
"""
import boto3
import chromadb
from youtube_transcript_api import YouTubeTranscriptApi
from typing import Dict, List, Optional, Tuple
from guardrails import with_guardrails, LanguageGuardrails
import streamlit as st
from langchain_aws import BedrockEmbeddings
import json
import base64
from config import aws_config, vector_store_config, app_config
from config_validation import validate_all_configs, ConfigValidationError
from hindi_urdu_converter import HindiUrduConverter
from vector_store import VectorStore
from question_generator import QuestionGenerator
from gtts import gTTS
import tempfile
import os

class LanguageListeningApp:
    def __init__(self):
        """Initialize the Language Listening Application."""
        # Validate configuration
        self._validate_configuration()
        
        # Initialize AWS clients
        self.bedrock = boto3.client(
            'bedrock',
            region_name=aws_config.AWS_REGION
        )
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=aws_config.AWS_REGION
        )
        self.translate = boto3.client(
            'translate',
            region_name=aws_config.AWS_REGION
        )
        
        # Try to initialize Polly, use gTTS as fallback
        try:
            self.polly = boto3.client(
                'polly',
                region_name=aws_config.AWS_REGION
            )
            self.use_polly = True
            print("Using Amazon Polly for TTS")
        except Exception as e:
            self.polly = None
            self.use_polly = False
            print("Falling back to gTTS for text-to-speech")
        
        # Initialize components
        self.guardrails = LanguageGuardrails()
        self.vector_store = VectorStore()
        self.question_generator = QuestionGenerator()
        self.converter = HindiUrduConverter()
        
        # Initialize session state
        if 'exercises' not in st.session_state:
            st.session_state.exercises = []
        if 'current_exercise' not in st.session_state:
            st.session_state.current_exercise = None
        if 'audio_cache' not in st.session_state:
            st.session_state.audio_cache = {}

    def _validate_configuration(self):
        """Validate all configuration settings."""
        results = validate_all_configs()
        
        # Check for critical failures
        critical_failures = [
            (name, message) for name, (success, message) in results.items()
            if not success and name != 'polly_voice'  # Polly is optional
        ]
        
        if critical_failures:
            error_msg = "\n".join([f"{name}: {message}" for name, message in critical_failures])
            raise ConfigValidationError(f"Configuration validation failed:\n{error_msg}")

    @with_guardrails
    def fetch_youtube_transcript(
        self,
        video_id: str,
        language: str = 'ur'
    ) -> Dict:
        """
        Fetch and process YouTube transcript.
        
        Args:
            video_id: YouTube video ID
            language: Target language code
            
        Returns:
            Processed transcript with metadata
        """
        # Get transcript
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id,
            languages=[language]
        )
        
        # Combine transcript text
        text = " ".join([entry['text'] for entry in transcript])
        
        # Create exercise
        exercise = {
            'video_id': video_id,
            'language': language,
            'text': text,
            'transcript': transcript
        }
        
        return exercise

    def generate_audio(
        self,
        text: str,
        language: str = 'ur'
    ) -> bytes:
        """
        Generate audio from text using available TTS service.
        Falls back to gTTS if Polly is not available.
        
        Args:
            text: Text to synthesize
            language: Target language code
            
        Returns:
            Audio data as bytes
        """
        # Check audio cache
        cache_key = f"{text}:{language}"
        if cache_key in st.session_state.audio_cache:
            return st.session_state.audio_cache[cache_key]
        
        try:
            if self.use_polly:
                # Try Polly first
                response = self.polly.synthesize_speech(
                    Text=text,
                    OutputFormat='mp3',
                    VoiceId=aws_config.POLLY_VOICE_ID
                )
                audio_data = response['AudioStream'].read()
                
                # Cache the audio
                st.session_state.audio_cache[cache_key] = audio_data
                return audio_data
                
        except Exception as e:
            print(f"Polly synthesis failed, falling back to gTTS: {str(e)}")
            self.use_polly = False  # Disable Polly for future requests
        
        # Fallback to gTTS
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            try:
                tts = gTTS(text=text, lang=language)
                tts.save(temp_file.name)
                with open(temp_file.name, 'rb') as f:
                    audio_data = f.read()
                os.unlink(temp_file.name)  # Clean up temp file
                
                # Cache the audio
                st.session_state.audio_cache[cache_key] = audio_data
                return audio_data
                
            except Exception as e:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)  # Clean up on error
                raise e

    def convert_hindi_to_urdu(self, text: str) -> str:
        """
        Convert Hindi text to Urdu script.
        Uses AWS Translate with fallback to character mapping.
        
        Args:
            text: Hindi text to convert
            
        Returns:
            Converted Urdu text
        """
        try:
            # Try AWS Translate first
            response = self.translate.translate_text(
                Text=text,
                SourceLanguageCode='hi',
                TargetLanguageCode='ur'
            )
            return response['TranslatedText']
            
        except Exception as e:
            if aws_config.TRANSLATION_FALLBACK:
                # Use character mapping fallback
                return self.converter.convert(text)
            raise e

    def create_exercise_from_youtube(
        self,
        video_id: str,
        language: str = 'ur'
    ) -> Dict:
        """
        Create a complete exercise from a YouTube video.
        
        Args:
            video_id: YouTube video ID
            language: Target language code
            
        Returns:
            Complete exercise with transcript, audio, and questions
        """
        # Fetch transcript
        exercise = self.fetch_youtube_transcript(video_id, language)
        
        # Generate questions
        questions = self.question_generator.generate_questions(
            exercise['text'],
            language=language
        )
        exercise['questions'] = questions
        
        # Generate audio
        audio = self.generate_audio(exercise['text'], language)
        exercise['audio'] = base64.b64encode(audio).decode()
        
        return exercise

    def display_exercise(self, exercise: Dict):
        """
        Display an exercise in the Streamlit UI.
        
        Args:
            exercise: Exercise to display
        """
        st.write("## Exercise Text")
        st.write(exercise['text'])
        
        st.write("## Audio")
        st.audio(
            base64.b64decode(exercise['audio']),
            format='audio/mp3'
        )
        
        st.write("## Questions")
        for i, q in enumerate(exercise['questions']):
            st.write(f"### Question {i+1}")
            st.write(q['question'])
            
            # Display options
            for j, option in enumerate(q['options']):
                st.write(f"{option}")
            
            # Add answer button
            if st.button(f"Show Answer {i+1}"):
                st.write(f"Correct Answer: {q['options'][int(q['correct_answer'])]}")
                st.write(f"Explanation: {q['explanation']}")

def main():
    """Main Streamlit application."""
    st.title("Language Listening Practice")
    
    try:
        # Initialize app
        app = LanguageListeningApp()
        
        # Sidebar navigation
        mode = st.sidebar.selectbox(
            "Mode",
            ["YouTube Exercise", "Practice", "My Exercises"]
        )
        
        if mode == "YouTube Exercise":
            st.write("## Create Exercise from YouTube")
            video_id = st.text_input("Enter YouTube Video ID")
            
            if st.button("Create Exercise"):
                with st.spinner("Creating exercise..."):
                    exercise = app.create_exercise_from_youtube(video_id)
                    st.session_state.current_exercise = exercise
                    
            if st.session_state.current_exercise:
                app.display_exercise(st.session_state.current_exercise)
                
        elif mode == "Practice":
            st.write("## Practice Exercises")
            text = st.text_area("Enter text for practice")
            
            if st.button("Generate Exercise"):
                with st.spinner("Generating exercise..."):
                    # Generate questions
                    questions = app.question_generator.generate_questions(text)
                    
                    # Generate audio
                    audio = app.generate_audio(text)
                    
                    exercise = {
                        'text': text,
                        'questions': questions,
                        'audio': base64.b64encode(audio).decode()
                    }
                    st.session_state.current_exercise = exercise
                    
            if st.session_state.current_exercise:
                app.display_exercise(st.session_state.current_exercise)
                
        else:  # My Exercises
            st.write("## My Exercises")
            exercises = app.vector_store.list_exercises()
            
            if exercises:
                for exercise in exercises:
                    st.write(f"### Exercise {exercise['id']}")
                    if st.button(f"Load Exercise {exercise['id']}"):
                        st.session_state.current_exercise = exercise
                        
                if st.session_state.current_exercise:
                    app.display_exercise(st.session_state.current_exercise)
            else:
                st.write("No exercises found. Create some exercises first!")
                
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.write("Please check your configuration and try again.")

if __name__ == "__main__":
    main()
