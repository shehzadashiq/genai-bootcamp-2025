import chromadb
import hashlib
import json
import logging
from typing import Dict, Optional, Any
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store service for caching summaries."""

    def __init__(self):
        """Initialize the vector store."""
        # Create data directory if it doesn't exist
        self.data_dir = "data/chroma"
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(path=self.data_dir)
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="summaries",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Use 384-dimensional dummy embedding to match collection
        self.dummy_embedding = [0.0] * 384
        
        logger.info("Vector store initialized")
    
    def _generate_content_hash(self, content: Any, content_type: str) -> str:
        """Generate a unique hash for content based on its type."""
        if isinstance(content, bytes):
            return hashlib.sha256(content).hexdigest()
        elif isinstance(content, str):
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        elif isinstance(content, dict):
            return hashlib.sha256(json.dumps(content, sort_keys=True).encode('utf-8')).hexdigest()
        else:
            raise ValueError(f"Unsupported content type for hashing: {type(content)}")

    def _get_cache_key(self, content: Any, content_type: str) -> str:
        """Generate a cache key based on content type and content."""
        content_hash = self._generate_content_hash(content, content_type)
        return f"{content_type}:{content_hash}"

    def _sanitize_metadata(self, metadata: Dict) -> Dict:
        """Sanitize metadata to ensure all values are valid types.
        
        Args:
            metadata: Dictionary of metadata
            
        Returns:
            Dict with sanitized values (only str, int, float, or bool)
        """
        sanitized = {}
        for key, value in metadata.items():
            if value is None:
                sanitized[key] = ""  # Convert None to empty string
            elif isinstance(value, (str, int, float, bool)):
                sanitized[key] = value
            else:
                sanitized[key] = str(value)  # Convert other types to string
        return sanitized

    async def get_summary(self, content: Any, content_type: str) -> Optional[Dict]:
        """Get a summary from the vector store cache.

        Args:
            content: The original content (URL, text, file bytes etc.)
            content_type: Type of content (url, text, document etc.)

        Returns:
            Optional[Dict]: The cached summary result if found, None otherwise
        """
        try:
            cache_key = self._get_cache_key(content, content_type)
            results = self.collection.get(where={"cache_key": cache_key}, limit=1)
            
            if results["metadatas"]:
                metadata = results["metadatas"][0].get("metadata", "{}")
                # Convert stored metadata string back to dict
                if isinstance(metadata, str):
                    metadata = json.loads(metadata)
                
                return {
                    "summary": results["metadatas"][0]["summary"],
                    "translated_summary": results["metadatas"][0]["translated_summary"],
                    "metadata": metadata
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving from cache: {str(e)}")
            return None

    async def store_summary(
        self,
        content: Any,
        result: Dict,
        content_type: str
    ) -> bool:
        """Store a summary in the vector store cache.

        Args:
            content: The original content (URL, text, file bytes etc.)
            result: The summary result dictionary
            content_type: Type of content (url, text, document etc.)

        Returns:
            bool: True if stored successfully, False otherwise
        """
        try:
            cache_key = self._get_cache_key(content, content_type)
            
            # Convert metadata dict to string to ensure compatibility
            metadata = result.get("metadata", {})
            if isinstance(metadata, dict):
                metadata = self._sanitize_metadata(metadata)
                metadata = json.dumps(metadata)
            elif metadata is None:
                metadata = "{}"

            # Store the document with metadata
            self.collection.add(
                documents=[result["summary"]],
                metadatas=[{
                    "cache_key": cache_key,
                    "summary": result["summary"],
                    "translated_summary": result["translated_summary"],
                    "metadata": metadata
                }],
                embeddings=[self.dummy_embedding],  # Using 384-dimensional embedding
                ids=[cache_key]  # Use cache_key as the document ID
            )
            return True
        except Exception as e:
            logger.error(f"Error storing in cache: {str(e)}")
            return False

    async def cleanup_old_entries(self, days: int = 30) -> None:
        """Clean up entries older than specified days."""
        try:
            cutoff_date = datetime.now().isoformat()
            
            # Get all entries
            results = self.collection.get(include=["metadatas", "ids"])
            
            if not results['ids']:
                return
            
            # Find old entries
            ids_to_delete = []
            for idx, metadata in enumerate(results['metadatas']):
                entry_date = datetime.fromisoformat(metadata['timestamp'])
                if (datetime.now() - entry_date).days > days:
                    ids_to_delete.append(results['ids'][idx])
            
            # Delete old entries
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                logger.info(f"Cleaned up {len(ids_to_delete)} old entries")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise
