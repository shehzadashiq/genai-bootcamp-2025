"""
Vector similarity search implementation using ChromaDB and Bedrock embeddings.
Provides functionality for storing and retrieving language exercises based on semantic similarity.
"""
from typing import Dict, List, Optional, Tuple, Any
import chromadb
import boto3
from config import vector_store_config, aws_config
import json
import hashlib
from langchain_aws.embeddings import BedrockEmbeddings
from langchain_community.vectorstores import Chroma
import os

class VectorStore:
    def __init__(self):
        """Initialize vector store with ChromaDB and Bedrock embeddings."""
        # Initialize Bedrock client
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=aws_config.AWS_REGION
        )
        
        # Initialize Bedrock embeddings
        self.embeddings = BedrockEmbeddings(
            client=self.bedrock_runtime,
            model_id=aws_config.BEDROCK_EMBEDDING_MODEL,
            model_kwargs={}  # Use default model parameters
        )
        
        # Ensure persistence directory exists
        os.makedirs(vector_store_config.PERSIST_DIRECTORY, exist_ok=True)
        
        # Initialize ChromaDB with LangChain integration
        self.vector_store = Chroma(
            collection_name=vector_store_config.COLLECTION_NAME,
            embedding_function=self.embeddings,
            persist_directory=vector_store_config.PERSIST_DIRECTORY
        )

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
            
        self.vector_store.add_texts(
            texts=[text],
            ids=[exercise_id],
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
            limit = vector_store_config.MAX_RESULTS
            
        results = self.vector_store.similarity_search_with_relevance_scores(
            query=query,
            k=limit,
            filter=filter_metadata
        )
        
        # Format results
        exercises = []
        for doc, score in results:
            exercise = {
                'id': doc.metadata.get('id', ''),
                'text': doc.page_content,
                'metadata': doc.metadata,
                'distance': 1.0 - score  # Convert similarity to distance
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
            # Search by ID in metadata
            results = self.vector_store.similarity_search_with_score(
                query="",  # Empty query to match only by filter
                k=1,
                filter={"id": exercise_id}
            )
            
            if results:
                doc, score = results[0]
                return {
                    'id': exercise_id,
                    'text': doc.page_content,
                    'metadata': doc.metadata
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
                
            # Delete old document
            self.delete_exercise(exercise_id)
            
            # Add new document
            self.add_exercise(
                exercise_id=exercise_id,
                text=text,
                metadata=metadata
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
            self.vector_store.delete(ids=[exercise_id])
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
            # Search with empty query to get all matching documents
            results = self.vector_store.similarity_search_with_score(
                query="",  # Empty query to match only by filter
                k=100,  # Large enough to get all documents
                filter=filter_metadata
            )
            
            exercises = []
            for doc, score in results:
                exercise = {
                    'id': doc.metadata.get('id', ''),
                    'text': doc.page_content,
                    'metadata': doc.metadata
                }
                exercises.append(exercise)
                
            return exercises
            
        except Exception:
            return []
