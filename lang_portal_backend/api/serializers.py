from rest_framework import serializers
from .models import (
    StudySession, StudyActivity, Word, Group, 
    WordReviewItem, WordMatchingGame, WordMatchingQuestion, WordMatchingStats,
    FlashcardGame, FlashcardReview, FlashcardStats
)

class WordSerializer(serializers.ModelSerializer):
    correct_count = serializers.SerializerMethodField()
    wrong_count = serializers.SerializerMethodField()

    class Meta:
        model = Word
        fields = ['id', 'urdu', 'urdlish', 'english', 'parts', 'correct_count', 'wrong_count']

    def get_correct_count(self, obj):
        return obj.wordreviewitem_set.filter(correct=True).count()

    def get_wrong_count(self, obj):
        return obj.wordreviewitem_set.filter(correct=False).count()

class GroupSerializer(serializers.ModelSerializer):
    word_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'word_count', 'created_at']
        
    def get_word_count(self, obj):
        return obj.words.count()

class StudyActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyActivity
        fields = ['id', 'name', 'url', 'thumbnail_url', 'description', 'created_at']

class StudySessionSerializer(serializers.ModelSerializer):
    activity_name = serializers.CharField(source='study_activity.name')
    group_name = serializers.CharField(source='group.name')
    review_items_count = serializers.SerializerMethodField()

    class Meta:
        model = StudySession
        fields = ['id', 'activity_name', 'group_name', 'start_time', 'end_time', 'review_items_count']

    def get_review_items_count(self, obj):
        return obj.wordreviewitem_set.count()

class StudySessionListSerializer(serializers.ModelSerializer):
    review_items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = StudySession
        fields = ['id', 'start_time', 'end_time', 'review_items_count']

    def get_review_items_count(self, obj):
        return obj.wordreviewitem_set.count()

class WordReviewItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordReviewItem
        fields = ['id', 'word', 'study_session', 'correct', 'created_at']

class WordMatchingQuestionSerializer(serializers.ModelSerializer):
    word_urdu = serializers.CharField(source='word.urdu', read_only=True)
    word_urdlish = serializers.CharField(source='word.urdlish', read_only=True)
    word_english = serializers.CharField(source='word.english', read_only=True)
    
    class Meta:
        model = WordMatchingQuestion
        fields = ['id', 'word_urdu', 'word_urdlish', 'word_english', 'selected_answer', 'is_correct', 'response_time']

class WordMatchingGameSerializer(serializers.ModelSerializer):
    questions = WordMatchingQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = WordMatchingGame
        fields = ['id', 'user', 'score', 'max_streak', 'total_questions', 'correct_answers',
                 'start_time', 'end_time', 'completed', 'questions']

class FlashcardReviewSerializer(serializers.ModelSerializer):
    word = WordSerializer()
    
    class Meta:
        model = FlashcardReview
        fields = ['id', 'game', 'word', 'confidence_level', 'time_spent', 'created_at']

class FlashcardGameSerializer(serializers.ModelSerializer):
    reviews = FlashcardReviewSerializer(many=True)
    
    class Meta:
        model = FlashcardGame
        fields = [
            'id', 'user', 'score', 'streak', 'max_streak', 
            'total_cards', 'cards_reviewed', 'start_time', 
            'end_time', 'completed', 'reviews'
        ]

class FlashcardStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlashcardStats
        fields = [
            'id', 'user', 'cards_reviewed', 'total_time_spent',
            'best_streak', 'last_reviewed', 'average_time_per_card'
        ]

class WordMatchingStatsSerializer(serializers.ModelSerializer):
    accuracy = serializers.FloatField(read_only=True)
    average_score = serializers.FloatField(read_only=True)
    
    class Meta:
        model = WordMatchingStats
        fields = ['user', 'games_played', 'total_score', 'best_score', 'total_correct',
                 'total_questions', 'last_played', 'accuracy', 'average_score']
