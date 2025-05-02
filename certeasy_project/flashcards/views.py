from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from .models import Flashcard
from .serializers import FlashcardSerializer


class FlashcardListCreateView(generics.ListCreateAPIView):
    queryset = Flashcard.objects.all()
    serializer_class = FlashcardSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['front_text', 'back_text', 'topic']
    filterset_fields = ['certification', 'topic']
    ordering_fields = ['created_at']

    def get_queryset(self):
        return Flashcard.objects.all()

class FlashcardDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Flashcard.objects.all()
    serializer_class = FlashcardSerializer
