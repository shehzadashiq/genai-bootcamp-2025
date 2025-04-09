from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.db.models import F
from .models import (
    Word, FlashcardGame, FlashcardReview, FlashcardStats
)
from .serializers import (
    WordSerializer, FlashcardGameSerializer, FlashcardReviewSerializer,
    FlashcardStatsSerializer
)
import random

class FlashcardViewSet(viewsets.ModelViewSet):
    queryset = FlashcardGame.objects.all()
    serializer_class = FlashcardGameSerializer

    def create(self, request):
        # Create a new flashcard game
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            game = serializer.save()
            
            # Get random words for the game
            words = list(Word.objects.all().order_by('?')[:game.total_cards])
            
            # Create review items for each word
            for word in words:
                FlashcardReview.objects.create(game=game, word=word)
            
            # Get or create stats for the user
            FlashcardStats.objects.get_or_create(user=game.user)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def review_card(self, request, pk=None):
        game = self.get_object()
        if game.completed:
            return Response(
                {"error": "Game is already completed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        word_id = request.data.get('word_id')
        confidence_level = request.data.get('confidence_level', 0)
        time_spent = request.data.get('time_spent', 0)

        try:
            review = FlashcardReview.objects.get(game=game, word_id=word_id)
            review.confidence_level = confidence_level
            review.time_spent = time_spent
            review.save()

            # Update game stats
            game.cards_reviewed = F('cards_reviewed') + 1
            game.score = F('score') + confidence_level
            if confidence_level >= 4:  # Good confidence
                game.streak = F('streak') + 1
            else:
                game.streak = 0
            game.save()
            game.refresh_from_db()

            # Update user stats
            stats = FlashcardStats.objects.get(user=game.user)
            stats.cards_reviewed = F('cards_reviewed') + 1
            stats.total_time_spent = F('total_time_spent') + (time_spent / 60)  # Convert to minutes
            stats.best_streak = max(game.streak, stats.best_streak)
            stats.last_reviewed = timezone.now()
            stats.save()

            # Check if game is completed
            if game.cards_reviewed >= game.total_cards:
                game.completed = True
                game.end_time = timezone.now()
                game.save()

            return Response({
                'success': True,
                'game_completed': game.completed,
                'current_streak': game.streak,
                'cards_remaining': game.total_cards - game.cards_reviewed
            })

        except FlashcardReview.DoesNotExist:
            return Response(
                {"error": "Review not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class FlashcardStatsView(generics.RetrieveAPIView):
    serializer_class = FlashcardStatsSerializer

    def get_object(self):
        stats, _ = FlashcardStats.objects.get_or_create(
            user=self.request.query_params.get('user', '')
        )
        return stats
