"""
Language Listening Application with guardrails.
Integrates YouTube transcripts, AWS services, and vector storage.
"""
import boto3
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
from services.vector_store_service import VectorStoreService
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
        self.vector_store = VectorStoreService()  # Use VectorStoreService directly
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
        try:
            # Get transcript list
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            transcript = None
            # Try to get Hindi transcript (including auto-generated)
            try:
                # Get all available transcripts
                available_transcripts = transcript_list._manually_created_transcripts.copy()
                available_transcripts.update(transcript_list._generated_transcripts)
                
                # Look for Hindi transcripts
                hindi_transcripts = [t for t in available_transcripts.values() if t.language_code == 'hi']
                if hindi_transcripts:
                    # Prefer manually created over auto-generated
                    transcript = next((t for t in hindi_transcripts if not t.is_generated), None)
                    if transcript:
                        print("Found manual Hindi transcript")
                    else:
                        # Use auto-generated if no manual transcript
                        transcript = hindi_transcripts[0]
                        print("Found auto-generated Hindi transcript")
            except Exception as e:
                print(f"Error getting Hindi transcript: {e}")
            
            # If no Hindi transcript, try Urdu
            if not transcript:
                try:
                    urdu_transcripts = [t for t in available_transcripts.values() if t.language_code == 'ur']
                    if urdu_transcripts:
                        transcript = urdu_transcripts[0]
                        print("Found Urdu transcript")
                except Exception as e:
                    print(f"No Urdu transcript available: {e}")
            
            # If still no transcript, try English as last resort
            if not transcript:
                try:
                    english_transcripts = [t for t in available_transcripts.values() if t.language_code == 'en']
                    if english_transcripts:
                        transcript = english_transcripts[0]
                        print("Using English transcript as fallback")
                except Exception as e:
                    print(f"No English transcript available: {e}")
                    # Try any available transcript as last resort
                    if available_transcripts:
                        transcript = next(iter(available_transcripts.values()))
                        print(f"Using available transcript in {transcript.language_code}")
            
            if not transcript:
                raise Exception("No transcript found in any language")
            
            # Get transcript data
            transcript_data = transcript.fetch()
            source_lang = transcript.language_code
            
            # Convert to Urdu if needed
            if source_lang != 'ur':
                processed_transcript = []
                for entry in transcript_data:
                    text = entry['text'].strip()
                    if text:
                        try:
                            urdu_text = self.convert_hindi_to_urdu(text)
                            processed_transcript.append({
                                **entry,
                                'text': urdu_text,
                                'original_text': text,
                                'source_language': source_lang
                            })
                        except Exception as e:
                            print(f"Error converting text to Urdu: {e}")
                            processed_transcript.append(entry)
            else:
                processed_transcript = transcript_data
            
            # Create exercise
            exercise = {
                'video_id': video_id,
                'language': 'ur',  # Target language is always Urdu
                'source_language': source_lang,
                'transcript': processed_transcript
            }
            
            return exercise
            
        except Exception as e:
            print(f"Error fetching transcript: {e}")
            raise e

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
        
        # Combine all transcript segments into full text
        full_text = " ".join(
            segment['text'].strip()
            for segment in exercise['transcript']
            if segment.get('text', '').strip()
        )
        exercise['full_text'] = full_text
        
        try:
            # Generate questions
            questions = self.question_generator.generate_questions(
                full_text,
                language=language
            )
            exercise['questions'] = questions
            
            # Generate audio
            audio = self.generate_audio(full_text, language)
            exercise['audio'] = base64.b64encode(audio).decode()
            
            return exercise
            
        except Exception as e:
            print(f"Error creating exercise: {str(e)}")
            raise ValueError(f"Failed to create exercise: {str(e)}")

    def display_exercise(self, exercise: Dict):
        """
        Display an exercise in the Streamlit UI.
        
        Args:
            exercise: Exercise to display
        """
        st.write("## Exercise Text")
        # Display full text if available, otherwise fall back to first segment
        if 'full_text' in exercise:
            st.write(exercise['full_text'])
        else:
            segments_text = " ".join(
                segment['text'].strip()
                for segment in exercise['transcript']
                if segment.get('text', '').strip()
            )
            st.write(segments_text)
        
        st.write("## Audio")
        st.audio(
            base64.b64decode(exercise['audio']),
            format='audio/mp3'
        )
        
        st.write("## Questions")
        if 'questions' in exercise:
            for i, q in enumerate(exercise['questions']):
                st.write(f"### Question {i+1}")
                st.write(q['question'])
                
                # Display options
                for option in q['options']:
                    st.write(option)
                
                # Add answer button
                if st.button(f"Show Answer {i+1}"):
                    st.write(f"Correct Answer: {q['options'][int(q['correct_answer'])]}")
                    st.write(f"Explanation: {q['explanation']}")
        else:
            st.error("No questions available for this exercise.")

    def practice_exercise(
        self,
        text: str,
        language: str = 'ur'
    ) -> Dict:
        """
        Create a practice exercise from a given text.
        
        Args:
            text: Text to practice
            language: Target language code
            
        Returns:
            Complete exercise with transcript, audio, and questions
        """
        try:
            # Generate questions
            questions = self.question_generator.generate_questions(
                text,
                language=language
            )
            
            # Generate audio
            audio = self.generate_audio(text, language)
            
            exercise = {
                'text': text,
                'questions': questions,
                'audio': base64.b64encode(audio).decode()
            }
            
            return exercise
            
        except Exception as e:
            print(f"Error creating exercise: {str(e)}")
            raise ValueError(f"Failed to create exercise: {str(e)}")

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
                    exercise = app.practice_exercise(text)
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
