from django.db import models
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
