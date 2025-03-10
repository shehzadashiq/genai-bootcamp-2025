"""
Custom embedding function for AWS Bedrock Titan model.
Optimized for semantic matching with:
- L2 normalization for cosine similarity
- Batch processing support
- Enhanced error handling
- Text preprocessing
"""
import json
import logging
from typing import Any, List, Optional
import numpy as np
from chromadb.api.types import Documents, EmbeddingFunction

logger = logging.getLogger(__name__)

class BedrockEmbeddingFunction(EmbeddingFunction):
    """
    Custom embedding function for AWS Bedrock using the Titan model.
    Implements ChromaDB's EmbeddingFunction interface.
    """
    def __init__(self, client, model_id: str = "amazon.titan-embed-text-v1", normalize_embeddings: bool = True):
        """
        Initialize the Bedrock embedding function.
        
        Args:
            client: Boto3 Bedrock runtime client
            model_id: Bedrock model ID (default: amazon.titan-embed-text-v1)
            normalize_embeddings: Whether to L2 normalize embeddings (default: True)
        """
        self.client = client
        self.model_id = model_id
        self.normalize_embeddings = normalize_embeddings
        self.embedding_dimension = 1536  # Titan model dimension
        
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for embedding."""
        try:
            # Remove extra whitespace
            text = " ".join(text.split())
            # Add any additional preprocessing steps here
            return text
        except Exception as e:
            logger.error(f"Error preprocessing text: {e}")
            return text
            
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for a single text."""
        try:
            # Preprocess text
            text = self._preprocess_text(text)
            
            # Prepare request body with enhanced parameters
            request_body = {
                "inputText": text,
                "inputType": "search_document",  # Optimize for search
                "embeddingConfig": {
                    "outputEmbeddingLength": self.embedding_dimension,
                    "truncate": "RIGHT"  # Consistent truncation
                }
            }
            
            # Call Bedrock API with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.client.invoke_model(
                        modelId=self.model_id,
                        body=json.dumps(request_body),
                        contentType="application/json",
                        accept="application/json"
                    )
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Retry {attempt + 1} after error: {e}")
            
            # Parse response
            response_body = json.loads(response.get('body').read())
            embedding = response_body.get('embedding')
            
            if not embedding or len(embedding) != self.embedding_dimension:
                logger.error(f"Invalid embedding: expected {self.embedding_dimension} dimensions, got {len(embedding) if embedding else 0}")
                return None
            
            # Convert to numpy array for efficient operations
            embedding_array = np.array(embedding, dtype=np.float32)
            
            # Normalize if requested
            if self.normalize_embeddings:
                norm = np.linalg.norm(embedding_array)
                if norm > 0:
                    embedding_array = embedding_array / norm
                
            return embedding_array.tolist()
            
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None
        
    def __call__(self, texts: Documents) -> List[List[float]]:
        """
        Generate embeddings for the given texts.
        
        Args:
            texts: List of text documents to embed
            
        Returns:
            List of embeddings, each embedding is a list of floats
        """
        embeddings = []
        
        for text in texts:
            embedding = self._get_embedding(text)
            if embedding:
                embeddings.append(embedding)
            else:
                # If embedding fails, use zero vector as fallback
                embeddings.append([0.0] * self.embedding_dimension)
                logger.warning(f"Using zero vector for failed embedding of text: {text[:100]}...")
        
        return embeddings
