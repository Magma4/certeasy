from django.db import models
from django.conf import settings
from django.utils import timezone
from certifications.models import Certification

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(default="")  # Empty string as default
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE, related_name='quizzes')
    time_limit = models.IntegerField(default=1800)  # Time limit in seconds (default 30 minutes)
    passing_score = models.IntegerField(default=70)  # Passing score percentage
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.certification.title}"

    class Meta:
        ordering = ['-created_at']

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    options = models.JSONField()  # Store options as a JSON array
    correct_answer = models.CharField(max_length=500)
    explanation = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Question {self.order} - {self.quiz.title}"

class QuizAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    answers = models.JSONField(default=dict)  # Store user's answers as JSON
    created_at = models.DateTimeField(auto_now_add=True)
    user_answers = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-start_time']

    @property
    def attempt_date(self):
        return self.start_time

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} - {self.attempt_date}"
