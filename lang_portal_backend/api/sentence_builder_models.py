from django.db import models

class WordCategory(models.Model):
    """Model for word categories (parts of speech)"""
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Word Categories"

class SentenceWord(models.Model):
    """Model for Urdu words with their categories and translations"""
    urdu_word = models.CharField(max_length=100)
    roman_urdu = models.CharField(max_length=100, blank=True, null=True)
    english_translation = models.CharField(max_length=100)
    category = models.ForeignKey(WordCategory, on_delete=models.CASCADE, related_name='words')
    difficulty_level = models.IntegerField(default=1)  # 1: Beginner, 2: Intermediate, 3: Advanced
    
    def __str__(self):
        return f"{self.urdu_word} ({self.english_translation})"

class SentencePattern(models.Model):
    """Model for valid sentence patterns"""
    pattern = models.CharField(max_length=255)  # e.g., "subject verb object"
    description = models.TextField(blank=True, null=True)
    example = models.TextField(blank=True, null=True)
    difficulty_level = models.IntegerField(default=1)  # 1: Beginner, 2: Intermediate, 3: Advanced
    
    def __str__(self):
        return self.pattern

class UserSentence(models.Model):
    """Model to store user-created sentences"""
    sentence = models.TextField()
    is_valid = models.BooleanField(default=False)
    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    pattern = models.ForeignKey(SentencePattern, on_delete=models.SET_NULL, null=True, blank=True)
    user_id = models.CharField(max_length=100, blank=True, null=True)  # To track user sessions
    
    def __str__(self):
        return self.sentence
