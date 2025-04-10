from django.db.models import Count, Sum, Case, When, Q
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
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404

from .models import StudySession, StudyActivity, Word, Group, WordReviewItem, WordGroup, WordMatchingGame, WordMatchingQuestion, WordMatchingStats, FlashcardGame, FlashcardReview, FlashcardStats
from .serializers import (
    StudySessionSerializer, 
    StudyActivitySerializer, 
    StudySessionListSerializer,
    WordSerializer,
    GroupSerializer,
    WordMatchingGameSerializer, 
    WordMatchingQuestionSerializer,
    WordMatchingStatsSerializer,
    FlashcardGameSerializer,
    FlashcardReviewSerializer,
    FlashcardStatsSerializer
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

    @action(detail=True, methods=['get'])
    def words(self, request, pk=None):
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
        
        # Check if we should merge groups by difficulty level
        merge_by_difficulty = request.query_params.get('merge_by_difficulty', 'false').lower() == 'true'
        
        if merge_by_difficulty:
            # Get all groups
            all_groups = list(queryset)
            
            # Create a dictionary to store merged groups by difficulty level
            merged_groups = {}
            
            # Map of difficulty levels in group names
            difficulty_keywords = {
                'beginner': 'Beginner',
                'intermediate': 'Intermediate',
                'advanced': 'Advanced'
            }
            
            # Group the groups by difficulty level
            for group in all_groups:
                for keyword, label in difficulty_keywords.items():
                    if keyword.lower() in group.name.lower():
                        if label not in merged_groups:
                            # Create a new merged group with this difficulty level
                            merged_groups[label] = {
                                'id': group.id,  # Use the ID of the first group with this difficulty
                                'name': f"{label} Words",
                                'word_count': group.word_count,
                                'original_groups': [group]
                            }
                        else:
                            # Add this group's word count to the merged group
                            merged_groups[label]['word_count'] += group.word_count
                            merged_groups[label]['original_groups'].append(group)
                        break
            
            # Convert merged groups to a list
            merged_groups_list = [
                {
                    'id': info['id'],
                    'name': info['name'],
                    'word_count': info['word_count']
                } for info in merged_groups.values()
            ]
            
            # Return the merged groups
            return Response({
                'items': merged_groups_list,
                'pagination': {
                    'current_page': 1,
                    'total_pages': 1,
                    'total_items': len(merged_groups_list),
                    'items_per_page': len(merged_groups_list)
                }
            })
        
        # If not merging, use the default implementation
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

    @action(detail=True, methods=['get'])
    def words(self, request, pk=None):
        """Get words for a specific group."""
        group = self.get_object()
        words = Word.objects.filter(wordgroup__group=group)
        page = self.paginate_queryset(words)
        if page is not None:
            serializer = WordSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = WordSerializer(words, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def study_sessions(self, request, pk=None):
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
        try:
            group_id = request.data.get('group_id')
            word_count = request.data.get('word_count', 10)
            difficulty = request.data.get('difficulty', 'easy')
            
            # Get the group
            group = Group.objects.get(id=group_id)
            
            # Check if this is a merged group (by checking if the name contains just the difficulty level)
            is_merged_group = any(keyword in group.name.lower() for keyword in ['beginner', 'intermediate', 'advanced']) and not any(lang in group.name.lower() for lang in ['urdu', 'english'])
            
            if is_merged_group:
                # Get all groups with the same difficulty level
                difficulty_level = None
                for level in ['beginner', 'intermediate', 'advanced']:
                    if level in group.name.lower():
                        difficulty_level = level
                        break
                
                if difficulty_level:
                    # Get all groups with this difficulty level
                    related_groups = Group.objects.filter(name__icontains=difficulty_level)
                    group_ids = related_groups.values_list('id', flat=True)
                    
                    # Get words from all related groups using WordGroup relationship
                    words = Word.objects.filter(wordgroup__group__id__in=group_ids).distinct()
                else:
                    # Fallback to just using the selected group
                    words = Word.objects.filter(wordgroup__group=group)
            else:
                # Regular group, just get its words
                words = Word.objects.filter(wordgroup__group=group)
            
            # Limit to the requested number of words
            if words.count() < word_count:
                word_count = words.count()
            
            # Randomly select words
            selected_words = random.sample(list(words), word_count)
            
            # Create a new study session
            study_session = StudySession.objects.create(
                group=group,
                study_activity=StudyActivity.objects.get(name='Vocabulary Quiz'),
                start_time=timezone.now()
            )
            
            # Generate quiz words with options
            quiz_words = []
            for word in selected_words:
                # Get options (including the correct answer)
                options = [word.english]
                
                # Get other random words for options
                other_words = Word.objects.exclude(id=word.id).order_by('?')[:3]
                for other_word in other_words:
                    options.append(other_word.english)
                
                # Shuffle options
                random.shuffle(options)
                
                # Find the index of the correct answer
                correct_option_index = options.index(word.english)
                
                quiz_words.append({
                    'word_id': word.id,
                    'word': WordSerializer(word).data,
                    'options': options,
                    'correct_option': correct_option_index
                })
                
                # We'll create WordReviewItem objects when answers are submitted
            
            # Store quiz data in session metadata
            study_session.metadata = {
                'quiz_data': {
                    'words': quiz_words
                }
            }
            study_session.save()
            
            # Return quiz data with word_id directly in the response
            response_data = {
                'session_id': study_session.id,
                'words': []
            }
            
            for quiz_word in quiz_words:
                response_data['words'].append({
                    'word_id': quiz_word['word_id'],
                    'word': quiz_word['word'],
                    'options': quiz_word['options']
                })
            
            return Response(response_data)
            
        except Group.DoesNotExist:
            return Response({'error': 'Group not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error starting vocabulary quiz: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def submit(self, request):
        """
        Submit quiz answers.
        """
        session_id = request.data.get('session_id')
        answers = request.data.get('answers', [])
        
        try:
            session = StudySession.objects.get(id=session_id)
            
            # Mark session as complete
            session.end_time = timezone.now()
            session.save()

            # Process answers
            correct_count = 0
            total_questions = len(answers)
            quiz_data = session.metadata.get('quiz_data', {})
            quiz_words = quiz_data.get('words', [])
            
            # Create a dictionary for faster lookups
            word_correct_options = {}
            for quiz_word in quiz_words:
                word_id = quiz_word.get('word_id')
                if word_id:
                    word_correct_options[str(word_id)] = quiz_word.get('correct_option')
            
            for answer in answers:
                word_id = answer.get('word_id')
                selected_id = answer.get('selected_id')
                
                if word_id is not None and selected_id is not None:
                    word = Word.objects.get(id=word_id)
                    
                    # Get the correct option from our dictionary
                    correct_option = word_correct_options.get(str(word_id))
                    is_correct = False
                    
                    if correct_option is not None:
                        is_correct = int(selected_id) == int(correct_option)
                    
                    # Check if a review item already exists for this word and session
                    review_item, created = WordReviewItem.objects.get_or_create(
                        word=word,
                        study_session=session,
                        defaults={'correct': is_correct}
                    )
                    
                    # If the review item already exists, update it
                    if not created:
                        review_item.correct = is_correct
                        review_item.save()
                    
                    if is_correct:
                        correct_count += 1
            
            # Calculate score percentage
            score_percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
            
            return Response({
                'total_questions': total_questions,
                'correct_answers': correct_count,
                'score_percentage': score_percentage
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

class WordMatchingGameViewSet(viewsets.ModelViewSet):
    queryset = WordMatchingGame.objects.all()
    serializer_class = WordMatchingGameSerializer

    @action(detail=False, methods=['post'])
    def start_game(self, request):
        user = request.data.get('user', 'anonymous')
        num_questions = request.data.get('num_questions', 10)
        
        # Create new game
        game = WordMatchingGame.objects.create(
            user=user,
            total_questions=num_questions
        )
        
        # Get random words for the game
        words = list(Word.objects.all().order_by('?')[:num_questions])
        
        # Create questions
        for word in words:
            # Get 3 random incorrect options
            incorrect_options = list(Word.objects.exclude(id=word.id)
                                  .order_by('?')[:3])
            
            WordMatchingQuestion.objects.create(
                game=game,
                word=word
            )
        
        serializer = self.get_serializer(game)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def submit_answer(self, request, pk=None):
        game = self.get_object()
        if game.completed:
            return Response(
                {"error": "Game is already completed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        question_id = request.data.get('question_id')
        answer = request.data.get('answer')
        response_time = request.data.get('response_time', 0)
        
        try:
            question = game.questions.get(id=question_id)
        except WordMatchingQuestion.DoesNotExist:
            return Response(
                {"error": "Question not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if answer is correct
        is_correct = question.word.english.lower() == answer.lower()
        
        # Update question
        question.selected_answer = answer
        question.is_correct = is_correct
        question.response_time = response_time
        question.save()
        
        # Update game score
        with transaction.atomic():
            game.correct_answers = F('correct_answers') + (1 if is_correct else 0)
            game.score = F('score') + (10 if is_correct else 0)
            
            # Check if game is completed
            if game.questions.filter(selected_answer__isnull=False).count() == game.total_questions:
                game.completed = True
                game.end_time = timezone.now()
            
            game.save()
            
            # Update user stats
            stats, _ = WordMatchingStats.objects.get_or_create(user=game.user)
            stats.games_played = F('games_played') + (1 if game.completed else 0)
            stats.total_score = F('total_score') + (10 if is_correct else 0)
            stats.total_correct = F('total_correct') + (1 if is_correct else 0)
            stats.total_questions = F('total_questions') + 1
            if game.completed:
                stats.last_played = timezone.now()
                # Update best score if current score is higher
                game.refresh_from_db()  # Get updated score
                if game.score > stats.best_score:
                    stats.best_score = game.score
            stats.save()
        
        game.refresh_from_db()
        serializer = self.get_serializer(game)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def get_options(self, request, pk=None):
        question_id = request.query_params.get('question_id')
        try:
            question = WordMatchingQuestion.objects.get(id=question_id, game_id=pk)
        except WordMatchingQuestion.DoesNotExist:
            return Response(
                {"error": "Question not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get correct answer and 3 random incorrect options
        correct_word = question.word
        incorrect_options = list(Word.objects.exclude(id=correct_word.id)
                               .order_by('?')[:3])
        
        # Combine and shuffle options
        options = [correct_word] + incorrect_options
        random.shuffle(options)
        
        return Response({
            'options': [word.english for word in options]
        })

class WordMatchingStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WordMatchingStats.objects.all()
    serializer_class = WordMatchingStatsSerializer
    
    def get_queryset(self):
        queryset = WordMatchingStats.objects.all()
        user = self.request.query_params.get('user', None)
        if user is not None:
            queryset = queryset.filter(user=user)
        return queryset

class FlashcardGameViewSet(viewsets.ModelViewSet):
    """
    API endpoint for flashcard game functionality.
    """
    queryset = FlashcardGame.objects.all()
    serializer_class = FlashcardGameSerializer

    def create(self, request):
        """Create a new flashcard game"""
        user = request.data.get('user')
        total_cards = request.data.get('total_cards', 10)
        
        # Get random words for the game
        words = Word.objects.order_by('?')[:total_cards]
        
        # Create new game
        game = FlashcardGame.objects.create(
            user=user,
            total_cards=total_cards,
            score=0,
            streak=0,
            max_streak=0,
            cards_reviewed=0,
            start_time=timezone.now()
        )
        
        # Create initial review for first word
        FlashcardReview.objects.create(
            game=game,
            word=words[0],
            confidence_level=0
        )
        
        serializer = self.get_serializer(game)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Get a specific game by ID"""
        try:
            game = FlashcardGame.objects.get(pk=pk)
            serializer = self.get_serializer(game)
            return Response(serializer.data)
        except FlashcardGame.DoesNotExist:
            return Response({"error": "Game not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def review_card(self, request, pk=None):
        try:
            game = FlashcardGame.objects.get(pk=pk)
        except FlashcardGame.DoesNotExist:
            return Response({"error": "Game not found"}, status=status.HTTP_404_NOT_FOUND)
        
        word_id = request.data.get('word_id')
        confidence_level = request.data.get('confidence_level')
        time_spent = request.data.get('time_spent', 0)
        
        # Update current review
        current_review = game.reviews.get(word_id=word_id)
        current_review.confidence_level = confidence_level
        current_review.time_spent = time_spent
        current_review.save()
        
        # Update game stats
        with transaction.atomic():
            game.cards_reviewed += 1
            
            # Update streak
            if confidence_level >= 3:  # Easy or Medium
                game.streak += 1
                game.max_streak = max(game.streak, game.max_streak)
            else:
                game.streak = 0
            
            # Update score based on confidence
            game.score += confidence_level * 10
            
            # Check if game is completed
            if game.cards_reviewed >= game.total_cards:
                game.completed = True
                game.end_time = timezone.now()
                game.save()
                
                # Update user stats
                stats, _ = FlashcardStats.objects.get_or_create(user=game.user)
                stats.cards_reviewed += game.total_cards
                stats.total_time_spent += sum(r.time_spent or 0 for r in game.reviews.all())
                stats.best_streak = max(stats.best_streak, game.max_streak)
                stats.last_reviewed = timezone.now()
                stats.average_time_per_card = (
                    stats.total_time_spent / stats.cards_reviewed 
                    if stats.cards_reviewed > 0 else 0
                )
                stats.save()
                
                return Response({
                    "success": True,
                    "game_completed": True,
                    "current_streak": game.streak,
                    "cards_remaining": 0
                })
            
            # Create next review if game not completed
            remaining_words = Word.objects.exclude(
                id__in=game.reviews.values_list('word_id', flat=True)
            ).order_by('?')
            
            if remaining_words.exists():
                FlashcardReview.objects.create(
                    game=game,
                    word=remaining_words[0],
                    confidence_level=0
                )
            
            game.save()
            
            return Response({
                "success": True,
                "game_completed": False,
                "current_streak": game.streak,
                "cards_remaining": game.total_cards - game.cards_reviewed
            })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        user = request.query_params.get('user')
        try:
            stats = FlashcardStats.objects.get(user=user)
            serializer = FlashcardStatsSerializer(stats)
            return Response(serializer.data)
        except FlashcardStats.DoesNotExist:
            return Response({
                "error": "Stats not found for user"
            }, status=status.HTTP_404_NOT_FOUND)
