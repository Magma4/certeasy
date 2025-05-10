from django.contrib import admin
from .models import Quiz, Question, QuizAttempt

# Register your models here.
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'certification', 'time_limit', 'passing_score', 'created_at')
    list_filter = ('certification', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'certification')
        }),
        ('Quiz Settings', {
            'fields': ('time_limit', 'passing_score')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'order', 'question_text', 'correct_answer')
    list_filter = ('quiz', 'created_at')
    search_fields = ('question_text', 'correct_answer')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Question Details', {
            'fields': ('quiz', 'order', 'question_text')
        }),
        ('Options and Answer', {
            'fields': ('options', 'correct_answer', 'explanation')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'completed', 'start_time', 'end_time')
    list_filter = ('completed', 'quiz', 'start_time')
    search_fields = ('user__username', 'quiz__title')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Attempt Information', {
            'fields': ('user', 'quiz', 'completed', 'score')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time')
        }),
        ('Answers', {
            'fields': ('answers',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'quiz')
