from django.urls import path
from .views import FlashcardListCreateView, FlashcardDetailView

from .views import FlashcardListCreateView, FlashcardDetailView, update_flashcard_progress

urlpatterns = [
    path('', FlashcardListCreateView.as_view(), name='flashcard-list-create'),
    path('<int:pk>/', FlashcardDetailView.as_view(), name='flashcard-detail'),
    path('update-progress/', update_flashcard_progress, name='update_flashcard_progress'),
]
