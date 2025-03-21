"""
Configuration settings for the Language Listening Application.
Includes guardrails configuration and AWS service settings.
"""
from typing import Dict, List
from dataclasses import dataclass, field
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass
class GuardrailsConfig:
    # Rate limiting settings
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Content safety thresholds
    TOXIC_CONTENT_THRESHOLD: float = 0.7
    
    # Audio constraints
    MIN_AUDIO_DURATION: float = 3.0  # seconds
    MAX_AUDIO_DURATION: float = 300.0  # seconds
    
    # Supported languages
    SUPPORTED_LANGUAGES: Dict[str, str] = field(
        default_factory=lambda: {
            'ur': 'Urdu',
            'hi': 'Hindi',
            'en': 'English'
        }
    )
    
    # Language detection confidence threshold
    LANGUAGE_CONFIDENCE_THRESHOLD: float = 0.8

class AWSConfig:
    """AWS service configuration."""
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # Bedrock models
    BEDROCK_MODEL_ID = os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-v2').strip('"')  # Strip quotes if present
    BEDROCK_EMBEDDING_MODEL = os.getenv('BEDROCK_EMBEDDING_MODEL', 'amazon.titan-embed-text-v1').strip('"')
    
    # Polly settings
    POLLY_VOICE_ID = os.getenv('POLLY_VOICE_ID', 'Arya')
    
    # Translation settings
    TRANSLATION_FALLBACK: bool = os.getenv('TRANSLATION_FALLBACK', 'True').lower() == 'true'

@dataclass
class VectorStoreConfig:
    # ChromaDB settings
    COLLECTION_NAME: str = 'listening_exercises'
    SIMILARITY_METRIC: str = 'cosine'
    EMBEDDING_DIMENSION: int = 1536  # Titan embedding dimension
    PERSIST_DIRECTORY: str = field(
        default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vector_store')
    )
    
    # Search settings
    DEFAULT_SEARCH_LIMIT: int = 5
    SIMILARITY_THRESHOLD: float = 0.7

@dataclass
class AppConfig:
    # Streamlit settings
    APP_TITLE: str = "Language Listening Practice App"
    THEME_PRIMARY_COLOR: str = "#FF4B4B"
    
    # Exercise generation settings
    QUESTIONS_PER_EXERCISE: int = 3
    OPTIONS_PER_QUESTION: int = 4
    
    # YouTube settings
    MAX_TRANSCRIPT_LENGTH: int = 5000  # characters
    
    # Debug mode
    DEBUG: bool = field(
        default_factory=lambda: os.getenv('DEBUG', 'False').lower() == 'true'
    )

# Create default configurations
guardrails_config = GuardrailsConfig()
aws_config = AWSConfig()
vector_store_config = VectorStoreConfig()
app_config = AppConfig()
