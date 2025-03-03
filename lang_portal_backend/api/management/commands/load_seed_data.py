import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Word, Group, StudyActivity, WordGroup

class Command(BaseCommand):
    help = 'Load seed data from JSON files'

    def handle(self, *args, **kwargs):
        seed_dir = os.path.join('db', 'seeds')
        
        # Load study activities
        self.stdout.write('Loading study activities...')
        with open(os.path.join(seed_dir, 'study_activities.json'), 'r', encoding='utf-8') as f:
            activities = json.load(f)
            for activity in activities:
                StudyActivity.objects.get_or_create(
                    id=activity['id'],
                    defaults={
                        'name': activity['name'],
                        'url': activity['url'],
                        'thumbnail_url': activity['thumbnail_url'],
                        'description': activity['description']
                    }
                )
        
        # Load word groups and their words
        self.stdout.write('Loading word groups and their words...')
        with transaction.atomic():
            with open(os.path.join(seed_dir, 'word_groups.json'), 'r', encoding='utf-8') as f:
                groups = json.load(f)
                for group_data in groups:
                    # Create group
                    group, created = Group.objects.get_or_create(
                        name=group_data['name'],
                        defaults={
                            'word_count': len(group_data['words'])
                        }
                    )
                    
                    # Create words and associate them with the group
                    for word_data in group_data['words']:
                        word, created = Word.objects.get_or_create(
                            urdu=word_data['urdu'],
                            urdlish=word_data['urdlish'],
                            english=word_data['english'],
                            defaults={
                                'parts': word_data.get('parts')
                            }
                        )
                        
                        # Associate word with group
                        WordGroup.objects.get_or_create(
                            word=word,
                            group=group
                        )
        
        # Load additional basic words
        self.stdout.write('Loading basic words...')
        try:
            with open(os.path.join(seed_dir, 'basic_words.json'), 'r', encoding='utf-8') as f:
                words = json.load(f)
                with transaction.atomic():
                    for word_data in words:
                        word, created = Word.objects.get_or_create(
                            urdu=word_data['urdu'],
                            urdlish=word_data['urdlish'],
                            english=word_data['english'],
                            defaults={
                                'parts': word_data.get('parts')
                            }
                        )
                        
                        # Add word to groups if specified
                        if 'group_ids' in word_data:
                            for group_id in word_data['group_ids']:
                                try:
                                    group = Group.objects.get(id=group_id)
                                    WordGroup.objects.get_or_create(
                                        word=word,
                                        group=group
                                    )
                                except Group.DoesNotExist:
                                    self.stdout.write(f'Group {group_id} not found for word {word.english}')
        except FileNotFoundError:
            self.stdout.write('No basic_words.json file found, skipping...')
        
        # Load common phrases
        self.stdout.write('Loading common phrases...')
        try:
            with open(os.path.join(seed_dir, 'common_phrases.json'), 'r', encoding='utf-8') as f:
                phrases = json.load(f)
                for phrase in phrases:
                    Word.objects.get_or_create(
                        urdu=phrase['urdu'],
                        urdlish=phrase['urdlish'],
                        english=phrase['english'],
                        defaults={
                            'parts': phrase.get('parts', 'phrase')
                        }
                    )
        except FileNotFoundError:
            self.stdout.write('No common phrases file found, skipping...')
        
        self.stdout.write(self.style.SUCCESS('Successfully loaded all seed data'))
