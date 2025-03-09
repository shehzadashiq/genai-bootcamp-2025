from django.db import models
from django.utils import timezone

class Word(models.Model):
    urdu = models.TextField(null=False)
    urdlish = models.TextField(null=False)
    english = models.TextField(null=False)
    parts = models.TextField(null=True)
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
