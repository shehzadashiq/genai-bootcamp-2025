import chromadb
import logging
import os
from typing import Optional, List, Dict, Any
from chromadb.config import Settings
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
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
        
        logger.info("Vector store initialized")
    
    async def store_summary(
        self,
        url: str,
        summary: str,
        translated_summary: str,
        audio_url: Optional[str]
    ) -> None:
        """Store summary and its metadata in the vector store."""
        try:
            metadata = {
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "translated_summary": translated_summary,
                "audio_url": audio_url if audio_url else ""
            }
            
            # Add to collection
            self.collection.add(
                documents=[summary],
                metadatas=[metadata],
                ids=[self._generate_id(url)]
            )
            
            # Persist changes
            self.client.persist()
            
            logger.info(f"Stored summary for URL: {url}")
            
        except Exception as e:
            logger.error(f"Error storing summary for {url}: {str(e)}")
            raise
    
    async def get_summary(self, url: str) -> Optional[Dict[str, Any]]:
        """Retrieve summary for a given URL."""
        try:
            # Query the collection
            results = self.collection.get(
                ids=[self._generate_id(url)],
                include=["metadatas", "documents"]
            )
            
            if results and results['ids']:
                document = results['documents'][0]
                metadata = results['metadatas'][0]
                
                return {
                    "summary": document,
                    "translated_summary": metadata.get("translated_summary", ""),
                    "audio_url": metadata.get("audio_url", "")
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving summary for {url}: {str(e)}")
            return None
    
    def _generate_id(self, url: str) -> str:
        """Generate a consistent ID for a URL."""
        from hashlib import sha256
        return sha256(url.encode()).hexdigest()
    
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
                self.client.persist()
                logger.info(f"Cleaned up {len(ids_to_delete)} old entries")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise
