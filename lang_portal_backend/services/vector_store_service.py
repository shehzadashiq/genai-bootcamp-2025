"""
Vector store service implementation using ChromaDB.
Provides robust vector similarity search for language exercises using:
- ChromaDB for vector storage and similarity search
- Bedrock embeddings (amazon.titan-embed-text-v1) for text embedding
- Cosine similarity metric for semantic matching
- Configurable similarity threshold and rate limiting
"""
import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
import boto3
from config import vector_store_config, aws_config
from datetime import datetime
from .language_service import LanguageService
from .bedrock_embeddings import BedrockEmbeddingFunction

logger = logging.getLogger(__name__)

class VectorStoreService:
    _instance = None
    _language_service = None
    _client = None
    _collection = None
    _bedrock_client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStoreService, cls).__new__(cls)
            try:
                cls._language_service = LanguageService()
                cls._bedrock_client = boto3.client(
                    'bedrock-runtime',
                    region_name=aws_config.AWS_REGION,
                    aws_access_key_id=aws_config.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=aws_config.AWS_SECRET_ACCESS_KEY
                )
                cls.initialize()
                logger.info("Vector store initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing ChromaDB: {e}")
                raise
        return cls._instance
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize ChromaDB database with Bedrock embeddings."""
        try:
            # Get persist directory from config
            persist_dir = os.path.abspath(vector_store_config.PERSIST_DIRECTORY)
            
            # Ensure persistence directory exists
            os.makedirs(persist_dir, exist_ok=True)
            
            # Initialize ChromaDB client
            cls._client = chromadb.PersistentClient(
                path=persist_dir
            )
            
            # Initialize custom Bedrock embedding function with enhanced settings
            embedding_function = BedrockEmbeddingFunction(
                client=cls._bedrock_client,
                model_id=aws_config.BEDROCK_EMBEDDING_MODEL,
                normalize_embeddings=True  # Enable L2 normalization for better cosine similarity
            )
            
            # Get or create collection with enhanced settings
            cls._collection = cls._client.get_or_create_collection(
                name=vector_store_config.COLLECTION_NAME,
                embedding_function=embedding_function,
                metadata={
                    "hnsw:space": vector_store_config.SIMILARITY_METRIC,
                    "hnsw:construction_ef": vector_store_config.HNSW_CONSTRUCTION_EF,
                    "hnsw:search_ef": vector_store_config.HNSW_SEARCH_EF,
                    "dimension": vector_store_config.EMBEDDING_DIMENSION,
                    "supported_languages": ",".join(vector_store_config.SUPPORTED_LANGUAGES),
                    "default_language": vector_store_config.DEFAULT_LANGUAGE
                }
            )
            
            logger.info(f"ChromaDB initialized successfully at {persist_dir}")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise
    
    def _preprocess_text(self, text: str, language: str = None) -> str:
        """Preprocess text for better semantic matching."""
        try:
            # Remove extra whitespace
            text = " ".join(text.split())
            
            # Convert script if needed
            if language == "ur" and self._language_service:
                text = self._language_service.convert_hindi_to_urdu(text)
            
            return text
        except Exception as e:
            logger.error(f"Error preprocessing text: {e}")
            return text
    
    def add_transcript(self, video_id: str, segments: List[Dict[str, Any]]) -> bool:
        """
        Add transcript segments to vector store.
        
        Args:
            video_id: YouTube video ID
            segments: List of transcript segments with text and metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not segments:
                logger.warning("No segments provided to add_transcript")
                return False
            
            # Prepare document data
            ids = []
            texts = []
            metadatas = []
            
            for i, segment in enumerate(segments):
                # Generate unique document ID
                doc_id = f"{video_id}_{i}"
                
                # Get text content and preprocess
                text = segment.get('text', '').strip()
                if not text:
                    continue
                
                # Preprocess text for better semantic matching
                language = segment.get('language', vector_store_config.DEFAULT_LANGUAGE)
                processed_text = self._preprocess_text(text, language)
                
                # Prepare metadata (ensure all values are scalar types)
                metadata = {
                    'video_id': video_id,
                    'start': str(segment.get('start', 0)),
                    'duration': str(segment.get('duration', 0)),
                    'language': language,
                    'timestamp': datetime.utcnow().isoformat(),
                    'source_language': segment.get('source_language', vector_store_config.DEFAULT_LANGUAGE),
                    'has_translation': str(segment.get('has_translation', False)).lower(),
                    'original_text': segment.get('original_text', text)
                }
                
                ids.append(doc_id)
                texts.append(processed_text)
                metadatas.append(metadata)
            
            if not texts:
                logger.warning("No valid text segments found")
                return False
            
            # Add documents in batches
            batch_size = vector_store_config.BATCH_SIZE
            for i in range(0, len(texts), batch_size):
                batch_end = min(i + batch_size, len(texts))
                self._collection.add(
                    ids=ids[i:batch_end],
                    documents=texts[i:batch_end],
                    metadatas=metadatas[i:batch_end]
                )
            
            logger.info(f"Successfully added {len(texts)} segments for video {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding transcript to vector store: {e}")
            return False
    
    def search_transcripts(self, query: str, k: int = None, min_score: float = None, language: str = None) -> List[Dict]:
        """
        Search for similar transcript segments using vector similarity search.
        
        Args:
            query: Search query text
            k: Number of results to return (default: DEFAULT_SEARCH_LIMIT)
            min_score: Minimum similarity score (default: SIMILARITY_THRESHOLD)
            language: Filter by language (default: None, search all languages)
            
        Returns:
            List of transcript segments with similarity scores
        """
        try:
            # Set default parameters from config
            k = k or vector_store_config.DEFAULT_SEARCH_LIMIT
            min_score = min_score or vector_store_config.SIMILARITY_THRESHOLD
            
            # Preprocess query text
            processed_query = self._preprocess_text(query, language)
            
            # Prepare where clause for language filtering
            where = {}
            if language:
                if language not in vector_store_config.SUPPORTED_LANGUAGES:
                    logger.warning(f"Unsupported language: {language}")
                    return []
                where["language"] = language
            
            # Query collection with enhanced parameters
            results = self._collection.query(
                query_texts=[processed_query],
                n_results=k * 2,  # Get more results to filter by score
                where=where,
                include=["metadatas", "documents", "distances"]
            )
            
            if not results or not results["ids"]:
                logger.info("No results found")
                return []
            
            # Process and format results
            processed_results = []
            for i in range(len(results["ids"][0])):
                # Convert distance to cosine similarity score (1 - distance)
                score = 1 - float(results["distances"][0][i])
                
                # Filter by minimum similarity score
                if score < min_score:
                    continue
                
                # Get result metadata
                metadata = results["metadatas"][0][i]
                
                # Convert metadata values back to appropriate types
                result = {
                    'id': results["ids"][0][i],
                    'text': results["documents"][0][i],
                    'score': round(score, 4),
                    'video_id': metadata['video_id'],
                    'start': float(metadata['start']),
                    'duration': float(metadata['duration']),
                    'language': metadata['language'],
                    'source_language': metadata['source_language'],
                    'has_translation': metadata['has_translation'] == 'true',
                    'original_text': metadata['original_text']
                }
                processed_results.append(result)
            
            # Sort by score and limit to k results
            processed_results.sort(key=lambda x: x['score'], reverse=True)
            return processed_results[:k]
            
        except Exception as e:
            logger.error(f"Error searching transcripts: {e}")
            return []
    
    def delete_video_chunks(self, video_id: str) -> bool:
        """Delete all chunks for a specific video with rate limiting."""
        try:
            # Get IDs first to ensure atomic deletion
            results = self._collection.get(
                where={"video_id": video_id}
            )
            
            if results and results['ids']:
                # Delete in batches to handle large videos
                batch_size = vector_store_config.BATCH_SIZE
                for i in range(0, len(results['ids']), batch_size):
                    batch_end = min(i + batch_size, len(results['ids']))
                    self._collection.delete(
                        ids=results['ids'][i:batch_end]
                    )
                    logger.debug(f"Deleted batch {i//batch_size + 1} of {(len(results['ids']) + batch_size - 1)//batch_size}")
                
                logger.info(f"Deleted {len(results['ids'])} chunks for video {video_id}")
                return True
            
            logger.warning(f"No chunks found for video {video_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error deleting chunks: {e}")
            return False
