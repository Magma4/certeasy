from django.contrib import admin
from .models import Resource

# Register your models here.
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'certification', 'type', 'created_by_ai')
    list_filter = ('type', 'created_by_ai')
