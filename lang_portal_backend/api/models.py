from django.db import models
from django.utils import timezone

class Word(models.Model):
    urdu = models.TextField(null=False)
    urdlish = models.TextField(null=False)
    english = models.TextField(null=False)
    parts = models.TextField(null=True)
    difficulty_level = models.IntegerField(default=1)
    usage_frequency = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.english} ({self.urdu})"

class Group(models.Model):
    name = models.TextField(null=False, unique=True)
    word_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    words = models.ManyToManyField(Word, through='WordGroup')

    def __str__(self):
        return self.name

class WordGroup(models.Model):
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('word', 'group')

class StudyActivity(models.Model):
    name = models.TextField(null=False, unique=True)
    url = models.TextField(null=True)
    thumbnail_url = models.TextField(null=True)
    description = models.TextField(null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class StudySession(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    study_activity = models.ForeignKey(StudyActivity, on_delete=models.CASCADE)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True)

class WordReviewItem(models.Model):
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    study_session = models.ForeignKey(StudySession, on_delete=models.CASCADE)
    correct = models.BooleanField(null=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('study_session', 'word')

class WordMatchingGame(models.Model):
    user = models.TextField(null=False)  # We'll add proper user auth later
    score = models.IntegerField(default=0)
    max_streak = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=10)
    correct_answers = models.IntegerField(default=0)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Game by {self.user} - Score: {self.score}"

class WordMatchingQuestion(models.Model):
    game = models.ForeignKey(WordMatchingGame, on_delete=models.CASCADE, related_name='questions')
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    selected_answer = models.TextField(null=True)
    is_correct = models.BooleanField(null=True)
    response_time = models.IntegerField(null=True)  # Time taken to answer in seconds
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('game', 'word')

    def __str__(self):
        return f"Question: {self.word.urdu}"

class WordMatchingStats(models.Model):
    user = models.TextField(null=False, unique=True)
    games_played = models.IntegerField(default=0)
    total_score = models.IntegerField(default=0)
    best_score = models.IntegerField(default=0)
    total_correct = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    last_played = models.DateTimeField(null=True)

    def __str__(self):
        return f"Stats for {self.user}"

    @property
    def average_score(self):
        return self.total_score / self.games_played if self.games_played > 0 else 0

    @property
    def accuracy(self):
        return (self.total_correct / self.total_questions * 100) if self.total_questions > 0 else 0

class FlashcardGame(models.Model):
    user = models.TextField(null=False)  # We'll add proper user auth later
    score = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)
    max_streak = models.IntegerField(default=0)
    total_cards = models.IntegerField(default=10)
    cards_reviewed = models.IntegerField(default=0)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True)
    completed = models.BooleanField(default=False)
    words = models.ManyToManyField(Word, through='FlashcardReview')

    def __str__(self):
        return f"Flashcard Game by {self.user} - Score: {self.score}"

class FlashcardReview(models.Model):
    game = models.ForeignKey(FlashcardGame, on_delete=models.CASCADE, related_name='reviews')
    word = models.ForeignKey(Word, on_delete=models.CASCADE)
    confidence_level = models.IntegerField(default=0)  # 0-5 scale
    time_spent = models.IntegerField(null=True)  # seconds
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('game', 'word')

    def __str__(self):
        return f"Review of {self.word.urdu} by {self.game.user}"

class FlashcardStats(models.Model):
    user = models.TextField(null=False, unique=True)
    cards_reviewed = models.IntegerField(default=0)
    total_time_spent = models.IntegerField(default=0)  # minutes
    best_streak = models.IntegerField(default=0)
    last_reviewed = models.DateTimeField(null=True)

    def __str__(self):
        return f"Flashcard Stats for {self.user}"

    @property
    def average_time_per_card(self):
        return self.total_time_spent / self.cards_reviewed if self.cards_reviewed > 0 else 0
