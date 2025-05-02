from django.db import models
from certifications.models import Certification

class Quiz(models.Model):
    certification = models.ForeignKey(Certification, on_delete=models.CASCADE, related_name="quizzes")
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    question_text = models.TextField()
    options = models.JSONField()
    correct_answer = models.CharField(max_length=255)

    def __str__(self):
        return f"Question: {self.question_text[:30]}..."
