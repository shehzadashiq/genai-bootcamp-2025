from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404

from .models import FlashcardGame, FlashcardReview, FlashcardStats, Word
from .serializers import FlashcardGameSerializer, FlashcardStatsSerializer

class FlashcardGameViewSet(viewsets.ModelViewSet):
    queryset = FlashcardGame.objects.all()
    serializer_class = FlashcardGameSerializer

    def create(self, request):
        try:
            with transaction.atomic():
                # Create the game first
                game = FlashcardGame.objects.create(
                    user=request.data.get('user', 'user1'),
                    total_cards=10,
                    cards_reviewed=0,
                    score=0,
                    streak=0,
                    max_streak=0,
                    start_time=timezone.now()
                )
                
                # Get random words
                words = list(Word.objects.order_by('?')[:10])
                
                # Create initial review for the first word only
                first_review = FlashcardReview.objects.create(
                    game=game,
                    word=words[0],
                    confidence_level=0,
                    time_spent=0
                )
                
                # Store all words in game.words without creating reviews
                game.words.add(*words)
                
                # Refresh game to get the reviews
                game.refresh_from_db()
                
                return Response(self.get_serializer(game).data)
        except Exception as e:
            print(f"Error creating game: {str(e)}")
            return Response({"error": str(e)}, status=500)

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
        
        try:
            # Try to get existing review
            current_review = game.reviews.get(word_id=word_id)
            current_review.confidence_level = confidence_level
            current_review.time_spent = time_spent
            current_review.save()
        except FlashcardReview.DoesNotExist:
            # Create new review if it doesn't exist
            current_review = FlashcardReview.objects.create(
                game=game,
                word_id=word_id,
                confidence_level=confidence_level,
                time_spent=time_spent
            )
        
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
            game.save()
        
        return Response(self.get_serializer(game).data)

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
