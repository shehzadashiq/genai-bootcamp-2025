from typing import List, Dict, Optional
import logging
import os
import json
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions
from .language_service import LanguageService

logger = logging.getLogger(__name__)

class VectorStoreService:
    _instance = None
    _db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")  # Absolute path to ChromaDB directory
    _language_service = None
    _client = None
    _collection = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStoreService, cls).__new__(cls)
            try:
                cls._language_service = LanguageService()
                cls._init_db()
                logger.info("Vector store initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing ChromaDB: {e}")
                raise
        return cls._instance
    
    @classmethod
    def _init_db(cls):
        """Initialize ChromaDB database."""
        try:
            # Ensure directory exists with correct permissions
            os.makedirs(cls._db_path, exist_ok=True)
            
            # Initialize ChromaDB with persistence
            cls._client = chromadb.PersistentClient(path=cls._db_path)
            
            # Get or create collection for transcript chunks
            cls._collection = cls._client.get_or_create_collection(
                name="transcript_chunks",
                embedding_function=embedding_functions.DefaultEmbeddingFunction(),
                metadata={"description": "Urdu transcript chunks for semantic search"}
            )
            
            logger.info(f"ChromaDB initialized successfully at {cls._db_path}")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise
    
    def add_transcript(self, video_id: str, transcript: List[Dict]) -> bool:
        """Add transcript chunks to vector store."""
        try:
            # Process each segment
            ids = []
            texts = []
            metadatas = []
            
            for i, segment in enumerate(transcript):
                text = segment.get('text', '').strip()
                if not text:
                    continue
                
                # Convert Hindi to Urdu if needed
                if not any(ord(char) >= 0x0600 and ord(char) <= 0x06FF for char in text):
                    text = self._language_service.convert_hindi_to_urdu(text)
                
                # Create document record
                doc_id = f"{video_id}_{i}"
                
                # Prepare metadata
                metadata = {
                    'video_id': video_id,
                    'start_time': str(segment.get('start', 0)),  # ChromaDB requires string values
                    'end_time': str(segment.get('start', 0) + segment.get('duration', 0)),
                    'language': segment.get('language', 'ur'),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                ids.append(doc_id)
                texts.append(text)
                metadatas.append(metadata)
            
            if ids:
                # Delete existing chunks for this video
                self.delete_video_chunks(video_id)
                
                # Add new chunks
                self._collection.add(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas
                )
                
                logger.info(f"Added {len(ids)} transcript chunks for video {video_id}")
                return True
            
            return False
                
        except Exception as e:
            logger.error(f"Error adding transcript: {e}")
            return False
    
    def search_transcripts(self, query: str, k: int = 5) -> List[Dict]:
        """Search for relevant transcript chunks."""
        try:
            if not query:
                return []
            
            # Convert query to Urdu
            urdu_query = self._language_service.convert_hindi_to_urdu(query)
            
            # Search using ChromaDB
            results = self._collection.query(
                query_texts=[urdu_query],
                n_results=k
            )
            
            # Format results
            formatted_results = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):  # First query results
                    formatted_results.append({
                        'text': doc,
                        'metadata': results['metadatas'][0][i],
                        'similarity_score': float(results['distances'][0][i]) if 'distances' in results else 1.0
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching transcripts: {e}")
            return []
    
    def delete_video_chunks(self, video_id: str) -> bool:
        """Delete all chunks for a specific video."""
        try:
            # ChromaDB doesn't support direct filtering in delete, so we need to find IDs first
            results = self._collection.get(
                where={"video_id": video_id}
            )
            
            if results and results['ids']:
                self._collection.delete(
                    ids=results['ids']
                )
                logger.info(f"Deleted {len(results['ids'])} chunks for video {video_id}")
                return True
            
            logger.warning(f"No chunks found for video {video_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error deleting chunks: {e}")
            return False
