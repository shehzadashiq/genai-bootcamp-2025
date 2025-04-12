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
import sys
import traceback
import shutil
import datetime

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

print("=" * 80)
print("SENTENCE BUILDER: Initializing views")
print(f"CHROMA_PERSIST_DIR: {CHROMA_PERSIST_DIR}")
print("=" * 80)
sys.stdout.flush()

# Reset ChromaDB directory to fix corruption
if os.path.exists(CHROMA_PERSIST_DIR):
    # Create backup directory
    backup_dir = os.path.join(os.path.dirname(CHROMA_PERSIST_DIR), 
                            f"sentence_builder_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    try:
        # Copy the entire directory to backup
        if not os.path.exists(backup_dir):
            shutil.copytree(CHROMA_PERSIST_DIR, backup_dir)
        print(f"SENTENCE BUILDER: Created backup at: {backup_dir}")
        sys.stdout.flush()
        
        # Remove the entire directory
        shutil.rmtree(CHROMA_PERSIST_DIR)
        print("SENTENCE BUILDER: Removed corrupted directory")
        sys.stdout.flush()
        
        # Create a fresh directory
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        print("SENTENCE BUILDER: Created fresh directory")
        sys.stdout.flush()
    except Exception as e:
        print(f"SENTENCE BUILDER ERROR: Failed to reset directory: {str(e)}")
        traceback.print_exc()
        sys.stdout.flush()

# Initialize Bedrock client for embeddings
try:
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1"
    )
    print("SENTENCE BUILDER: Successfully initialized Bedrock client")
    sys.stdout.flush()
except Exception as e:
    print(f"SENTENCE BUILDER ERROR: Failed to initialize Bedrock client: {str(e)}")
    traceback.print_exc()
    sys.stdout.flush()

# Initialize Bedrock embeddings
embeddings = BedrockEmbeddings(
    client=bedrock_runtime,
    model_id="amazon.titan-embed-text-v1"
)

# Initialize ChromaDB client
try:
    print("SENTENCE BUILDER: Initializing ChromaDB client")
    sys.stdout.flush()
    
    # Create a fresh ChromaDB client using the Client class (compatible with older versions)
    chroma_client = chromadb.Client(chromadb.Settings(
        persist_directory=CHROMA_PERSIST_DIR,
        chroma_db_impl="duckdb+parquet",
    ))
    
    # Check if collection exists, if not create it
    try:
        sentence_collection = chroma_client.get_collection(name="sentence_patterns")
        print(f"SENTENCE BUILDER: Found existing collection 'sentence_patterns'")
    except Exception as e:
        print(f"SENTENCE BUILDER: Creating new collection 'sentence_patterns'")
        sentence_collection = chroma_client.create_collection(
            name="sentence_patterns",
            metadata={"hnsw:space": "cosine"}
        )
    
    # Initialize the collection with existing patterns from the database
    try:
        # Get all patterns from the database
        patterns = SentencePattern.objects.all()
        print(f"SENTENCE BUILDER: Found {len(patterns)} patterns in database")
        
        if patterns:
            # Check if collection is empty
            collection_count = sentence_collection.count()
            if collection_count == 0:
                print(f"SENTENCE BUILDER: Adding {len(patterns)} patterns to ChromaDB")
                
                # Prepare data for batch addition
                ids = []
                embeddings_list = []
                metadatas = []
                documents = []
                
                for pattern in patterns:
                    pattern_text = f"{pattern.pattern} - {pattern.example if pattern.example else ''}"
                    try:
                        # Generate embedding for the pattern
                        pattern_embedding = embeddings.embed_query(pattern_text)
                        
                        # Add to lists for batch addition
                        ids.append(f"pattern_{pattern.id}")
                        embeddings_list.append(pattern_embedding)
                        metadatas.append({
                            "pattern_id": pattern.id,
                            "pattern": pattern.pattern,
                            "example": pattern.example,
                            "difficulty_level": pattern.difficulty_level
                        })
                        documents.append(pattern_text)
                        
                        print(f"SENTENCE BUILDER: Generated embedding for pattern {pattern.id}: {pattern.pattern}")
                    except Exception as e:
                        print(f"SENTENCE BUILDER ERROR: Failed to generate embedding for pattern {pattern.id}: {str(e)}")
                
                # Add all patterns to ChromaDB in one batch
                if ids:
                    sentence_collection.add(
                        ids=ids,
                        embeddings=embeddings_list,
                        metadatas=metadatas,
                        documents=documents
                    )
                    print(f"SENTENCE BUILDER: Successfully added {len(ids)} patterns to ChromaDB")
            else:
                print(f"SENTENCE BUILDER: Collection already contains {collection_count} items, skipping initialization")
    except Exception as e:
        print(f"SENTENCE BUILDER ERROR: Failed to initialize collection with patterns: {str(e)}")
        traceback.print_exc()
    
    print("SENTENCE BUILDER: ChromaDB initialized successfully")
    sys.stdout.flush()
except Exception as e:
    print(f"SENTENCE BUILDER ERROR: Failed to initialize ChromaDB: {str(e)}")
    traceback.print_exc()
    sys.stdout.flush()

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
        
        # Normalize the sentence - make full stop optional
        normalized_sentence = sentence
        if not normalized_sentence.endswith('۔'):
            # Try both with and without the full stop for better matching
            normalized_sentence_with_stop = f"{normalized_sentence} ۔"
        else:
            normalized_sentence_with_stop = normalized_sentence
        
        # Get sentence embeddings for both versions
        sentence_embedding = embeddings.embed_query(normalized_sentence)
        sentence_embedding_with_stop = embeddings.embed_query(normalized_sentence_with_stop)
        
        # Query ChromaDB for similar patterns with both versions
        results = sentence_collection.query(
            query_embeddings=[sentence_embedding, sentence_embedding_with_stop],
            n_results=3,
            include=["metadatas", "documents", "distances"]
        )
        
        # Process the results - use the best match from either query
        is_valid = False
        feedback = "The sentence structure doesn't match any known pattern."
        pattern_id = None
        
        best_distance = 1.0  # Initialize with worst possible distance
        best_metadata = None
        
        # Check results for both queries
        if results and results['distances']:
            # Check first query results (without stop)
            if results['distances'][0] and len(results['distances'][0]) > 0:
                if results['distances'][0][0] < best_distance:
                    best_distance = results['distances'][0][0]
                    best_metadata = results['metadatas'][0][0]
            
            # Check second query results (with stop)
            if len(results['distances']) > 1 and results['distances'][1] and len(results['distances'][1]) > 0:
                if results['distances'][1][0] < best_distance:
                    best_distance = results['distances'][1][0]
                    best_metadata = results['metadatas'][1][0]
        
        # Use a more lenient threshold (0.5 instead of 0.3)
        if best_metadata and best_distance < 0.5:
            is_valid = True
            pattern_id = best_metadata.get('pattern_id')
            feedback = f"Good job! Your sentence follows a valid pattern: {best_metadata.get('pattern')}"
        elif best_metadata:
            # Suggest the closest pattern
            feedback = f"Your sentence doesn't quite match a valid pattern. Try using this structure: {best_metadata.get('pattern')}"
            if best_metadata.get('example'):
                feedback += f" Example: {best_metadata.get('example')}"
        
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
            "similarity_score": 1 - best_distance if best_metadata else 0,
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
