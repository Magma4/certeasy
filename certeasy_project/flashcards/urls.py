from django.urls import path
from .views import FlashcardListCreateView, FlashcardDetailView

urlpatterns = [
    path('', FlashcardListCreateView.as_view(), name='flashcard-list-create'),
    path('<int:pk>/', FlashcardDetailView.as_view(), name='flashcard-detail'),
]
