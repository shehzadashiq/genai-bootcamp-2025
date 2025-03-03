import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lang_portal_backend.settings')
django.setup()

from api.models import StudyActivity, Group, Word, WordGroup

# Check StudyActivity
print("\nChecking StudyActivity...")
activities = StudyActivity.objects.all()
print(f"Total activities: {activities.count()}")
for activity in activities:
    print(f"- {activity.name}")

# Check Groups and Words
print("\nChecking Groups...")
groups = Group.objects.all()
print(f"Total groups: {groups.count()}")
for group in groups:
    word_count = Word.objects.filter(wordgroup__group=group).count()
    print(f"- {group.name}: {word_count} words")
