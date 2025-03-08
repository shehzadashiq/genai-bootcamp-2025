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
    try:
        logger.info(f"Request data: {request.data}")
        logger.info(f"Request content type: {request.content_type}")
        
        if not isinstance(request.data, dict):
            logger.error(f"Invalid request data type: {type(request.data)}")
            return Response(
                {'error': 'Invalid request format. Expected JSON object with url field'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        video_url = request.data.get('url')
        if not video_url:
            logger.error("No URL provided in request")
            return Response(
                {'error': 'URL is required. Please provide a valid YouTube URL'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not isinstance(video_url, str):
            logger.error(f"Invalid URL type: {type(video_url)}")
            return Response(
                {'error': 'URL must be a string'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        logger.info(f"Extracting video ID from URL: {video_url}")
        try:
            video_id = listening_service.extract_video_id(video_url)
        except ValueError as e:
            logger.error(f"Invalid YouTube URL: {str(e)}")
            return Response(
                {'error': f'Invalid YouTube URL: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info(f"Getting transcript for video ID: {video_id}")
        try:
            transcript = listening_service.get_transcript(video_url)
        except Exception as e:
            logger.error(f"Failed to get transcript: {str(e)}")
            return Response(
                {'error': f'Failed to get transcript: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.info("Storing transcript")
        try:
            listening_service.store_transcript(video_url, transcript)
        except Exception as e:
            logger.error(f"Failed to store transcript: {str(e)}")
            # Continue since we already have the transcript
            
        logger.info("Transcript downloaded and stored successfully")
        return Response({
            'video_id': video_id,
            'message': 'Transcript downloaded and stored successfully'
        })
    except Exception as e:
        logger.error(f"Unexpected error in download_transcript: {str(e)}", exc_info=True)
        return Response(
            {'error': 'An unexpected error occurred'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def get_listening_questions(request):
    try:
        video_url = request.data.get('url')
        if not video_url:
            return Response({'error': 'URL is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        result = listening_service.get_questions_for_video(video_url)
        return Response(result)
    except Exception as e:
        logger.error(f"Error in get_listening_questions: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def get_transcript_and_stats(request):
    try:
        video_url = request.data.get('url')
        if not video_url:
            return Response({'error': 'URL is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        result = listening_service.get_transcript_with_stats(video_url)
        return Response(result)
    except Exception as e:
        logger.error(f"Error in get_transcript_and_stats: {str(e)}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def test_bedrock(request):
    """Test AWS Bedrock connection."""
    try:
        service = ListeningService()
        if not service._runtime:
            return Response({
                'status': 'error',
                'message': 'Bedrock client not initialized',
                'details': 'Check AWS credentials and Bedrock access'
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
            'details': 'Error testing Bedrock connection'
        }, status=500)

@api_view(['POST'])
def test_hindi_to_urdu(request):
    """Test Hindi to Urdu conversion using AWS Translate."""
    try:
        text = request.data.get('text', '')
        if not text:
            return Response({
                'status': 'error',
                'message': 'No text provided'
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
            'message': str(e)
        }, status=500)

@api_view(['POST'])
def search_transcripts(request):
    """Search through stored transcripts using semantic search."""
    try:
        if not request.data.get('query'):
            return Response({
                'status': 'error',
                'message': 'Query is required'
            }, status=400)
            
        query = request.data['query']
        k = request.data.get('k', 5)  # Number of results to return
        
        # Get ListeningService instance to handle Hindi-Urdu conversion if needed
        service = ListeningService()
        
        # Convert query to Urdu script if it's in Hindi
        # This ensures consistent search regardless of input script
        urdu_query = service.convert_hindi_to_urdu(query)
        
        # Search using vector store
        vector_store = VectorStoreService()
        results = vector_store.search_transcripts(urdu_query, k=k)
        
        return Response({
            'status': 'success',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error searching transcripts: {e}")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)
