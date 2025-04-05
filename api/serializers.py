from rest_framework import serializers
from .models import (
    Word, Group, WordGroup, StudyActivity, StudySession, WordReviewItem,
    WordMatchingGame, WordMatchingQuestion, WordMatchingStats,
    FlashcardGame, FlashcardReview, FlashcardStats
)

class WordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Word
        fields = ['id', 'urdu', 'urdlish', 'english', 'parts', 'difficulty_level', 'usage_frequency']

class FlashcardGameSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlashcardGame
        fields = [
            'id', 'user', 'score', 'streak', 'max_streak', 'total_cards',
            'cards_reviewed', 'start_time', 'end_time', 'completed'
        ]

class FlashcardReviewSerializer(serializers.ModelSerializer):
    word = WordSerializer(read_only=True)
    
    class Meta:
        model = FlashcardReview
        fields = ['id', 'game', 'word', 'confidence_level', 'time_spent', 'created_at']

class FlashcardStatsSerializer(serializers.ModelSerializer):
    average_time_per_card = serializers.FloatField(read_only=True)
    
    class Meta:
        model = FlashcardStats
        fields = [
            'id', 'user', 'cards_reviewed', 'total_time_spent',
            'best_streak', 'last_reviewed', 'average_time_per_card'
        ]
