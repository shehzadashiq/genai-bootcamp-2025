from rest_framework import serializers
from .sentence_builder_models import WordCategory, SentenceWord, SentencePattern, UserSentence

class WordCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WordCategory
        fields = '__all__'

class SentenceWordSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = SentenceWord
        fields = ['id', 'urdu_word', 'roman_urdu', 'english_translation', 'category', 'category_name', 'difficulty_level']

class SentencePatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = SentencePattern
        fields = '__all__'

class UserSentenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSentence
        fields = '__all__'
        read_only_fields = ['is_valid', 'feedback', 'created_at']

class WordsByCategorySerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    category_name = serializers.CharField()
    words = SentenceWordSerializer(many=True)
