from django.db import models
from django.contrib.auth.models import User
from certifications.models import Certification
from quizzes.models import Quiz
from resources.models import Resource
from flashcards.models import FlashcardSet

class StudyPlan(models.Model):
    ACTIVITY_TYPES = [
        ('quiz', 'Quiz'),
        ('resource', 'Resource'),
        ('flashcard', 'Flashcards'),
        ('exam', 'Exam'),
    ]

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_plans')
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE, related_name='study_plans')
    title = models.CharField(max_length=200)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    duration = models.IntegerField(help_text='Duration in minutes')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    # Optional related content
    quiz = models.ForeignKey(Quiz, on_delete=models.SET_NULL, null=True, blank=True)
    resource = models.ForeignKey(Resource, on_delete=models.SET_NULL, null=True, blank=True)
    flashcard_set = models.ForeignKey(FlashcardSet, on_delete=models.SET_NULL, null=True, blank=True)

    # For exam scheduling
    exam_date = models.DateField(null=True, blank=True)
    exam_time = models.TimeField(null=True, blank=True)
    exam_location = models.CharField(max_length=200, null=True, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['scheduled_date', 'scheduled_time']
        indexes = [
            models.Index(fields=['user', 'scheduled_date']),
            models.Index(fields=['certification', 'activity_type']),
        ]

    def __str__(self):
        return f"{self.user.username}'s {self.activity_type} - {self.title}"

    def get_duration_display(self):
        hours = self.duration // 60
        minutes = self.duration % 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
