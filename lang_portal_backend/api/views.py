"""
API views for the Language Portal Backend.
"""
from django.db.models import Count, F, Sum, Case, When, Q
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import random
import logging
import json

from .models import StudySession, StudyActivity, Word, Group, WordReviewItem, WordGroup
from .serializers import (
    StudySessionSerializer, 
    StudyActivitySerializer, 
    StudySessionListSerializer,
    WordSerializer,
    GroupSerializer
)
from services.vector_store_service import VectorStoreService
from services.language_service import LanguageService
from config import vector_store_config, guardrails_config

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class StudyActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows study activities to be viewed.
    """
    queryset = StudyActivity.objects.all().order_by('id')
    serializer_class = StudyActivitySerializer
    pagination_class = PageNumberPagination

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response({
                'items': serializer.data,
                'pagination': {
                    'current_page': int(request.query_params.get('page', 1)),
                    'total_pages': self.paginator.page.paginator.num_pages,
                    'total_items': self.paginator.page.paginator.count,
                    'items_per_page': self.paginator.page_size
                }
            })
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'items': serializer.data,
            'pagination': None
        })

@method_decorator(csrf_exempt, name='dispatch')
class StudySessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows study sessions to be viewed.
    """
    queryset = StudySession.objects.all().order_by('-start_time')
    serializer_class = StudySessionSerializer
    pagination_class = PageNumberPagination

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response({
                'items': serializer.data,
                'pagination': {
                    'current_page': int(request.query_params.get('page', 1)),
                    'total_pages': self.paginator.page.paginator.num_pages,
                    'total_items': self.paginator.page.paginator.count,
                    'items_per_page': self.paginator.page_size
                }
            })
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'items': serializer.data,
            'pagination': None
        })

    def get_words(self, request, pk=None):
        """Get words for a specific study session."""
        study_session = self.get_object()
        words = Word.objects.filter(
            wordreviewitem__study_session=study_session
        ).distinct()
        
        page = self.paginate_queryset(words)
        if page is not None:
            serializer = WordSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = WordSerializer(words, many=True)
        return Response(serializer.data)

@method_decorator(csrf_exempt, name='dispatch')
class WordViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows words to be viewed.
    """
    queryset = Word.objects.all().order_by('id')
    serializer_class = WordSerializer
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        """
        This view should return a list of all words.
        """
        return Word.objects.all().order_by('id')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            pagination = self.paginator.get_paginated_response(serializer.data)
            return Response({
                'items': serializer.data,
                'pagination': {
                    'current_page': request.query_params.get('page', 1),
                    'total_pages': self.paginator.page.paginator.num_pages,
                    'total_items': self.paginator.page.paginator.count,
                    'items_per_page': self.paginator.page_size
                }
            })
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'items': serializer.data,
            'pagination': None
        })

@method_decorator(csrf_exempt, name='dispatch')
class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows groups to be viewed.
    """
    queryset = Group.objects.all().order_by('id')
    serializer_class = GroupSerializer
    pagination_class = PageNumberPagination

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            pagination = self.paginator.get_paginated_response(serializer.data)
            return Response({
                'items': serializer.data,
                'pagination': {
                    'current_page': request.query_params.get('page', 1),
                    'total_pages': self.paginator.page.paginator.num_pages,
                    'total_items': self.paginator.page.paginator.count,
                    'items_per_page': self.paginator.page_size
                }
            })
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'items': serializer.data,
            'pagination': None
        })

    def get_words(self, request, pk=None):
        """Get words for a specific group."""
        group = self.get_object()
        words = Word.objects.filter(wordgroup__group=group)
        page = self.paginate_queryset(words)
        if page is not None:
            serializer = WordSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = WordSerializer(words, many=True)
        return Response(serializer.data)

    def get_study_sessions(self, request, pk=None):
        """Get study sessions for a specific group."""
        group = self.get_object()
        sessions = StudySession.objects.filter(group=group)
        page = self.paginate_queryset(sessions)
        if page is not None:
            serializer = StudySessionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = StudySessionListSerializer(sessions, many=True)
        return Response(serializer.data)

