from rest_framework import generics
from .models import Quiz
from .serializers import QuizSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend

class QuizListCreateView(generics.ListCreateAPIView):
    queryset = Quiz.objects.all() 
    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title']
    filterset_fields = ['certification']
    ordering_fields = ['created_at']


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
