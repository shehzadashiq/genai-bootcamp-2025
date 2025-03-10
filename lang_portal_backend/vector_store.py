"""
Vector similarity search implementation using ChromaDB and Bedrock embeddings.
Provides functionality for storing and retrieving language exercises based on semantic similarity.
"""
from typing import Dict, List, Optional, Tuple, Any
from services.vector_store_service import VectorStoreService

class VectorStore:
    def __init__(self):
        """Initialize vector store using VectorStoreService."""
        self.vector_store = VectorStoreService()

    def add_exercise(
        self,
        exercise_id: str,
        text: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Add an exercise to the vector store.
        
        Args:
            exercise_id: Unique identifier for the exercise
            text: Exercise text content to embed
            metadata: Optional metadata for filtering
        """
        if metadata is None:
            metadata = {}
            
        # Add ID to metadata for retrieval
        metadata['id'] = exercise_id
            
        # Add as single document
        self.vector_store._collection.add(
            ids=[exercise_id],
            documents=[text],
            metadatas=[metadata]
        )

    def search_similar(
        self,
        query: str,
        filter_metadata: Optional[Dict] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Search for similar exercises using vector similarity.
        
        Args:
            query: Search query text
            filter_metadata: Optional metadata filters
            limit: Maximum number of results
            
        Returns:
            List of similar exercises with scores
        """
        if limit is None:
            limit = 5
            
        # Use VectorStoreService search with filters
        results = self.vector_store._collection.query(
            query_texts=[query],
            n_results=limit,
            where=filter_metadata
        )
        
        # Format results
        exercises = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                exercise = {
                    'id': results['ids'][0][i],
                    'text': doc,
                    'metadata': results['metadatas'][0][i],
                    'distance': float(results['distances'][0][i]) if 'distances' in results else 1.0
                }
                exercises.append(exercise)
            
        return exercises

    def get_exercise(self, exercise_id: str) -> Optional[Dict]:
        """
        Get a specific exercise by ID.
        
        Args:
            exercise_id: ID of exercise to retrieve
            
        Returns:
            Exercise data if found, None otherwise
        """
        try:
            results = self.vector_store._collection.get(
                ids=[exercise_id]
            )
            
            if results and results['documents']:
                return {
                    'id': exercise_id,
                    'text': results['documents'][0],
                    'metadata': results['metadatas'][0]
                }
            return None
            
        except Exception:
            return None

    def update_exercise(
        self,
        exercise_id: str,
        text: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Update an existing exercise.
        
        Args:
            exercise_id: ID of exercise to update
            text: New exercise text
            metadata: New metadata
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            if metadata is None:
                metadata = {}
                
            # Add ID to metadata
            metadata['id'] = exercise_id
                
            # Update document
            self.vector_store._collection.update(
                ids=[exercise_id],
                documents=[text],
                metadatas=[metadata]
            )
            return True
            
        except Exception:
            return False

    def delete_exercise(self, exercise_id: str) -> bool:
        """
        Delete an exercise from the store.
        
        Args:
            exercise_id: ID of exercise to delete
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            self.vector_store._collection.delete(
                ids=[exercise_id]
            )
            return True
        except Exception:
            return False

    def list_exercises(
        self,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        List all exercises matching the filter criteria.
        
        Args:
            filter_metadata: Optional metadata filters
            
        Returns:
            List of matching exercises
        """
        try:
            results = self.vector_store._collection.get(
                where=filter_metadata
            )
            
            exercises = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents']):
                    exercise = {
                        'id': results['ids'][i],
                        'text': doc,
                        'metadata': results['metadatas'][i]
                    }
                    exercises.append(exercise)
                    
            return exercises
            
        except Exception:
            return []
