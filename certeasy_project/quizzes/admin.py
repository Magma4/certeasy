from django.contrib import admin
from .models import Quiz,  Question

# Register your models here.
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('certification', 'title', 'created_at')
    list_filter = ('certification', 'title')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'question_text', 'options', 'correct_answer')
    list_filter = ('quiz', 'question_text', 'options', 'correct_answer' )
