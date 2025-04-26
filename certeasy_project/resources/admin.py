from django.contrib import admin
from .models import Resource

# Register your models here.
@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'certification', 'type', 'created_by_ai')
    list_filter = ('certification', 'type', 'created_by_ai')
