from django.db import models
from django.conf import settings
from certifications.models import Certification

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="flashcard_progress")
    flashcard = models.ForeignKey(Flashcard, on_delete=models.CASCADE, related_name="progress")
    ease_factor = models.FloatField(default=2.5)
    interval = models.IntegerField(default=0)  # in days
    next_review_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.flashcard.id} - {self.next_review_date}"
