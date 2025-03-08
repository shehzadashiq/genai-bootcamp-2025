from typing import List, Dict, Optional
import logging
import os
import math
import sqlite3
import json
from datetime import datetime
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .language_service import LanguageService

logger = logging.getLogger(__name__)

class VectorStoreService:
    _instance = None
    _db_path = "vector_store.db"
    _language_service = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStoreService, cls).__new__(cls)
            try:
                cls._language_service = LanguageService()
                cls._init_db()
                logger.info("Vector store initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing vector store: {e}")
                raise
        return cls._instance
    
    @classmethod
    def _init_db(cls):
        """Initialize SQLite database."""
        try:
            with sqlite3.connect(cls._db_path) as conn:
                cursor = conn.cursor()
                # Create table for transcript chunks
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS transcript_chunks (
                        id TEXT PRIMARY KEY,
                        video_id TEXT NOT NULL,
                        text TEXT NOT NULL,
                        vector BLOB NOT NULL,
                        metadata TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Create index on video_id for faster deletion
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_video_id 
                    ON transcript_chunks(video_id)
                """)
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _get_bigrams(self, text: str) -> List[str]:
        """Get character bigrams from text."""
        chars = list(text)
        return [''.join(pair) for pair in zip(chars, chars[1:])]
    
    def _vectorize_text(self, text: str) -> np.ndarray:
        """Convert text to a dense vector using character bigrams."""
        try:
            # Get bigrams
            bigrams = self._get_bigrams(text)
            if not bigrams:
                return np.array([])
                
            # Count frequencies
            from collections import Counter
            counter = Counter(bigrams)
            total = len(bigrams)
            
            # Create normalized frequency vector
            unique_bigrams = sorted(counter.keys())
            vector = np.array([counter[bigram]/total for bigram in unique_bigrams])
            
            # Normalize vector
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
                
            return vector
            
        except Exception as e:
            logger.error(f"Error vectorizing text: {e}")
            return np.array([])
    
    def add_transcript(self, video_id: str, transcript: List[Dict]) -> bool:
        """Add transcript chunks to vector store."""
        try:
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()
                
                # Process each segment
                for i, segment in enumerate(transcript):
                    text = segment.get('text', '').strip()
                    if not text:
                        continue
                    
                    # Convert Hindi to Urdu if needed
                    if not any(ord(char) >= 0x0600 and ord(char) <= 0x06FF for char in text):
                        text = self._language_service.convert_hindi_to_urdu(text)
                    
                    # Create document record
                    doc_id = f"{video_id}_{i}"
                    vector = self._vectorize_text(text)
                    
                    # Prepare metadata
                    metadata = {
                        'video_id': video_id,
                        'start_time': segment.get('start', 0),
                        'end_time': segment.get('start', 0) + segment.get('duration', 0),
                        'language': segment.get('language', 'ur'),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    # Store in database
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO transcript_chunks 
                        (id, video_id, text, vector, metadata)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            doc_id,
                            video_id,
                            text,
                            vector.tobytes(),
                            json.dumps(metadata)
                        )
                    )
                
                conn.commit()
                logger.info(f"Added transcript chunks for video {video_id}")
                return True
                
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
            
            # Vectorize query
            query_vector = self._vectorize_text(urdu_query)
            if query_vector.size == 0:
                return []
            
            # Get all chunks from database
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, text, vector, metadata FROM transcript_chunks")
                chunks = cursor.fetchall()
            
            if not chunks:
                return []
            
            # Calculate similarities
            results = []
            for chunk_id, text, vector_bytes, metadata_json in chunks:
                vector = np.frombuffer(vector_bytes).reshape(1, -1)
                query_vector_reshaped = query_vector.reshape(1, -1)
                
                if vector.shape[1] != query_vector_reshaped.shape[1]:
                    continue  # Skip if vectors have different dimensions
                
                similarity = cosine_similarity(query_vector_reshaped, vector)[0][0]
                results.append({
                    'text': text,
                    'metadata': json.loads(metadata_json),
                    'similarity_score': float(similarity)
                })
            
            # Sort by similarity and get top k
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return results[:k]
            
        except Exception as e:
            logger.error(f"Error searching transcripts: {e}")
            return []
    
    def delete_video_chunks(self, video_id: str) -> bool:
        """Delete all chunks for a specific video."""
        try:
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM transcript_chunks WHERE video_id = ?",
                    (video_id,)
                )
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Deleted {cursor.rowcount} chunks for video {video_id}")
                    return True
                else:
                    logger.warning(f"No chunks found for video {video_id}")
                    return False
                
        except Exception as e:
            logger.error(f"Error deleting chunks: {e}")
            return False
