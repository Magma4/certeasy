from rest_framework import generics, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from .models import Flashcard, UserFlashcardProgress
from .serializers import FlashcardSerializer
from django.utils import timezone


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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_due_flashcards(request):
    # Fetch all flashcards
    all_cards = Flashcard.objects.all()
    due_cards = []

    for card in all_cards:
        progress, created = UserFlashcardProgress.objects.get_or_create(user=request.user, flashcard=card)
        if progress.next_review_date <= timezone.now():
            due_cards.append(card)

    serializer = FlashcardSerializer(due_cards, many=True)
    return Response(serializer.data)

import csv
from django.http import HttpResponse

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_flashcards(request):
    cert_id = request.GET.get('cert_id')
    if cert_id:
        flashcards = Flashcard.objects.filter(certification_id=cert_id)
    else:
        flashcards = Flashcard.objects.all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="flashcards.csv"'

    writer = csv.writer(response)
    writer.writerow(['Front Text (Question)', 'Back Text (Answer)', 'Topic', 'Certification'])

    for card in flashcards:
        writer.writerow([card.front_text, card.back_text, card.topic, card.certification.title])

    return response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_flashcard_review(request, pk):
    try:
        flashcard = Flashcard.objects.get(pk=pk)
    except Flashcard.DoesNotExist:
        return Response({'error': 'Flashcard not found'}, status=404)

    quality = request.data.get('quality')
    if quality is None:
        return Response({'error': 'Quality rating is required'}, status=400)

    try:
        quality = int(quality)
        if quality < 0 or quality > 5:
            raise ValueError()
    except ValueError:
        return Response({'error': 'Quality must be an integer between 0 and 5'}, status=400)

    progress, created = UserFlashcardProgress.objects.get_or_create(user=request.user, flashcard=flashcard)
    progress.update_srs(quality)

    return Response({
        'success': True,
        'next_review_date': progress.next_review_date,
        'interval': progress.interval,
        'ease_factor': progress.ease_factor
    })
