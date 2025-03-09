from rest_framework import serializers
from .models import StudySession, StudyActivity, Word, Group, WordReviewItem

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
        fields = ['id', 'created_at', 'review_items_count']

    def get_review_items_count(self, obj):
        return obj.wordreviewitem_set.count()

class WordReviewItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordReviewItem
        fields = ['id', 'word', 'study_session', 'correct', 'created_at']