@method_decorator(csrf_exempt, name='dispatch')
class VocabularyQuizViewSet(viewsets.ViewSet):
    """
    API endpoint for vocabulary quiz functionality.
    """
    @action(detail=False, methods=['post'])
    def start(self, request):
        """Start a new vocabulary quiz."""
        group_id = request.data.get('group_id')
        word_count = request.data.get('word_count', 10)
        
        try:
            group = Group.objects.get(id=group_id)
            # Get random words from the group using WordGroup relationship
            words = Word.objects.filter(wordgroup__group=group).order_by('?')[:word_count]
            
            if not words:
                return Response({
                    'error': 'No words available in this group'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create study session for vocabulary quiz
            study_activity = StudyActivity.objects.get(name='Vocabulary Quiz')
            session = StudySession.objects.create(
                group=group,
                study_activity=study_activity,
                start_time=timezone.now()
            )

            # Prepare quiz data
            quiz_words = []
            for word in words:
                # For each word, get 3 random incorrect options
                incorrect_options = Word.objects.exclude(id=word.id).order_by('?')[:3]
                options = [{'id': opt.id, 'text': opt.english} for opt in incorrect_options]
                options.append({'id': word.id, 'text': word.english})
                random.shuffle(options)
                
                quiz_words.append({
                    'id': word.id,
                    'urdu': word.urdu,
                    'options': options
                })

            return Response({
                'session_id': session.id,
                'words': quiz_words
            })
            
        except Group.DoesNotExist:
            return Response({
                'error': 'Group not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except StudyActivity.DoesNotExist:
            # Create Vocabulary Quiz activity if it doesn't exist
            study_activity = StudyActivity.objects.create(
                name='Vocabulary Quiz',
                description='Test your vocabulary knowledge with multiple choice questions',
                thumbnail_url='https://example.com/quiz-thumbnail.jpg'  # Replace with actual thumbnail
            )
            # Retry the request
            return self.start(request)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def submit(self, request):
        """Submit quiz answers."""
        session_id = request.data.get('session_id')
        answers = request.data.get('answers', [])

        try:
            session = StudySession.objects.get(id=session_id)
            
            # Mark session as complete
            session.end_time = timezone.now()
            session.save()

            # Process answers
            correct_count = 0
            for answer in answers:
                word_id = answer.get('word_id')
                selected_id = answer.get('selected_id')
                
                if word_id and selected_id:
                    word = Word.objects.get(id=word_id)
                    is_correct = word_id == selected_id
                    
                    WordReviewItem.objects.create(
                        word=word,
                        study_session=session,
                        correct=is_correct
                    )
                    
                    if is_correct:
                        correct_count += 1

            return Response({
                'total_questions': len(answers),
                'correct_answers': correct_count,
                'score_percentage': (correct_count / len(answers)) * 100 if answers else 0
            })

        except StudySession.DoesNotExist:
            return Response({
                'error': 'Study session not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Word.DoesNotExist:
            return Response({
                'error': 'Word not found'
            }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@csrf_exempt
def last_study_session(request):
    """Get the last study session."""
    last_session = StudySession.objects.order_by('-start_time').first()
    if last_session:
        serializer = StudySessionSerializer(last_session)
        return Response(serializer.data)
    return Response({
        'id': None,
        'start_time': None,
        'group': None,
        'study_activity': None,
        'word_count': 0,
        'correct_count': 0
    })

@api_view(['GET'])
@csrf_exempt
def study_progress(request):
    """Get study progress statistics."""
    # Calculate statistics for the last 7 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)
    
    daily_stats = []
    current_date = start_date
    
    while current_date <= end_date:
        next_date = current_date + timedelta(days=1)
        
        # Get sessions for this day
        daily_sessions = StudySession.objects.filter(
            start_time__gte=current_date,
            start_time__lt=next_date
        )
        
        # Calculate statistics
        total_words = WordReviewItem.objects.filter(
            study_session__in=daily_sessions
        ).count()
        
        correct_words = WordReviewItem.objects.filter(
            study_session__in=daily_sessions,
            correct=True
        ).count()
        
        daily_stats.append({
            'date': current_date.date().isoformat(),
            'total_words': total_words,
            'correct_words': correct_words,
            'accuracy': (correct_words / total_words * 100) if total_words > 0 else 0
        })
        
        current_date += timedelta(days=1)
    
    return Response(daily_stats)

@api_view(['GET'])
@csrf_exempt
def quick_stats(request):
    """Get quick statistics for the dashboard."""
    # Get total words studied
    total_words = WordReviewItem.objects.count()
    
    # Get completed study sessions (those with end_time set)
    total_study_sessions = StudySession.objects.filter(end_time__isnull=False).count()
    
    # Calculate overall accuracy
    correct_words = WordReviewItem.objects.filter(correct=True).count()
    success_rate = round((correct_words / total_words * 100), 1) if total_words > 0 else 0
    
    # Get active groups (those with sessions in the last 7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    total_active_groups = Group.objects.filter(
        studysession__start_time__gte=seven_days_ago
    ).distinct().count()
    
    # Calculate study streak
    today = timezone.now().date()
    study_streak = 0
    current_date = today
    
    while True:
        has_session = StudySession.objects.filter(
            start_time__date=current_date,
            end_time__isnull=False  # Only count completed sessions
        ).exists()
        
        if not has_session:
            break
            
        study_streak += 1
        current_date -= timedelta(days=1)
    
    return Response({
        'success_rate': success_rate,
        'total_study_sessions': total_study_sessions,
        'total_active_groups': total_active_groups,
        'study_streak': study_streak
    })

@api_view(['POST'])
@csrf_exempt
def create_study_activity(request):
    try:
        group = Group.objects.get(id=request.data.get('group_id'))
        activity = StudyActivity.objects.get(id=request.data.get('activity_id'))
        
        session = StudySession.objects.create(
            group=group,
            study_activity=activity
        )
        
        serializer = StudySessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except (Group.DoesNotExist, StudyActivity.DoesNotExist):
        return Response({'error': 'Invalid group_id or activity_id'}, status=status.HTTP_400_BAD_REQUEST)

# Listening Practice Views
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from services.listening_service import ListeningService

listening_service = ListeningService()

@api_view(['POST'])
def download_transcript(request):
    """Download and process transcript from YouTube video."""
    try:
        # Get video URL or ID from request
        video_input = request.data.get('url')
        if not video_input:
            return Response({
                'data': {
                    'status': 'error',
                    'message': 'Video URL or ID is required',
                    'code': 'MISSING_URL'
                }
            }, status=400)

        # Initialize listening service with AWS permission check
        try:
            listening_service = ListeningService()
        except ValueError as e:
            # Handle AWS permission errors
            if "Missing required AWS permissions" in str(e):
                logger.error(f"AWS permissions error: {e}")
                return Response({
                    'data': {
                        'status': 'error',
                        'message': str(e),
                        'code': 'AWS_PERMISSIONS_ERROR',
                        'required_permissions': aws_config.REQUIRED_PERMISSIONS
                    }
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            raise
        
        try:
            # Extract and validate video ID
            video_id = listening_service.extract_video_id(video_input)
            if not video_id:
                logger.warning("Invalid video ID format")
                return Response({
                    'data': {
                        'status': 'error',
                        'message': 'Invalid video URL or ID format',
                        'code': 'INVALID_VIDEO_ID'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get transcript with translations and vector search
            try:
                transcript = listening_service.get_transcript(video_id)
                if not transcript:
                    raise ValueError("No transcript available for this video")
                
                # Return response with metadata
                logger.info(f"Successfully processed transcript for video {video_id}")
                return Response({
                    'data': {
                        'status': 'success',
                        'transcript': transcript,
                        'metadata': {
                            'video_id': video_id,
                            'segments': len(transcript),
                            'languages': list(set(seg['language'] for seg in transcript)),
                            'has_translations': any(seg.get('has_translation', False) for seg in transcript),
                            'processed_at': timezone.now().isoformat()
                        }
                    }
                })
                
            except (TranscriptsDisabled, NoTranscriptFound) as e:
                logger.warning(f"YouTube transcript error for video {video_id}: {e}")
                return Response({
                    'data': {
                        'status': 'error',
                        'message': f'No transcript available: {str(e)}',
                        'code': 'NO_TRANSCRIPT'
                    }
                }, status=status.HTTP_404_NOT_FOUND)
                
            except ValueError as e:
                logger.warning(f"Transcript processing error for video {video_id}: {e}")
                return Response({
                    'data': {
                        'status': 'error',
                        'message': str(e),
                        'code': 'TRANSCRIPT_PROCESSING_ERROR'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except ValueError as e:
            logger.warning(f"Value error in download_transcript: {e}")
            return Response({
                'data': {
                    'status': 'error',
                    'message': str(e),
                    'code': 'INVALID_VIDEO_ID'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error in download_transcript: {e}")
        return Response({
            'data': {
                'status': 'error',
                'message': 'An unexpected error occurred',
                'code': 'INTERNAL_SERVER_ERROR'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def get_listening_questions(request):
    """Get questions for a YouTube video."""
    try:
        # Log request data
        logger.info(f"Received questions request: {request.data}")
        
        # Validate request data
        url = request.data.get('url')
        if not url:
            logger.warning("Missing url in request")
            return Response({
                'data': {
                    'status': 'error',
                    'message': 'Video URL or ID is required',
                    'code': 'MISSING_URL'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize services
        try:
            listening_service = ListeningService()
        except ValueError as e:
            # Handle AWS permission errors
            if "Missing required AWS permissions" in str(e):
                logger.error(f"AWS permissions error: {e}")
                return Response({
                    'data': {
                        'status': 'error',
                        'message': str(e),
                        'code': 'AWS_PERMISSIONS_ERROR',
                        'required_permissions': aws_config.REQUIRED_PERMISSIONS
                    }
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            raise
        
        try:
            # Extract and validate video ID
            video_id = listening_service.extract_video_id(url)
            if not video_id:
                logger.warning("Invalid video ID format")
                return Response({
                    'data': {
                        'status': 'error',
                        'message': 'Invalid video URL or ID format',
                        'code': 'INVALID_VIDEO_ID'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get questions for the video
            try:
                questions = listening_service.get_questions(video_id)
                if not questions:
                    logger.warning(f"No questions generated for video {video_id}")
                    return Response({
                        'data': {
                            'status': 'error',
                            'message': 'Failed to generate questions for this video',
                            'code': 'NO_QUESTIONS_GENERATED'
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Return success response
                logger.info(f"Successfully generated {len(questions)} questions for video {video_id}")
                return Response({
                    'data': {
                        'status': 'success',
                        'questions': questions,
                        'metadata': {
                            'video_id': video_id,
                            'count': len(questions),
                            'generated_at': timezone.now().isoformat(),
                            'source': 'bedrock',
                            'model': aws_config.BEDROCK_MODEL_ID
                        }
                    }
                })
                
            except ValueError as e:
                error_message = str(e)
                error_code = 'QUESTION_GENERATION_ERROR'
                
                # Map specific errors to codes
                if "No transcript available" in error_message:
                    error_code = 'NO_TRANSCRIPT'
                elif "Empty transcript text" in error_message:
                    error_code = 'EMPTY_TRANSCRIPT'
                elif "No JSON array found" in error_message:
                    error_code = 'INVALID_MODEL_RESPONSE'
                elif "Invalid questions format" in error_message:
                    error_code = 'INVALID_QUESTION_FORMAT'
                elif "Service temporarily unavailable" in error_message:
                    error_code = 'MODEL_NOT_READY'
                elif "Rate limit exceeded" in error_message:
                    error_code = 'RATE_LIMIT_EXCEEDED'
                
                logger.warning(f"Value error in get_questions: {error_message}")
                return Response({
                    'data': {
                        'status': 'error',
                        'message': error_message,
                        'code': error_code
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except ValueError as e:
            logger.warning(f"Value error in extract_video_id: {e}")
            return Response({
                'data': {
                    'status': 'error',
                    'message': str(e),
                    'code': 'INVALID_VIDEO_ID'
                }
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error in get_questions: {e}")
        return Response({
            'data': {
                'status': 'error',
                'message': 'An unexpected error occurred',
                'code': 'INTERNAL_SERVER_ERROR'
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def get_transcript_and_stats(request):
    """Get transcript and statistics for a YouTube video."""
    try:
        # Accept either video_id or url parameter
        video_id = request.data.get('video_id') or request.data.get('url')
        if not video_id:
            return Response({
                'status': 'error',
                'message': 'Video ID or URL is required',
                'code': 'MISSING_URL'
            }, status=400)
            
        # Extract video ID if URL is provided
        try:
            video_id = listening_service.extract_video_id(video_id)
        except ValueError as e:
            logger.error(f"Invalid video ID or URL: {e}")
            return Response({
                'status': 'error',
                'message': str(e),
                'code': 'INVALID_VIDEO_ID'
            }, status=400)
            
        result = listening_service.get_transcript_with_stats(video_id)
        return Response({
            'status': 'success',
            'data': result
        })
        
    except ValueError as e:
        logger.error(f"Invalid video ID: {e}")
        return Response({
            'status': 'error',
            'message': str(e),
            'code': 'INVALID_VIDEO_ID'
        }, status=400)
    except Exception as e:
        logger.error(f"Error getting transcript and stats: {e}")
        return Response({
            'status': 'error',
            'message': str(e),
            'code': 'INTERNAL_SERVER_ERROR'
        }, status=500)

@api_view(['POST'])
def test_hindi_to_urdu(request):
    """Test Hindi to Urdu conversion using AWS Translate."""
    try:
        text = request.data.get('text', '')
        if not text:
            return Response({
                'status': 'error',
                'message': 'No text provided',
                'code': 'MISSING_TEXT'
            }, status=400)
            
        service = ListeningService()
        converted_text = service.convert_hindi_to_urdu(text)
        
        return Response({
            'status': 'success',
            'original': text,
            'converted': converted_text
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e),
            'code': 'INTERNAL_SERVER_ERROR'
        }, status=500)

@api_view(['POST'])
def search_transcripts(request):
    """
    Search through stored transcripts using semantic search.
    
    Features:
    - Semantic similarity search using ChromaDB and Bedrock embeddings
    - Language-specific filtering and script conversion
    - Configurable similarity threshold and result limits
    - Rate limiting and guardrails support
    """
    try:
        # Validate request
        if not request.data.get('query'):
            return Response({
                'status': 'error',
                'message': 'Query is required',
                'code': 'MISSING_QUERY'
            }, status=400)
        
        # Get search parameters with enhanced validation
        query = request.data['query']
        k = min(int(request.data.get('k', vector_store_config.DEFAULT_SEARCH_LIMIT)), 
                vector_store_config.MAX_SEARCH_LIMIT)
        min_score = max(float(request.data.get('min_score', vector_store_config.SIMILARITY_THRESHOLD)), 
                       vector_store_config.MIN_SIMILARITY_THRESHOLD)
        language = request.data.get('language', vector_store_config.DEFAULT_LANGUAGE)
        
        # Validate language
        if language and language not in vector_store_config.SUPPORTED_LANGUAGES:
            return Response({
                'status': 'error',
                'message': f'Unsupported language. Must be one of: {", ".join(vector_store_config.SUPPORTED_LANGUAGES)}',
                'code': 'INVALID_LANGUAGE'
            }, status=400)
            
        # Convert query to Urdu if needed
        processed_query = query
        if language == "ur" and listening_service._language_service:
            try:
                processed_query = listening_service._language_service.convert_hindi_to_urdu(query)
            except Exception as e:
                logger.warning(f"Failed to convert query to Urdu: {e}")
        
        # Search transcripts
        results = listening_service._vector_store.search_transcripts(
            query=processed_query,
            k=k,
            min_score=min_score,
            language=language
        )
        
        return Response({
            'status': 'success',
            'query': {
                'original': query,
                'processed': processed_query,
                'language': language
            },
            'results': results,
            'metadata': {
                'total_results': len(results),
                'similarity_threshold': min_score,
                'max_results': k
            }
        })
        
    except Exception as e:
        logger.error(f"Error searching transcripts: {e}")
        return Response({
            'status': 'error',
            'message': str(e),
            'code': 'INTERNAL_SERVER_ERROR'
        }, status=500)

@api_view(['GET'])
def test_bedrock(request):
    """Test AWS Bedrock connection."""
    try:
        service = ListeningService()
        if not service._runtime:
            return Response({
                'status': 'error',
                'message': 'Bedrock client not initialized',
                'details': 'Check AWS credentials and Bedrock access',
                'code': 'BEDROCK_NOT_INITIALIZED'
            }, status=500)
            
        # Test simple prompt using Claude 3 format
        body = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": "Say hello in Urdu."
                }
            ],
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "temperature": 0.5,
            "top_k": 250,
            "top_p": 0.5
        })
        
        response = service._runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=body.encode(),
            contentType='application/json',
            accept='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        return Response({
            'status': 'success',
            'message': 'Bedrock connection successful',
            'response': response_body
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e),
            'details': 'Error testing Bedrock connection',
            'code': 'INTERNAL_SERVER_ERROR'
        }, status=500)
