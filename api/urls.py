from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'flashcards', views.FlashcardViewSet, basename='flashcard')

urlpatterns = [
    path('', include(router.urls)),
    path('flashcards/stats/', views.FlashcardStatsView.as_view(), name='flashcard-stats'),
]
