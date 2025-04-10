from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from collections import defaultdict
import chromadb
import os
import json
import boto3
from langchain_community.embeddings import BedrockEmbeddings
import numpy as np

from .sentence_builder_models import WordCategory, SentenceWord, SentencePattern, UserSentence
from .sentence_builder_serializers import (
    WordCategorySerializer, 
    SentenceWordSerializer, 
    SentencePatternSerializer, 
    UserSentenceSerializer,
    WordsByCategorySerializer
)

# Setup ChromaDB for sentence embeddings
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'chroma_db', 'sentence_builder')
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

# Initialize Bedrock client for embeddings
bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"
)

# Initialize Bedrock embeddings
embeddings = BedrockEmbeddings(
    client=bedrock_runtime,
    model_id="amazon.titan-embed-text-v1"
)

# Initialize ChromaDB client
chroma_client = chromadb.Client(chromadb.Settings(
    persist_directory=CHROMA_PERSIST_DIR,
    chroma_db_impl="duckdb+parquet",
))

# Create or get the collection
try:
    sentence_collection = chroma_client.get_collection("sentence_patterns")
except:
    sentence_collection = chroma_client.create_collection(
        name="sentence_patterns",
        metadata={"hnsw:space": "cosine"}
    )

class WordCategoryViewSet(viewsets.ModelViewSet):
    """API endpoint for word categories"""
    queryset = WordCategory.objects.all()
    serializer_class = WordCategorySerializer

class SentenceWordViewSet(viewsets.ModelViewSet):
    """API endpoint for words"""
    queryset = SentenceWord.objects.all()
    serializer_class = SentenceWordSerializer
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get words grouped by category"""
        categories = WordCategory.objects.all()
        result = []
        
        for category in categories:
            words = SentenceWord.objects.filter(category=category)
            if words:
                result.append({
                    'category_id': category.id,
                    'category_name': category.name,
                    'words': SentenceWordSerializer(words, many=True).data
                })
        
        return Response(result)

class SentencePatternViewSet(viewsets.ModelViewSet):
    """API endpoint for sentence patterns"""
    queryset = SentencePattern.objects.all()
    serializer_class = SentencePatternSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new sentence pattern and add to ChromaDB"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Add to ChromaDB
        pattern = serializer.instance
        pattern_text = f"{pattern.pattern} - {pattern.example if pattern.example else ''}"
        pattern_embedding = embeddings.embed_query(pattern_text)
        
        sentence_collection.add(
            ids=[f"pattern_{pattern.id}"],
            embeddings=[pattern_embedding],
            metadatas=[{
                "pattern_id": pattern.id,
                "pattern": pattern.pattern,
                "example": pattern.example,
                "difficulty_level": pattern.difficulty_level
            }],
            documents=[pattern_text]
        )
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

class SentenceBuilderViewSet(viewsets.ViewSet):
    """API endpoint for sentence validation and suggestions"""
    
    @action(detail=False, methods=['post'])
    def validate_sentence(self, request):
        """Validate a user-constructed sentence"""
        sentence = request.data.get('sentence', '')
        user_id = request.data.get('user_id', None)
        
        if not sentence:
            return Response(
                {"error": "Sentence is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get sentence embedding
        sentence_embedding = embeddings.embed_query(sentence)
        
        # Query ChromaDB for similar patterns
        results = sentence_collection.query(
            query_embeddings=[sentence_embedding],
            n_results=3,
            include=["metadatas", "documents", "distances"]
        )
        
        # Process the results
        is_valid = False
        feedback = "The sentence structure doesn't match any known pattern."
        pattern_id = None
        
        if results and results['distances'] and results['distances'][0]:
            # Check if the closest pattern is similar enough (distance < 0.3)
            if results['distances'][0][0] < 0.3:
                is_valid = True
                pattern_id = results['metadatas'][0][0].get('pattern_id')
                feedback = f"Good job! Your sentence follows a valid pattern: {results['metadatas'][0][0].get('pattern')}"
            else:
                # Suggest the closest pattern
                feedback = f"Your sentence doesn't quite match a valid pattern. Try using this structure: {results['metadatas'][0][0].get('pattern')}"
                if results['metadatas'][0][0].get('example'):
                    feedback += f" Example: {results['metadatas'][0][0].get('example')}"
        
        # Save the user sentence
        user_sentence = UserSentence.objects.create(
            sentence=sentence,
            is_valid=is_valid,
            feedback=feedback,
            user_id=user_id,
            pattern_id=pattern_id
        )
        
        return Response({
            "is_valid": is_valid,
            "feedback": feedback,
            "sentence_id": user_sentence.id,
            "similar_patterns": [
                {
                    "pattern": meta.get('pattern'),
                    "example": meta.get('example'),
                    "similarity": 1 - dist  # Convert distance to similarity
                }
                for meta, dist in zip(results['metadatas'][0], results['distances'][0])
            ] if results and results['metadatas'] and results['distances'] else []
        })
    
    @action(detail=False, methods=['get'])
    def get_user_sentences(self, request):
        """Get sentences created by a specific user"""
        user_id = request.query_params.get('user_id', None)
        
        if not user_id:
            return Response(
                {"error": "user_id parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sentences = UserSentence.objects.filter(user_id=user_id).order_by('-created_at')
        serializer = UserSentenceSerializer(sentences, many=True)
        
        return Response(serializer.data)
