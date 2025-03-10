from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from api.models import StudyActivity, Group, Word, StudySession, WordGroup, WordReviewItem
import random
from datetime import timedelta
import json
import os

class Command(BaseCommand):
    help = 'Seeds the database with initial data'

    def _load_json_file(self, filename):
        """Helper to load JSON file from seeds directory"""
        json_file_path = os.path.join('db', 'seeds', filename)
        with open(json_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def handle(self, *args, **options):
        try:
            # Create study activities from JSON
            with transaction.atomic():
                study_activities_data = self._load_json_file('study_activities.json')
                created_study_activities = []
                
                for activity_data in study_activities_data:
                    activity, created = StudyActivity.objects.get_or_create(
                        name=activity_data['name'],
                        defaults={
                            'description': activity_data.get('description', ''),
                            'thumbnail_url': activity_data.get('thumbnail_url', ''),
                            'url': activity_data.get('url', '')
                        }
                    )
                    created_study_activities.append(activity)
                    if created:
                        self.stdout.write(f'Created study activity: {activity_data["name"]}')

            # Create word groups from JSON
            with transaction.atomic():
                word_groups_data = self._load_json_file('word_groups.json')
                created_groups = []
                
                for group_data in word_groups_data:
                    group, created = Group.objects.get_or_create(
                        name=group_data['name']
                    )
                    created_groups.append(group)
                    if created:
                        self.stdout.write(f'Created group: {group_data["name"]}')

            # Dictionary to track unique words by their Urdu text
            unique_words = {}

            # Load and create basic words from JSON
            with transaction.atomic():
                basic_words_data = self._load_json_file('basic_words.json')
                
                for word_data in basic_words_data:
                    word, created = Word.objects.get_or_create(
                        urdu=word_data['urdu'],
                        urdlish=word_data['urdlish'],
                        english=word_data['english'],
                        defaults={
                            'parts': json.dumps(word_data.get('parts', {}))
                        }
                    )
                    unique_words[word.urdu] = word
                    if created:
                        self.stdout.write(f'Created basic word: {word_data["english"]}')

            # Load and create common phrases from JSON
            with transaction.atomic():
                common_phrases_data = self._load_json_file('common_phrases.json')
                
                for phrase_data in common_phrases_data:
                    word, created = Word.objects.get_or_create(
                        urdu=phrase_data['urdu'],
                        urdlish=phrase_data['urdlish'],
                        english=phrase_data['english'],
                        defaults={
                            'parts': json.dumps(phrase_data.get('parts', {}))
                        }
                    )
                    unique_words[word.urdu] = word
                    if created:
                        self.stdout.write(f'Created common phrase: {phrase_data["english"]}')

            # Convert unique words dictionary to list
            created_words = list(unique_words.values())

            # Clear existing word-group assignments
            with transaction.atomic():
                WordGroup.objects.all().delete()
                self.stdout.write('Cleared existing word-group assignments')

            # Distribute words across groups based on complexity
            # Sort words by complexity (using length as a simple metric)
            sorted_words = sorted(created_words, key=lambda w: len(w.urdu))
            words_per_group = len(sorted_words) // len(created_groups)
            remaining_words = len(sorted_words) % len(created_groups)

            start_idx = 0
            for i, group in enumerate(created_groups):
                try:
                    with transaction.atomic():
                        # Calculate number of words for this group
                        extra_word = 1 if i < remaining_words else 0
                        group_word_count = words_per_group + extra_word
                        
                        # Get words for this group
                        group_words = sorted_words[start_idx:start_idx + group_word_count]
                        start_idx += group_word_count

                        # Create WordGroup entries
                        for word in group_words:
                            WordGroup.objects.create(
                                word=word,
                                group=group
                            )
                        
                        # Update word count
                        group.word_count = len(group_words)
                        group.save()
                        
                        self.stdout.write(f'Assigned {len(group_words)} words to group: {group.name}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Error assigning words to group {group.name}: {str(e)}'))

            # Create sample study sessions
            now = timezone.now()
            for i in range(10):  # Create 10 study sessions over the past week
                try:
                    with transaction.atomic():
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
                        if group_words.exists():
                            # Create some word reviews
                            word_list = list(group_words)
                            num_reviews = min(random.randint(3, 6), len(word_list))
                            for word in random.sample(word_list, num_reviews):
                                WordReviewItem.objects.create(
                                    word=word,
                                    study_session=session,
                                    correct=random.choice([True, True, False])  # 66% chance of correct
                                )
                        self.stdout.write(f'Created study session {i+1}/10')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Error creating study session {i+1}: {str(e)}'))

            self.stdout.write(self.style.SUCCESS('Successfully seeded database'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error seeding database: {str(e)}'))
            raise
