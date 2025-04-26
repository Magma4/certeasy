from django.contrib import admin
from .models import Flashcard

# Register your models here.
@admin.register(Flashcard)
class FlashcardAdmin(admin.ModelAdmin):
    list_display = ('certification', 'front_text', 'back_text', 'topic', 'created_at')
    list_filter = ('certification', 'topic', 'created_at')
