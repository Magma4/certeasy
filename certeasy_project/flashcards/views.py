from rest_framework import generics
from .models import Flashcard
from .serializers import FlashcardSerializer
from rest_framework.permissions import IsAuthenticated


class FlashcardListCreateView(generics.ListCreateAPIView):

    serializer_class = FlashcardSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        certification_id = self.request.query_params.get('certification_id')
        if certification_id:
            return Flashcard.objects.filter(certification_id=certification_id)
        return Flashcard.objects.all()

class FlashcardDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Flashcard.objects.all()
    serializer_class = FlashcardSerializer
