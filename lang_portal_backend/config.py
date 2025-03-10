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
    """AWS configuration settings."""
    
    # AWS credentials
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    
    # Required IAM permissions for each service
    REQUIRED_PERMISSIONS = [
        # Bedrock permissions
        "bedrock:ListFoundationModels",
        "bedrock:InvokeModel",
        "bedrock-runtime:InvokeModel",
        # Polly permissions
        "polly:DescribeVoices",
        "polly:SynthesizeSpeech",
        # Translate permissions
        "translate:TranslateText",
        "translate:ListLanguages"
    ]
    
    # Bedrock settings
    BEDROCK_MODEL_ID = "anthropic.claude-v2"  # Claude v2 for question generation
    BEDROCK_MAX_TOKENS = 2000
    BEDROCK_TEMPERATURE = 0.3  # Lower for more focused responses
    BEDROCK_TOP_P = 0.9
    
    # Vector store settings
    VECTOR_STORE_SIMILARITY_THRESHOLD = 0.7  # Higher means more similar
    VECTOR_STORE_EMBEDDING_DIM = 1536  # Titan embedding dimension
    VECTOR_STORE_EMBEDDING_MODEL = "amazon.titan-embed-text-v1"
    VECTOR_STORE_COLLECTION_NAME = "questions"  # ChromaDB collection name
    
    # Translation settings
    TRANSLATION_LANGUAGES = {
        "hi": "Hindi",  # Source language
        "ur": "Urdu"   # Target language
    }
    TRANSLATION_DEFAULT_SOURCE = "hi"
    TRANSLATION_DEFAULT_TARGET = "ur"
    
    # Bedrock prompt templates
    QUESTION_GENERATION_PROMPT = """You are an expert at creating multiple choice questions. Generate 5 questions based on this transcript. Your response must be ONLY a JSON array with no other text.

Each question must have these exact fields:
1. "question": A clear, focused question about key concepts
2. "options": An array of exactly 4 strings with prefixes "A. ", "B. ", "C. ", "D. "
3. "correct_answer": The full text of the correct option (must match one of the options exactly)

Example response format:
[
  {
    "question": "What is the main topic discussed?",
    "options": [
      "A. First option",
      "B. Second option",
      "C. Third option",
      "D. Fourth option"
    ],
    "correct_answer": "B. Second option"
  }
]

Transcript:
{text}"""
    
    # Polly settings
    POLLY_VOICE_ID = os.getenv('POLLY_VOICE_ID', 'Arya')
    
    # Translation settings
    TRANSLATION_FALLBACK: bool = os.getenv('TRANSLATION_FALLBACK', 'True').lower() == 'true'
    TRANSLATION_SOURCE_LANGS = ['hi', 'en']  # Source languages to translate from
    TRANSLATION_TARGET_LANG = 'ur'  # Target language (Urdu)

    @classmethod
    def validate_config(cls) -> None:
        """Validate required configuration settings."""
        missing = []
        if not cls.AWS_ACCESS_KEY_ID:
            missing.append('AWS_ACCESS_KEY_ID')
        if not cls.AWS_SECRET_ACCESS_KEY:
            missing.append('AWS_SECRET_ACCESS_KEY')
        if not cls.AWS_REGION:
            missing.append('AWS_REGION')
            
        if missing:
            raise ValueError(
                f"Missing required AWS configuration: {', '.join(missing)}. " +
                "Please set these environment variables."
            )

@dataclass
class VectorStoreConfig:
    """
    Vector store configuration using ChromaDB with Bedrock embeddings.
    
    Features:
    - ChromaDB for vector storage and similarity search
    - Bedrock embeddings (amazon.titan-embed-text-v1) for text embedding
    - Cosine similarity metric for semantic matching
    - Configurable similarity threshold and rate limiting
    """
    # ChromaDB settings
    COLLECTION_NAME: str = 'language_exercises'
    SIMILARITY_METRIC: str = 'cosine'  # Using cosine similarity for semantic matching
    EMBEDDING_DIMENSION: int = 1536  # Titan embedding dimension
    PERSIST_DIRECTORY: str = field(
        default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chroma_db')
    )
    
    # Search settings
    DEFAULT_SEARCH_LIMIT: int = 10  # Increased for better recall
    SIMILARITY_THRESHOLD: float = 0.7  # Minimum similarity score for matches
    BATCH_SIZE: int = 50  # Reduced for better rate limiting
    
    # HNSW index settings for better accuracy
    HNSW_CONSTRUCTION_EF: int = 400  # Increased for better accuracy
    HNSW_SEARCH_EF: int = 400  # Increased for better accuracy
    
    # Language-specific settings
    DEFAULT_LANGUAGE: str = 'ur'  # Default to Urdu
    SUPPORTED_LANGUAGES: List[str] = field(
        default_factory=lambda: ['ur', 'hi', 'en']  # Matches guardrails config
    )
    
    # Rate limiting settings
    MAX_CONCURRENT_REQUESTS: int = 5
    REQUEST_TIMEOUT: int = 30  # seconds

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
    # DEBUG: bool = field(
    #     default_factory=lambda: os.getenv('DEBUG', 'False').lower() == 'true'
    # )

# Create default configurations
guardrails_config = GuardrailsConfig()
aws_config = AWSConfig()
vector_store_config = VectorStoreConfig()
app_config = AppConfig()
