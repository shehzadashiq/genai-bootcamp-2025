import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.utils import timezone
from datetime import timedelta

from internal.models.models import (
    Word,
    Group,
    StudySession,
    StudyActivity,
    WordReviewItem,
    WordGroup,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def sample_word():
    return Word.objects.create(
        urdu="سلام",
        urdlish="salaam",
        english="hello",
        parts={
            "pos": ["interjection"],
            "categories": ["common", "greetings"],
            "difficulty": "beginner",
        },
    )


@pytest.fixture
def sample_group():
    return Group.objects.create(name="Basic Words")


@pytest.fixture
def sample_study_activity():
    return StudyActivity.objects.create(
        name="Vocabulary Review",
        thumbnail_url="https://example.com/thumb.jpg",
        description="Review vocabulary words",
    )


@pytest.fixture
def sample_study_session(sample_group, sample_study_activity):
    return StudySession.objects.create(
        group=sample_group, study_activity=sample_study_activity
    )


@pytest.fixture
def sample_word_review(sample_word, sample_study_session):
    return WordReviewItem.objects.create(
        word=sample_word,
        study_session=sample_study_session,
        correct=True,
    )


@pytest.mark.django_db
class TestDashboardEndpoints:
    def test_quick_stats(self, api_client, sample_word_review):
        url = reverse("dashboard-quick-stats")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "success_rate" in response.data
        assert "total_study_sessions" in response.data
        assert "total_active_groups" in response.data
        assert "study_streak_days" in response.data

    def test_last_study_session(self, api_client, sample_study_session):
        url = reverse("dashboard-last-study-session")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == sample_study_session.id
        assert response.data["group_id"] == sample_study_session.group.id

    def test_study_progress(self, api_client, sample_word_review):
        url = reverse("dashboard-study-progress")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_words_studied"] == 1
        assert response.data["total_available_words"] == 1


@pytest.mark.django_db
class TestWordEndpoints:
    def test_list_words(self, api_client, sample_word):
        url = reverse("word-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["english"] == sample_word.english

    def test_create_word(self, api_client):
        url = reverse("word-list")
        data = {
            "urdu": "کتاب",
            "urdlish": "kitaab",
            "english": "book",
            "parts": {
                "pos": ["noun"],
                "categories": ["common", "objects"],
                "difficulty": "beginner",
            },
        }
        response = api_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Word.objects.count() == 1
        assert Word.objects.first().english == "book"

    def test_retrieve_word(self, api_client, sample_word):
        url = reverse("word-detail", kwargs={"pk": sample_word.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["english"] == sample_word.english


@pytest.mark.django_db
class TestGroupEndpoints:
    def test_list_groups(self, api_client, sample_group):
        url = reverse("group-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == sample_group.name

    def test_create_group(self, api_client):
        url = reverse("group-list")
        data = {"name": "Advanced Words"}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert Group.objects.count() == 1
        assert Group.objects.first().name == "Advanced Words"

    def test_group_words(self, api_client, sample_group, sample_word):
        WordGroup.objects.create(word=sample_word, group=sample_group)
        url = reverse("group-words", kwargs={"pk": sample_group.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["english"] == sample_word.english


@pytest.mark.django_db
class TestStudySessionEndpoints:
    def test_start_session(self, api_client, sample_group, sample_study_activity):
        url = reverse("studyactivity-start-session")
        data = {
            "group_id": sample_group.id,
            "study_activity_id": sample_study_activity.id,
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert "id" in response.data
        assert StudySession.objects.count() == 1

    def test_review_word(self, api_client, sample_study_session, sample_word):
        url = reverse(
            "studysession-review-word", kwargs={"pk": sample_study_session.id}
        )
        data = {"word_id": sample_word.id, "correct": True}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["correct"] == True
        assert WordReviewItem.objects.count() == 1


@pytest.mark.django_db
class TestSystemManagement:
    def test_reset_history(self, api_client, sample_word_review):
        assert WordReviewItem.objects.count() == 1
        url = reverse("reset_history")
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert WordReviewItem.objects.count() == 0
        assert StudySession.objects.count() == 0

    def test_full_reset(
        self, api_client, sample_word, sample_group, sample_word_review
    ):
        assert Word.objects.count() == 1
        assert Group.objects.count() == 1
        url = reverse("full_reset")
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert Word.objects.count() == 0
        assert Group.objects.count() == 0
