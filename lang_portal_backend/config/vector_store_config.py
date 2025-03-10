"""
Vector Store Configuration for Language Portal Backend.
Includes settings for ChromaDB and embeddings configuration.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Language Settings
DEFAULT_LANGUAGE = 'ur'  # Urdu
SUPPORTED_LANGUAGES = ['ur', 'hi', 'en']  # Urdu, Hindi, English

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY = os.getenv('CHROMA_PERSIST_DIRECTORY', 'chroma_db')
COLLECTION_NAME = os.getenv('CHROMA_COLLECTION_NAME', 'transcripts')
EMBEDDING_FUNCTION = 'amazon.titan-embed-text-v1'
EMBEDDING_DIMENSION = 1536  # Titan model embedding dimension

# Search Configuration
SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', '0.7'))
MAX_RESULTS = int(os.getenv('MAX_SEARCH_RESULTS', '10'))
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '100'))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '20'))

# Rate Limiting
MAX_REQUESTS_PER_MINUTE = int(os.getenv('MAX_REQUESTS_PER_MINUTE', '60'))
MAX_TOKENS_PER_REQUEST = int(os.getenv('MAX_TOKENS_PER_REQUEST', '1000'))

# Metadata Fields
METADATA_FIELDS = [
    'video_id',
    'start',
    'duration',
    'language',
    'source_language',
    'has_translation',
]

def get_vector_store_config():
    """Get vector store configuration."""
    return {
        'languages': {
            'default': DEFAULT_LANGUAGE,
            'supported': SUPPORTED_LANGUAGES,
        },
        'chroma': {
            'persist_directory': CHROMA_PERSIST_DIRECTORY,
            'collection_name': COLLECTION_NAME,
            'embedding_function': EMBEDDING_FUNCTION,
            'embedding_dimension': EMBEDDING_DIMENSION,
        },
        'search': {
            'similarity_threshold': SIMILARITY_THRESHOLD,
            'max_results': MAX_RESULTS,
            'chunk_size': CHUNK_SIZE,
            'chunk_overlap': CHUNK_OVERLAP,
        },
        'rate_limiting': {
            'max_requests_per_minute': MAX_REQUESTS_PER_MINUTE,
            'max_tokens_per_request': MAX_TOKENS_PER_REQUEST,
        },
        'metadata': {
            'fields': METADATA_FIELDS,
        },
    }
