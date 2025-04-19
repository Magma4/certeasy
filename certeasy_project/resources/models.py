from django.db import models
from certifications.models import Certification

# Create your models here.
class Resource(models.Model):
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='resources/')
    resource_type = models.CharField(max_length=50, choices=[('pdf', 'PDF'), ('video', 'Video'), ('image', 'Image')])
