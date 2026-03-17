from django.urls import path
from .views import FlashcardListCreateView, FlashcardDetailView, get_due_flashcards, submit_flashcard_review, export_flashcards

urlpatterns = [
    path('', FlashcardListCreateView.as_view(), name='flashcard-list-create'),
    path('<int:pk>/', FlashcardDetailView.as_view(), name='flashcard-detail'),
    path('due/', get_due_flashcards, name='flashcards-due'),
    path('<int:pk>/review/', submit_flashcard_review, name='flashcard-review'),
    path('export/', export_flashcards, name='flashcards-export'),
]
