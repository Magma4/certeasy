from django.db import models
from certifications.models import Certification

# Create your models here.
class Resource(models.Model):
    RESOURCE_TYPES = [
        ('pdf', 'PDF'),
        ('video', 'Video'),
        ('quiz', 'Quiz'),
        ('flashcard', 'Flashcard'),
    ]

    certification = models.ForeignKey(Certification, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='resources/', blank=True, null=True)
    type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    created_by_ai = models.BooleanField(default=False)

    def __str__(self):
        return self.title
