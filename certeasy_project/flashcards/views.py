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

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import UserFlashcardProgress, Flashcard
from datetime import timedelta
from django.utils import timezone
import json

@login_required
@require_POST
def update_flashcard_progress(request):
    try:
        data = json.loads(request.body)
        flashcard_id = data.get('flashcard_id')
        difficulty = data.get('difficulty') # 'easy', 'medium', 'hard'

        flashcard = Flashcard.objects.get(id=flashcard_id)
        progress, created = UserFlashcardProgress.objects.get_or_create(
            user=request.user,
            flashcard=flashcard
        )

        # Basic SM-2 algorithm adaptation
        if difficulty == 'easy':
            progress.ease_factor += 0.15
            progress.interval = max(1, progress.interval * progress.ease_factor)
        elif difficulty == 'medium':
            progress.interval = max(1, progress.interval * 1.2)
        elif difficulty == 'hard':
            progress.ease_factor = max(1.3, progress.ease_factor - 0.20)
            progress.interval = 1 # reset to 1 day
        else:
            return JsonResponse({'success': False, 'message': 'Invalid difficulty'}, status=400)

        progress.next_review_date = timezone.now().date() + timedelta(days=int(progress.interval))
        progress.save()

        return JsonResponse({'success': True, 'next_review': str(progress.next_review_date)})
    except Flashcard.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Flashcard not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
