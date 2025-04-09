"""
Vector store service implementation using ChromaDB.
"""
import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
import boto3
import json
from config import vector_store_config, aws_config
from datetime import datetime
from .language_service import LanguageService

logger = logging.getLogger(__name__)

class BedrockEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        self.bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=aws_config.AWS_REGION,
            aws_access_key_id=aws_config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=aws_config.AWS_SECRET_ACCESS_KEY
        )
        self.model_id = aws_config.BEDROCK_EMBEDDING_MODEL

    def __call__(self, texts: Documents) -> Embeddings:
        embeddings = []
        for text in texts:
            try:
                response = self.bedrock.invoke_model(
                    modelId=self.model_id,
                    body=json.dumps({
                        "inputText": text
                    })
                )
                embedding = json.loads(response['body'].read())['embedding']
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Error getting embedding: {e}")
                # Return zero vector as fallback
                embeddings.append([0.0] * vector_store_config.EMBEDDING_DIMENSION)
        return embeddings

class VectorStoreService:
    _instance = None
    _language_service = None
    _client = None
    _collection = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStoreService, cls).__new__(cls)
            try:
                cls._language_service = LanguageService()
                cls.initialize()
                logger.info("Vector store initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing ChromaDB: {e}")
                raise
        return cls._instance
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize ChromaDB database."""
        try:
            # Ensure persistence directory exists
            os.makedirs(vector_store_config.PERSIST_DIRECTORY, exist_ok=True)
            
            # Initialize ChromaDB with persistence
            cls._client = chromadb.Client(
                chromadb.Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=vector_store_config.PERSIST_DIRECTORY,
                    anonymized_telemetry=False
                )
            )
            
            # Initialize custom embedding function for Bedrock
            embedding_function = BedrockEmbeddingFunction()
            
            # Get or create collection with specific settings
            cls._collection = cls._client.get_or_create_collection(
                name=vector_store_config.COLLECTION_NAME,
                embedding_function=embedding_function,
                metadata={
                    "hnsw:space": vector_store_config.SIMILARITY_METRIC,
                    "hnsw:construction_ef": 100,  # Higher value = better accuracy, slower construction
                    "hnsw:search_ef": 100,  # Higher value = better accuracy, slower search
                    "dimension": vector_store_config.EMBEDDING_DIMENSION
                }
            )
            
            logger.info(f"ChromaDB initialized successfully at {vector_store_config.PERSIST_DIRECTORY}")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            raise
    
    def add_transcript(self, video_id: str, transcript: List[Dict]) -> bool:
        """Add transcript chunks to vector store."""
        try:
            # Create chunks from transcript first
            chunks = []
            chunk_ids = []
            
            for i, segment in enumerate(transcript):
                text = segment.get('text', '').strip()
                if text:
                    chunk_id = f"{video_id}_{i}"
                    chunks.append({
                        'text': text,
                        'start': segment.get('start', 0),
                        'duration': segment.get('duration', 0)
                    })
                    chunk_ids.append(chunk_id)
            
            if not chunks:
                logger.error(f"No valid chunks created for video {video_id}")
                return False

            # Delete existing chunks first
            if not self.delete_video_chunks(video_id):
                logger.warning(f"Failed to delete existing chunks for video {video_id}, proceeding with add")

            # Add chunks in batches
            batch_size = 50
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                batch_ids = chunk_ids[i:i + batch_size]
                try:
                    self._collection.add(
                        ids=batch_ids,
                        documents=[chunk['text'] for chunk in batch_chunks],
                        metadatas=[{
                            'video_id': video_id,
                            'start': chunk['start'],
                            'duration': chunk['duration']
                        } for chunk in batch_chunks]
                    )
                    logger.info(f"Added batch of {len(batch_chunks)} chunks for video {video_id}")
                except Exception as e:
                    logger.error(f"Error adding batch of chunks: {str(e)}")
                    # Continue with next batch even if one fails
                    continue

            return True

        except Exception as e:
            logger.error(f"Error processing transcript: {str(e)}")
            return False

    def get_video_chunks(self, video_id: str) -> List[Dict]:
        """Get all chunks for a specific video."""
        try:
            results = self._collection.get(
                where={"video_id": video_id}
            )
            
            if not results or not results['ids']:
                logger.warning(f"No chunks found for video {video_id}")
                return []
            
            chunks = []
            for i, doc_id in enumerate(results['ids']):
                chunks.append({
                    'id': doc_id,
                    'text': results['documents'][i],
                    'start': results['metadatas'][i]['start'],
                    'duration': results['metadatas'][i]['duration']
                })
            
            return sorted(chunks, key=lambda x: x['start'])
            
        except Exception as e:
            logger.error(f"Error retrieving chunks for video {video_id}: {str(e)}")
            return []

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
            # Find all chunks for this video
            results = self._collection.get(
                where={"video_id": video_id}
            )
            
            if not results or not results['ids']:
                logger.info(f"No existing chunks found for video {video_id}")
                return True
                
            # Delete chunks in batches to avoid overwhelming the DB
            batch_size = 50
            for i in range(0, len(results['ids']), batch_size):
                batch_ids = results['ids'][i:i + batch_size]
                try:
                    self._collection.delete(
                        ids=batch_ids
                    )
                    logger.info(f"Deleted batch of {len(batch_ids)} chunks for video {video_id}")
                except Exception as e:
                    logger.error(f"Error deleting batch of chunks: {str(e)}")
                    # Continue with next batch even if one fails
                    continue
                    
            return True
            
        except Exception as e:
            logger.error(f"Error deleting chunks for video {video_id}: {str(e)}")
            return False
