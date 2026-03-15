from django.db import models
from certifications.models import Certification
from django.conf import settings
from django.utils import timezone
import datetime

# Create your models here.


class Flashcard(models.Model):
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE, related_name="flashcards")
    front_text = models.TextField()
    back_text = models.TextField()
    topic = models.CharField(max_length=255, blank=True, null=True)  # optional field
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Flashcard: {self.front_text[:30]}..."

class UserFlashcardProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='flashcard_progress')
    flashcard = models.ForeignKey(Flashcard, on_delete=models.CASCADE)

    # Spaced Repetition System (SRS) fields (SuperMemo-2 algorithm)
    next_review_date = models.DateTimeField(default=timezone.now)
    interval = models.IntegerField(default=0)  # Interval in days
    ease_factor = models.FloatField(default=2.5) # Easiness factor
    repetitions = models.IntegerField(default=0) # Number of successful reps

    class Meta:
        unique_together = ('user', 'flashcard')

    def update_srs(self, quality):
        """
        Update the SRS parameters based on the quality of response.
        quality: 0-5 (0 = blackout, 5 = perfect response)
        """
        if quality < 3:
            self.repetitions = 0
            self.interval = 1
        else:
            if self.repetitions == 0:
                self.interval = 1
            elif self.repetitions == 1:
                self.interval = 6
            else:
                self.interval = int(round(self.interval * self.ease_factor))
            self.repetitions += 1

        self.ease_factor = self.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        if self.ease_factor < 1.3:
            self.ease_factor = 1.3

        self.next_review_date = timezone.now() + datetime.timedelta(days=self.interval)
        self.save()
