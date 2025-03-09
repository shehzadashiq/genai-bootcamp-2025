from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import StudyActivity, Group, Word, StudySession, WordGroup, WordReviewItem
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Seeds the database with initial data'

    def handle(self, *args, **options):
        # Create study activities
        study_activities = [
            {
                'name': 'Vocabulary Quiz',
                'description': 'Test your knowledge with a vocabulary quiz',
                'thumbnail_url': '/images/vocab-quiz.png',
                'url': '/apps/vocabulary-quiz'
            },
            {
                'name': 'Flashcards',
                'description': 'Practice with digital flashcards',
                'thumbnail_url': '/images/flashcards.png',
                'url': '/apps/flashcards'
            },
            {
                'name': 'Word Matching',
                'description': 'Match Urdu words with their English translations',
                'thumbnail_url': '/images/word-matching.png',
                'url': '/apps/word-matching'
            },
            {
                'name': 'Sentence Builder',
                'description': 'Create sentences using learned vocabulary',
                'thumbnail_url': '/images/sentence-builder.png',
                'url': '/apps/sentence-builder'
            }
        ]

        created_study_activities = []
        for activity_data in study_activities:
            activity, created = StudyActivity.objects.get_or_create(
                name=activity_data['name'],
                defaults={
                    'description': activity_data['description'],
                    'thumbnail_url': activity_data['thumbnail_url'],
                    'url': activity_data['url']
                }
            )
            created_study_activities.append(activity)
            if created:
                self.stdout.write(f'Created study activity: {activity_data["name"]}')

        # Create groups if they don't exist
        groups = [
            'Beginner Urdu',
            'Intermediate Urdu',
            'Advanced Urdu'
        ]

        created_groups = []
        for group_name in groups:
            group, created = Group.objects.get_or_create(
                name=group_name
            )
            created_groups.append(group)
            if created:
                self.stdout.write(f'Created group: {group_name}')

        # Create some words if they don't exist
        words = [
            ('سلام', 'salaam', 'hello'),
            ('شکریہ', 'shukriya', 'thank you'),
            ('خدا حافظ', 'khuda hafiz', 'goodbye'),
            ('کیا حال ہے', 'kya haal hai', 'how are you'),
            ('میرا نام', 'mera naam', 'my name'),
            ('آپ کا نام', 'aap ka naam', 'your name'),
            ('کھانا', 'khana', 'food'),
            ('پانی', 'pani', 'water'),
            ('گھر', 'ghar', 'house'),
            ('کتاب', 'kitaab', 'book')
        ]

        created_words = []
        for urdu, urdlish, english in words:
            word, created = Word.objects.get_or_create(
                urdu=urdu,
                urdlish=urdlish,
                english=english
            )
            created_words.append(word)
            if created:
                self.stdout.write(f'Created word: {english}')

        # Assign words to groups
        for group in created_groups:
            # Assign 5-8 random words to each group
            num_words = random.randint(5, 8)
            selected_words = random.sample(created_words, num_words)

            for word in selected_words:
                WordGroup.objects.get_or_create(
                    word=word,
                    group=group
                )

        # Create some study sessions with word reviews
        now = timezone.now()
        for _ in range(10):  # Create 10 study sessions over the past week
            # Random activity and group
            activity = random.choice(created_study_activities)
            group = random.choice(created_groups)

            # Random time in the past week
            random_hours = random.randint(0, 24 * 7)  # Up to 7 days ago
            start_time = now - timedelta(hours=random_hours)
            end_time = start_time + timedelta(minutes=random.randint(15, 60))

            # Create session
            session = StudySession.objects.create(
                study_activity=activity,
                group=group,
                start_time=start_time,
                end_time=end_time
            )

            # Get words from the group
            group_words = Word.objects.filter(wordgroup__group=group)

            # Create some word reviews
            for word in random.sample(list(group_words), random.randint(3, 6)):
                WordReviewItem.objects.create(
                    word=word,
                    study_session=session,
                    correct=random.choice([True, True, False])  # 66% chance of correct
                )

        self.stdout.write(self.style.SUCCESS('Successfully seeded database'))
