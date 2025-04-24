from rest_framework import generics
from .models import Quiz
from .serializers import QuizSerializer
from rest_framework.permissions import IsAuthenticated

class QuizListCreateView(generics.ListCreateAPIView):
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        certification_id = self.request.query_params.get('certification_id')
        if certification_id:
            return Quiz.objects.filter(certification_id=certification_id)
        return Quiz.objects.all()


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
