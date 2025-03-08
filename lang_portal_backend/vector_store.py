"""
Vector similarity search implementation using ChromaDB and Bedrock embeddings.
Provides functionality for storing and retrieving language exercises based on semantic similarity.
"""
from typing import Dict, List, Optional, Tuple
import chromadb
from chromadb.utils import embedding_functions
import boto3
from config import vector_store_config, aws_config
import json
import hashlib

class VectorStore:
    def __init__(self):
        """Initialize vector store with ChromaDB and Bedrock embeddings."""
        self.client = chromadb.Client()
        
        # Use Bedrock embeddings
        self.bedrock = boto3.client(
            'bedrock-runtime',
            region_name=aws_config.AWS_REGION
        )
        
        # Create embedding function using Bedrock
        self.embedding_function = embedding_functions.BedrockEmbeddingFunction(
            client=self.bedrock,
            model_name=aws_config.BEDROCK_EMBEDDING_MODEL
        )
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name=vector_store_config.COLLECTION_NAME,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": vector_store_config.SIMILARITY_METRIC}
        )

    def _generate_id(self, content: Dict) -> str:
        """Generate a unique ID for the content."""
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]

    def add_exercise(
        self,
        content: Dict,
        metadata: Optional[Dict] = None,
        ids: Optional[List[str]] = None
    ) -> str:
        """
        Add an exercise to the vector store.
        
        Args:
            content: Dictionary containing exercise content
            metadata: Optional metadata for the exercise
            ids: Optional list of IDs to use (must match content length)
            
        Returns:
            ID of the added exercise
        """
        # Generate exercise ID if not provided
        if not ids:
            exercise_id = self._generate_id(content)
            ids = [exercise_id]
        
        # Convert content to string for embedding
        content_str = json.dumps(content)
        
        # Add to collection
        self.collection.add(
            documents=[content_str],
            metadatas=[metadata] if metadata else None,
            ids=ids
        )
        
        return ids[0]

    def search_similar(
        self,
        query: str,
        n_results: int = None,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search for similar exercises using semantic similarity.
        
        Args:
            query: Search query text
            n_results: Number of results to return (default: config default)
            where: Optional metadata filter
            where_document: Optional document content filter
            
        Returns:
            List of similar exercises with their similarity scores
        """
        if n_results is None:
            n_results = vector_store_config.DEFAULT_SEARCH_LIMIT
            
        # Query the collection
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where,
            where_document=where_document
        )
        
        # Process results
        exercises = []
        for i in range(len(results['ids'][0])):
            exercise_id = results['ids'][0][i]
            content = json.loads(results['documents'][0][i])
            metadata = results['metadatas'][0][i] if results['metadatas'] else {}
            distance = results['distances'][0][i] if 'distances' in results else None
            
            # Convert distance to similarity score (1 - normalized distance)
            similarity = 1 - (distance / 2) if distance is not None else None
            
            # Only include results above similarity threshold
            if similarity is None or similarity >= vector_store_config.SIMILARITY_THRESHOLD:
                exercises.append({
                    'id': exercise_id,
                    'content': content,
                    'metadata': metadata,
                    'similarity': similarity
                })
        
        return exercises

    def update_exercise(
        self,
        exercise_id: str,
        content: Dict,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Update an existing exercise in the vector store.
        
        Args:
            exercise_id: ID of the exercise to update
            content: New content for the exercise
            metadata: Optional new metadata
        """
        content_str = json.dumps(content)
        
        self.collection.update(
            ids=[exercise_id],
            documents=[content_str],
            metadatas=[metadata] if metadata else None
        )

    def delete_exercise(self, exercise_id: str) -> None:
        """
        Delete an exercise from the vector store.
        
        Args:
            exercise_id: ID of the exercise to delete
        """
        self.collection.delete(ids=[exercise_id])

    def get_exercise(self, exercise_id: str) -> Optional[Dict]:
        """
        Retrieve an exercise by its ID.
        
        Args:
            exercise_id: ID of the exercise to retrieve
            
        Returns:
            Exercise content and metadata, or None if not found
        """
        try:
            result = self.collection.get(
                ids=[exercise_id],
                include=['documents', 'metadatas']
            )
            
            if result['documents']:
                content = json.loads(result['documents'][0])
                metadata = result['metadatas'][0] if result['metadatas'] else {}
                
                return {
                    'id': exercise_id,
                    'content': content,
                    'metadata': metadata
                }
        except Exception:
            pass
            
        return None

    def list_exercises(
        self,
        where: Optional[Dict] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict]:
        """
        List exercises with optional filtering.
        
        Args:
            where: Optional metadata filter
            limit: Maximum number of exercises to return
            offset: Number of exercises to skip
            
        Returns:
            List of exercises matching the criteria
        """
        # Get all matching exercises
        result = self.collection.get(
            where=where,
            limit=limit,
            offset=offset,
            include=['documents', 'metadatas']
        )
        
        exercises = []
        for i in range(len(result['ids'])):
            exercise_id = result['ids'][i]
            content = json.loads(result['documents'][i])
            metadata = result['metadatas'][i] if result['metadatas'] else {}
            
            exercises.append({
                'id': exercise_id,
                'content': content,
                'metadata': metadata
            })
            
        return exercises
