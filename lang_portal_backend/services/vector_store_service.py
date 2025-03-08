from typing import List, Dict, Optional
import logging
import pickle
import os
import math
from datetime import datetime
from collections import Counter
from .language_service import LanguageService

logger = logging.getLogger(__name__)

class VectorStoreService:
    _instance = None
    _store = None  # List of document records
    _store_path = "vector_store.pkl"
    _language_service = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStoreService, cls).__new__(cls)
            try:
                cls._language_service = LanguageService()
                if os.path.exists(cls._store_path):
                    logger.info("Loading existing vector store...")
                    with open(cls._store_path, 'rb') as f:
                        cls._store = pickle.load(f)
                else:
                    logger.info("Creating new vector store...")
                    cls._store = []
            except Exception as e:
                logger.error(f"Error initializing vector store: {e}")
                raise
        return cls._instance
    
    def _save_store(self):
        """Save the current state of the vector store."""
        try:
            with open(self._store_path, 'wb') as f:
                pickle.dump(self._store, f)
            logger.info("Vector store saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
            return False
    
    def _get_bigrams(self, text: str) -> List[str]:
        """Get character bigrams from text."""
        chars = list(text)
        return [''.join(pair) for pair in zip(chars, chars[1:])]
    
    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two sparse vectors."""
        # Get common bigrams
        common_bigrams = set(vec1.keys()) & set(vec2.keys())
        
        # Calculate dot product
        dot_product = sum(vec1[bigram] * vec2[bigram] for bigram in common_bigrams)
        
        # Calculate magnitudes
        mag1 = math.sqrt(sum(v * v for v in vec1.values()))
        mag2 = math.sqrt(sum(v * v for v in vec2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0
            
        return dot_product / (mag1 * mag2)
    
    def _vectorize_text(self, text: str) -> Dict[str, float]:
        """Convert text to a sparse vector using character bigrams."""
        # Get bigrams
        bigrams = self._get_bigrams(text)
        if not bigrams:
            return {}
            
        # Count frequencies
        counter = Counter(bigrams)
        total = len(bigrams)
        
        # Create normalized frequency dictionary
        return {bigram: count/total for bigram, count in counter.items()}
    
    def add_transcript(self, video_id: str, transcript: List[Dict]) -> bool:
        """Add transcript chunks to vector store."""
        try:
            # Process each segment
            for segment in transcript:
                text = segment.get('text', '').strip()
                if not text:
                    continue
                
                # Convert Hindi to Urdu
                urdu_text = self._language_service.convert_hindi_to_urdu(text)
                
                # Create document record
                doc = {
                    'id': f"{video_id}_{len(self._store)}",
                    'video_id': video_id,
                    'text': urdu_text,
                    'original_text': text,
                    'vector': self._vectorize_text(urdu_text),
                    'metadata': {
                        'start_time': segment.get('start', 0),
                        'end_time': segment.get('start', 0) + segment.get('duration', 0),
                        'language': segment.get('language', 'ur'),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                }
                
                self._store.append(doc)
            
            # Save store
            if not self._save_store():
                return False
            
            logger.info(f"Added {len(transcript)} segments for video {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding transcript: {e}")
            return False
    
    def search_transcripts(self, query: str, k: int = 5) -> List[Dict]:
        """Search for relevant transcript chunks."""
        try:
            if not self._store:
                return []
            
            # Convert query to Urdu
            urdu_query = self._language_service.convert_hindi_to_urdu(query)
            
            # Vectorize query
            query_vector = self._vectorize_text(urdu_query)
            if not query_vector:
                return []
            
            # Calculate similarities
            results = []
            for doc in self._store:
                similarity = self._cosine_similarity(query_vector, doc['vector'])
                results.append((doc, similarity))
            
            # Sort by similarity
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Format top k results
            return [{
                'text': doc['original_text'],
                'metadata': doc['metadata'],
                'similarity_score': similarity
            } for doc, similarity in results[:k]]
            
        except Exception as e:
            logger.error(f"Error searching transcripts: {e}")
            return []
    
    def delete_video_chunks(self, video_id: str) -> bool:
        """Delete all chunks for a specific video."""
        try:
            initial_len = len(self._store)
            self._store = [doc for doc in self._store if doc['video_id'] != video_id]
            
            if len(self._store) == initial_len:
                return False
            
            if not self._save_store():
                return False
            
            logger.info(f"Deleted chunks for video {video_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting chunks: {e}")
            return False
