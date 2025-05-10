from django.db import models
from certifications.models import Certification
from django.conf import settings

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
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']

class VideoView(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    watched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'resource')
